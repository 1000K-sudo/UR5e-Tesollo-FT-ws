#!/usr/bin/env python3
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
"""
test_onrobot_ft.py
==================
Standalone live acquisition test for the OnRobot HEX-E v2 force/torque sensor
connected via EtherCAT on the TP-Link UE300 USB adapter (enxe4fac4b94578).

Calculates and displays real-time 3-axis forces (Fx, Fy, Fz), torques (Tx, Ty, Tz)
and vector norms (total force ||F|| and total torque ||T||).

No ROS 2 required.

Usage
-----
    sudo python3 test_onrobot_ft.py
    sudo python3 test_onrobot_ft.py --iface enxe4fac4b94578 --rate 100 --tare-samples 200
    sudo python3 test_onrobot_ft.py --iface enxe4fac4b94578 --no-tare

Requirements
------------
    pip install pysoem

The script needs raw socket access.  Either run with sudo or grant capability:
    sudo setcap cap_net_raw+ep $(which python3)
"""

import argparse
import csv
from datetime import datetime
import os
import struct
import sys
import time

try:
    import pysoem
except ImportError:
    sys.exit(
        "ERROR: pysoem not found.\n"
        "Install options:\n"
        "  sudo pip3 install pysoem                          # system-wide (preferred for sudo use)\n"
        "  pip3 install --target /opt/pysoem pysoem         # if system pip is read-only\n"
        "    then run with: sudo PYTHONPATH=/opt/pysoem python3 test_onrobot_ft.py\n"
        "\n"
        "The script must be run with root privileges (sudo) or CAP_NET_RAW capability:\n"
        "  sudo python3 test_onrobot_ft.py\n"
        "  sudo setcap cap_net_raw+ep $(which python3)  # then run without sudo"
    )

# ---------------------------------------------------------------------------
# EtherCAT / PDO constants
# ---------------------------------------------------------------------------
IFACE_DEFAULT = "enxe4fac4b94578"   # TP-Link UE300 on this machine
IN_LEN = 56                         # 6×REAL32 + 6×INT32 + INT16 + UINT16 + UINT32
OUT_LEN = 4                         # FILTER(UINT16) + ZERO(UINT16)


# ---------------------------------------------------------------------------
# EtherCAT PDO decode helpers for OnRobot HEX-E v2 (56-byte TxPDO / 4-byte RxPDO)
# ---------------------------------------------------------------------------
def decode_status(u32):
    """Decode the STATUS UDINT bitfield from the sensor PDO."""
    def get(b):
        return (u32 >> b) & 1

    def getf(lo, hi):
        return (u32 >> lo) & ((1 << (hi - lo + 1)) - 1)

    sensor_no = getf(0, 2)
    multi_err = bool(get(3))
    overload = {
        "Tz": bool(get(4)),
        "Ty": bool(get(5)),
        "Tx": bool(get(6)),
        "Fz": bool(get(7)),
        "Fy": bool(get(8)),
        "Fx": bool(get(9)),
    }
    sensor_err_grp = getf(10, 12)
    daq_comm_grp = getf(13, 15)
    calib_missing = bool(get(16))

    sensor_err_txt = {0: "ok", 1: "sensor not detected", 2: "sensor failure"}.get(
        sensor_err_grp, f"code {sensor_err_grp}"
    )
    daq_comm_txt = {0: "ok", 1: "DAQ error", 2: "communication error"}.get(
        daq_comm_grp, f"code {daq_comm_grp}"
    )

    pieces = []
    overload_axes = [k for k, v in overload.items() if v]
    if overload_axes:
        pieces.append("OVERLOAD: " + ",".join(overload_axes))
    if sensor_no != 0:
        pieces.append(f"sensor#{sensor_no}")
    if sensor_err_grp != 0:
        pieces.append(sensor_err_txt)
    if daq_comm_grp != 0:
        pieces.append(daq_comm_txt)
    if calib_missing:
        pieces.append("calibration missing")
    if multi_err:
        pieces.append("multiple errors")

    return {
        "raw": u32,
        "sensor_number": sensor_no,
        "multiple_errors": multi_err,
        "overload": overload,
        "sensor_error_group": sensor_err_grp,
        "daq_comm_error_group": daq_comm_grp,
        "calibration_missing": calib_missing,
        "summary": "OK" if not pieces else "; ".join(pieces),
    }


def unpack_inputs(inp_bytes):
    """Parse the 56-byte TxPDO input frame."""
    if len(inp_bytes) < IN_LEN:
        raise ValueError(f"Expected {IN_LEN} input bytes, got {len(inp_bytes)}")
    off = 0
    fx_r, fy_r, fz_r, tx_r, ty_r, tz_r = struct.unpack_from("<6f", inp_bytes, off)
    off += 24
    fx_i, fy_i, fz_i, tx_i, ty_i, tz_i = struct.unpack_from("<6i", inp_bytes, off)
    off += 24
    (divider,) = struct.unpack_from("<h", inp_bytes, off)
    off += 2
    (sample_counter,) = struct.unpack_from("<H", inp_bytes, off)
    off += 2
    (status_u32,) = struct.unpack_from("<I", inp_bytes, off)
    off += 4

    scaled = (
        {
            "Fx": fx_i / divider, "Fy": fy_i / divider, "Fz": fz_i / divider,
            "Tx": tx_i / divider, "Ty": ty_i / divider, "Tz": tz_i / divider,
        }
        if divider else None
    )

    return {
        "floats": {"Fx": fx_r, "Fy": fy_r, "Fz": fz_r,
                   "Tx": tx_r, "Ty": ty_r, "Tz": tz_r},
        "ints": {"Fx": fx_i, "Fy": fy_i, "Fz": fz_i,
                 "Tx": tx_i, "Ty": ty_i, "Tz": tz_i, "divider": divider},
        "scaled": scaled,
        "sample_counter": sample_counter,
        "status": decode_status(status_u32),
    }


def write_outputs(slave, filter_value=None, zero_cmd=False):
    """Write the 4-byte RxPDO output frame (FILTER + ZERO command)."""
    if slave.output is None or len(slave.output) < OUT_LEN:
        return
    buf = bytearray(slave.output)
    filt = filter_value if filter_value is not None else struct.unpack_from("<H", buf, 0)[0]
    struct.pack_into("<H", buf, 0, int(filt) & 0xFFFF)
    struct.pack_into("<H", buf, 2, 1 if zero_cmd else 0)
    slave.output = bytes(buf)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="OnRobot HEX-E v2 live F/T acquisition test (no ROS 2)"
    )
    ap.add_argument(
        "--iface", default=IFACE_DEFAULT,
        help=f"EtherCAT network interface (default: {IFACE_DEFAULT})"
    )
    ap.add_argument(
        "--rate", type=float, default=100.0,
        help="Display / cyclic rate in Hz (default: 100)"
    )
    ap.add_argument(
        "--duration", type=float, default=0,
        help="Run duration in seconds (0 = run forever, Ctrl-C to stop)"
    )
    ap.add_argument(
        "--tare-samples", type=int, default=100,
        help="Number of samples to average for software tare (default: 100)"
    )
    ap.add_argument(
        "--no-tare", action="store_true",
        help="Skip software tare and display raw values"
    )
    ap.add_argument(
        "--set-filter", type=int, default=None,
        help="Write FILTER value via RxPDO (0=no filter … higher=more filtering)"
    )
    ap.add_argument(
        "--format", choices=["csv", "txt", "npy", "all", "none"], default="csv",
        help="Export file format at session end: csv (default), txt, npy, all, none"
    )
    ap.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "onrobot_ft_recordings"),
        help="Directory to save the recorded files (default: data/onrobot_ft_recordings)"
    )
    ap.add_argument(
        "--prefix", default="OnRobot_force",
        help="Prefix for output file name (default: 'OnRobot_force')"
    )
    args = ap.parse_args()

    period = 1.0 / max(args.rate, 1.0)
    do_tare = not args.no_tare

    # ------------------------------------------------------------------
    print("=" * 70)
    print("  OnRobot HEX-E v2  –  Live F/T Acquisition Test")
    print("=" * 70)
    print(f"  Interface    : {args.iface}")
    print(f"  Rate         : {args.rate:.0f} Hz")
    print(f"  Duration     : {'∞' if args.duration == 0 else f'{args.duration}s'}")
    print(f"  Software tare: {'YES (' + str(args.tare_samples) + ' samples)' if do_tare else 'NO (raw values)'}")
    print(f"  Auto-record  : {args.format.upper() if args.format != 'none' else 'OFF'} -> {args.output_dir}")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Open EtherCAT master
    # ------------------------------------------------------------------
    m = pysoem.Master()
    try:
        m.open(args.iface)
    except Exception as e:
        sys.exit(f"ERROR: Cannot open interface '{args.iface}': {e}\n"
                 "Make sure you run with sudo (or setcap cap_net_raw+ep).")

    try:
        # --- bus scan ---
        n_slaves = m.config_init()
        if n_slaves <= 0:
            sys.exit("ERROR: No EtherCAT slaves found on this interface.\n"
                     "Check cable, power (24 V) and that the interface name is correct.")

        print(f"\nFound {n_slaves} slave(s):")
        for i, s in enumerate(m.slaves):
            try:
                man = s.man
                prod = s.id
                rev = s.rev
            except AttributeError:
                man = s.manufacturer
                prod = s.product_code
                rev = s.revision_number
            print(f"  [slave {i}]  vendor=0x{man:08X}  product=0x{prod:08X}  rev=0x{rev:08X}  name={s.name!r}")

        m.config_map()
        s0 = m.slaves[0]

        if s0.input is not None and len(s0.input) != IN_LEN:
            print(f"  WARNING: expected {IN_LEN} input bytes, device has {len(s0.input)}")
        if s0.output is not None and len(s0.output) != OUT_LEN:
            print(f"  WARNING: expected {OUT_LEN} output bytes, device has {len(s0.output)}")

        # --- bring to OP ---
        m.state = pysoem.OP_STATE
        m.write_state()
        print("\nBringing slaves to OP state ", end="", flush=True)
        for _ in range(300):
            m.send_processdata()
            m.receive_processdata(1000)
            if all(s.state == pysoem.OP_STATE for s in m.slaves):
                break
            time.sleep(0.01)
            print(".", end="", flush=True)
        else:
            print(" WARNING: not all slaves reached OP, continuing anyway.")
        print(" OK\n")

        # --- software tare ---
        bias = {"Fx": 0.0, "Fy": 0.0, "Fz": 0.0, "Tx": 0.0, "Ty": 0.0, "Tz": 0.0}
        if do_tare:
            print(f">>> Software tare: collecting {args.tare_samples} samples …")
            print("    DO NOT apply any force/torque to the sensor during this phase.\n")
            tare_buf = []
            while len(tare_buf) < args.tare_samples:
                t0 = time.time()
                write_outputs(s0, filter_value=args.set_filter, zero_cmd=False)
                m.send_processdata()
                m.receive_processdata(1000)
                d = unpack_inputs(s0.input)
                tare_buf.append(d["floats"].copy())
                pct = len(tare_buf) / args.tare_samples * 100
                print(f"    Tare progress: {len(tare_buf):>3d}/{args.tare_samples}  "
                      f"Fz_raw={d['floats']['Fz']:+8.3f} N", end="\r")
                dt = time.time() - t0
                if period - dt > 0:
                    time.sleep(period - dt)

            for axis in bias:
                bias[axis] = sum(s[axis] for s in tare_buf) / len(tare_buf)
            print(f"\n    Tare offset  →  "
                  f"Fx={bias['Fx']:+.3f}  Fy={bias['Fy']:+.3f}  Fz={bias['Fz']:+.3f} N  |  "
                  f"Tx={bias['Tx']:+.3f}  Ty={bias['Ty']:+.3f}  Tz={bias['Tz']:+.3f} Nm")
            print("    Tare DONE.\n")
        else:
            print("    Tare skipped – displaying raw values.\n")

        # ------------------------------------------------------------------
        # Live display loop
        # ------------------------------------------------------------------
        print("-" * 88)
        print("  Live Force/Torque & Norms  (Ctrl-C to stop)")
        print("-" * 88)
        print(f"  {'SC':>6}  {'Fx':>8} {'Fy':>8} {'Fz':>8} {'||F||':>8}  "
              f"{'Tx':>8} {'Ty':>8} {'Tz':>8} {'||T||':>8}  STATUS")
        print(f"  {'':>6}  {'[N]':>8} {'[N]':>8} {'[N]':>8} {'[N]':>8}  "
              f"{'[Nm]':>8} {'[Nm]':>8} {'[Nm]':>8} {'[Nm]':>8}")
        print("-" * 88)

        t_end = time.time() + args.duration if args.duration > 0 else None
        t_start = time.time()
        cycle = 0
        max_f_norm = 0.0
        max_t_norm = 0.0
        max_f_raw_norm = 0.0
        max_t_raw_norm = 0.0
        recorded_samples = []

        while True:
            t0 = time.time()

            write_outputs(s0, filter_value=args.set_filter, zero_cmd=False)
            m.send_processdata()
            wkc = m.receive_processdata(1000)

            d = unpack_inputs(s0.input)
            st = d["status"]
            sc = d["sample_counter"]

            # Apply tare
            f = {k: d["floats"][k] - bias[k] for k in bias}

            # Norms calculation (total force and total torque magnitudes)
            f_norm = (f["Fx"]**2 + f["Fy"]**2 + f["Fz"]**2) ** 0.5
            t_norm = (f["Tx"]**2 + f["Ty"]**2 + f["Tz"]**2) ** 0.5
            f_raw_norm = (d["floats"]["Fx"]**2 + d["floats"]["Fy"]**2 + d["floats"]["Fz"]**2) ** 0.5
            t_raw_norm = (d["floats"]["Tx"]**2 + d["floats"]["Ty"]**2 + d["floats"]["Tz"]**2) ** 0.5

            if f_norm > max_f_norm:
                max_f_norm = f_norm
            if t_norm > max_t_norm:
                max_t_norm = t_norm
            if f_raw_norm > max_f_raw_norm:
                max_f_raw_norm = f_raw_norm
            if t_raw_norm > max_t_raw_norm:
                max_t_raw_norm = t_raw_norm

            status_str = st["summary"]

            # Store in RAM buffer (near-zero overhead)
            if args.format != "none":
                now_epoch = time.time()
                time_rel = now_epoch - t_start
                recorded_samples.append((
                    time_rel,
                    now_epoch,
                    sc,
                    f["Fx"], f["Fy"], f["Fz"],
                    f["Tx"], f["Ty"], f["Tz"],
                    d["floats"]["Fx"], d["floats"]["Fy"], d["floats"]["Fz"],
                    d["floats"]["Tx"], d["floats"]["Ty"], d["floats"]["Tz"],
                    f_norm, t_norm,
                    f_raw_norm, t_raw_norm,
                    status_str,
                ))

            print(
                f"  {sc:>6d}  "
                f"{f['Fx']:>+8.2f} {f['Fy']:>+8.2f} {f['Fz']:>+8.2f} {f_norm:>8.2f}  "
                f"{f['Tx']:>+8.3f} {f['Ty']:>+8.3f} {f['Tz']:>+8.3f} {t_norm:>8.3f}  "
                f"{status_str}"
            )

            # Extra status breakdown on error
            if status_str != "OK":
                ol = [k for k, v in st["overload"].items() if v]
                if ol:
                    print(f"    ↳ OVERLOAD on: {', '.join(ol)}")
                if st["sensor_error_group"] != 0:
                    print(f"    ↳ sensor error group: {st['sensor_error_group']}")
                if st["daq_comm_error_group"] != 0:
                    print(f"    ↳ DAQ/comm error group: {st['daq_comm_error_group']}")
                if st["calibration_missing"]:
                    print("    ↳ calibration data missing in sensor!")

            cycle += 1
            dt = time.time() - t0
            sleep = period - dt
            if sleep > 0:
                time.sleep(sleep)
            if t_end and time.time() >= t_end:
                break

    except KeyboardInterrupt:
        print("\n\nInterrupted by user (Ctrl-C).")
    finally:
        try:
            m.close()
        except Exception:
            pass
        elapsed = time.time() - t_start if "t_start" in dir() else 0
        cycle_count = cycle if "cycle" in dir() else 0
        freq = cycle_count / elapsed if elapsed > 0 else 0
        print(f"\nSession ended. Cycles: {cycle_count}  "
              f"Duration: {elapsed:.1f}s  Mean rate: {freq:.1f} Hz")

        if cycle_count > 0:
            print("-" * 70)
            if do_tare:
                print("  Session Peak Statistics (TARED):")
                print(f"    ||F|| max (Total tared force)  : {max_f_norm:.3f} N  [Raw max: {max_f_raw_norm:.3f} N]")
                print(f"    ||T|| max (Total tared torque) : {max_t_norm:.4f} Nm [Raw max: {max_t_raw_norm:.4f} Nm]")
            else:
                print("  Session Peak Statistics (RAW):")
                print(f"    ||F|| max (Total raw force)  : {max_f_norm:.3f} N")
                print(f"    ||T|| max (Total raw torque) : {max_t_norm:.4f} Nm")
            print("-" * 70)

        if "recorded_samples" in locals() and recorded_samples and args.format != "none":
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{args.prefix}_{timestamp_str}"
            session_dir = os.path.join(args.output_dir, base_name)
            os.makedirs(session_dir, exist_ok=True)

            formats_to_save = ["csv", "txt", "npy"] if args.format == "all" else [args.format]

            headers = [
                "time_rel_s", "time_epoch_s", "sample_counter",
                "Fx_tared_N", "Fy_tared_N", "Fz_tared_N",
                "Tx_tared_Nm", "Ty_tared_Nm", "Tz_tared_Nm",
                "Fx_raw_N", "Fy_raw_N", "Fz_raw_N",
                "Tx_raw_Nm", "Ty_raw_Nm", "Tz_raw_Nm",
                "F_norm_tared_N", "T_norm_tared_Nm",
                "F_norm_raw_N", "T_norm_raw_Nm",
                "status",
            ]

            tare_bias_line = (
                f"# Tare bias: Fx={bias['Fx']:.4f}N Fy={bias['Fy']:.4f}N Fz={bias['Fz']:.4f}N "
                f"Tx={bias['Tx']:.4f}Nm Ty={bias['Ty']:.4f}Nm Tz={bias['Tz']:.4f}Nm"
            )

            for fmt in formats_to_save:
                file_path = os.path.join(session_dir, f"{base_name}.{fmt}")
                if fmt == "csv":
                    with open(file_path, "w", newline="", encoding="utf-8") as fp:
                        writer = csv.writer(fp)
                        writer.writerow([f"# OnRobot HEX-E v2 Recording - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                        writer.writerow([tare_bias_line])
                        writer.writerow(headers)
                        writer.writerows(recorded_samples)
                    print(f"  [Export] Data saved ({len(recorded_samples)} samples) -> {file_path}")

                elif fmt == "txt":
                    with open(file_path, "w", encoding="utf-8") as fp:
                        fp.write(f"# OnRobot HEX-E v2 Recording - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        fp.write(f"{tare_bias_line}\n")
                        fp.write("\t".join(headers) + "\n")
                        for row in recorded_samples:
                            fp.write("\t".join(str(x) for x in row) + "\n")
                    print(f"  [Export] Data saved ({len(recorded_samples)} samples) -> {file_path}")

                elif fmt == "npy":
                    try:
                        import numpy as np
                        numeric_data = np.array([row[:-1] for row in recorded_samples], dtype=np.float64)
                        np.save(file_path, numeric_data)
                        print(f"  [Export] NumPy binary data saved ({len(recorded_samples)} samples, "
                              f"shape {numeric_data.shape}) -> {file_path}")
                    except ImportError:
                        print("  [Export] WARNING: numpy is not installed, .npy export skipped.")


if __name__ == "__main__":
    main()

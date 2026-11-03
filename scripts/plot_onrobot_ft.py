#!/usr/bin/env python3
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
"""
plot_onrobot_ft.py
==================
Visualizer and curve plotter for force and torque data recorded by
test_onrobot_ft.py (OnRobot HEX-E v2 6-axis F/T sensor).

Plots triaxial force components (Fx, Fy, Fz), torque components (Tx, Ty, Tz),
as well as the corresponding Euclidean vector norms:
  ||F|| = sqrt(Fx^2 + Fy^2 + Fz^2)  -> Total force magnitude measured by the sensor (N)
  ||T|| = sqrt(Tx^2 + Ty^2 + Tz^2)  -> Total torque magnitude measured by the sensor (N·m)

Usage:
------
    # Plot the latest recorded CSV or NPY file:
    python3 plot_onrobot_ft.py --latest

    # Plot a specific CSV or NPY file:
    python3 plot_onrobot_ft.py OnRobot_force_20260918_170202.csv
    python3 plot_onrobot_ft.py OnRobot_force_20260922_144631.npy

    # Plot raw (untared) values:
    python3 plot_onrobot_ft.py --latest --raw

    # Plot only the force and torque norms ||F|| and ||T||:
    python3 plot_onrobot_ft.py --latest --norm-only

    # Save PNG figures without opening an interactive GUI window (headless mode):
    python3 plot_onrobot_ft.py --latest --save-only
"""

import argparse
import csv
import glob
import math
import os
import sys
import tempfile

# Avoid Matplotlib warning if .config is read-only
if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib_onrobot")

# Headless environment support when no X11/Wayland display is active or --save-only is passed
if "--save-only" in sys.argv or ("DISPLAY" not in os.environ and "WAYLAND_DISPLAY" not in os.environ):
    import matplotlib
    matplotlib.use("Agg")

import matplotlib.pyplot as plt


def find_latest_file(search_dir, extensions=(".csv", ".npy", ".txt")):
    """Search for the most recent acquisition file in the directory or its session subfolders."""
    files = []
    for ext in extensions:
        pattern = os.path.join(search_dir, "**", f"OnRobot_force_*{ext}")
        files.extend(glob.glob(pattern, recursive=True))
    if not files:
        for ext in extensions:
            files.extend(glob.glob(os.path.join(search_dir, "**", f"*{ext}"), recursive=True))
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def find_latest_csv(search_dir):
    """Backward compatibility: search for the latest CSV file."""
    return find_latest_file(search_dir, extensions=(".csv",))


def load_data_csv(csv_path):
    """Load data from a CSV or TXT file (with or without explicit norm columns)."""
    time_s = []
    fx_t, fy_t, fz_t, fn_t = [], [], [], []
    tx_t, ty_t, tz_t, tn_t = [], [], [], []
    fx_r, fy_r, fz_r, fn_r = [], [], [], []
    tx_r, ty_r, tz_r, tn_r = [], [], [], []
    tare_info = ""
    header_indices = {}
    header_indices_lower = {}

    delimiter = "\t" if csv_path.endswith(".txt") else ","
    try:
        with open(csv_path, "r", encoding="utf-8", errors="replace") as f_peek:
            for line_peek in f_peek:
                line_p = line_peek.strip()
                if line_p and not line_p.startswith("#"):
                    if "\t" in line_p and "," not in line_p:
                        delimiter = "\t"
                    elif "," in line_p and "\t" not in line_p:
                        delimiter = ","
                    elif ";" in line_p and "," not in line_p:
                        delimiter = ";"
                    break
    except Exception:
        pass

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=delimiter)
        raw_rows = []
        for row in reader:
            if not row:
                continue
            line = row[0].strip()
            if line.startswith("#"):
                if "Tare bias" in line:
                    tare_info = line.lstrip("# ")
                continue

            row_lower = [c.strip().lower() for c in row]
            # Detect header row (case-insensitive)
            if not header_indices and any(h in row_lower for h in [
                "time_rel_s", "time", "time_s", "t", "fx_tared_n", "fx", "sample_counter"
            ]):
                header_indices = {col.strip(): idx for idx, col in enumerate(row)}
                header_indices_lower = {col.strip().lower(): idx for idx, col in enumerate(row)}
                continue

            raw_rows.append(row)

        for row in raw_rows:
            try:
                def get_val(keys, default=0.0):
                    if isinstance(keys, str):
                        keys = [keys]
                    for k in keys:
                        idx = header_indices.get(k)
                        if idx is None:
                            idx = header_indices_lower.get(k.lower())
                        if idx is not None and len(row) > idx:
                            val_str = row[idx].strip()
                            if val_str != "":
                                return float(val_str)
                    return default

                if header_indices:
                    t = get_val(["time_rel_s", "time_s", "time", "t"])
                    if t == 0.0 and "time_rel_s" not in header_indices and "time_rel_s" not in header_indices_lower:
                        try:
                            t = float(row[0].strip())
                        except (ValueError, IndexError):
                            t = 0.0

                    fxt = get_val(["Fx_tared_N", "Fx_tared", "Fx", "fx"])
                    fyt = get_val(["Fy_tared_N", "Fy_tared", "Fy", "fy"])
                    fzt = get_val(["Fz_tared_N", "Fz_tared", "Fz", "fz"])
                    txt = get_val(["Tx_tared_Nm", "Tx_tared", "Tx", "tx"])
                    tyt = get_val(["Ty_tared_Nm", "Ty_tared", "Ty", "ty"])
                    tzt = get_val(["Tz_tared_Nm", "Tz_tared", "Tz", "tz"])

                    fxr = get_val(["Fx_raw_N", "Fx_raw"])
                    fyr = get_val(["Fy_raw_N", "Fy_raw"])
                    fzr = get_val(["Fz_raw_N", "Fz_raw"])
                    txr = get_val(["Tx_raw_Nm", "Tx_raw"])
                    tyr = get_val(["Ty_raw_Nm", "Ty_raw"])
                    tzr = get_val(["Tz_raw_Nm", "Tz_raw"])

                    has_fn_t = ("F_norm_tared_N" in header_indices or "f_norm_tared_n" in header_indices_lower or
                                "F_norm" in header_indices or "f_norm" in header_indices_lower)
                    fnt = (get_val(["F_norm_tared_N", "F_norm", "fn_tared", "fn"])
                           if has_fn_t else math.sqrt(fxt**2 + fyt**2 + fzt**2))

                    has_tn_t = ("T_norm_tared_Nm" in header_indices or "t_norm_tared_nm" in header_indices_lower or
                                "T_norm" in header_indices or "t_norm" in header_indices_lower)
                    tnt = (get_val(["T_norm_tared_Nm", "T_norm", "tn_tared", "tn"])
                           if has_tn_t else math.sqrt(txt**2 + tyt**2 + tzt**2))

                    has_fn_r = ("F_norm_raw_N" in header_indices or "f_norm_raw_n" in header_indices_lower)
                    fnr = (get_val(["F_norm_raw_N", "fn_raw"])
                           if has_fn_r else math.sqrt(fxr**2 + fyr**2 + fzr**2))

                    has_tn_r = ("T_norm_raw_Nm" in header_indices or "t_norm_raw_nm" in header_indices_lower)
                    tnr = (get_val(["T_norm_raw_Nm", "tn_raw"])
                           if has_tn_r else math.sqrt(txr**2 + tyr**2 + tzr**2))
                else:
                    t = float(row[0].strip())
                    fxt = float(row[3].strip())
                    fyt = float(row[4].strip())
                    fzt = float(row[5].strip())
                    txt = float(row[6].strip())
                    tyt = float(row[7].strip())
                    tzt = float(row[8].strip())

                    fxr = float(row[9].strip()) if len(row) >= 15 else 0.0
                    fyr = float(row[10].strip()) if len(row) >= 15 else 0.0
                    fzr = float(row[11].strip()) if len(row) >= 15 else 0.0
                    txr = float(row[12].strip()) if len(row) >= 15 else 0.0
                    tyr = float(row[13].strip()) if len(row) >= 15 else 0.0
                    tzr = float(row[14].strip()) if len(row) >= 15 else 0.0

                    fnt = float(row[15].strip()) if len(row) >= 19 else math.sqrt(fxt**2 + fyt**2 + fzt**2)
                    tnt = float(row[16].strip()) if len(row) >= 19 else math.sqrt(txt**2 + tyt**2 + tzt**2)
                    fnr = float(row[17].strip()) if len(row) >= 19 else math.sqrt(fxr**2 + fyr**2 + fzr**2)
                    tnr = float(row[18].strip()) if len(row) >= 19 else math.sqrt(txr**2 + tyr**2 + tzr**2)

                time_s.append(t)
                fx_t.append(fxt)
                fy_t.append(fyt)
                fz_t.append(fzt)
                fn_t.append(fnt)

                tx_t.append(txt)
                ty_t.append(tyt)
                tz_t.append(tzt)
                tn_t.append(tnt)

                fx_r.append(fxr)
                fy_r.append(fyr)
                fz_r.append(fzr)
                fn_r.append(fnr)

                tx_r.append(txr)
                ty_r.append(tyr)
                tz_r.append(tzr)
                tn_r.append(tnr)

            except (ValueError, IndexError):
                continue

    return {
        "time": time_s,
        "tared": {"Fx": fx_t, "Fy": fy_t, "Fz": fz_t, "F_norm": fn_t,
                  "Tx": tx_t, "Ty": ty_t, "Tz": tz_t, "T_norm": tn_t},
        "raw": {"Fx": fx_r, "Fy": fy_r, "Fz": fz_r, "F_norm": fn_r,
                "Tx": tx_r, "Ty": ty_r, "Tz": tz_r, "T_norm": tn_r},
        "tare_info": tare_info,
    }


def load_data_npy(npy_path):
    """Load data from a binary NPY file."""
    try:
        import numpy as np
    except ImportError:
        sys.exit("Error: 'numpy' module is required to load a .npy file")

    arr = np.load(npy_path)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2 or arr.shape[1] < 9:
        raise ValueError(f"Unexpected NPY file format: shape={arr.shape}")

    t = arr[:, 0].tolist()
    fx_t = arr[:, 3].tolist()
    fy_t = arr[:, 4].tolist()
    fz_t = arr[:, 5].tolist()
    tx_t = arr[:, 6].tolist()
    ty_t = arr[:, 7].tolist()
    tz_t = arr[:, 8].tolist()

    has_raw = arr.shape[1] >= 15
    fx_r = arr[:, 9].tolist() if has_raw else [0.0] * len(t)
    fy_r = arr[:, 10].tolist() if has_raw else [0.0] * len(t)
    fz_r = arr[:, 11].tolist() if has_raw else [0.0] * len(t)
    tx_r = arr[:, 12].tolist() if has_raw else [0.0] * len(t)
    ty_r = arr[:, 13].tolist() if has_raw else [0.0] * len(t)
    tz_r = arr[:, 14].tolist() if has_raw else [0.0] * len(t)

    has_norms = arr.shape[1] >= 19
    if has_norms:
        fn_t = arr[:, 15].tolist()
        tn_t = arr[:, 16].tolist()
        fn_r = arr[:, 17].tolist()
        tn_r = arr[:, 18].tolist()
    else:
        fn_t = np.sqrt(arr[:, 3]**2 + arr[:, 4]**2 + arr[:, 5]**2).tolist()
        tn_t = np.sqrt(arr[:, 6]**2 + arr[:, 7]**2 + arr[:, 8]**2).tolist()
        fn_r = np.sqrt(arr[:, 9]**2 + arr[:, 10]**2 + arr[:, 11]**2).tolist() if has_raw else [0.0] * len(t)
        tn_r = np.sqrt(arr[:, 12]**2 + arr[:, 13]**2 + arr[:, 14]**2).tolist() if has_raw else [0.0] * len(t)

    tare_info = ""
    txt_candidate = os.path.splitext(npy_path)[0] + ".txt"
    if os.path.isfile(txt_candidate):
        try:
            with open(txt_candidate, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if "Tare bias" in line:
                        tare_info = line.strip().lstrip("# ")
                        break
        except Exception:
            pass

    return {
        "time": t,
        "tared": {"Fx": fx_t, "Fy": fy_t, "Fz": fz_t, "F_norm": fn_t,
                  "Tx": tx_t, "Ty": ty_t, "Tz": tz_t, "T_norm": tn_t},
        "raw": {"Fx": fx_r, "Fy": fy_r, "Fz": fz_r, "F_norm": fn_r,
                "Tx": tx_r, "Ty": ty_r, "Tz": tz_r, "T_norm": tn_r},
        "tare_info": tare_info,
    }


def load_data(file_path):
    """Load data from a .csv, .txt, or .npy file."""
    if file_path.endswith(".npy"):
        return load_data_npy(file_path)
    return load_data_csv(file_path)


def plot_3axes_figure(t, d_plot, target_file, label_suffix=""):
    """Generate the figure with the 3 triaxial components (Fx, Fy, Fz and Tx, Ty, Tz)."""
    fig, (ax_f, ax_t) = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True)
    fig.suptitle(
        f"Triaxial Force & Torque Components – OnRobot HEX-E v2\n{os.path.basename(target_file)}",
        fontsize=13,
        fontweight="bold"
    )
    badge_props = dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.9, edgecolor="#bdc3c7")

    # Subplot 1: Forces Fx, Fy, Fz
    ax_f.axhline(0, color="#7f8c8d", linestyle=":", alpha=0.6, lw=0.9)
    ax_f.plot(t, d_plot["Fx"], label=f"Fx{label_suffix}", color="#e74c3c", lw=1.3, alpha=0.9)
    ax_f.plot(t, d_plot["Fy"], label=f"Fy{label_suffix}", color="#2ecc71", lw=1.3, alpha=0.9)
    ax_f.plot(t, d_plot["Fz"], label=f"Fz{label_suffix}", color="#3498db", lw=1.3, alpha=0.9)
    ax_f.set_ylabel("Forces (N)", fontsize=11, fontweight="bold")
    ax_f.grid(True, linestyle="--", alpha=0.6)
    ax_f.margins(y=0.15)
    ax_f.legend(loc="upper right", framealpha=0.92, fontsize=10)

    stats_f = (
        f"Fx : [{min(d_plot['Fx']):+.2f}, {max(d_plot['Fx']):+.2f}] N\n"
        f"Fy : [{min(d_plot['Fy']):+.2f}, {max(d_plot['Fy']):+.2f}] N\n"
        f"Fz : [{min(d_plot['Fz']):+.2f}, {max(d_plot['Fz']):+.2f}] N"
    )
    ax_f.text(0.015, 0.95, stats_f, transform=ax_f.transAxes, fontsize=9.5, verticalalignment="top", bbox=badge_props)

    # Subplot 2: Torques Tx, Ty, Tz
    ax_t.axhline(0, color="#7f8c8d", linestyle=":", alpha=0.6, lw=0.9)
    ax_t.plot(t, d_plot["Tx"], label=f"Tx{label_suffix}", color="#e67e22", lw=1.3, alpha=0.9)
    ax_t.plot(t, d_plot["Ty"], label=f"Ty{label_suffix}", color="#9b59b6", lw=1.3, alpha=0.9)
    ax_t.plot(t, d_plot["Tz"], label=f"Tz{label_suffix}", color="#1abc9c", lw=1.3, alpha=0.9)
    ax_t.set_xlabel("Time (s)", fontsize=11, fontweight="bold")
    ax_t.set_ylabel("Torques (N·m)", fontsize=11, fontweight="bold")
    ax_t.grid(True, linestyle="--", alpha=0.6)
    ax_t.margins(y=0.15)
    ax_t.legend(loc="upper right", framealpha=0.92, fontsize=10)

    stats_t = (
        f"Tx : [{min(d_plot['Tx']):+.3f}, {max(d_plot['Tx']):+.3f}] N·m\n"
        f"Ty : [{min(d_plot['Ty']):+.3f}, {max(d_plot['Ty']):+.3f}] N·m\n"
        f"Tz : [{min(d_plot['Tz']):+.3f}, {max(d_plot['Tz']):+.3f}] N·m"
    )
    ax_t.text(0.015, 0.95, stats_t, transform=ax_t.transAxes, fontsize=9.5, verticalalignment="top", bbox=badge_props)

    plt.tight_layout()
    return fig


def plot_norm_figure(t, d_plot, target_file, label_suffix="", f_max=0, t_at_f_max=0, f_mean=0, t_max=0, t_at_t_max=0, t_mean=0):
    """Generate the figure with the Euclidean norms ||F|| and ||T||."""
    fig, (ax_f, ax_t) = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True)
    fig.suptitle(
        f"Euclidean Vector Norms (Total Force ||F|| & Total Torque ||T||) – OnRobot HEX-E v2\n{os.path.basename(target_file)}",
        fontsize=13,
        fontweight="bold"
    )
    badge_props = dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.9, edgecolor="#bdc3c7")

    # Subplot 1: Force Norm ||F||
    ax_f.axhline(0, color="#7f8c8d", linestyle=":", alpha=0.5, lw=0.9)
    ax_f.plot(t, d_plot["F_norm"], label=f"||F|| Total Force (Peak: {f_max:.2f} N){label_suffix}", color="#1b4f72", lw=2.2)
    ax_f.fill_between(t, 0, d_plot["F_norm"], color="#2980b9", alpha=0.15)
    ax_f.plot(t_at_f_max, f_max, marker="o", color="#c0392b", markersize=6, zorder=5)
    ax_f.set_ylabel("||F|| Force (N)", fontsize=11, fontweight="bold")
    ax_f.grid(True, linestyle="--", alpha=0.6)
    ax_f.margins(y=0.18)
    ax_f.legend(loc="upper right", framealpha=0.92, fontsize=10)

    stats_box_f = (
        f"||F|| max  : {f_max:.2f} N (at t={t_at_f_max:.2f} s)\n"
        f"||F|| mean : {f_mean:.2f} N"
    )
    ax_f.text(0.015, 0.95, stats_box_f, transform=ax_f.transAxes, fontsize=9.5, verticalalignment="top", bbox=badge_props)

    # Subplot 2: Torque Norm ||T||
    ax_t.axhline(0, color="#7f8c8d", linestyle=":", alpha=0.5, lw=0.9)
    ax_t.plot(t, d_plot["T_norm"], label=f"||T|| Total Torque (Peak: {t_max:.3f} N·m){label_suffix}", color="#5b2c6f", lw=2.2)
    ax_t.fill_between(t, 0, d_plot["T_norm"], color="#8e44ad", alpha=0.15)
    ax_t.plot(t_at_t_max, t_max, marker="o", color="#c0392b", markersize=6, zorder=5)
    ax_t.set_xlabel("Time (s)", fontsize=11, fontweight="bold")
    ax_t.set_ylabel("||T|| Torque (N·m)", fontsize=11, fontweight="bold")
    ax_t.grid(True, linestyle="--", alpha=0.6)
    ax_t.margins(y=0.18)
    ax_t.legend(loc="upper right", framealpha=0.92, fontsize=10)

    stats_box_t = (
        f"||T|| max  : {t_max:.3f} N·m (at t={t_at_t_max:.2f} s)\n"
        f"||T|| mean : {t_mean:.3f} N·m"
    )
    ax_t.text(0.015, 0.95, stats_box_t, transform=ax_t.transAxes, fontsize=9.5, verticalalignment="top", bbox=badge_props)

    plt.tight_layout()
    return fig


def save_fig(fig, path):
    """Safely save a Matplotlib figure with automatic /tmp fallback if read-only."""
    try:
        fig.savefig(path, dpi=150)
        print(f"Figure saved -> {path}")
    except (OSError, PermissionError) as err:
        fallback_dir = tempfile.gettempdir()
        fallback_path = os.path.join(fallback_dir, os.path.basename(path))
        try:
            fig.savefig(fallback_path, dpi=150)
            print(f"WARNING: Cannot write to '{path}' ({err}). Figure saved to -> {fallback_path}")
        except Exception as err2:
            print(f"WARNING: Unable to save PNG figure: {err2}")


def main():
    parser = argparse.ArgumentParser(description="Plot OnRobot HEX-E v2 Force and Torque curves (3-Axis Components & Euclidean Norms)")
    parser.add_argument("data_file", nargs="?", default=None, help="Acquisition file to plot (.csv, .npy, .txt) or directory")
    parser.add_argument("--latest", action="store_true", help="Automatically plot the most recent recording file")
    parser.add_argument("--raw", action="store_true", help="Plot raw (untared) values instead of tared values")
    parser.add_argument("--axes-only", action="store_true", help="Generate only the 3-axis components plot (Fx,Fy,Fz and Tx,Ty,Tz)")
    parser.add_argument("--norm-only", action="store_true", help="Generate only the Euclidean norms plot (||F|| and ||T||)")
    parser.add_argument("-o", "--output", default=None, help="Custom output PNG file path")
    parser.add_argument("--save-only", action="store_true", help="Save PNG figure without opening an interactive GUI window")
    parser.add_argument("--no-save", action="store_true", help="Do not save PNG figure to disk (display only)")
    parser.add_argument(
        "--dir",
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "onrobot_ft_recordings"),
        help="Search directory for recording files"
    )
    args = parser.parse_args()

    target_file = args.data_file
    if target_file and os.path.isdir(target_file):
        target_file = find_latest_file(target_file)
        if not target_file:
            sys.exit(f"No acquisition file found in specified directory: {args.data_file}")
    elif args.latest or target_file is None:
        target_file = find_latest_file(args.dir)
        if not target_file:
            sys.exit(f"No acquisition file found in: {args.dir}")

    if not os.path.isfile(target_file):
        sys.exit(f"File not found: {target_file}")

    print(f"Loading data from: {target_file}")
    data = load_data(target_file)
    n_points = len(data["time"])
    if n_points == 0:
        sys.exit("File contains no valid measurement samples.")

    t = data["time"]
    t_span = t[-1] - t[0] if n_points > 1 else 0
    freq_est = n_points / t_span if t_span > 0 else 0

    print(f"Loaded samples: {n_points} | Duration: {t_span:.2f} s | Mean rate: {freq_est:.1f} Hz")
    if data["tare_info"]:
        print(f"Tare info: {data['tare_info']}")

    d_plot = data["raw"] if args.raw else data["tared"]
    label_suffix = " (raw)" if args.raw else ""

    # Compute peak and mean statistics on Euclidean norms
    f_norm = d_plot["F_norm"]
    t_norm = d_plot["T_norm"]

    idx_f_max = max(range(len(f_norm)), key=lambda i: f_norm[i])
    f_max = f_norm[idx_f_max]
    t_at_f_max = t[idx_f_max]
    f_mean = sum(f_norm) / len(f_norm)

    idx_t_max = max(range(len(t_norm)), key=lambda i: t_norm[i])
    t_max = t_norm[idx_t_max]
    t_at_t_max = t[idx_t_max]
    t_mean = sum(t_norm) / len(t_norm)

    # Display detailed statistics in console
    print("-" * 75)
    print(f"Force/Torque Statistics{' [RAW]' if args.raw else ' [TARED]'}:")
    print(f"  Force Norm  ||F|| : Peak = {f_max:6.2f} N (at t={t_at_f_max:.2f} s) | Mean = {f_mean:6.2f} N")
    print(f"  Torque Norm ||T|| : Peak = {t_max:6.3f} N·m (at t={t_at_t_max:.2f} s) | Mean = {t_mean:6.3f} N·m")
    print(f"  Force Components  : Fx=[{min(d_plot['Fx']):+.2f}, {max(d_plot['Fx']):+.2f}] N  "
          f"Fy=[{min(d_plot['Fy']):+.2f}, {max(d_plot['Fy']):+.2f}] N  "
          f"Fz=[{min(d_plot['Fz']):+.2f}, {max(d_plot['Fz']):+.2f}] N")
    print(f"  Torque Components : Tx=[{min(d_plot['Tx']):+.3f}, {max(d_plot['Tx']):+.3f}] N·m  "
          f"Ty=[{min(d_plot['Ty']):+.3f}, {max(d_plot['Ty']):+.3f}] N·m  "
          f"Tz=[{min(d_plot['Tz']):+.3f}, {max(d_plot['Tz']):+.3f}] N·m")
    print("-" * 75)

    base_path = os.path.splitext(target_file)[0]

    # Determine which figures to generate (default: both separate figures)
    gen_axes = not args.norm_only
    gen_norm = not args.axes_only

    if gen_axes:
        fig_axes = plot_3axes_figure(t, d_plot, target_file, label_suffix)
        if not args.no_save:
            path_axes = args.output if args.output else f"{base_path}_3axes.png"
            save_fig(fig_axes, path_axes)

    if gen_norm:
        fig_norm = plot_norm_figure(t, d_plot, target_file, label_suffix,
                                    f_max, t_at_f_max, f_mean, t_max, t_at_t_max, t_mean)
        if not args.no_save:
            if args.output and not gen_axes:
                path_norm = args.output
            elif args.output:
                path_norm = f"{os.path.splitext(args.output)[0]}_norme.png"
            else:
                path_norm = f"{base_path}_norme.png"
            save_fig(fig_norm, path_norm)

    if not args.save_only and ("DISPLAY" in os.environ or "WAYLAND_DISPLAY" in os.environ):
        plt.show()


if __name__ == "__main__":
    main()

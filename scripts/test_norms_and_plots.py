#!/usr/bin/env python3
# ==============================================================================
# Author: Kamil BENMADI
# Email: kamil.benmadi@sigma-clermont.fr
# GitHub: https://github.com/1000K-sudo
# LinkedIn: https://www.linkedin.com/in/kamilb-
# ==============================================================================
"""
test_norms_and_plots.py
=======================
Unit and integration tests for force/torque norm calculations,
file exports, and curve plotting in plot_onrobot_ft.py and test_onrobot_ft.py.
"""

import csv
import math
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(WORKSPACE_DIR, "data", "onrobot_ft_recordings")
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import plot_onrobot_ft
import test_onrobot_ft


class TestNormCalculations(unittest.TestCase):
    def test_norm_math(self):
        """Verify vector norm math ||F|| and ||T||."""
        fx, fy, fz = 3.0, 4.0, 12.0
        expected_norm = 13.0  # sqrt(9 + 16 + 144) = sqrt(169) = 13
        calculated = math.sqrt(fx**2 + fy**2 + fz**2)
        self.assertAlmostEqual(calculated, expected_norm, places=7)

        tx, ty, tz = 0.3, 0.4, 0.0
        expected_t_norm = 0.5
        calculated_t = math.sqrt(tx**2 + ty**2 + tz**2)
        self.assertAlmostEqual(calculated_t, expected_t_norm, places=7)

    def test_load_existing_legacy_csv(self):
        """Test loading real existing recorded CSV from workspace (legacy 16-col format)."""
        csv_file = os.path.join(DATA_DIR, "OnRobot_force_20260922_144631.csv")
        self.assertTrue(os.path.isfile(csv_file))

        data = plot_onrobot_ft.load_data(csv_file)
        self.assertIn("time", data)
        self.assertIn("F_norm", data["tared"])
        self.assertIn("T_norm", data["tared"])
        self.assertIn("F_norm", data["raw"])
        self.assertIn("T_norm", data["raw"])

        n_pts = len(data["time"])
        self.assertGreater(n_pts, 0)
        self.assertEqual(len(data["tared"]["F_norm"]), n_pts)
        self.assertEqual(len(data["tared"]["T_norm"]), n_pts)

        # Verify norm calculation correctness on the first row
        fx = data["tared"]["Fx"][0]
        fy = data["tared"]["Fy"][0]
        fz = data["tared"]["Fz"][0]
        fn = data["tared"]["F_norm"][0]
        self.assertAlmostEqual(fn, math.sqrt(fx**2 + fy**2 + fz**2), places=5)

        tx = data["tared"]["Tx"][0]
        ty = data["tared"]["Ty"][0]
        tz = data["tared"]["Tz"][0]
        tn = data["tared"]["T_norm"][0]
        self.assertAlmostEqual(tn, math.sqrt(tx**2 + ty**2 + tz**2), places=5)

    def test_load_existing_legacy_npy(self):
        """Test loading real existing recorded NPY from workspace (legacy 15-col format)."""
        npy_file = os.path.join(DATA_DIR, "OnRobot_force_20260922_144631.npy")
        self.assertTrue(os.path.isfile(npy_file))

        data = plot_onrobot_ft.load_data(npy_file)
        self.assertIn("time", data)
        self.assertIn("F_norm", data["tared"])
        self.assertIn("T_norm", data["tared"])

        n_pts = len(data["time"])
        self.assertGreater(n_pts, 0)

        # Check peak norm
        f_max = max(data["tared"]["F_norm"])
        t_max = max(data["tared"]["T_norm"])
        self.assertGreater(f_max, 5.0)  # We know it peaks around 8.70 N
        self.assertGreater(t_max, 0.5)  # We know it peaks around 1.14 Nm

    def test_new_format_with_norm_columns(self):
        """Test saving with new 20-col CSV and 19-col NPY format and reading back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "test_new.csv")
            npy_path = os.path.join(tmpdir, "test_new.npy")
            txt_path = os.path.join(tmpdir, "test_new.txt")

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

            samples = []
            for i in range(10):
                t = i * 0.01
                sc = 1000 + i
                fxt, fyt, fzt = 1.0, 2.0, 2.0  # norm = 3.0
                txt, tyt, tzt = 0.1, 0.2, 0.2  # norm = 0.3
                fxr, fyr, fzr = 4.0, 0.0, 3.0  # norm = 5.0
                txr, tyr, tzr = 0.4, 0.0, 0.3  # norm = 0.5
                fnt = math.sqrt(fxt**2 + fyt**2 + fzt**2)
                tnt = math.sqrt(txt**2 + tyt**2 + tzt**2)
                fnr = math.sqrt(fxr**2 + fyr**2 + fzr**2)
                tnr = math.sqrt(txr**2 + tyr**2 + tzr**2)
                samples.append((
                    t, 1700000000.0 + t, sc,
                    fxt, fyt, fzt,
                    txt, tyt, tzt,
                    fxr, fyr, fzr,
                    txr, tyr, tzr,
                    fnt, tnt,
                    fnr, tnr,
                    "OK"
                ))

            # Write CSV
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["# Tare bias: Fx=0.0 Fy=0.0 Fz=0.0 Tx=0.0 Ty=0.0 Tz=0.0"])
                writer.writerow(headers)
                writer.writerows(samples)

            # Write TXT
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("# Tare bias: Fx=0.0\n")
                f.write("\t".join(headers) + "\n")
                for row in samples:
                    f.write("\t".join(str(x) for x in row) + "\n")

            # Write NPY
            numeric_data = np.array([row[:-1] for row in samples], dtype=np.float64)
            np.save(npy_path, numeric_data)

            # Test loading CSV
            d_csv = plot_onrobot_ft.load_data(csv_path)
            self.assertEqual(len(d_csv["time"]), 10)
            self.assertAlmostEqual(d_csv["tared"]["F_norm"][0], 3.0, places=5)
            self.assertAlmostEqual(d_csv["tared"]["T_norm"][0], 0.3, places=5)
            self.assertAlmostEqual(d_csv["raw"]["F_norm"][0], 5.0, places=5)
            self.assertAlmostEqual(d_csv["raw"]["T_norm"][0], 0.5, places=5)

            # Test loading TXT
            d_txt = plot_onrobot_ft.load_data(txt_path)
            self.assertEqual(len(d_txt["time"]), 10)
            self.assertAlmostEqual(d_txt["tared"]["F_norm"][0], 3.0, places=5)

            # Test loading NPY
            d_npy = plot_onrobot_ft.load_data(npy_path)
            self.assertEqual(len(d_npy["time"]), 10)
            self.assertAlmostEqual(d_npy["tared"]["F_norm"][0], 3.0, places=5)
            self.assertAlmostEqual(d_npy["tared"]["T_norm"][0], 0.3, places=5)

    def test_plot_cli_execution(self):
        """Test executing plot_onrobot_ft.py CLI with various flags."""
        script = os.path.join(SCRIPT_DIR, "plot_onrobot_ft.py")
        csv_file = os.path.join(DATA_DIR, "OnRobot_force_20260922_144631.csv")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_png = os.path.join(tmpdir, "test_out.png")

            # 1. Normal plot with explicit --output
            res = subprocess.run(
                [sys.executable, script, csv_file, "--save-only", "-o", out_png],
                capture_output=True, text=True, check=True
            )
            self.assertIn("Statistiques d'effort/couple", res.stdout)
            self.assertIn("Norme Force  ||F||", res.stdout)
            self.assertIn("Norme Couple ||T||", res.stdout)
            self.assertTrue(os.path.isfile(out_png))
            self.assertGreater(os.path.getsize(out_png), 1000)

            # 2. Raw plot
            res_raw = subprocess.run(
                [sys.executable, script, csv_file, "--raw", "--save-only", "-o", out_png],
                capture_output=True, text=True, check=True
            )
            self.assertIn("[BRUT]", res_raw.stdout)

            # 3. Norm-only plot
            res_norm = subprocess.run(
                [sys.executable, script, csv_file, "--norm-only", "--save-only", "-o", out_png],
                capture_output=True, text=True, check=True
            )
            self.assertIn("Norme Force  ||F||", res_norm.stdout)

            # 4. Save-only with automatic fallback when directory is read-only
            res_fallback = subprocess.run(
                [sys.executable, script, csv_file, "--save-only"],
                capture_output=True, text=True, check=True
            )
            self.assertIn("Graphique sauvegardé", res_fallback.stdout)

            # 5. --no-save flag
            res_nosave = subprocess.run(
                [sys.executable, script, csv_file, "--no-save", "--save-only"],
                capture_output=True, text=True, check=True
            )
            self.assertNotIn("Graphique sauvegardé", res_nosave.stdout)

    def test_single_point_csv(self):
        """Edge case: file with exactly one data point."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "single.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["# Tare bias: Fx=0 Fy=0 Fz=0 Tx=0 Ty=0 Tz=0"])
                writer.writerow([
                    "time_rel_s", "time_epoch_s", "sample_counter",
                    "Fx_tared_N", "Fy_tared_N", "Fz_tared_N",
                    "Tx_tared_Nm", "Ty_tared_Nm", "Tz_tared_Nm",
                    "Fx_raw_N", "Fy_raw_N", "Fz_raw_N",
                    "Tx_raw_Nm", "Ty_raw_Nm", "Tz_raw_Nm",
                    "status"
                ])
                writer.writerow([0.0, 1000.0, 1, 3.0, 4.0, 0.0, 0.1, 0.2, 0.2, 3.0, 4.0, 0.0, 0.1, 0.2, 0.2, "OK"])

            d = plot_onrobot_ft.load_data(csv_path)
            self.assertEqual(len(d["time"]), 1)
            self.assertAlmostEqual(d["tared"]["F_norm"][0], 5.0)

            # Test plotting single point
            script = os.path.join(SCRIPT_DIR, "plot_onrobot_ft.py")
            out_png = os.path.join(tmpdir, "single.png")
            res = subprocess.run(
                [sys.executable, script, csv_path, "--save-only", "-o", out_png],
                capture_output=True, text=True, check=True
            )
            self.assertIn("Points chargés : 1", res.stdout)
            self.assertIn("Durée : 0.00 s", res.stdout)
            self.assertTrue(os.path.isfile(out_png))

    def test_negative_values_norm(self):
        """Edge case: negative forces and torques."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "neg.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["time_rel_s", "time_epoch_s", "sample_counter",
                                 "Fx_tared_N", "Fy_tared_N", "Fz_tared_N",
                                 "Tx_tared_Nm", "Ty_tared_Nm", "Tz_tared_Nm",
                                 "status"])
                writer.writerow([0.0, 1000.0, 1, -6.0, -8.0, 0.0, -0.3, -0.4, 0.0, "OK"])

            d = plot_onrobot_ft.load_data(csv_path)
            self.assertAlmostEqual(d["tared"]["F_norm"][0], 10.0)
            self.assertAlmostEqual(d["tared"]["T_norm"][0], 0.5)

    def test_1d_npy_array(self):
        """Edge case: 1D NumPy array shape (19,) and (15,) loaded cleanly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            npy19_path = os.path.join(tmpdir, "single19.npy")
            # 19 columns: time, epoch, sc, 3xFt, 3xTt, 3xFr, 3xTr, 2xNt, 2xNr
            row19 = np.array([0.5, 1700.0, 10,
                              3.0, 4.0, 12.0, 0.3, 0.4, 0.0,
                              1.0, 2.0, 2.0, 0.1, 0.2, 0.2,
                              13.0, 0.5, 3.0, 0.3], dtype=np.float64)
            np.save(npy19_path, row19)

            d19 = plot_onrobot_ft.load_data(npy19_path)
            self.assertEqual(len(d19["time"]), 1)
            self.assertAlmostEqual(d19["tared"]["F_norm"][0], 13.0)
            self.assertAlmostEqual(d19["tared"]["T_norm"][0], 0.5)

            npy15_path = os.path.join(tmpdir, "single15.npy")
            row15 = np.array([0.5, 1700.0, 10,
                              3.0, 4.0, 12.0, 0.3, 0.4, 0.0,
                              0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
            np.save(npy15_path, row15)

            d15 = plot_onrobot_ft.load_data(npy15_path)
            self.assertEqual(len(d15["time"]), 1)
            self.assertAlmostEqual(d15["tared"]["F_norm"][0], 13.0)
            self.assertAlmostEqual(d15["tared"]["T_norm"][0], 0.5)

    def test_flexible_headers_csv(self):
        """Test flexible header names and semicolon delimiters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Custom uppercase / short names
            csv_path = os.path.join(tmpdir, "custom_hdr.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Time", "Fx", "Fy", "Fz", "Tx", "Ty", "Tz"])
                writer.writerow([0.1, 1.0, 2.0, 2.0, 0.1, 0.2, 0.2])
                writer.writerow([0.2, 3.0, 4.0, 0.0, 0.0, 0.3, 0.4])

            d = plot_onrobot_ft.load_data(csv_path)
            self.assertEqual(len(d["time"]), 2)
            self.assertAlmostEqual(d["time"][0], 0.1)
            self.assertAlmostEqual(d["tared"]["F_norm"][0], 3.0)
            self.assertAlmostEqual(d["tared"]["F_norm"][1], 5.0)

            # 2. Semicolon delimiter
            semi_path = os.path.join(tmpdir, "semi.csv")
            with open(semi_path, "w", encoding="utf-8") as f:
                f.write("time;Fx;Fy;Fz;Tx;Ty;Tz\n")
                f.write("0.0;3.0;4.0;12.0;0.3;0.4;0.0\n")

            d_semi = plot_onrobot_ft.load_data(semi_path)
            self.assertEqual(len(d_semi["time"]), 1)
            self.assertAlmostEqual(d_semi["tared"]["F_norm"][0], 13.0)

    def test_directory_argument(self):
        """Test passing a directory path directly to plot_onrobot_ft.py CLI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "OnRobot_force_20260924_120000.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["time_rel_s", "time_epoch_s", "sample_counter",
                                 "Fx_tared_N", "Fy_tared_N", "Fz_tared_N",
                                 "Tx_tared_Nm", "Ty_tared_Nm", "Tz_tared_Nm",
                                 "status"])
                writer.writerow([0.0, 1000.0, 1, 3.0, 4.0, 0.0, 0.1, 0.2, 0.2, "OK"])

            script = os.path.join(SCRIPT_DIR, "plot_onrobot_ft.py")
            out_png = os.path.join(tmpdir, "dir_out.png")
            res = subprocess.run(
                [sys.executable, script, tmpdir, "--save-only", "-o", out_png],
                capture_output=True, text=True, check=True
            )
            self.assertIn("Points chargés : 1", res.stdout)
            self.assertTrue(os.path.isfile(out_png))

    def test_synthetic_ethercat_frame_decoding(self):
        """Test unpack_inputs and decode_status from test_onrobot_ft.py."""
        # Frame structure: 6f (floats), 6i (ints), h (divider), H (counter), I (status)
        floats = (3.0, 4.0, 12.0, 0.3, 0.4, 0.0)
        ints = (3000, 4000, 12000, 300, 400, 0)
        divider = 1000
        sc = 1234
        status_u32 = 0  # OK

        payload = struct.pack("<6f6ihHI", *floats, *ints, divider, sc, status_u32)
        self.assertEqual(len(payload), 56)

        d = test_onrobot_ft.unpack_inputs(payload)
        self.assertAlmostEqual(d["floats"]["Fx"], 3.0, places=5)
        self.assertAlmostEqual(d["floats"]["Fy"], 4.0, places=5)
        self.assertAlmostEqual(d["floats"]["Fz"], 12.0, places=5)
        self.assertAlmostEqual(d["floats"]["Tx"], 0.3, places=5)
        self.assertAlmostEqual(d["floats"]["Ty"], 0.4, places=5)
        self.assertAlmostEqual(d["floats"]["Tz"], 0.0, places=5)

        self.assertEqual(d["sample_counter"], 1234)
        self.assertEqual(d["status"]["summary"], "OK")
        self.assertFalse(d["status"]["multiple_errors"])

        # Check scaled ints
        self.assertAlmostEqual(d["scaled"]["Fx"], 3.0, places=5)
        self.assertAlmostEqual(d["scaled"]["Fz"], 12.0, places=5)

        # Norm check on unpacked floats
        f_norm = math.sqrt(d["floats"]["Fx"]**2 + d["floats"]["Fy"]**2 + d["floats"]["Fz"]**2)
        t_norm = math.sqrt(d["floats"]["Tx"]**2 + d["floats"]["Ty"]**2 + d["floats"]["Tz"]**2)
        self.assertAlmostEqual(f_norm, 13.0, places=5)
        self.assertAlmostEqual(t_norm, 0.5, places=5)

    def test_status_bitfield_overload(self):
        """Test decode_status detects overload and error codes."""
        # Bit 7 = Fz overload, Bit 9 = Fx overload
        status_val = (1 << 7) | (1 << 9)
        st = test_onrobot_ft.decode_status(status_val)
        self.assertTrue(st["overload"]["Fz"])
        self.assertTrue(st["overload"]["Fx"])
        self.assertFalse(st["overload"]["Fy"])
        self.assertIn("OVERLOAD: Fz,Fx", st["summary"])

        # Sensor error group = 1 (bits 10..12) -> code 1 = "sensor not detected"
        status_err = 1 << 10
        st_err = test_onrobot_ft.decode_status(status_err)
        self.assertEqual(st_err["sensor_error_group"], 1)
        self.assertIn("sensor not detected", st_err["summary"])


if __name__ == "__main__":
    unittest.main()

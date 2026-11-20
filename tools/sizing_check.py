#!/usr/bin/env python3
"""
sizing_check.py - first-order sizing numbers for the SC buck-boost converter.

Reproduces the "workbench model" in docs/reference/SC_Buck-Boost_Converter_System_Design_Notes.pdf
(pages 7-9) so anyone can change one number and see what happens.

    python3 tools/sizing_check.py                 # default numbers from the design notes
    python3 tools/sizing_check.py --cfly 4.7e-9   # try a smaller flying cap
    python3 tools/sizing_check.py --help

Pure Python 3, no packages needed. These are FIRST-ORDER estimates, not simulation results.
The same equations are implemented in veriloga/power_stage/pwr_avg.va.
"""
import argparse
import math

# Mode table: name, gain m, SSL factor k  (Rssl = 1 / (k * fsw * Cfly))
MODES = [("x2", 2.0, 1.0), ("x1", 1.0, 1.0), ("x1/2", 0.5, 4.0)]


def ron(vin, a):
    """Switch on-resistance. Rises at low Vin because gate overdrive shrinks (design notes p.7)."""
    vdrive = min(vin, a.vnom)
    vov = max(vdrive - a.vth, 0.05)
    return a.ron_full * (a.vnom - a.vth) / vov


def rout(vin, fsw, k, a):
    rssl = 1.0 / (k * fsw * a.cfly)
    rfsl = 2.0 * ron(vin, a)
    return math.hypot(rssl, rfsl)


def imax(vin, m, k, a, fsw=None):
    """Largest current a mode can regulate at a given fsw (default: VCO ceiling)."""
    fsw = a.fmax if fsw is None else fsw
    return (m * vin - a.vout) / rout(vin, fsw, k, a)


def fsw_required(vin, m, k, iout, a):
    """Solve Rout(fsw) = (m*Vin - Vout)/Iout for fsw. Returns None if impossible at any fsw."""
    dv = m * vin - a.vout
    if dv <= 0:
        return None
    r_need = dv / iout
    rfsl = 2.0 * ron(vin, a)
    if r_need <= rfsl:
        return None  # fast-switching limit alone is too big
    rssl = math.sqrt(r_need ** 2 - rfsl ** 2)
    return 1.0 / (k * rssl * a.cfly)


def band_edges(a):
    """Weakest point of each band, from the design notes' threshold rule."""
    h = a.hyst / 2
    return [
        ("x2", 2.0, 1.0, a.vin_min),          # x2 bottom: least headroom, highest Ron
        ("x1", 1.0, 1.0, a.v_lo - h),         # x1 low edge (~1.175 V)
        ("x1/2", 0.5, 4.0, a.v_hi - h),       # x1/2 low edge (~2.375 V)
    ]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cfly", type=float, default=6.8e-9, help="flying cap [F] (notes: 6.8 nF)")
    p.add_argument("--cout", type=float, default=1.5e-6, help="output cap [F] (notes: 1.5 uF)")
    p.add_argument("--ron-full", type=float, default=0.5, help="switch Ron at full 1 V drive [ohm]")
    p.add_argument("--vth", type=float, default=0.4, help="switch threshold [V] (check PDK)")
    p.add_argument("--vnom", type=float, default=1.0, help="max useful gate drive in Ron formula [V]")
    p.add_argument("--fmax", type=float, default=20e6, help="fsw ceiling [Hz] (ring runs at 2x)")
    p.add_argument("--fmin", type=float, default=100e3, help="fsw floor [Hz]")
    p.add_argument("--vout", type=float, default=1.0)
    p.add_argument("--iout", type=float, default=20e-3)
    p.add_argument("--vin-min", type=float, default=0.6)
    p.add_argument("--vin-max", type=float, default=3.0)
    p.add_argument("--v-lo", type=float, default=1.2, help="x2/x1 threshold [V]")
    p.add_argument("--v-hi", type=float, default=2.4, help="x1/x1/2 threshold [V]")
    p.add_argument("--hyst", type=float, default=0.05, help="total hysteresis per threshold [V]")
    a = p.parse_args()

    print("=" * 72)
    print("SC buck-boost first-order sizing  (Cfly=%.2g F, Cout=%.2g F, Ron_full=%.2g ohm, fsw<=%.3g Hz)"
          % (a.cfly, a.cout, a.ron_full, a.fmax))
    print("=" * 72)

    print("\n1) Weakest point of each mode band, at the fsw ceiling")
    print("   %-5s %7s %8s %8s %9s %9s  %s" % ("mode", "Vin", "Ron", "Rout", "Imax", "f_req", "meets Iout?"))
    for name, m, k, vin in band_edges(a):
        i = imax(vin, m, k, a)
        f = fsw_required(vin, m, k, a.iout, a)
        fs = "%.2f MHz" % (f / 1e6) if f else "impossible"
        print("   %-5s %6.3fV %7.2fO %7.2fO %7.1fmA %9s  %s" %
              (name, vin, ron(vin, a), rout(vin, a.fmax, k, a), i * 1e3, fs,
               "yes" if i >= a.iout else "NO"))

    print("\n2) Required fsw at Iout = %.0f mA vs. Vin (mode chosen by thresholds, rising Vin)" % (a.iout * 1e3))
    fmin_seen, fmax_seen = 1e99, 0
    for vin in [0.6, 0.8, 1.0, 1.15, 1.25, 1.5, 1.8, 2.1, 2.35, 2.45, 2.7, 3.0]:
        if vin < a.v_lo:
            name, m, k = MODES[0]
        elif vin < a.v_hi:
            name, m, k = MODES[1]
        else:
            name, m, k = MODES[2]
        f = fsw_required(vin, m, k, a.iout, a)
        if f:
            fmin_seen, fmax_seen = min(fmin_seen, f), max(fmax_seen, f)
        print("   Vin=%.2f V  %-5s f_req = %s" % (vin, name, "%.3f MHz" % (f / 1e6) if f else "impossible"))
    print("   -> span about %.2f to %.1f MHz at full load" % (fmin_seen / 1e6, fmax_seen / 1e6))

    print("\n3) Light load: current delivered at the fsw floor (%.0f kHz). Loads below this burst." % (a.fmin / 1e3))
    for name, m, k, vin in [("x2", 2.0, 1.0, a.v_lo - a.hyst / 2), ("x1", 1.0, 1.0, a.v_hi - a.hyst / 2),
                            ("x1/2", 0.5, 4.0, a.vin_max)]:
        print("   %-5s Vin=%.3f V  I_at_floor = %.2f mA" % (name, vin, imax(vin, m, k, a, a.fmin) * 1e3))

    print("\n4) Ripple step from one charge transfer, Cfly/(Cfly+Cout) * (m*Vin - Vout), worst at top of each band")
    for name, m, vin in [("x2", 2.0, a.v_lo + a.hyst / 2), ("x1", 1.0, a.v_hi + a.hyst / 2), ("x1/2", 0.5, a.vin_max)]:
        step = a.cfly / (a.cfly + a.cout) * (m * vin - a.vout)
        print("   %-5s Vin=%.3f V  step = %.1f mV" % (name, vin, step * 1e3))
    print("   (add the hold-comparator hysteresis to get total ripple)")

    print("\n5) Ideal efficiency ceiling  eta = Vout / (m * Vin)")
    for vin, name, m in [(2.4, "x1/2", 0.5), (2.4, "x1", 1.0), (0.6, "x2", 2.0), (1.2, "x1", 1.0)]:
        print("   Vin=%.1f V in %-5s -> %.0f %%" % (vin, name, 100 * a.vout / (m * vin)))
    print("   NOTE: 2.4 V sits on the x1/x1/2 threshold. Approached from below it is still x1 (~42 %).")

    print("\n6) Loop plant spread (small-signal, SSL-dominated)")
    print("   DC gain dVout/dfsw = dV/fsw ; output pole wp = k*fsw*Cfly/Cout")
    print("   %-5s %6s %6s %9s %12s %12s %10s" % ("mode", "Vin", "Iout", "fsw", "K_lin[V/V]", "K_exp[V/V]", "pole[Hz]"))
    span = math.log(a.fmax / a.fmin)  # exponential VCO law: dfsw/dvctrl = fsw * ln(fmax/fmin) / 1V
    klin_all, kexp_all, pole_all = [], [], []
    for name, m, k, vin in [("x2", 2.0, 1.0, 0.6), ("x2", 2.0, 1.0, 1.175), ("x1", 1.0, 1.0, 1.175),
                            ("x1", 1.0, 1.0, 2.375), ("x1/2", 0.5, 4.0, 2.375), ("x1/2", 0.5, 4.0, 3.0)]:
        for iout in (1e-3, 20e-3):
            f = fsw_required(vin, m, k, iout, a)
            if not f or f < a.fmin or f > a.fmax:
                continue
            dv = m * vin - a.vout
            kvco_lin = (a.fmax - a.fmin) / 1.0       # Hz/V over a 1 V control range
            kvco_exp = f * span / 1.0
            klin, kexp = dv / f * kvco_lin, dv / f * kvco_exp
            pole = k * f * a.cfly / a.cout / (2 * math.pi)
            klin_all.append(klin); kexp_all.append(kexp); pole_all.append(pole)
            print("   %-5s %5.2fV %4.0fmA %7.2fMHz %12.3g %12.3g %10.0f" %
                  (name, vin, iout * 1e3, f / 1e6, klin, kexp, pole))
    print("   gain spread: linear VCO law %.0fx, exponential law %.0fx ; pole spread %.0fx"
          % (max(klin_all) / min(klin_all), max(kexp_all) / min(kexp_all), max(pole_all) / min(pole_all)))


if __name__ == "__main__":
    main()

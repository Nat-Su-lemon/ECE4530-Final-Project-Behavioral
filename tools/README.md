# Tools

## `sizing_check.py`

First-order sizing calculator. It reproduces the design notes' "workbench model" (p.7–9) so anyone can change one number and immediately see the consequences. Pure Python 3, no packages needed.

```bash
python3 tools/sizing_check.py                  # design-notes defaults
python3 tools/sizing_check.py --cfly 4.7e-9    # smaller flying cap
python3 tools/sizing_check.py --fmax 15e6 --ron-full 0.8
python3 tools/sizing_check.py --help           # all options
```

It prints six sections:

1. **Weakest point of each mode band:** Ron, Rout, Imax at the fsw ceiling, and the fsw needed for 20 mA.
2. **Required fsw vs. Vin** at full load (the frequency range the VCO must cover).
3. **Light load:** current delivered at the fsw floor (below this, the converter bursts).
4. **Ripple step** from one charge transfer, worst case per band.
5. **Ideal efficiency ceilings**, including the 2.4 V threshold warning ([OPEN-03](../docs/process/OPEN_ISSUES.md#open-03)).
6. **Loop plant spread:** DC gain and output pole across corners, linear vs. exponential VCO law ([OPEN-04](../docs/process/OPEN_ISSUES.md#open-04)).

The equations match `veriloga/power_stage/pwr_avg.va`. If you change one, change the other.

When a design number changes, rerun this script and update the table in [`docs/design/02_power_stage.md` §9](../docs/design/02_power_stage.md#9-current-numbers-output-of-python3-toolssizing_checkpy).

# 02: Power Stage (switch network, Cfly, gate drive)

**Owner:** Nathaniel. **Models:** [`veriloga/power_stage/pwr_sw.va`](../../veriloga/power_stage/pwr_sw.va) (L2, one switch + driver) and [`veriloga/power_stage/pwr_avg.va`](../../veriloga/power_stage/pwr_avg.va) (L1, the whole stage averaged).
**Reference:** design notes p.5–9.

## 1. Topology

One flying capacitor C1 and five switches. Switches **a** and **b** connect C1+ (`c1p`) to Vin and Vout. Switches **c, d, e** connect C1− (`c1n`) to ground, Vin and Vout. Only c, d and e change with the mode. (Net diagram: [01_interfaces](01_interfaces.md#power-stage-nets).)

## 2. Switch phases by mode

Every mode runs two non-overlapping phases, **Φ1** and **Φ2**, with a dead time between them.

| Mode | Gain m | Φ1 closed | Φ2 closed | What C1 does |
|---|---|---|---|---|
| ×2 (step-up) | 2 | a, c | b, d | Charges to Vin. Then d lifts its bottom plate to Vin, and b delivers about 2·Vin |
| ×1 (charge bucket) | 1 | a, c | b, c | Charges to Vin, then shares charge with Cout. c follows both phases and is off in the gap |
| ×½ (step-down) | ½ | a, e | b, c | In series between Vin and Vout in Φ1, then in parallel with Cout in Φ2 |

## 3. Routing by switch (what `mode_route` implements)

| Control | ×½ | ×1 | ×2 |
|---|---|---|---|
| ctl_a | Φ1 | Φ1 | Φ1 |
| ctl_b | Φ2 | Φ2 | Φ2 |
| ctl_c | Φ2 | **Φ1 OR Φ2** | Φ1 |
| ctl_d | off | off | Φ2 |
| ctl_e | Φ1 | off | off |

Every control comes from a phase. So **when the clock stops and both phases are low, all five switches are off**, with no special parked state ([DEC-008](../process/DECISIONS.md#dec-008)). The v0.1 plan had c held constantly ON in ×1; that changed to Φ1|Φ2 here so that "stopped" automatically means "all off".

## 4. Pairs that must never conduct together

| Pair | What shorts | When it could happen |
|---|---|---|
| a & b | Vin to Vout through C1 | Not enough dead time / driver skew |
| c & d | Vin to ground | ×2, not enough dead time |
| c & e | Vout to ground | ×½, not enough dead time |
| d & e | Vin to Vout | Only during a bad mode change. Prevented because the latch changes only while stopped |

[`veriloga/checkers/sw_check.va`](../../veriloga/checkers/sw_check.va) watches all four pairs in every L2 simulation and prints `SW_CHECK` lines to the log.

## 5. Gate drive and oxide stress (Nathaniel's main design problem)

The table below assumes a threshold near 0.4 V. Check the threshold and the device ratings against the PDK.

| Switch | Connects | Active in | Highest terminal voltage | Gate drive | Device guess |
|---|---|---|---|---|---|
| a | Vin ↔ C1+ | all modes, Φ1 | up to 3 V | **Boosted**: gate above Vin + Vth (≈3.4 V at Vin = 3 V) | likely thick-oxide |
| b | C1+ ↔ Vout | all modes, Φ2 | up to 3 V (×½), 2.4 V (×1) | **Boosted** in ×2 and ×1. In ×½, a Vin ≥ 2.4 V can drive it directly | likely thick-oxide |
| c | C1− ↔ GND | ×½ Φ2, ×1 both, ×2 Φ1 | ≈1.2 V | Plain, ~1 V is enough | thin may do |
| d | Vin ↔ C1− | ×2, Φ2 only | up to 3 V while off in other modes | **Boosted**, bootstrapped from C1+ (≈2·Vin in Φ2) | likely thick-oxide |
| e | C1− ↔ Vout | ×½, Φ1 only | ≈1.2 V | Plain, a Vin ≥ 2.4 V is enough | thin may do |

**First task ([OPEN-01](../process/OPEN_ISSUES.md#open-01)):** list the PDK devices with their max Vds and Vgs. That decides the driver topology. If there are no thick-oxide devices, the proposal's external-switch plan carries more weight.

Other gate-drive rules from the design notes:
- Gate nodes and bootstrap caps **leak**. A 1 pF bootstrap cap with 1 nA of leakage loses 1 V in about 1 µs, so gate nodes need pull-downs and a power-on reset.
- Driver edges must fit inside the dead-time budget. Verify dead time **at the switch gates**, not at the non-overlap output.
- Floating level shifters with 1 V thresholds are probably the hardest circuit in the project.

## 6. Output resistance, current capability, efficiency

Charge conservation means the input current is m × the output current, so the **ideal efficiency is η = Vout / (m·Vin)**. Real efficiency is lower because of output resistance, gate-drive loss and control current.

| Quantity | Formula | Notes |
|---|---|---|
| Slow-switching limit | Rssl = 1 / (k · fsw · Cfly) | k = 1 for ×2 and ×1, k = 4 for ×½ |
| Fast-switching limit | Rfsl ≈ 2 · Ron | two switches in series in each phase |
| Ron vs. drive | Ron = Ron_full · (1 V − Vth) / (min(Vin, 1 V) − Vth) | rises at low Vin because overdrive shrinks |
| Output resistance | Rout = √(Rssl² + Rfsl²) | |
| Max regulated current | Imax = (m·Vin − Vout) / Rout | |
| Required fsw | fsw = Iout / (k · Cfly · ΔV), corrected for Rfsl | ΔV = m·Vin − Vout |
| Gate-drive loss | P = Cg · Vin² · fsw | lower fsw at light load saves power |

These exact equations are in `pwr_avg.va` and [`tools/sizing_check.py`](../../tools/sizing_check.py).

## 7. Mode thresholds

**Rule:** a mode is allowed once its ideal output is ≥ 20 % above Vout. That puts the thresholds at **1.2 V and 2.4 V**, each with about **50 mV** of hysteresis. The headroom percentage is the real design parameter; the thresholds follow from it.

| Mode | Vin range | Ideal output | Weakest point for current |
|---|---|---|---|
| ×2 | 0.6 – 1.2 V | 1.2 – 2.4 V | Vin = 0.6 V: only 0.2 V headroom and Ron at its highest |
| ×1 | 1.2 – 2.4 V | 1.2 – 2.4 V | Low edge ≈1.18 V, where Rout ≈ 1/(f·Cfly) |
| ×½ | 2.4 – 3.0 V | 1.2 – 1.5 V | Low edge ≈2.4 V |

> ⚠️ The **efficiency anchor (2.4 V)** sits right on the ×1/×½ threshold. Approached from below, 2.4 V is still ×1, where the ideal efficiency is only ≈42 %. See [OPEN-03](../process/OPEN_ISSUES.md#open-03). `tb_L2_T4_efficiency.scs` approaches 2.4 V from above for this reason.

## 8. Ripple

Ripple has two parts:
1. the hold-comparator hysteresis (in burst mode), and
2. the step from one charge transfer, ≈ Cfly/(Cfly + Cout) × (m·Vin − Vout).

The step is largest at the top of the ×2 and ×1 bands, so it sets the Cfly : Cout ratio. With Cfly = 6.8 nF and Cout = 1.5 µF, `sizing_check.py` gives a 6.5 mV step. The design notes quote ≈8 mV worst case, which probably includes a hysteresis or margin term ([OPEN-10](../process/OPEN_ISSUES.md#open-10)). Either way it is inside 10 mV, but not by much once the comparator hysteresis is added.

## 9. Current numbers (output of `python3 tools/sizing_check.py`)

Inputs: Cfly = 6.8 nF, Cout = 1.5 µF, Ron_full = 0.5 Ω, Vth = 0.4 V, fsw ceiling 20 MHz, floor 100 kHz. These reproduce the design notes' workbench model.

| Check | Result | Design notes |
|---|---|---|
| ×2 at 0.6 V: Imax at 20 MHz | 25.2 mA (needs 15.4 MHz for 20 mA) | meets 20 mA |
| ×1 at 1.175 V: Imax at 20 MHz | 23.6 mA (needs 16.9 MHz) | "about 23.6 mA" ✓ |
| ×½ at 2.375 V: Imax at 20 MHz | 89.6 mA (needs 3.9 MHz) | ✓ |
| fsw span needed at 20 mA | ≈1.5 – 17 MHz; down to ≈0.07 MHz at light load | "0.07 to 15 MHz" ✓ |
| Current at the 100 kHz floor | ≈0.9 – 1.4 mA → lighter loads burst | "about 1 mA" ✓ |
| Output pole range | ≈80 Hz – 12 kHz | "80 Hz to 10 kHz" ✓ |

Rerun the script whenever a number changes, and update this table in the same commit.

## 10. How the power stage is modeled

### L1: `pwr_avg` (averaged)
The whole switch network becomes a Thevenin source **m·Vin behind Rout(fsw, Vin, mode)**, and draws **m·Iout** from Vin (plus optional gate loss `cg_tot·Vin·fsw`). It takes `vctrl` directly and converts it with the same VCO law as `vco.va`. Use it for long loop simulations (start-up, Vin ramps, load steps, compensation). It ignores ripple, the stop cycle during mode changes, and dead time.

### L2: `pwr_sw` × 5 + C1 (switched)
Each switch is a resistor that moves smoothly between Roff and **Ron(vdrv)**. Ron uses the formula above, with `vdrv` tied to `vin` in the testbenches. Optional parameters:

| Parameter | Use |
|---|---|
| `td` | driver delay. Set different values per switch to test dead-time margin against skew |
| `tsw` | on/off transition time |
| `coff` | switch capacitance p–n (from device size) |
| `cg` | gate charge drawn from `vdrv` at every turn-on → gate-drive loss appears in input power |

**Swap boundary ([DEC-011](../process/DECISIONS.md#dec-011)):** `pwr_sw` = driver + switch in ONE cell, controlled by a logic-level `ctl`. At L3 Nathaniel draws a `schematic` view of `pwr_sw` with the same pins. Inside it, the level shifter, driver and nMOS can be arranged however he wants. If the real version needs extra pins (a boosted rail, a bootstrap cap to C1+), add them to the `.va`, the symbol and all netlists in the same commit.

Recommended order for Nathaniel's swaps (also in [06](06_modeling_levels_and_swap_plan.md)):
1. Fill in `ron_full`, `coff`, `cg` from the chosen PDK device size. This is still behavioral, but realistic.
2. Real nMOS with an **ideal** floating gate drive (ideal sources referenced to each switch's source). This checks Ron, Vgs/Vds stress and efficiency.
3. Real drivers / level shifters / bootstrap. Move `nov_check` to the gate nodes and check skew.

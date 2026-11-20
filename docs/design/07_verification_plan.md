# 07: Verification Plan

Two kinds of tests:
- **Unit tests (U)** check one block, or one group of blocks, with ideal stimulus.
- **Standard testbenches (T1–T6)**, defined in the design notes p.15, check the whole converter at L1 (averaged) and L2 (switched).

**Rule:** testbenches do not change when a block is swapped. Only the config view changes ([08](08_cadence_workflow.md)).

All runnable netlists are in [`sim/spectre/`](../../sim/spectre/). How to run them: [`sim/README.md`](../../sim/README.md).

## Checkers (always on)

| Checker | Watches | Log keyword |
|---|---|---|
| [`nov_check`](../../veriloga/checkers/nov_check.va) | Two signals that must never be high together; reports minimum dead time | `NOV_CHECK` |
| [`sw_check`](../../veriloga/checkers/sw_check.va) | Forbidden pairs a&b, c&d, c&e, d&e | `SW_CHECK` |

After every L2 / U1 run: `grep -E "NOV_CHECK|SW_CHECK" <logfile>`. Any count other than 0 is a failure.

## Unit tests

### U1: Clock chain
`tb_U1_clk_chain.scs`. Fixed vctrl, scripted hold pulses, a fault pulse, mode changes ×1 → ×½ → ×2 → ×1.

| Check | Pass criterion |
|---|---|
| Frequency | fsw of `q` = law(VCTRL) (10.05 MHz at VCTRL = 0.5, linear) |
| Non-overlap | `NOV_CHECK` overlaps = 0, min dead time ≈ `TDEAD` |
| Forbidden pairs | `SW_CHECK` all 0 |
| Stop timing | Phases stop only after a Φ2 falling edge; no truncated pulses |
| Restart | First pulse after every stop is a full-width Φ1 |
| Mode change | Latch changes only while `stopped` = 1; `mismatch` clears after the latch; ctl_a…e follow the routing table in each mode |

### U2: Power stage, open loop
`tb_U2_pwr_open_loop.scs`. Ideal Φ1/Φ2 pulse sources and routing gains, no logic.

| Check | Pass criterion |
|---|---|
| No-load ratio (RLOAD large) | Vout → m·Vin for each mode |
| Loaded droop | Vout ≈ m·Vin − Iout·Rout, with Rout from `tools/sizing_check.py` at the same FSW (±10 %) |
| ×2 at 0.6 V, 20 mA | Vout ≥ 1.0 V at FSW ≈ 15.4 MHz (the weakest corner) |

## Standard testbenches (design notes p.15)

| Test | Stimulus | Shows | L1 netlist | L2 netlist | Pass criterion (proposed) |
|---|---|---|---|---|---|
| **T1** | Start-up at Vin = 0.6, 1.8, 3 V | Soft-start, inrush, first pulses | `tb_L1_T1_startup` | `tb_L2_T1_startup` | Vout settles to 1 V ± 1 %; first pulse is Φ1; record peak I(Vin) |
| **T2** | Vin ramp 0.6 → 3 → 0.6 V at 20 mA | Mode changes, hysteresis, Vout dip | `tb_L1_T2_vin_ramp` | `tb_L2_T2_vin_ramp` | Switch points at 1.225/2.425 V rising and 1.175/2.375 V falling; no chatter; Vout dip recorded (limit TBD, [OPEN-07](../process/OPEN_ISSUES.md#open-07)) |
| **T3** | Load step 1 → 20 mA at Vin = 0.6, 2.4, 3 V | Transient and recovery | `tb_L1_T3_load_step` | (add when needed) | Undershoot/overshoot and recovery time recorded (limit TBD) |
| **T4** | DC sweep of Vin at 1, 5, 20 mA | Efficiency and ripple curves | (L1 gives η ceiling only) | `tb_L2_T4_efficiency` (one point; sweep VIN) | η ≥ 75 % at 2.4 V / 20 mA (in ×½); ripple ≤ 10 mV p-p |
| **T5** | Output short, overload, Vin below UVLO | Protection and recovery | - | (add with OCP model) | Switching stops, all switches off, clean restart |
| **T6** | Light-load sweep 0.05 – 5 mA at Vin = 0.6, 1.2, 2.4 V | VCO floor, hold-gate bursts, ripple in hold | `tb_L1_T6_light_load` | (L2 for real ripple) | Regulates in bursts; ripple ≤ 10 mV |

## Measurements (ADE calculator / Spectre)

| Quantity | Expression | Window |
|---|---|---|
| Input power | `average(-V(vin) * I(Vin:p))` (Spectre: current into the source's + terminal) | last 20 % of the sim, after settling |
| Output power | `average(V(vout) * V(vout) / RLOAD)` | same |
| Efficiency | Pout / Pin. Report power-stage-only and with control/logic supply separately once real supplies exist | same |
| Ripple | `ymax(V(vout)) − ymin(V(vout))` | same |
| fsw | `frequency(V(q))` | steady state |
| Mode switch points | `cross(V(mt_half) − VDDL/2, …)` and the Vin value at those times | T2 |

## Regression set

Run after **every** block swap, and before merging any change to a model:

1. `tb_U1_clk_chain`: 0 checker violations
2. `tb_U2_pwr_open_loop` in ×2 at 0.6 V
3. `tb_L1_T2_vin_ramp`: switch points unchanged
4. `tb_L2_T1_startup` at 0.6 V and 3.0 V
5. `tb_L2_T2_vin_ramp`: 0 checker violations
6. `tb_L2_T4_efficiency` at 2.4 V (from above)

Record results in the PR description and, for milestone swaps, in `CHANGELOG.md`.

## Practical tips

- `errpreset=moderate` is enough for the behavioral runs. Use `conservative` only for final efficiency numbers.
- The VCO's `$bound_step` sets the timestep in L2, so don't add a global `maxstep` unless needed.
- L2 runs are long. The netlists save only the important nets (`save=selected`).
- Approach Vin = 2.4 V **from above** when measuring the efficiency anchor ([OPEN-03](../process/OPEN_ISSUES.md#open-03)).

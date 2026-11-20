# 06: Modeling Levels and Swap Plan

The project moves from whiteboard to layout in **refinement levels** (design notes p.14). Each block moves down a level **only after its current model passes its own test**, and **the older model stays as the reference**.

## Levels

| Level | Content | Exit criterion | In this repo |
|---|---|---|---|
| **L0** whiteboard | Spec, block diagram, budgets | Every block has an owner, inputs, outputs and a target | ✅ `docs/design/00–05`, design-notes PDF |
| **L1** ideal Verilog-A | Averaged power stage, ideal error amp + hold comparator, ideal VCO with hold gate, mode selector | Standard testbenches run end to end, **interfaces frozen** | `pwr_avg`, `err_amp`, `hold_cmp`, `mode_sel`, `uvlo_fault`; `sim/spectre/tb_L1_*` |
| **L2** non-ideal Verilog-A | Five switches with Ron, Roff, Coff, real dead time, hold gate and mode latch | Spec met with margin, block specs written | Full clock chain + 5× `pwr_sw`; `sim/spectre/tb_L2_*`, `tb_U*` |
| **L3** schematics | One block at a time replaced with transistors | No ideal blocks left except external parts | Cadence `schematic` views, selected by config ([08](08_cadence_workflow.md)) |
| **L4** real components | PDK or external FETs, capacitors with ESR and board parasitics | Results table for report and poster | - |
| **L5** layout | Layout, extraction, post-layout simulation | Post-layout spec table complete | - |

### Why two behavioral levels? ([DEC-005](../process/DECISIONS.md#dec-005))

- **L1 (averaged)** has no switching events, so a 20 ms Vin ramp takes seconds. It's the right tool for loop compensation, mode thresholds and start-up behavior.
- **L2 (switched)** simulates every edge. It's slow but shows ripple, dead time, stop/restart, forbidden pairs and efficiency.

The two share parameters (`common_params.scs`) and the same VCO law. **The first L2 check is that it agrees with L1** (same mode switch points, same average Vout, similar settling).

## Model ↔ level map

| Block | L1 | L2 | L3 (real) owner |
|---|---|---|---|
| Power stage | `pwr_avg` | 5× `pwr_sw` + C1 | Nathaniel |
| Gate drivers | (inside `pwr_avg`) | (inside `pwr_sw`: `td`, `tsw`, `cg`, Ron(vdrv)) | Nathaniel |
| VCO | (law inside `pwr_avg`) | `vco` | Sam |
| ÷2, NOV, hold gate, mode latch | (not in loop; unit test `tb_U1`) | `div2`, `nov_gen`, `en_hold`, `mode_route` | Sam |
| Mode select | `mode_sel` | `mode_sel` | Sam |
| Error amp, hold comparator | `err_amp`, `hold_cmp` | same | Brandon |
| UVLO / soft-start / OCP | `uvlo_fault` | same | Alex |
| Bandgap, LDO | ideal sources | ideal sources | Alex |

## Swap milestones (L2 → L3)

Order is chosen by **impact on efficiency and correctness** and by **owner readiness**. Owners work in parallel, but **only one swap at a time is merged into the shared config**, and the regression set ([07](07_verification_plan.md#regression-set)) is rerun after each one.

| Milestone | Swap | Owner | Why now | Watch |
|---|---|---|---|---|
| **M0** | Nothing. All L2 behavioral, regression passes, golden waveforms saved | all | Baseline | Everything |
| **M1** | `pwr_sw` parameters from the PDK device (Ron, Coff, Cg), then real nMOS with an *ideal floating* gate drive | Nathaniel | Real Ron and capacitances set efficiency and Rout | T4 efficiency, ×2 at 0.6 V current |
| **M2** | Real gate drivers / level shifters / bootstrap inside `pwr_sw` | Nathaniel | Hardest analog piece; adds skew | Move `nov_check` to gate nodes; dead time > 0 at all corners; Vgs/Vds within ratings |
| **M3** | `div2` (std-cell DFF) → `en_hold`, `mode_route` (logic) → `nov_gen` | Sam | Pure digital, low risk | `tb_U1` matches behavioral timing |
| **M4** | `vco` (current-starved ring) | Sam | Real f(vctrl), supply sensitivity | Refit `vco.va` and `pwr_avg.va` law to the measured curve |
| **M5** | `err_amp`, `hold_cmp` | Brandon | Needs a realistic plant to tune against | T3, T6, stability at every band edge |
| **M6** | `mode_sel` comparators | Sam | Offsets shift thresholds | T2 hysteresis, no chatter |
| **M7** | LDO, bandgap, UVLO / soft-start / OCP | Alex | Logic supply at Vin = 0.6 V | T1, T5 with the real `vdd` |

## Per-swap checklist (copy into your PR description)

- [ ] Real schematic has **exactly** the same pin names and order as the `.va`/symbol
- [ ] Block's own unit test passes at schematic level, compared against the behavioral run
- [ ] Config override set for this one cell; nothing else changed
- [ ] Regression set rerun; overlays against the M0 golden waveforms saved
- [ ] `NOV_CHECK` and `SW_CHECK` report 0 violations
- [ ] Characterized parameters pushed **back into the behavioral model** (e.g., VCO law, comparator delay/offset, Ron, driver delay)
- [ ] New milestone config saved; `CHANGELOG.md` entry added; this table updated

## Keeping behavioral models alive

Never delete a `veriloga` view after its block goes real. Refit its parameters to the real circuit instead. Teammates can then keep running fast behavioral simulations that still reflect reality, and full transistor-level runs are needed only for final verification.

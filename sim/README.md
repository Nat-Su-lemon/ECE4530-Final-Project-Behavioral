# Simulation

Plain-text **Spectre** netlists for every testbench ([DEC-015](../docs/process/DECISIONS.md#dec-015)). They run from the command line without drawing schematics, and they are the drawing reference for the Cadence testbench schematics.

## How the files fit together

```
sim/spectre/
  common_params.scs      shared numbers (Cfly, Cout, Ron, fsw limits, thresholds, ki...). Edit HERE.
  l1_core.scs            L1 circuit: pwr_avg + err_amp + hold_cmp + mode_sel + uvlo_fault + Cout + Rload
  l2_core.scs            L2 circuit: full clock chain + 5x pwr_sw + C1 + control + checkers
  tb_L1_T*.scs           L1 tests  = common_params + stimulus + l1_core + analysis
  tb_L2_T*.scs           L2 tests  = common_params + stimulus + l2_core + analysis
  tb_U*.scs              unit tests (self-contained)
```

## Run

```bash
cd sim/spectre                          # paths inside the netlists are relative to here
spectre tb_L1_T2_vin_ramp.scs +log tb_L1_T2_vin_ramp.log
grep -E "NOV_CHECK|SW_CHECK" *.log      # L2 and U1 runs: every count must be 0
viva &                                  # open the .raw results directory to plot
```

To change a test-specific value (VIN, RLOAD, TSTOP…), edit the `parameters` line at the top of that testbench. To change a shared value, edit `common_params.scs`. Spectre doesn't allow defining a parameter twice, which is why they are split this way.

## Testbench list

| File | Level | Test | Runtime | What to look at |
|---|---|---|---|---|
| `tb_U1_clk_chain.scs` | L2 | Unit: clock chain with scripted hold / fault / mode changes | seconds | checker counts, restart at Φ1, routing per mode |
| `tb_U2_pwr_open_loop.scs` | L2 | Unit: power stage with ideal phases (set mode with KC1/KC2/KD/KE) | seconds | Vout vs m·Vin, droop vs Rout |
| `tb_L1_T1_startup.scs` | L1 | T1 start-up (VIN_FINAL = 0.6 / 1.8 / 3.0) | fast | fault release, Vout settling, inrush |
| `tb_L1_T2_vin_ramp.scs` | L1 | T2 Vin ramp 0.6 → 3 → 0.6 V, 20 mA | fast | mode switch points, hysteresis, Vout dips |
| `tb_L1_T3_load_step.scs` | L1 | T3 load step 1 ↔ 20 mA (VIN = 0.6 / 2.4 / 3.0) | fast | undershoot, recovery, compensation |
| `tb_L1_T6_light_load.scs` | L1 | T6 light load (RLOAD 20 k … 200 Ω) | fast | vctrl at floor, hold_req bursts |
| `tb_L2_T1_startup.scs` | L2 | T1 start-up, switched | minutes | first pulse = Φ1, checkers, inrush |
| `tb_L2_T2_vin_ramp.scs` | L2 | T2 Vin ramp, compressed to 2 ms | long | mode-change handshake, checkers, agreement with L1 |
| `tb_L2_T4_efficiency.scs` | L2 | Efficiency + ripple at 2.4 V / 20 mA (from above) | minutes | η ≥ 75 %, ripple ≤ 10 mV |

Not written yet: L2 T3, T5 (needs an OCP model), a full T4 Vin sweep. Add them as needed, using the same pattern.

Pass criteria and measurement expressions: [`docs/design/07_verification_plan.md`](../docs/design/07_verification_plan.md).

## Status

⚠️ These netlists have not been run in Spectre yet ([OPEN-16](../docs/process/OPEN_ISSUES.md#open-16)). Expect small syntax fixes on the first run, and log them in `CHANGELOG.md`.

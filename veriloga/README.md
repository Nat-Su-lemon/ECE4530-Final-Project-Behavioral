# Verilog-A Models

The source of truth for every behavioral model ([DEC-001](../docs/process/DECISIONS.md#dec-001)). Each file holds one module. The **module name = file name = Cadence cell name**.

Every file starts with a header that says: owner of the real circuit, refinement level, pins, what is modeled, what is ignored, and what replaces it later. Read the header before using a model.

## Index

| Folder | File | Stage / role | Level | Pins (in order) | Real-circuit owner |
|---|---|---|---|---|---|
| `clock_chain/` | [`vco.va`](clock_chain/vco.va) | 1: ring VCO, vctrl → 2·fsw | L1/L2 | `vctrl, clk, vdd, vss` | Sam |
| | [`div2.va`](clock_chain/div2.va) | 2: ÷2, 50 % duty, rst holds q = 1 | L1/L2 | `clk, rst, q, qb, vdd, vss` | Sam |
| | [`nov_gen.va`](clock_chain/nov_gen.va) | 3: non-overlap, fixed dead time | L1/L2 | `clk, phi1, phi2, vdd, vss` | Sam |
| | [`en_hold.va`](clock_chain/en_hold.va) | 4: hold gate, stop in gap, restart at Φ1 | L1/L2 | `clk, phi1_in, phi2_in, hold_req, fault, mismatch, phi1, phi2, stopped, vdd, vss` | Sam |
| | [`mode_route.va`](clock_chain/mode_route.va) | 5: mode latch + routing to ctl_a…e | L1/L2 | `phi1, phi2, stopped, mt_half, mt_x2, ctl_a…ctl_e, mismatch, vdd, vss` | Sam |
| `power_stage/` | [`pwr_sw.va`](power_stage/pwr_sw.va) | one switch + driver, Ron(vdrv), gate loss | L2 | `p, n, ctl, vdrv, vdd, vss` | Nathaniel |
| | [`pwr_avg.va`](power_stage/pwr_avg.va) | whole power stage averaged + VCO law | L1 | `vin, vout, vctrl, hold_req, fault, mt_half, mt_x2, vdd, vss` | shared |
| `control/` | [`err_amp.va`](control/err_amp.va) | error amp, clamped integrator (+kp) | L1/L2 | `vout_sense, vref, vctrl, vdd, vss` | Brandon |
| | [`hold_cmp.va`](control/hold_cmp.va) | hold comparator (light load) | L1/L2 | `vout_sense, vref, hold_req, vdd, vss` | Brandon |
| | [`mode_sel.va`](control/mode_sel.va) | Vin thresholds with hysteresis | L1/L2 | `vin_sense, mt_half, mt_x2, vdd, vss` | Sam |
| `support/` | [`uvlo_fault.va`](support/uvlo_fault.va) | UVLO + start-up delay → fault | L1/L2 | `vin, fault, vdd, vss` | Alex |
| `checkers/` | [`nov_check.va`](checkers/nov_check.va) | test: overlap / dead-time monitor | test | `sig1, sig2, vdd, vss` | - |
| | [`sw_check.va`](checkers/sw_check.va) | test: forbidden switch pairs | test | `ctl_a…ctl_e, vdd, vss` | - |

## Shared coding rules

```verilog
`include "constants.vams"
`include "disciplines.vams"
// logic threshold
vth = V(vdd, vss) / 2;
// detect an input edge (puts a timestep exactly on it)
@(cross(V(in, vss) - vth, +1)) state = 1;
// drive a logic output that follows the supply
V(out, vss) <+ V(vdd, vss) * transition(state, td, tr);
```

- Only `@cross`, `@timer`, `@initial_step`, `@final_step`, `transition()`, `idtmod()`, `ddt()` and ordinary math. Nothing fancier.
- Integer state changes happen **only inside events**, never by comparing a voltage in the continuous part and feeding the result to `transition()`.
- Defaults are placeholders from the design notes. Testbenches override them from `sim/spectre/common_params.scs`.
- `vco.va` and `pwr_avg.va` implement the **same vctrl → fsw law**. Change both together.

## Status

⚠️ Not yet compiled in Spectre ([OPEN-16](../docs/process/OPEN_ISSUES.md#open-16)). Logic was checked with a Python event model. The first person to compile these, please record the result in `CHANGELOG.md`.

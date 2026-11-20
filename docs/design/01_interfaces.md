# 01: Interfaces and Conventions

**Freeze these first.** A real circuit can replace a behavioral model only if it has exactly the same pins. Changing a pin means changing the model, the symbol, every netlist that uses it, and this file, all in the same commit (see [CONTRIBUTING](../process/CONTRIBUTING.md)).

## Global conventions ([DEC-006](../process/DECISIONS.md#dec-006))

| Rule | Why |
|---|---|
| Every logic cell has `vdd` and `vss` pins. Outputs swing `vss`…`vdd`; inputs switch at `V(vdd,vss)/2`. | The real logic supply (Alex's LDO, maybe 0.6 V at start-up) drops in without editing any model. |
| Logic outputs are written `V(out,vss) <+ V(vdd,vss) * transition(state, td, tr);` | Smooth, simulator-friendly edges that follow the supply. |
| Logic inputs are detected with `@(cross(V(in,vss) - vth, ±1))`, never by thresholding inside `transition()`. | The simulator puts a timestep exactly on the edge, so timing is accurate. |
| Lowercase pin names, single wires, no buses. Same names in the `.va` file, the Cadence symbol and the future schematic. | Buses make Verilog-A and the symbol↔schematic swap more fragile. |
| Module name = Cadence cell name = file name. | Cadence expects the module name to match the cell. |
| Active-high unless the name says otherwise. | One less thing to get wrong. |
| Frequencies are quoted as **fsw** (switching frequency) unless the text says "ring". The ring runs at **2 × fsw** ([DEC-016](../process/DECISIONS.md#dec-016)). | The design notes quote fsw. |

## System signals (design notes p.3–4 → our pin names)

| Design-notes signal | Our net/pin | From → To | Meaning |
|---|---|---|---|
| vin_sense | `vin` (MVP: no divider) | Vin → mode_sel | Input voltage for the thresholds |
| vout_sense | `vout` (MVP: no divider) | Cout → err_amp, hold_cmp | Output feedback |
| vref | `vref` | Bandgap → err_amp, hold_cmp | Reference. MVP: ideal 1.0 V. If the bandgap is ~0.5 V, add a Vout divider in the testbench |
| vctrl | `vctrl` | err_amp → vco (stage 1) / pwr_avg | Frequency command, 0…1 V |
| hold_req | `hold_req` | hold_cmp → en_hold (stage 4) | Vout above target, stop the clock |
| mode_target | `mt_half`, `mt_x2` | mode_sel → mode_route (stage 5) | Wanted mode, a **level** (not a pulse). Two bits, see encoding below |
| stopped | `stopped` | en_hold → mode_route, div2.rst | Clock halted, all phases low |
| en / fault | `fault` (active high) | uvlo_fault (UVLO, soft-start, OCP) → en_hold | Fault reasons to stop the clock |
| mismatch request | `mismatch` | mode_route → en_hold | mode_target ≠ latched mode, so stop and change |
| reset | *(not a pin yet)* | POR → div2, latch, gate nodes | Known state at power-up. Behavioral models start in a safe state by themselves (`@initial_step`); add a real `por` pin at L3 ([OPEN-09](../process/OPEN_ISSUES.md#open-09)) |
| ctl_a … ctl_e | `ctl_a` … `ctl_e` | mode_route → gate drivers (inside `pwr_sw`) | One logic control per switch |
| gate_a … gate_e | *(internal to `pwr_sw` until L3)* | gate drivers → switches | Level-shifted gate drive |
| vdd_logic, vdd_drv, ibias | `vdd` (logic), `vdrv` (driver supply) | LDO → everything | MVP: ideal sources. `vdrv` is tied to `vin` in the testbenches |

Internal clock-chain nets: `clk` (ring, 2·fsw), `q`/`qb` (÷2 outputs, fsw), `phi1u`/`phi2u` (ungated phases), `phi1`/`phi2` (gated phases).

## Mode encoding

| `mt_half` | `mt_x2` | Wanted mode | Internal code in `mode_route` / `pwr_avg` | Ideal no-load Vout |
|---|---|---|---|---|
| 0 | 0 | ×1 | 0 | Vin |
| 1 | x | ×½ | 1 | Vin / 2 |
| 0 | 1 | ×2 | 2 | 2·Vin |

`mt_half` has priority. With the thresholds 0.75 V apart (1.2 vs 2.4 V), both bits can never be high at the same time from a working `mode_sel`; the priority only matters for bad stimulus.

## Cell list and pin order

Pin order matters for netlists and must match the Cadence symbol.

| Cell (= module = file) | Pins, in order | Level | Owner of real version |
|---|---|---|---|
| `vco` | `vctrl, clk, vdd, vss` | L1/L2 | Sam |
| `div2` | `clk, rst, q, qb, vdd, vss` | L1/L2 | Sam |
| `nov_gen` | `clk, phi1, phi2, vdd, vss` | L1/L2 | Sam |
| `en_hold` | `clk, phi1_in, phi2_in, hold_req, fault, mismatch, phi1, phi2, stopped, vdd, vss` | L1/L2 | Sam |
| `mode_route` | `phi1, phi2, stopped, mt_half, mt_x2, ctl_a, ctl_b, ctl_c, ctl_d, ctl_e, mismatch, vdd, vss` | L1/L2 | Sam |
| `pwr_sw` | `p, n, ctl, vdrv, vdd, vss` | L2 | Nathaniel |
| `pwr_avg` | `vin, vout, vctrl, hold_req, fault, mt_half, mt_x2, vdd, vss` | L1 | shared (loop model) |
| `err_amp` | `vout_sense, vref, vctrl, vdd, vss` | L1/L2 | Brandon |
| `hold_cmp` | `vout_sense, vref, hold_req, vdd, vss` | L1/L2 | Brandon |
| `mode_sel` | `vin_sense, mt_half, mt_x2, vdd, vss` | L1/L2 | Sam |
| `uvlo_fault` | `vin, fault, vdd, vss` | L1/L2 | Alex |
| `nov_check` *(test)* | `sig1, sig2, vdd, vss` | - | - |
| `sw_check` *(test)* | `ctl_a, ctl_b, ctl_c, ctl_d, ctl_e, vdd, vss` | - | - |

Hierarchy wrappers to draw in Cadence (schematic only), matching `sim/spectre/l2_core.scs`:

| Wrapper | Contains | Pins |
|---|---|---|
| `clk_gen` | vco, div2, nov_gen, en_hold, mode_route | `vctrl, hold_req, fault, mt_half, mt_x2, ctl_a…ctl_e, stopped, vdd, vss` |
| `pwr_stage` | 5× pwr_sw + C1 | `vin, vout, gnd, ctl_a…ctl_e, vdrv, vdd, vss` |
| `top_conv` | clk_gen + pwr_stage + err_amp + hold_cmp + mode_sel + uvlo_fault | `vin, vout, vref, vdd, gnd` |

## Power-stage nets

```
   Vin                 Vout              Vin
    |                   |                 |
   [a]                 [e]               [d]
    |                   |                 |
   c1p ----||---- c1n --+-----------------+
    |      C1           |
   [b]                 [c]
    |                   |
   Vout                GND          Cout from Vout to GND (testbench), plus load
```

| Switch | Between | Instance in netlists |
|---|---|---|
| a | vin ↔ c1p | `XSa (vin c1p ctl_a vin vdd 0)` |
| b | c1p ↔ vout | `XSb (c1p vout ctl_b vin vdd 0)` |
| c | c1n ↔ gnd | `XSc (c1n 0 ctl_c vin vdd 0)` |
| d | c1n ↔ vin | `XSd (c1n vin ctl_d vin vdd 0)` |
| e | c1n ↔ vout | `XSe (c1n vout ctl_e vin vdd 0)` |

The routing table and the forbidden pairs are in [02_power_stage](02_power_stage.md).

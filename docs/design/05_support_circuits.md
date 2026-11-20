# 05: Support Circuits (Alex)

**Owner:** Alex. **Models:** [`veriloga/support/uvlo_fault.va`](../../veriloga/support/uvlo_fault.va) plus ideal sources in the testbenches.
**Reference:** design notes p.2, 4, 14–15.

The support circuits feed every other block. Any of them **can be cut** if time is short, but a cut block **stays as a Verilog-A model** so the start-up (T1) and protection (T5) tests remain complete.

| Block | Job / target | Status in this repo | Cut priority |
|---|---|---|---|
| Bandgap | Sub-1 V reference (a classic 1.2 V bandgap does not fit a 1 V rail); must work from Vout after start-up | **Ideal `Vref` source = 1.0 V** in all testbenches | Required |
| Gate-drive LDO + logic supply | `vdd_logic`, `vdd_drv`, `ibias` for drivers, VCO, clock logic. Start-up path from 0.6 V, then hand-over to a Vout-derived rail | **Ideal `Vdd` source = VDDL (1.0 V)**. `pwr_sw.vdrv` tied to `vin` | Required |
| UVLO | Stop switching when Vin is too low | **Modeled:** `uvlo_fault.va` (`v_on` 0.58 V, `v_off` 0.55 V) | Easiest to reduce |
| Soft-start | Limit inrush at start-up | **Stand-in:** `uvlo_fault.va` holds `fault` for `tdelay` (2 µs) after UVLO clears. No ramp yet | Easiest to reduce |
| Overcurrent (OCP) | Stop on overload / short | **Not modeled.** Add as another input OR'd into `fault` | Easiest to reduce |
| Power-on reset (POR) | Known state for div2, latch, gate nodes; pull-downs so nothing floats | **Implicit:** behavioral models start safe (`@initial_step`, en_hold starts stopped). No pin yet | Required at L3 |

## How support signals enter the chain

All fault reasons go into **`en_hold.fault`** (active high). The clock then stops in the next dead-time gap, which leaves all switches off. If more fault sources are added (OCP, soft-start), OR them into the single `fault` net, or give `en_hold` more inputs and update [01_interfaces](../design/01_interfaces.md) in the same commit.

## Things Alex's real circuits must survive (from the design notes)

- **Start-up at Vin = 0.6 V.** The VCO, logic and drivers run from Vin, hand over to a Vout-derived rail, and use a POR so nothing floats ([OPEN-09](../process/OPEN_ISSUES.md#open-09)).
- The VCO frequency moves with its supply, so it should run from the regulated rail.
- Standard cells need checking at 0.6 V in slow corners.
- A soft-start can be implemented by ramping the error-amp clamp `vmax` (a fsw ceiling that rises over time). In the behavioral model this would be a ramp on a new `vmax` pin. That's a cheap option if the real soft-start gets cut.

## Swapping in Alex's real blocks

1. **LDO:** replace the `Vdd` source with the LDO schematic powered from `vin` (and later Vout). Rerun T1 at 0.6 V, the hardest corner for the logic supply.
2. **Bandgap:** replace `Vref`. If the reference is ~0.5 V, add a 2:1 divider on `vout` → `vout_sense` for `err_amp` and `hold_cmp`, and on `vin` → `vin_sense` for `mode_sel` (scaling its thresholds).
3. **UVLO / soft-start / OCP:** give the real cells the same pins as `uvlo_fault` (`vin, fault, vdd, vss`) or extend the interface on purpose.

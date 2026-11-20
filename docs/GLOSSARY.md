# Glossary

| Term | Meaning in this project |
|---|---|
| **SC converter** | Switched-capacitor converter: moves charge with capacitors and switches instead of an inductor |
| **Cfly / C1** | The single flying capacitor (6.8 nF starting value). Top plate `c1p`, bottom plate `c1n` |
| **Cout / C2** | Output capacitor (≈1.5 µF, probably external) |
| **×2, ×1, ×½** | Gain modes, Vout/Vin. Whiteboard names: ×2 = "1:2", ×½ = "2:1" ([DEC-003](process/DECISIONS.md#dec-003)) |
| **m** | Ideal gain of the current mode (2, 1, 0.5) |
| **k** | SSL factor: Rssl = 1/(k·fsw·Cfly). k = 1 for ×2 and ×1, 4 for ×½ |
| **Φ1, Φ2 (phi1, phi2)** | The two non-overlapping clock phases. Φ1 = charge, Φ2 = discharge/deliver |
| **Dead time (tdead)** | Gap where both phases are low; prevents shoot-through |
| **Ungated phases (phi1u, phi2u)** | nov_gen outputs before the hold gate |
| **fsw** | Switching frequency (one Φ1 + one Φ2 per period). All frequencies are quoted as fsw ([DEC-016](process/DECISIONS.md#dec-016)) |
| **Ring frequency** | VCO output = 2·fsw (div2 halves it) |
| **vctrl** | Error-amp output that commands the VCO frequency |
| **VCO law** | Mapping vctrl → fsw. `law=0` linear, `law=1` exponential |
| **Rssl / Rfsl** | Slow- / fast-switching-limit output resistance |
| **Rout** | √(Rssl² + Rfsl²): the converter's effective output resistance |
| **Ron(Vin)** | Switch on-resistance; rises at low Vin because gate overdrive shrinks |
| **Hold gate** | Stage 4 (`en_hold`): stops the clock inside a dead-time gap |
| **hold_req** | Hold comparator output: Vout above target, stop the clock (light load) |
| **Burst mode** | Light-load operation where the clock repeatedly stops and restarts |
| **mode_target** | Wanted mode from mode select, as two level bits `mt_half`, `mt_x2` |
| **mismatch** | Stage 5 → stage 4: the latched mode ≠ mode_target, so stop to change mode |
| **stopped** | Stage 4 → stage 5 and div2 reset: clock halted, all phases low |
| **fault** | Alex's stop reasons (UVLO, soft-start, OCP), active high |
| **ctl_a…ctl_e** | Logic controls for the five switches (before the gate drivers) |
| **Boosted drive** | Gate drive above Vin (needed for a, b, d), e.g., bootstrapped |
| **Thick-oxide** | PDK device that tolerates higher Vgs/Vds (likely needed for a, b, d) |
| **UVLO** | Under-voltage lockout |
| **OCP** | Over-current protection |
| **POR** | Power-on reset |
| **LDO** | Low-dropout regulator (logic and driver supplies) |
| **L0–L5** | Refinement levels: whiteboard → ideal VA → non-ideal VA → schematics → real parts → layout ([06](design/06_modeling_levels_and_swap_plan.md)) |
| **M0–M7** | Swap milestones from behavioral to real circuits ([06](design/06_modeling_levels_and_swap_plan.md#swap-milestones-l2--l3)) |
| **Config view** | Cadence Hierarchy-Editor view that chooses `veriloga` or `schematic` per cell |
| **Regression set** | The tests rerun after every swap ([07](design/07_verification_plan.md#regression-set)) |
| **DEC-xxx / OPEN-xx** | Entries in [DECISIONS.md](process/DECISIONS.md) / [OPEN_ISSUES.md](process/OPEN_ISSUES.md) |

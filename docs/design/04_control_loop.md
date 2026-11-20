# 04: Control Loop (error amp, hold comparator, mode select)

**Owners:** Brandon (error amp, compensation, hold comparator) and Sam (mode select).
**Models:** [`err_amp.va`](../../veriloga/control/err_amp.va), [`hold_cmp.va`](../../veriloga/control/hold_cmp.va), [`mode_sel.va`](../../veriloga/control/mode_sel.va).
**Reference:** design notes p.8–9, 13.

## 1. How regulation works

```
 vref ---(+)--> [ err_amp ] --vctrl--> [ VCO ] --fsw--> [ SC stage: Rout(fsw) ] --> Vout ---+
          ^ -                                                                             |
          +-------------------------------------------------------------------------------+
          |
          +--> [ hold_cmp ] --hold_req--> [ en_hold ] stops the clock (bursts at light load)
```

- **Heavy or medium load:** the loop settles at the fsw where **Rout = (m·Vin − Vout) / Iout**. The error amp sets that fsw continuously.
- **Light load:** below roughly 1 mA, even the VCO floor (100 kHz) delivers too much current. Vout rises, vctrl pins at its minimum, and the **hold comparator** stops the clock until Vout falls. The converter runs in bursts.
- **Why a continuous frequency command** (replacing the proposal's hysteretic pulse-skipping): a continuous command is easier to reason about and compensate (design notes p.8). This also replaced the v0.1 plan's "pulse-skip first" MVP ([DEC-004](../process/DECISIONS.md#dec-004)).

## 2. Error amp model (`err_amp.va`)

```
 e     = vref − vout_sense
 dx/dt = ki · e              (x is clamped to [vmin, vmax]: anti-windup)
 vctrl = clamp(x + kp·e, vmin, vmax)
```

- A pure integrator (kp = 0) gives the "slow, clear dominant pole" the design notes ask for. kp > 0 adds a zero (PI).
- **Anti-windup clamp:** the integrator state lives on an internal node, and a stiff conductance (`gcl`) pushes it back if it leaves [vmin, vmax]. Without the clamp, x would run far negative during light-load bursts (Vout above target for a long time), and the next load step would see a huge undershoot. See [DEC-012](../process/DECISIONS.md#dec-012).
- Defaults: `ki = 2e4`, `kp = 0`, `vmin = 0`, `vmax = 1`. This is a starting point from the quick loop check in §6, **not a tuned design**.

## 3. Hold comparator model (`hold_cmp.va`)

- `hold_req` = 1 when Vout > vref + `v_ofs` + `hyst`/2, and 0 when Vout < vref + `v_ofs` − `hyst`/2.
- Defaults: `v_ofs` = 5 mV, `hyst` = 2 mV.
- **The thresholds sit above vref** so the comparator does not fight the error amp in normal regulation ([DEC-013](../process/DECISIONS.md#dec-013)).
- Burst-mode ripple ≈ hysteresis + one charge-transfer step (≈6.5 mV worst case), which must fit inside 10 mV.

## 4. Mode select model (`mode_sel.va`)

- Two comparators on Vin with centred hysteresis: thresholds `v_lo` = 1.2 V, `v_hi` = 2.4 V, `hyst` = 50 mV ([DEC-014](../process/DECISIONS.md#dec-014)).
- Switch points: ×2→×1 at 1.225 V rising, ×1→×2 at 1.175 V falling, ×1→×½ at 2.425 V rising, ×½→×1 at 2.375 V falling.
- The output is a level (`mt_half`, `mt_x2`). Stage 5 does the stop/latch handshake.
- Real circuit: Vin divider + two comparators with hysteresis against vref. Offsets shift the thresholds, so verify with T2.

## 5. Loop dynamics (small-signal, SSL-dominated)

Linearize the output node: Cout·dVout/dt = (m·Vin − Vout)·k·fsw·Cfly − Iload.

| Quantity | Expression | Range (from `sizing_check.py`) |
|---|---|---|
| Plant DC gain dVout/dfsw | ΔV / fsw = ΔV²·k·Cfly / Iout | spreads ≈1000× |
| Output pole | ωp = k·fsw·Cfly / Cout | ≈80 Hz … 12 kHz |
| VCO gain, linear law | dfsw/dvctrl = (fsw_max − fsw_min)/1 V ≈ 20 MHz/V | constant |
| VCO gain, exponential law | dfsw/dvctrl = fsw·ln(fsw_max/fsw_min)/1 V | ∝ fsw |
| Loop DC gain (vctrl → Vout), linear | ΔV·Kvco/fsw | **0.2 … 256 V/V (≈1200×)** |
| Loop DC gain, exponential | ΔV·ln(fmax/fmin) | **0.9 … 7.3 V/V (≈8×)** |

**Key observation:** with a linear VCO law, the fsw in the denominator is what makes the gain spread so large. An **exponential (log-linear) VCO law cancels it**, leaving only the ΔV spread, about 8× instead of about 1000×. A current-starved ring with a subthreshold V-to-I naturally comes out close to exponential. The design notes mention an optional `gain_code` (mode/Vin-dependent mirror ratio) that would reduce the spread to about 140×. Both `vco.va` and `pwr_avg.va` have a `law` parameter so the team can compare. The default stays linear, because the design notes ask for a V-to-I "as linear as the range allows" ([DEC-017](../process/DECISIONS.md#dec-017), [OPEN-04](../process/OPEN_ISSUES.md#open-04)).

## 6. First loop observations (quick Python averaged model, not Spectre)

To choose sensible defaults, the L1 equations (same as `pwr_avg.va` + clamped integrator + hold comparator) were integrated in Python. Test: load step 1 → 20 mA at Vin = 0.6, 1.18, 2.4 and 3.0 V.

| Setting | Behavior |
|---|---|
| ki = 2 (very slow) | vctrl stays near maximum. The **hold comparator** does all the regulating; Vout sits at ≈ vref + 5 mV. Good transient (dip ≈ 0), but the clock runs at maximum frequency even at light load (wastes gate-drive power) |
| ki = 2e4 (chosen default) | At Vin = 0.6 V the error amp regulates (Vout = 1.000 V). At the other corners the error amp and hold comparator share the job (Vout ≈ 1.005 V, vctrl ≈ 0.55–0.6). Load-step dip ≤ 3 mV |
| ki = 1e5, kp = 1 (fast) | Vout = 1.000 V at full load everywhere, but **≈200 mV undershoot** on the load step. The integrator had wound down to the floor during light load (correct behavior) and needs time to slew back |

**What this tells Brandon** ([OPEN-05](../process/OPEN_ISSUES.md#open-05), [OPEN-06](../process/OPEN_ISSUES.md#open-06)):
1. With a hold comparator above vref, a slow integrator lets the hold loop take over (bang-bang regulation at max fsw). That's robust but inefficient at light load.
2. A fast integrator gives exact regulation but a large undershoot when the load steps up from the burst region. Options include an undershoot comparator that forces vctrl up, a larger kp, a lower hold offset, or an exponential VCO law (faster slewing at the low end).
3. Loop stability across the ≈1000× gain spread is the core design problem. Plan to tune with T3 and T6 at every band edge.

## 7. Suggested tuning procedure (L1, fast)

1. Run `tb_L1_T3_load_step.scs` at Vin = 0.6, 1.175, 2.4 (from above), 3.0 V.
2. Sweep `KI` and `KP` (ADE parametric or edit `common_params.scs`). Record undershoot, recovery time and limit cycling.
3. Repeat with `LAW=1` to compare the two VCO laws.
4. Run `tb_L1_T6_light_load.scs` (RLOAD 20 kΩ … 200 Ω) and check the burst ripple.
5. Write the chosen ki/kp/law and the reason into [DECISIONS.md](../process/DECISIONS.md) and update this page.
6. Only then go to L2 (switched) to confirm, and later to Brandon's transistor-level amp.

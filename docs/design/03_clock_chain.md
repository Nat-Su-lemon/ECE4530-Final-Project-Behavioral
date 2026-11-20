# 03: Clock Generation Chain

**Owner:** Sam. **Models:** [`veriloga/clock_chain/`](../../veriloga/clock_chain/). **Reference:** design notes p.10–13, whiteboard photo `whiteboard_clock_generation.jpg`.

Five stages turn `vctrl` into the five switch controls, and can stop cleanly at any moment.

```
          vctrl                                   hold_req, fault, mismatch        mt_half, mt_x2
            |                                               |                            |
            v                                               v                            v
      +-----------+  clk   +----------+  q   +---------+ phi1u  +-----------+  phi1  +------------+
      | 1. VCO    |------->| 2. div2  |----->| 3. NOV  |------->| 4. en_hold|------->| 5. mode    |--> ctl_a..ctl_e
      | ring      | 2*fsw  | 50% duty |  fsw | dead    | phi2u  | stop only |  phi2  | latch +    |
      |           |        |          |      | time    |------->| in a gap  |------->| routing    |--> mismatch --+
      +-----------+   |    +----------+      +---------+        +-----------+        +------------+               |
                      |         ^ rst                              |  ^   stopped        ^ stopped                |
                      +---------|----------------------------------+  |   |              |                        |
                        (clk to en_hold, for the restart)             |   +--------------+                        |
                                +-------------------------------------+---(stopped -> div2.rst)                   |
                                                                      +-------------------------------------------+
                                                                        (mismatch -> en_hold)
```

## Rules for the chain (design notes p.13)

1. **Stop and restart only in the dead-time gap.**
2. **The latch changes only while `stopped` is high.** This keeps d and e from conducting together.
3. **Every control is phase-driven**, so low phases mean all switches are off.
4. **Floating nodes drift.** Gate nodes need pull-downs and a power-on reset (real circuit).
5. Switches a, b, d see up to 3 V; their drivers must follow (Nathaniel).

---

## Stage 1: VCO ring (`vco.va`)

| | |
|---|---|
| Job | Convert vctrl to a clock at **2 × fsw** (div2 halves it) |
| Behavioral model | `fsw = fsw_min + (fsw_max − fsw_min)·u`, u = (vctrl − vlo)/(vhi − vlo) clamped to 0…1. Optional exponential law (`law=1`). Clean 50 % square wave, `$bound_step` keeps ≥20 points per ring cycle |
| Defaults | fsw 100 kHz … 20 MHz over vctrl 0 … 1 V, linear |
| Ignores | jitter, supply/temperature dependence, start-up, real duty error |
| Real circuit | Current-starved ring of 5 inverters. f ≈ I / (2·N·C·Vdd): N = 5, C = 10 fF, Vdd = 1 V gives 3.1 µA → 31 MHz and 15 nA → 0.15 MHz. Sub-blocks: V-to-I converter, bias mirror (optional `gain_code` scales it), starved inverters, floor/ceiling clamps, output buffer |
| Why bias current, not supply | Wide range from one control, full-rail swing, logic levels not tied to vctrl |
| Verify (real) | f vs vctrl/supply/temperature/corners, min and max f, start-up at Vin = 0.6 V. Run it from the regulated rail |

> The same vctrl→fsw law is coded in `pwr_avg.va`. **If you change one, change both** so that L1 and L2 agree. After characterizing the real ring, refit `fsw_min`, `fsw_max` and `law` to the measured curve.

## Stage 2: Divide-by-two (`div2.va`)

| | |
|---|---|
| Job | Exact 50 % duty: q and qb always opposite (a ring's own duty is never exact) |
| Behavioral model | Toggle on rising clk, 50 ps clk-to-q, **active-high `rst` holds q = 1** |
| Reset connection | `rst` = `stopped`. Reset is held only while the clock is stopped |
| Why q = 1 during reset | nov_gen makes Φ1 from q = 1, so the chain restarts at Φ1 ([DEC-009](../process/DECISIONS.md#dec-009)) |
| Real circuit | Standard-cell DFF (QB→D) with a set/preset input. Check at 0.6 V in slow corners |
| Verify | duty across the full frequency range, reset behavior |

## Stage 3: Non-overlap generator (`nov_gen.va`)

| | |
|---|---|
| Job | Make Φ1/Φ2 so each phase falls a fixed dead time before the other rises |
| Behavioral model | Φ1 rises `tdead` after q rises; Φ2 rises `tdead` after q falls; each falls immediately on the opposite edge |
| Default | `tdead` = 2 ns (placeholder) |
| Budget | At 15 MHz the half period is ≈33 ns (25 ns at the 20 MHz ceiling). The dead time must be a small fraction of that but longer than the worst driver skew. Too little causes shoot-through (a/b, c/d, c/e). Too much wastes charge-transfer time at the top frequency |
| Real circuit | Cross-coupled NOR pair with fixed delay cells in the feedback |
| Verify | dead time **at the switch gates** (move `nov_check` there once drivers exist) |

```
 q      ____/~~~~~~~~~~~~~~\______________/~~~~
 phi1u  ______/~~~~~~~~~~~~\________________/~~      rises tdead after q rises
 phi2u  ~~~~\________________/~~~~~~~~~~~~\____      rises tdead after q falls
             |<->|          |<->|
             tdead          tdead
```

## Stage 4: Enable and hold gate (`en_hold.va`)

| | |
|---|---|
| Job | Stop the clock for any stop reason, acting only inside a dead-time gap so no switch is cut mid-conduction |
| Stop reasons | `hold_req` (light load / over-voltage, Brandon), `fault` (UVLO / soft-start / OCP, Alex), `mismatch` (mode change, stage 5) |
| Stop | `stop_req` = OR of the three, sampled on the **falling edge of the ungated Φ2**. That instant is inside the gap before Φ1 (design notes p.12) |
| Gating | Φ1 and Φ2 forced low while stopped. `stopped` output tells stage 5 and the div2 reset |
| Restart | When `stop_req` is clear, the gate re-opens on the **next rising ring-clock edge**. div2 is still in reset on that edge, so it does not toggle, and the first Φ1 is a full-width pulse ([DEC-010](../process/DECISIONS.md#dec-010)) |
| Power-up | Starts stopped (`g = 0`), which acts as the power-on reset for the chain |
| Latency | Worst-case stop delay is one switching period: ≈65 ns at 15 MHz, ≈10 µs at 100 kHz. That variable delay is why a fixed delay cannot replace the `stopped` flag |
| Real circuit | Reason combiner (OR), sampling flop (clocked by Φ2u falling), synchronous release flop (clocked by ring clk), gating ANDs, stopped flag |

**Stop / restart timing (behavioral model):**

```
 clk (ring)  _/~\_/~\_/~\_/~\_/~\_/~\_/~\_/~\_/~\_/~\_/~\_
 q           __/~~~\___/~~~\___/~~~~~~~~~~~~~~~~~~~~~~~~\___/~~      held at 1 while stopped
 stop_req    ______/~~~~~~~~~~~~~~~~~~~~\_____________________
 phi2 (out)  ~\_____/~~\________________________________/~~~      last Phi2 completes normally
 phi1 (out)  ___/~~\______________________/~~~~~~~~~~~\_______      restart = full-width Phi1
 stopped     __________/~~~~~~~~~~~~~~~~~~\__________________
                       ^ sampled at Phi2u falling     ^ released on next ring rising edge
```

> **Note for Sam:** the design notes say "samples on the falling edge of the ungated Φ2" and "restarts at Φ1" but don't specify how the restart is timed. The synchronous release here is the simplest behavior with no runt pulse. The real circuit can do it differently as long as it restarts at Φ1 without a short pulse ([OPEN-12](../process/OPEN_ISSUES.md#open-12)).

> **Known simplification:** faults are acted on only in the gap (≤ one period). If Alex needs an instant hard stop (for example, for overcurrent), add an asynchronous path. That is safe only if the drivers can tolerate a mid-pulse cut.

## Stage 5: Mode latch and routing (`mode_route.va`)

| | |
|---|---|
| Job | Hold the mode in 2 bits, map gated phases onto ctl_a…e (routing table in [02 §3](02_power_stage.md#3-routing-by-switch-what-mode_route-implements)) |
| Latch | Transparent only while `stopped` is high |
| Mismatch | `mismatch` = (requested mode ≠ latched mode) → stage 4 stops the clock |
| Safe state | Low phases ⇒ every switch off; no special parked state |
| Real circuit | 2-bit D-latch enabled by `stopped`, AND/OR routing, XOR compare |

### Mode change walkthrough: ×1 → ×½ (design notes p.12)

| Step | What happens | Signal view |
|---|---|---|
| 1 | Vin crosses 2.425 V. `mode_sel` raises `mt_half` while the latch still says ×1 | `mt_half` ↑ |
| 2 | Stage 5 raises `mismatch`. Stage 4 now has a stop reason | `mismatch` ↑ |
| 3 | At the next gap (Φ2u falling), stage 4 holds Φ1 and Φ2 low. In ×1, c follows the phases, so it turns off too | all ctl = 0 |
| 4 | `stopped` goes high. The latch takes ×½ and `mismatch` clears | `stopped` ↑, `mismatch` ↓ |
| 5 | On the next ring rising edge the gate releases and the clock restarts at Φ1. Routing now uses the ×½ column | `stopped` ↓, Φ1 ↑ (a, e on) |

The break in switching is about one clock period. That is fine as long as the mode doesn't chatter; preventing chatter is the job of the threshold hysteresis.

## Verification of the chain

Unit test [`sim/spectre/tb_U1_clk_chain.scs`](../../sim/spectre/tb_U1_clk_chain.scs) runs the whole chain with scripted hold pulses, a fault pulse and three mode changes. Pass criteria are in [07_verification_plan](07_verification_plan.md#u1-clock-chain).

The stop/restart logic was also checked with a quick Python event simulation of these exact rules (200 random hold, fault and mode events). Result: no forbidden pairs, no Φ overlap, minimum gap = tdead, every restart begins with Φ1, minimum Φ1 width 23 ns (= T_ring − tdead) at fsw = 20 MHz. This is a logic check only; the Spectre run is still to do ([OPEN-16](../process/OPEN_ISSUES.md#open-16)).

# Design Decision Log

Every non-obvious choice in this repo, with **why** it was made and **what was rejected**. Add new decisions at the bottom with the next number. Never renumber or delete one. If a decision is reversed, set its status to *Superseded by DEC-0xx* and add the new one.

Statuses: **Accepted** (in use), **Proposed** (in use in the models but needs owner confirmation), **Superseded**.

| ID | Title | Status | Owner to confirm |
|---|---|---|---|
| [DEC-001](#dec-001) | `.va` files in the repo are the source of truth | Accepted | all |
| [DEC-002](#dec-002) | Design-notes PDF overrides whiteboard and the v0.1 plan | Accepted | all |
| [DEC-003](#dec-003) | Name modes by gain: ×2, ×1, ×½ | Accepted | all |
| [DEC-004](#dec-004) | Regulate with a VCO frequency command + hold gate | Accepted | Brandon |
| [DEC-005](#dec-005) | Two behavioral levels: L1 averaged and L2 switched | Accepted | all |
| [DEC-006](#dec-006) | All logic pins reference `vdd`/`vss` | Accepted | all |
| [DEC-007](#dec-007) | Signal names follow the design notes | Accepted | all |
| [DEC-008](#dec-008) | In ×1, ctl_c = Φ1 OR Φ2; stopped ⇒ all switches off | Accepted | Sam, Nathaniel |
| [DEC-009](#dec-009) | div2 reset holds q = 1 (Φ1 side) | Proposed | Sam |
| [DEC-010](#dec-010) | Stop on Φ2u falling, restart on next ring-clock rising edge | Proposed | Sam |
| [DEC-011](#dec-011) | Switch + driver are one swappable cell (`pwr_sw`) | Proposed | Nathaniel |
| [DEC-012](#dec-012) | Error amp = clamped integrator (anti-windup), ki = 2e4 start | Proposed | Brandon |
| [DEC-013](#dec-013) | Hold comparator threshold sits above vref | Proposed | Brandon |
| [DEC-014](#dec-014) | Mode thresholds 1.2 / 2.4 V, 50 mV centred hysteresis | Accepted | Sam |
| [DEC-015](#dec-015) | Keep plain-text Spectre netlists as reference testbenches | Accepted | all |
| [DEC-016](#dec-016) | Quote frequencies as fsw; ring = 2·fsw | Accepted | Sam |
| [DEC-017](#dec-017) | Linear VCO law by default, `law` parameter for exponential | Proposed | Sam, Brandon |

---

### DEC-001
**`.va` files in the repo are the source of truth** · Accepted · 2026-11-19

- **Context:** Cadence stores Verilog-A inside its library database, which is awkward to diff and review in git.
- **Decision:** Keep every model as a plain `.va` file under `veriloga/`. Cadence views symlink to (or are copied from) these files. Module name = cell name = file name.
- **Why:** Reviewable diffs, one obvious place to edit, works without Cadence (any text editor, GitHub).
- **Rejected:** committing only the Cadence library (opaque diffs, lock-file conflicts).

### DEC-002
**Design-notes PDF overrides whiteboard and the v0.1 plan** · Accepted · 2026-11-19

- **Context:** Three sources existed: two whiteboard photos, the v0.1 Markdown plan (written from the photos), and Sam's System Design Notes PDF (Nov 19). They disagreed on regulation method, ×1 switch-c behavior, owners and signal names.
- **Decision:** The PDF is authoritative. Where this repo deviates from it, a decision here says so explicitly (DEC-009, DEC-010, DEC-011 add detail the PDF leaves open).
- **Why:** It's the newest, most complete and team-reviewed document, and it already folds in the professor's feedback.

### DEC-003
**Name modes by gain (×2, ×1, ×½)** · Accepted · 2026-11-19

- **Context:** The whiteboard used ratios ("2:1", "1:2"), which are ambiguous (is 2:1 Vin:Vout or Vout:Vin?).
- **Decision:** Use gain = Vout/Vin everywhere: ×2 (step-up), ×1, ×½ (step-down). Whiteboard 2:1 = ×½, 1:2 = ×2. Internal code: 0 = ×1, 1 = ×½, 2 = ×2. mode_target bits: `mt_half`, `mt_x2`.
- **Why:** Unambiguous; matches the design notes.
- **Changed from v0.1:** `m_div`/`m_dbl` → `mt_half`/`mt_x2`; mode code 1 was "2:1", which is the same switch pattern, now called ×½.

### DEC-004
**Regulate with a VCO frequency command + hold gate** · Accepted · 2026-11-19

- **Context:** v0.1 proposed a fixed-frequency hysteretic comparator (pulse skipping) as the MVP, with VCO control as step 2. The design notes record the team's choice: the error amp continuously sets fsw through the VCO, and a hold comparator stops the clock only at light load.
- **Decision:** Follow the design notes. `err_amp` drives `vctrl`; `hold_cmp` drives `hold_req`. Pulse-skip-only operation is still possible for debugging: tie `vctrl` to a constant and let `hold_cmp` regulate.
- **Why:** Team decision; a continuous command is easier to compensate. Light-load bursting is still covered by the hold gate.
- **Changed from v0.1:** `fb_cmp` (pulse-skip enable, active-high "run") removed; replaced by `hold_cmp` (active-high "stop") + `err_amp`. `vctrl_pi` replaced by `err_amp` with anti-windup.

### DEC-005
**Two behavioral levels: L1 averaged and L2 switched** · Accepted · 2026-11-19

- **Context:** The design notes' refinement levels put an *averaged* power stage at L1 and switches at L2. v0.1 only had a switched model.
- **Decision:** Add `pwr_avg.va` (L1) next to the switched `pwr_sw` network (L2). Both use the same parameters and VCO law.
- **Why:** The loop poles sit at 80 Hz – 12 kHz, so loop tests need milliseconds of simulated time. A switched simulation of that is very slow; the averaged one takes seconds. Brandon can tune compensation without waiting on clock edges.
- **Trade-off:** One more model to keep consistent. The first L2 test is that it agrees with L1.

### DEC-006
**All logic pins reference `vdd`/`vss`** · Accepted · 2026-11-19 (carried from v0.1)

- **Decision:** Outputs swing vss…vdd, thresholds at V(vdd,vss)/2. No hard-coded logic voltages.
- **Why:** The logic supply will be 0.6 V at start-up and ~1 V later (Alex's LDO). Models must work at any supply without edits, and real blocks need supply pins anyway.

### DEC-007
**Signal names follow the design notes** · Accepted · 2026-11-19

- **Decision:** `hold_req`, `fault`, `mismatch`, `stopped`, `ctl_a…ctl_e`, `vctrl`, `vref`, `mt_half`/`mt_x2` (= mode_target).
- **Changed from v0.1:** `fb_en` (active-high run) → `hold_req` (active-high stop); `pgood` → `fault` (inverted); `hold` → `mismatch`; `sa…se` → `ctl_a…ctl_e`; `pwr_sw.ctrl` → `ctl`.
- **Why:** One vocabulary across the PDF, the models and conversations.

### DEC-008
**In ×1, ctl_c = Φ1 OR Φ2; stopped ⇒ all switches off** · Accepted · 2026-11-19

- **Context:** The whiteboard showed switch c "ON" in ×1; v0.1 implemented it as constant-on while running.
- **Decision:** ctl_c = Φ1|Φ2 in ×1 (off in the dead-time gap), as in the design notes. Every control is derived from a phase.
- **Why:** When the clock stops, both phases are low, so every switch is off automatically. No special parked state, and no extra logic to get wrong.

### DEC-009
**div2 reset holds q = 1 (the Φ1 side)** · Proposed (Sam to confirm) · 2026-11-19

- **Context:** The design notes say the ÷2 reset is held while stopped "so the first edge after any restart always begins Φ1", but don't say which q level. nov_gen makes Φ1 from q = 1.
- **Decision:** `div2.rst` (active high, = `stopped`) holds q = 1.
- **Why:** The chain stops right after q rises (at Φ2u falling), so holding q = 1 changes nothing at the stop instant, and the ungated Φ1 is already high when the gate re-opens. Restarting therefore begins with Φ1.
- **Alternative:** hold q = 0 and swap the Φ1/Φ2 assignment in nov_gen. That's equivalent; pick whichever suits the real flop (set vs. reset input).

### DEC-010
**Stop on Φ2u falling; restart on the next ring-clock rising edge** · Proposed (Sam to confirm) · 2026-11-19

- **Context:** The design notes specify the stop (sample on Φ2u falling, inside the gap) but not the restart timing. v0.1 sampled on either phase's falling edge and could resume on either phase.
- **Decision:** Stop: sample `hold_req | fault | mismatch` on Φ2u falling. Restart: when no stop reason remains, re-open on the next rising edge of the ring clock (`en_hold` got a `clk` pin). div2 is still in reset on that edge, so it doesn't toggle, and the first Φ1 is full width (one ring period).
- **Why:** An asynchronous release would give a Φ1 pulse of random width, possibly a runt that the drivers can't handle. A Python event simulation of these rules (200 random stop/mode events) showed no overlaps, no forbidden pairs, every restart at Φ1, and minimum Φ1 width = T_ring − tdead.
- **Cost:** One extra pin on `en_hold`, and restart latency of up to one ring period.

### DEC-011
**Switch + driver are one swappable cell (`pwr_sw`)** · Proposed (Nathaniel to confirm) · 2026-11-19

- **Context:** The design notes have separate `ctl_x` → driver → `gate_x` → switch interfaces. Behaviorally, a separate driver model would need to know each switch's source voltage, boost rails and so on, which is exactly the hard design problem.
- **Decision:** One cell per switch, controlled by logic-level `ctl`, with a `vdrv` pin for the available drive. It models Ron(vdrv) (design-notes formula), Roff, Coff, driver delay, transition time and gate-charge loss.
- **Why:** Keeps the behavioral model simple and honest. At L3, Nathaniel's schematic of `pwr_sw` can contain driver + level shifter + nMOS arranged however he wants. The top level doesn't change.
- **If extra pins are needed** (boost rail, bootstrap cap to C1+): add them to the `.va`, the symbol and all netlists in one commit.

### DEC-012
**Error amp = clamped integrator with anti-windup; ki = 2e4 starting value** · Proposed (Brandon) · 2026-11-19

- **Context:** v0.1's `vctrl_pi` used an unclamped `idt()`, which winds up during light-load bursts and causes huge undershoot on the next load step.
- **Decision:** The integrator state lives on an internal node with a stiff clamp to [vmin, vmax]. Defaults: ki = 2e4 V/(V·s), kp = 0.
- **Why ki = 2e4:** A quick Python averaged-loop run (see [04 §6](../design/04_control_loop.md#6-first-loop-observations-quick-python-averaged-model-not-spectre)) showed ki = 2 leaves all regulation to the hold comparator, while ki = 1e5 gives about 200 mV undershoot on a 1→20 mA step. ki = 2e4 regulates at every corner with a dip of 3 mV or less. **This is a starting point, not a design.**

### DEC-013
**Hold comparator threshold sits above vref** · Proposed (Brandon) · 2026-11-19

- **Decision:** `hold_req` trips at vref + 5 mV (`v_ofs`) with 2 mV hysteresis.
- **Why:** If the hold threshold were at vref, it would fight the error amp during normal regulation. Above vref, it only acts when the error amp is pinned at the VCO floor (light load) or on overshoot.
- **Consequence:** A slow error amp lets the hold loop regulate at about vref + 5 mV ([OPEN-06](OPEN_ISSUES.md#open-06)).

### DEC-014
**Mode thresholds 1.2 / 2.4 V with 50 mV centred hysteresis** · Accepted · 2026-11-19

- **Context:** v0.1 used placeholders (1.2 / 2.3 V, 100 mV). The design notes derive the thresholds from a 20 % headroom rule.
- **Decision:** `v_lo` = 1.2 V, `v_hi` = 2.4 V, `hyst` = 50 mV centred on each threshold.
- **Known issue:** the 2.4 V efficiency anchor sits on `v_hi` ([OPEN-03](OPEN_ISSUES.md#open-03)).

### DEC-015
**Keep plain-text Spectre netlists as reference testbenches** · Accepted · 2026-11-19

- **Decision:** `sim/spectre/*.scs` hold every testbench as text: shared parameters in `common_params.scs`, the circuit in `l1_core`/`l2_core`, stimulus per test.
- **Why:** Runnable from the command line without drawing schematics. Reviewable in git. They serve as the drawing reference for the Cadence schematics.
- **Rule:** If a schematic and its netlist disagree, fix one of them in the same commit.

### DEC-016
**Quote frequencies as fsw; ring = 2·fsw** · Accepted · 2026-11-19

- **Context:** The design notes say "20 MHz VCO ceiling" but also "the ring runs at twice fsw". Their numbers (33 ns half-period at 15 MHz, 65 ns stop latency) only work if 15/20 MHz are fsw.
- **Decision:** All frequencies in docs and parameters are fsw. `vco.va` takes `fsw_min`/`fsw_max` and internally runs the ring at 2·fsw.

### DEC-017
**Linear VCO law by default; `law` parameter for exponential** · Proposed (Sam, Brandon) · 2026-11-19

- **Context:** The design notes ask for a V-to-I "as linear as the range allows". The loop analysis ([04 §5](../design/04_control_loop.md#5-loop-dynamics-small-signal-ssl-dominated)) shows a linear law makes the loop gain spread about 1200×, while an exponential law cuts that to about 8×.
- **Decision:** Default `law=0` (linear) to match the design notes; `law=1` (exponential) is available in `vco.va` and `pwr_avg.va` for comparison.
- **Next step:** Brandon/Sam compare both in L1 T3 and decide ([OPEN-04](OPEN_ISSUES.md#open-04)).

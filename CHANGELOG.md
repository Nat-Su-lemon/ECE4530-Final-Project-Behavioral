# Changelog

All notable changes to this repository. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Every entry says **what** changed and **why**, or links the decision ([`docs/process/DECISIONS.md`](docs/process/DECISIONS.md)) that explains why.

Versions follow project milestones, not software releases: `0.x` = behavioral (L0–L2), `1.x` = real circuits (L3+).

## [Unreleased]

*Nothing yet. Add entries here as you work. Next expected: results of the first Spectre run ([OPEN-16](docs/process/OPEN_ISSUES.md#open-16)).*

---

## [0.2.0] - 2026-11-19: Repository created; plan reconciled with the System Design Notes

This version turns the v0.1 chat plan (below) into a structured repository and updates everything to match Sam's **System Design Notes** PDF (Nov 19 2026), which is now the primary reference ([DEC-002](docs/process/DECISIONS.md#dec-002)).

### Added
- **Reference material:** `docs/reference/SC_Buck-Boost_Converter_System_Design_Notes.pdf` and both whiteboard photos (`docs/reference/whiteboard/`), plus `docs/reference/README.md`. It maps each PDF section to a repo doc and lists the whiteboard ↔ PDF differences. *Why:* everyone works from the same sources, with clear authority.
- **Design docs** `docs/design/00–08`: system overview, interfaces, power stage, clock chain, control loop, support circuits, modeling levels & swap plan, verification plan, Cadence workflow. *Why:* the user asked for thorough, understandable documentation. One page per area keeps each owner's reading short.
- **Process docs:** `DECISIONS.md` (17 decisions with rationale and rejected alternatives), `OPEN_ISSUES.md` (16 open items with owners and "close by"), `CONTRIBUTING.md`, `GLOSSARY.md`. *Why:* keep the reasoning traceable as the team swaps in real circuits.
- **Verilog-A models as separate `.va` files** (previously only code blocks inside Markdown) under `veriloga/`, each with a standard header. *Why:* reviewable in git, one source of truth for Cadence ([DEC-001](docs/process/DECISIONS.md#dec-001)).
- **`pwr_avg.va`:** L1 averaged power stage with the VCO law built in. *Why:* the design notes' L1 level calls for an averaged stage, and loop poles at 80 Hz–12 kHz need millisecond simulations, which are too slow when switched ([DEC-005](docs/process/DECISIONS.md#dec-005)).
- **`err_amp.va`:** clamped integrator with anti-windup (+ optional kp). *Why:* v0.1's unclamped `idt()` would wind up during light-load bursts ([DEC-012](docs/process/DECISIONS.md#dec-012)).
- **`hold_cmp.va`:** hold comparator with threshold above vref. *Why:* the design notes' light-load mechanism ([DEC-013](docs/process/DECISIONS.md#dec-013)).
- **`sw_check.va`:** monitors the four forbidden switch pairs (a&b, c&d, c&e, d&e). *Why:* the design notes list these shorts; the checker catches them automatically in every L2 run.
- **`pwr_sw.va` features:** Ron that depends on drive voltage (design-notes formula, new `vdrv` pin), driver delay `td`, `coff`, gate-charge loss `cg`. *Why:* the ×2 / 0.6 V corner depends on Ron rising at low Vin, and efficiency needs gate-drive loss ([DEC-011](docs/process/DECISIONS.md#dec-011)).
- **VCO `law` parameter** (linear / exponential) in `vco.va` and `pwr_avg.va`. *Why:* loop-gain spread is about 1200× with a linear law and about 8× with an exponential law. The team should compare before deciding ([DEC-017](docs/process/DECISIONS.md#dec-017)).
- **Spectre netlists** `sim/spectre/`: `common_params`, `l1_core`, `l2_core`, testbenches L1 T1/T2/T3/T6, L2 T1/T2/T4, unit tests U1 (clock chain) and U2 (power stage open loop). *Why:* runnable without schematics, and the drawing reference for Cadence ([DEC-015](docs/process/DECISIONS.md#dec-015)).
- **`tools/sizing_check.py`:** reproduces the design notes' workbench numbers (25.2 mA at ×2/0.6 V, 23.6 mA at ×1/1.175 V, about 1 mA at the 100 kHz floor, pole range 80 Hz–12 kHz) plus the ripple step, efficiency ceilings and loop-gain spread. *Why:* lets anyone change a number and see the consequence without Cadence.
- `.gitignore` (Spectre/Cadence outputs, lock files) and `.gitattributes` (LF endings for text, PDF/JPG as binary). *Why:* avoid committing simulation junk; the original README already showed a CRLF/LF-only diff on Windows.

### Changed (relative to the v0.1 plan)
- **Mode names** 2:1 / 1:1 / 1:2 → **×½ / ×1 / ×2** (gain); mode bits `m_div`/`m_dbl` → `mt_half`/`mt_x2`. *Why:* unambiguous, matches the PDF ([DEC-003](docs/process/DECISIONS.md#dec-003)).
- **Regulation:** v0.1's "pulse-skip with a hysteretic comparator first, VCO loop later" → **error amp sets fsw via the VCO from the start, hold comparator only at light load**. *Why:* the team's recorded choice in the design notes ([DEC-004](docs/process/DECISIONS.md#dec-004)).
- **Signal names** aligned to the PDF: `fb_en` → `hold_req` (polarity inverted: now 1 = stop), `pgood` → `fault` (inverted), `hold` → `mismatch`, `sa…se` → `ctl_a…ctl_e`, `pwr_sw.ctrl` → `ctl` ([DEC-007](docs/process/DECISIONS.md#dec-007)).
- **Switch c in ×1:** constant ON while running → **Φ1 OR Φ2**. *Why:* every control is then phase-derived, so a stopped clock means all switches are off automatically ([DEC-008](docs/process/DECISIONS.md#dec-008)).
- **`en_hold`:** v0.1 sampled stop on *either* phase's falling edge and could resume on either phase. Now it **samples only on Φ2u falling** (as the PDF says) and **restarts synchronously on the next ring-clock edge, always at Φ1, with a full-width pulse**. Added a `clk` pin. *Why:* the PDF requires restart at Φ1, and the synchronous release avoids runt pulses ([DEC-010](docs/process/DECISIONS.md#dec-010)).
- **`div2`:** active-low `rstb` → active-high **`rst` driven by `stopped`, holding q = 1**. *Why:* the PDF says the ÷2 reset is held while stopped so restarts begin at Φ1 ([DEC-009](docs/process/DECISIONS.md#dec-009)).
- **`vco`:** parameters changed from `f0/kvco/v0/fmin/fmax` (ring frequency) to **`fsw_min/fsw_max/vlo/vhi/law`** (switching frequency; ring = 2·fsw). *Why:* the PDF quotes frequencies as fsw (100 kHz floor, 20 MHz ceiling) ([DEC-016](docs/process/DECISIONS.md#dec-016)).
- **`mode_sel`:** thresholds 1.2/2.3 V, 100 mV → **1.2/2.4 V, 50 mV** centred hysteresis. *Why:* derived in the PDF from the 20 % headroom rule ([DEC-014](docs/process/DECISIONS.md#dec-014)).
- **`startup` → `uvlo_fault`:** output inverted (`pgood` → `fault`). *Why:* matches the hold gate's "stop reason" inputs.
- **Placeholder sizing:** C1 10 nF / Cout 100 nF / Ron 1 Ω → **Cfly 6.8 nF / Cout 1.5 µF / Ron 0.5 Ω, fsw 100 kHz–20 MHz**. *Why:* the PDF's workbench values.
- **Owners** corrected per the PDF: Nathaniel = switches + gate drivers; Sam = clock generation + mode select; Brandon = error amp + hold comparator; Alex = support circuits.
- **Testbench plan:** v0.1's U1–U6 / I1–I8 replaced by the PDF's **standard testbenches T1–T6** plus two unit tests, each mapped to L1/L2 netlists.
- **Swap plan:** v0.1's ad-hoc milestones are now anchored to the PDF's **refinement levels L0–L5**, with milestones M0–M7 for the L2 → L3 swaps.
- `README.md` rewritten as the project entry point.

### Removed
- `fb_cmp` (fixed-frequency pulse-skip comparator) and `vctrl_pi` (unclamped PI). Superseded by `hold_cmp` + `err_amp` ([DEC-004](docs/process/DECISIONS.md#dec-004), [DEC-012](docs/process/DECISIONS.md#dec-012)).
- The v0.1 standalone Markdown files `01_interfaces.md`…`05_swap_roadmap.md`. Their content was merged into `docs/design/` and updated.

### Found while reconciling (logged as open issues)
- **OPEN-03:** the 75 % efficiency anchor at 2.4 V sits exactly on the ×1/×½ threshold. Approached from below, the converter is in ×1 (ideal η about 42 %).
- **OPEN-04 / 05 / 06:** quick averaged-loop runs show the loop-gain spread and a trade-off between exact regulation (fast integrator, about 200 mV load-step undershoot from light load) and hold-comparator regulation (slow integrator, Vout ≈ vref + 5 mV at max fsw).
- **OPEN-10:** ripple step computes to 6.5 mV vs. the PDF's ≈8 mV; total ripple margin to 10 mV is thin once comparator hysteresis is added.

### Verified
- `tools/sizing_check.py` reproduces the PDF's numbers (see `docs/design/02_power_stage.md` §9).
- Clock-chain stop/restart/mode-change rules simulated in a Python event model with 200 random hold/fault/mode events: 0 forbidden-pair violations, 0 phase overlaps, min gap = tdead, every restart at Φ1, min Φ1 width = T_ring − tdead.
- **Not verified:** nothing has been compiled or simulated in Spectre yet ([OPEN-16](docs/process/OPEN_ISSUES.md#open-16)).

---

## [0.1.0] - 2026-11-19: Initial behavioral modeling plan (chat draft, not committed)

Six Markdown files written from the two whiteboard photos, before the design notes were available:
`README.md`, `01_interfaces.md`, `02_clock_chain_models.md`, `03_power_stage_and_control_models.md`, `04_testbench_plan.md`, `05_swap_roadmap.md`.

Contents: MVP rules (one block = one cell, logic referenced to vdd/vss, swap one block at a time), the 5-switch truth table from the whiteboard, Verilog-A code blocks for vco, div2, nov_gen, en_hold, mode_route, pwr_sw, fb_cmp, vctrl_pi, mode_sel, startup, nov_check, a unit/integration test list (U1–U6, I1–I8), and Cadence config-view swap instructions. Superseded by 0.2.0.

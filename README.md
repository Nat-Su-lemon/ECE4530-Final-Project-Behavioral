# ECE4530 Final Project: Switched-Capacitor Buck-Boost Converter (Behavioral Models)

Verilog-A behavioral models, Spectre testbenches and design documentation for a **switched-capacitor buck-boost converter** that regulates **1 V from a 0.6–3 V input at up to 20 mA**. It uses one flying capacitor, five switches and three gain modes (×2, ×1, ×½), with a VCO-based frequency loop.

The idea: build a **complete behavioral model first**, then **replace one block at a time with its real transistor circuit** in Cadence. The same tests run after every swap.

> 📄 Primary design reference: [`docs/reference/SC_Buck-Boost_Converter_System_Design_Notes.pdf`](docs/reference/SC_Buck-Boost_Converter_System_Design_Notes.pdf)

---

## Status (2026-11-19)

| Area | State |
|---|---|
| L0: specs, block diagram, owners, budgets | ✅ Documented (`docs/design/`) |
| L1: averaged loop model | ✅ Written (`pwr_avg` + control models, `tb_L1_*`). ⚠️ not yet run in Spectre |
| L2: switched model (clock chain + 5 switches) | ✅ Written (`tb_L2_*`, `tb_U*`). ⚠️ not yet run in Spectre |
| L3+: real circuits | ⏳ Not started; swap plan in [06](docs/design/06_modeling_levels_and_swap_plan.md) |
| Clock-chain stop/restart logic | ✅ Checked with a Python event model |
| Sizing numbers | ✅ Reproduce the design notes (`tools/sizing_check.py`) |

Open questions and risks: [`docs/process/OPEN_ISSUES.md`](docs/process/OPEN_ISSUES.md). The most important ones right now: **OPEN-01** (PDK device ratings), **OPEN-03** (the efficiency anchor sits on a mode threshold), **OPEN-16** (first Spectre run).

## Specs at a glance

| Vin | Vout | Iout | Ripple | Efficiency | Modes |
|---|---|---|---|---|---|
| 0.6 – 3 V | 1 V | ≤ 20 mA | 10 mV | 75 % @ 2.4 V | ×2 (0.6–1.2 V), ×1 (1.2–2.4 V), ×½ (2.4–3 V) |

## Block diagram

```
 Mode select (Sam) --mode_target--> Clock generation (Sam) <--vctrl, hold_req-- Error amp + hold cmp (Brandon)
        ^                                  | ctl_a..e                                       ^
        | vin                              v                                                | vout
        |                          Gate drivers (Nathaniel)                                 |
        |                                  | gate_a..e                                      |
  Vin 0.6-3 V ----------------> Switch network: 5 switches + Cfly (Nathaniel) --> Vout --> Cout --> Load
                       Support (Alex): bandgap, LDO, UVLO, soft-start, OCP
```

Clock chain: **VCO → ÷2 → non-overlap → hold gate → mode latch + routing**. Details: [03_clock_chain](docs/design/03_clock_chain.md).

## Repository map

```
.
├── README.md                     you are here
├── CHANGELOG.md                  what changed, when, and why
├── docs/
│   ├── design/
│   │   ├── 00_system_overview.md     specs, 1 V process issues, block diagram, owners
│   │   ├── 01_interfaces.md          signals, pin lists, conventions, mode encoding  <- freeze first
│   │   ├── 02_power_stage.md         topology, routing, forbidden pairs, gate drive, Rout/eff, sizing
│   │   ├── 03_clock_chain.md         the 5 stages, stop/restart timing, mode-change walkthrough
│   │   ├── 04_control_loop.md        error amp, hold comparator, mode select, loop dynamics
│   │   ├── 05_support_circuits.md    bandgap, LDO, UVLO, soft-start, OCP, POR
│   │   ├── 06_modeling_levels_and_swap_plan.md   L0-L5, milestones M0-M7, per-swap checklist
│   │   ├── 07_verification_plan.md   unit tests, T1-T6, pass criteria, regression set
│   │   └── 08_cadence_workflow.md    library, Verilog-A cells, config views, ADE, git
│   ├── process/
│   │   ├── DECISIONS.md          design decision log (DEC-001...), with rationale
│   │   ├── OPEN_ISSUES.md        open decisions and risks (OPEN-01...), with owners
│   │   └── CONTRIBUTING.md       branch/commit rules, how to change a model, changelog format
│   ├── reference/                design-notes PDF + whiteboard photos (read-only)
│   └── GLOSSARY.md
├── veriloga/                     behavioral models (source of truth), see veriloga/README.md
│   ├── clock_chain/   vco, div2, nov_gen, en_hold, mode_route
│   ├── power_stage/   pwr_sw (L2 switch+driver), pwr_avg (L1 averaged stage)
│   ├── control/       err_amp, hold_cmp, mode_sel
│   ├── support/       uvlo_fault
│   └── checkers/      nov_check, sw_check (test only)
├── sim/
│   ├── README.md
│   └── spectre/       common_params, l1_core, l2_core, tb_L1_*, tb_L2_*, tb_U*
└── tools/
    └── sizing_check.py           first-order sizing calculator (reproduces the design notes)
```

## Quick start

**1. Read** (about 20 min): [00_system_overview](docs/design/00_system_overview.md) → [01_interfaces](docs/design/01_interfaces.md) → [06_modeling_levels_and_swap_plan](docs/design/06_modeling_levels_and_swap_plan.md). Then your own block's page:

| You | Your page | Your models |
|---|---|---|
| Nathaniel: switches + gate drivers | [02_power_stage](docs/design/02_power_stage.md) | `veriloga/power_stage/` |
| Sam: clock generation + mode select | [03_clock_chain](docs/design/03_clock_chain.md) | `veriloga/clock_chain/`, `control/mode_sel.va` |
| Brandon: error amp + hold comparator | [04_control_loop](docs/design/04_control_loop.md) | `control/err_amp.va`, `control/hold_cmp.va` |
| Alex: support circuits | [05_support_circuits](docs/design/05_support_circuits.md) | `support/uvlo_fault.va` |

**2. Play with the numbers** (no Cadence needed):
```bash
python3 tools/sizing_check.py
```

**3. Simulate** (needs Spectre):
```bash
cd sim/spectre
spectre tb_U1_clk_chain.scs +log tb_U1_clk_chain.log      # clock chain unit test
spectre tb_L1_T2_vin_ramp.scs +log tb_L1_T2_vin_ramp.log  # whole loop, averaged
grep -E "NOV_CHECK|SW_CHECK" *.log                          # must all be 0
```

**4. Set up Cadence:** follow [08_cadence_workflow](docs/design/08_cadence_workflow.md) (one Verilog-A cell per model, config views for swapping).

## Team

| Person | Owns |
|---|---|
| Nathaniel | Switch network, Cfly, gate drivers, level shifters |
| Sam | Clock generation chain, mode select |
| Brandon | Error amp, compensation, hold comparator |
| Alex | Bandgap, LDO, UVLO, soft-start, overcurrent |

## Contributing

Read [CONTRIBUTING](docs/process/CONTRIBUTING.md). In short: one change per branch, update docs and `CHANGELOG.md` in the same commit, log design choices in `DECISIONS.md`, and rerun the regression set before merging.

# Reference Material

Original source documents. **Don't edit these.** Add new versions next to them with a date in the file name.

| File | What | Date / author | Authority |
|---|---|---|---|
| [`SC_Buck-Boost_Converter_System_Design_Notes.pdf`](SC_Buck-Boost_Converter_System_Design_Notes.pdf) | System design notes (16 pages): specs, block diagram, interfaces, owners, power stage, gate drive, sizing, regulation, clock chain, refinement levels, standard testbenches, open decisions | Nov 19 2026, Sam | **Primary** ([DEC-002](../process/DECISIONS.md#dec-002)) |
| [`whiteboard/whiteboard_clock_generation.jpg`](whiteboard/whiteboard_clock_generation.jpg) | Whiteboard: clock generation chain (5 stages), system specs, "hard things" | Nov 2026, team | Superseded by the PDF where they differ |
| [`whiteboard/whiteboard_mosfet_switching.jpg`](whiteboard/whiteboard_mosfet_switching.jpg) | Whiteboard: MOSFET switching per mode, unified 5-switch network | Nov 2026, team | Superseded by the PDF where they differ |

## Where the PDF content lives in this repo

| PDF section (page) | Repo doc |
|---|---|
| Summary, Specifications, 1 V process (1–2) | [00_system_overview](../design/00_system_overview.md) |
| Top-level system, Interfaces, Block owners (2–4) | [00_system_overview](../design/00_system_overview.md), [01_interfaces](../design/01_interfaces.md) |
| Power stage, Switch phases, Routing, Forbidden pairs (5–6) | [02_power_stage §1–4](../design/02_power_stage.md) |
| Gate drive and oxide stress (6–7) | [02_power_stage §5](../design/02_power_stage.md#5-gate-drive-and-oxide-stress-nathaniels-main-design-problem) |
| Output resistance, efficiency, thresholds, ripple (7–8) | [02_power_stage §6–9](../design/02_power_stage.md) |
| Regulation by frequency, light load, loop dynamics (8–9) | [04_control_loop](../design/04_control_loop.md) |
| Clock generation chain, stages 1–5, rules (10–13) | [03_clock_chain](../design/03_clock_chain.md) |
| Other blocks (13–14) | [05_support_circuits](../design/05_support_circuits.md), [02](../design/02_power_stage.md), [04](../design/04_control_loop.md) |
| Refinement levels (14) | [06_modeling_levels_and_swap_plan](../design/06_modeling_levels_and_swap_plan.md) |
| Standard testbenches (15) | [07_verification_plan](../design/07_verification_plan.md) |
| Open decisions and risks, References (15–16) | [OPEN_ISSUES](../process/OPEN_ISSUES.md) |

## Differences between the whiteboard and the PDF (resolved in favor of the PDF)

| Topic | Whiteboard | PDF / repo |
|---|---|---|
| Mode names | 2:1, 1:1, 1:2 (ratio) | ×½, ×1, ×2 (gain) |
| Switch c in ×1 | "ON" | Φ1 OR Φ2 (off in the gap) |
| Regulation | VCO + feedback (details open) | Error amp → vctrl → VCO; hold comparator for light load |
| Owners | "me" (clock gen), Natsu (gate drive), Brandon, Alex | Sam (clock gen + mode select), Nathaniel (switches + drivers), Brandon (error amp), Alex (support) |

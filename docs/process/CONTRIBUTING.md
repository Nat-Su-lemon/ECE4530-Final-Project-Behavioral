# Contributing: How We Work in This Repo

Short version: **one change per branch, update the docs and the changelog in the same commit, rerun the regression before merging.**

## Branches and commits

| Thing | Convention | Example |
|---|---|---|
| Branch | `<owner>/<block>-<what>` | `nathaniel/pwr_sw-pdk-ron`, `sam/en_hold-restart` |
| Commit message | `<area>: <what changed>` and, in the body, **why** | `en_hold: restart on ring clk edge` / body: "avoids runt Phi1, see DEC-010" |
| Areas | `docs`, `va/<cell>`, `sim`, `tools`, `cadence`, `repo` | |
| Merge | Pull request to `main`; at least one teammate reads it | |

Don't commit simulation outputs, Cadence lock files or logs (`.gitignore` handles the usual ones).

## When you change a Verilog-A model

1. Edit the file in `veriloga/`. That file is the source of truth ([DEC-001](DECISIONS.md#dec-001)).
2. Keep the **header comment** current: owner, level, pins, what is modeled / ignored, swap target.
3. **Pins changed?** Update, in the same commit:
   - the Cadence symbol (regenerate from the `.va`),
   - every netlist in `sim/spectre/` that instantiates the cell,
   - [`docs/design/01_interfaces.md`](../design/01_interfaces.md) (cell list + pin order),
   - the model index in [`veriloga/README.md`](../../veriloga/README.md).
4. **Behavior or defaults changed?** Update the block's page in `docs/design/` and, if it's a design choice, add a `DEC-` entry.
5. Changed the VCO law? Change **both** `vco.va` and `pwr_avg.va`.
6. Run the regression set ([07](../design/07_verification_plan.md#regression-set)) and paste the results into the PR.
7. Add a `CHANGELOG.md` line under **[Unreleased]**.

## When you swap in a real circuit

Follow the per-swap checklist in [06](../design/06_modeling_levels_and_swap_plan.md#per-swap-checklist-copy-into-your-pr-description). In short: same pins, unit test first, one config override, regression, push characterized numbers back into the behavioral model, changelog entry.

## When a number changes (Cfly, Cout, Ron, thresholds, fsw limits…)

1. Change it in `sim/spectre/common_params.scs` (and the ADE global variable).
2. If it's also a model default, change the `.va` default so standalone use matches.
3. Rerun `python3 tools/sizing_check.py` with the new value and update the tables in [`02_power_stage.md` §9](../design/02_power_stage.md#9-current-numbers-output-of-python3-toolssizing_checkpy).
4. Changelog line, plus a DEC entry if it's a design decision.

## Decisions and open issues

- A choice someone might later ask "why?" about goes in [`DECISIONS.md`](DECISIONS.md) (never renumber; supersede instead).
- An unknown, risk or unverified assumption goes in [`OPEN_ISSUES.md`](OPEN_ISSUES.md) with an owner and "close by".

## CHANGELOG format

We follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Sections: **Added / Changed / Removed / Fixed / Verified**. Every entry says **what** and **why** (or links the DEC that explains why). When the team reaches a milestone (M0, M1, …), move [Unreleased] into a new version heading with the date.

## Style for docs

- Short sentences, tables over paragraphs, one idea per bullet.
- Use the gain names ×2 / ×1 / ×½ ([DEC-003](DECISIONS.md#dec-003)).
- Use fsw for switching frequency and say "ring" for 2·fsw ([DEC-016](DECISIONS.md#dec-016)).
- Mark placeholders as *placeholder* and say who will replace them.

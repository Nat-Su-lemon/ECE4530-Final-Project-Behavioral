# 08: Cadence Workflow (Virtuoso + Spectre + Verilog-A)

How to get the models in this repo into Cadence, build the schematics and testbenches, and swap behavioral blocks for real circuits one at a time.

## 1. Source of truth ([DEC-001](../process/DECISIONS.md#dec-001))

- **The `.va` files in this repo are the source of truth.** Cadence keeps its own copy of each Verilog-A view at `<lib>/<cell>/veriloga/veriloga.va`.
- **Best option (Linux, shared server):** make that Cadence file a **symlink** to the repo file. Then editing either one edits both, and git sees every change.
  ```bash
  # after creating the veriloga view once in Virtuoso (step 3):
  cd /path/to/cds/sc_conv/vco/veriloga
  mv veriloga.va veriloga.va.orig
  ln -s /path/to/ECE4530-Final-Project-Behavioral/veriloga/clock_chain/vco.va veriloga.va
  ```
- **If symlinks aren't possible:** copy repo → Cadence after every pull, and Cadence → repo before every commit. Diff to check you didn't lose an edit.
- The Cadence library itself (schematics, symbols, configs, ADE states) is binary-ish. See §7 for what to commit.

## 2. Create the library

1. Library Manager → **File → New → Library**. Name it `sc_conv`.
2. Attach it to the course PDK technology library (so the real devices are available later).

## 3. Create one cell per Verilog-A model

For each file in `veriloga/` (the cell name must equal the module name):

1. **File → New → Cellview**. Library `sc_conv`, cell = module name (e.g., `vco`), **Type = VerilogA**.
2. Paste the file contents (or symlink, §1) and save. Virtuoso compiles on save. Fix errors from the parser log.
3. Accept the offer to **create a symbol**. Tidy it: inputs left, outputs right, `vdd` top, `vss` bottom. **Never rename pins later.**
4. Repeat for: `vco, div2, nov_gen, en_hold, mode_route, pwr_sw, pwr_avg, err_amp, hold_cmp, mode_sel, uvlo_fault, nov_check, sw_check`.

`include "constants.vams"` and `"disciplines.vams"` are found automatically by Spectre.

## 4. Draw the wrappers and testbenches

The plain-text netlists in `sim/spectre/` are the **reference drawings**. Each schematic should contain exactly the instances and nets of the matching netlist.

| Schematic cell | Draw it from |
|---|---|
| `clk_gen` | the clock-chain section of `l2_core.scs` |
| `pwr_stage` | the power-stage section of `l2_core.scs` (5× `pwr_sw` + C1) |
| `top_conv` | `l2_core.scs` without the sources/loads |
| `tb_L1_*`, `tb_L2_*`, `tb_U*` | the matching `.scs` files. Turn the `parameters` into ADE design variables |

Use analogLib for `vsource`, `isource`, `cap`, `res`, `vcvs`.

## 5. Config views: how swapping works

For each testbench, create a **config** view (Hierarchy Editor, top = the `tb_xxx` schematic):

- **View List:** `spectre veriloga schematic`
- **Stop List:** `spectre veriloga`

Because `veriloga` comes before `schematic`, **every cell uses its behavioral model by default**. Cells that only have a schematic (wrappers, testbenches) use the schematic.

**To swap a block to real:** in the Hierarchy Editor's cell table, set that cell's **View to Use = `schematic`**, save, and rerun. To go back, clear the override. "Real" is an explicit opt-in per cell, so you always know what you're simulating.

**Always open ADE on the config view**, not the schematic, or the bindings are ignored.

Keep one config per milestone (`config_M0_allbeh`, `config_M1_realsw`, …) so old results can be reproduced.

## 6. ADE Explorer / Assembler

- One ADE Explorer state per testbench, with the outputs from [07 §Measurements](07_verification_plan.md#measurements-ade-calculator--spectre) saved as expressions.
- One **ADE Assembler** setup containing the regression set ([07](07_verification_plan.md#regression-set)), so the regression is one click.
- Turn `common_params.scs` into ADE **global variables** with the same names (`CFLY`, `COUT`, `RON`, `KI`…). The netlists and ADE then agree.

## 7. Cadence + git

| Commit | Don't commit |
|---|---|
| `veriloga/*.va` (source of truth) | Simulation results (`*.raw`, `psf/`, `simulation/`) |
| `sim/spectre/*.scs` | Lock files (`*.cdslck`), `*.log` |
| Docs, tools | `.cadence/` dbs, `panic.log`, `CDS.log*` |
| *Optionally* the `sc_conv` library (schematics/symbols/configs) **once it exists**, if the team agrees | |

`.gitignore` at the repo root already ignores the usual outputs. If the team commits the Cadence library, put it under `cadence/sc_conv/` and add its `cds.lib` line as relative: `DEFINE sc_conv ./cadence/sc_conv`.

## 8. Running the netlists without schematics

```bash
cd sim/spectre
spectre tb_U1_clk_chain.scs +log tb_U1_clk_chain.log
grep -E "NOV_CHECK|SW_CHECK" tb_U1_clk_chain.log
```

View the results with ViVA (`viva &`, open the `.raw` directory) or the ADE "results browser". Paths in the netlists are relative, so run from `sim/spectre/`.

# Open Issues and Risks

Things that are undecided, unverified or risky. Each has an owner and a "how we close it". When one closes, write the outcome here (don't delete it), and if it led to a choice, add a [DECISIONS.md](DECISIONS.md) entry.

Sources: design notes p.15 "Open decisions and risks" (marked **[notes]**), plus findings while building this repo (marked **[repo]**).

| ID | Issue | Owner | Status |
|---|---|---|---|
| [OPEN-01](#open-01) | PDK device ratings vs. 3 V | Nathaniel | Open |
| [OPEN-02](#open-02) | Final Cfly and VCO ceiling | Nathaniel, Sam | Open |
| [OPEN-03](#open-03) | Efficiency anchor (2.4 V) sits on the ×1/×½ threshold | Sam, all | Open |
| [OPEN-04](#open-04) | Loop gain spread: VCO law / gain_code | Brandon, Sam | Open |
| [OPEN-05](#open-05) | Load-step undershoot after light load | Brandon | Open |
| [OPEN-06](#open-06) | Hold comparator vs. error amp: who regulates | Brandon | Open |
| [OPEN-07](#open-07) | No transient pass/fail number | all | Open |
| [OPEN-08](#open-08) | Minimum load and VCO floor | Sam, Brandon | Open |
| [OPEN-09](#open-09) | Start-up from 0.6 V, supply hand-over, POR | Alex | Open |
| [OPEN-10](#open-10) | Ripple budget: 6.5 mV step vs. notes' 8 mV, plus hysteresis | Nathaniel, Brandon | Open |
| [OPEN-11](#open-11) | Capacitors on chip or off | Nathaniel | Open |
| [OPEN-12](#open-12) | Restart timing of the hold gate | Sam | Open |
| [OPEN-13](#open-13) | Floating nodes when stopped (C1, bootstrap, gates) | Nathaniel, Alex | Open |
| [OPEN-14](#open-14) | Which support blocks to cut | Alex, all | Open |
| [OPEN-15](#open-15) | Convert references to IEEE format | all | Open |
| [OPEN-16](#open-16) | Models and netlists not yet run in Spectre | all | Open |

---

### OPEN-01
**PDK device ratings vs. 3 V** · [notes] · Nathaniel
Switches a, b, d see up to 3 V; their gates need ≈3.4–4 V. Needed: a list of PDK devices with max Vds/Vgs (thin vs. thick oxide). If there's no thick-oxide device, the external-switch plan from the proposal becomes more likely.
**Close by:** a table of devices + ratings in `docs/design/02_power_stage.md` §5, plus the chosen device per switch.

### OPEN-02
**Final Cfly and VCO ceiling** · [notes] · Nathaniel, Sam
Cfly and the fsw ceiling set Imax at the worst corner (×2 at 0.6 V, ×1 at 1.175 V) and trade against gate-drive loss. Current: 6.8 nF and 20 MHz → 25.2 / 23.6 mA at the weakest points (`tools/sizing_check.py`).
**Close by:** find the smallest Cfly and lowest ceiling that carry 20 mA at every band edge, add margin, confirm in L2 T2.

### OPEN-03
**The efficiency anchor (2.4 V) sits on the ×1/×½ threshold** · [repo] · Sam, all
With `v_hi` = 2.4 V and centred 50 mV hysteresis, ×1→×½ happens at 2.425 V rising. Vin = 2.4 V approached from below is still ×1, whose ideal efficiency is 1/2.4 ≈ **42 %**, far below the 75 % spec. Approached from above it's ×½ (ideal 83 %).
**Options:** (a) define the efficiency test as approached from above (current testbench choice, `tb_L2_T4`); (b) lower `v_hi` (e.g., 2.35 V → ×½ from 2.375 V rising; ×½ headroom at 2.375 V is 18.75 % instead of 20 %); (c) move the efficiency anchor (it's marked "can change").
**Close by:** team decision → DEC entry.

### OPEN-04
**Loop gain spread: VCO law / gain_code** · [notes + repo] · Brandon, Sam
Plant gain spreads ≈1000× across mode, Vin and load. A linear VCO law gives ≈1200× loop-gain spread; an exponential law gives ≈8×. The design notes' optional `gain_code` gives ≈140×.
**Close by:** run L1 T3 with `LAW=0` and `LAW=1` at all band edges; decide law vs. gain_code after the first loop simulation (as the notes suggest).

### OPEN-05
**Load-step undershoot after light load** · [repo] · Brandon
At light load, the integrator correctly winds down to the VCO floor. When the load then steps to 20 mA, it has to slew all the way back up. With a fast integrator, the quick Python model showed ≈200 mV undershoot.
**Ideas:** undershoot comparator that kicks vctrl up; larger kp; smaller hold offset; exponential VCO law.
**Close by:** T3 from a light-load starting point meets the (yet to be set) transient limit.

### OPEN-06
**Hold comparator vs. error amp: who regulates** · [repo] · Brandon
Because the hold threshold is above vref (DEC-013), a slow error amp leaves the hold comparator regulating at vref + 5 mV at max fsw. That's robust but inefficient. A fast error amp regulates exactly but undershoots (OPEN-05).
**Close by:** choose ki/kp/v_ofs together; document in DEC-012/013.

### OPEN-07
**No transient pass/fail number** · [notes] · all
"A load-step pass limit is needed before L1 sign-off."
**Close by:** e.g., "≤ 50 mV undershoot for a 1→20 mA step in 100 ns, recovery to ±1 % in ≤ 100 µs". Pick a number, put it in `07_verification_plan.md`.

### OPEN-08
**Minimum load and VCO floor** · [notes] · Sam, Brandon
At the 100 kHz floor the converter delivers ≈0.9–1.4 mA, so lighter loads run in bursts. The floor should come from the lowest load that must regulate smoothly.
**Close by:** pick a minimum smooth load, set `FSW_MIN`.

### OPEN-09
**Start-up from 0.6 V, supply hand-over, POR** · [notes] · Alex
The VCO, logic and drivers must run from Vin at 0.6 V, hand over to a Vout-derived rail, and use a power-on reset so nothing floats. Behavioral models currently use an ideal 1 V `vdd` and start in a safe state by themselves.
**Close by:** an LDO/POR model with a real start-up sequence, T1 at 0.6 V passing with it.

### OPEN-10
**Ripple budget** · [repo] · Nathaniel, Brandon
`sizing_check.py` gives a 6.5 mV charge-transfer step (Cfly = 6.8 nF, Cout = 1.5 µF, top of ×2/×1 bands); the notes say ≈8 mV worst case. Add the hold-comparator hysteresis (2 mV default) and comparator delay overshoot, and the margin to 10 mV is thin.
**Close by:** measure ripple in L2 T4/T6 at band tops; adjust Cout or hysteresis.

### OPEN-11
**Capacitors on chip or off** · [notes] · Nathaniel
Cout in the µF range is external. Cfly in the nF range is revisited after L2.

### OPEN-12
**Restart timing of the hold gate** · [repo] · Sam
The design notes don't specify how the restart is timed. The model re-opens synchronously on a ring-clock rising edge to avoid runt Φ1 pulses (DEC-010). The real circuit can do something else as long as it restarts at Φ1 without a short pulse.
**Close by:** Sam confirms or changes DEC-010.

### OPEN-13
**Floating nodes when stopped** · [notes] · Nathaniel, Alex
When stopped, all switches are off, so C1 floats (leaks slowly) and bootstrap caps/gate nodes drift (1 pF at 1 nA loses 1 V in about 1 µs). At light load, stop periods can be long (bursting).
**Close by:** pull-downs/POR in the real drivers; check that a long stop followed by a restart is safe (no Vgs overstress, correct first pulse).

### OPEN-14
**Which support blocks to cut** · [notes] · Alex, all
The bandgap and gate-drive supply are required. UVLO, soft-start and OCP are the easiest to reduce. Any cut block stays as a Verilog-A model so T1 and T5 remain complete.

### OPEN-15
**Convert references to IEEE format** · [notes] · all
LTC3245 datasheet, TI slpy005, ADI power-design handbook §4, LTC7820, TI snoa998a. Remove tracking parameters from URLs.

### OPEN-16
**Models and netlists not yet run in Spectre** · [repo] · all
Everything in `veriloga/` and `sim/spectre/` was written carefully but **has not been compiled or simulated in Spectre yet** (no simulator was available while writing). Logic was checked with a Python event model and sizing with `tools/sizing_check.py`.
**Close by:** first person with Cadence access runs `tb_U1_clk_chain`, `tb_U2_pwr_open_loop` and `tb_L1_T2_vin_ramp`, fixes any syntax issues, and records the result in `CHANGELOG.md`.

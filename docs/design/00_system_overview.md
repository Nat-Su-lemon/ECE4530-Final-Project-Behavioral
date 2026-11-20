# 00: System Overview

> **Source of truth:** [`docs/reference/SC_Buck-Boost_Converter_System_Design_Notes.pdf`](../reference/SC_Buck-Boost_Converter_System_Design_Notes.pdf) (Sam, Nov 19 2026). The whiteboard photos in [`docs/reference/whiteboard/`](../reference/whiteboard/) came first. Where the two disagree, the PDF wins ([DEC-002](../process/DECISIONS.md#dec-002)).

## What we are building

A **switched-capacitor (SC) buck-boost converter** that regulates **1 V** from a **0.6–3 V** input at up to **20 mA**, using **one flying capacitor (C1 / Cfly) and five switches (a–e)**.

Three gain modes cover the whole input range:

| Mode | Gain (Vout/Vin) | Whiteboard name | Used for Vin |
|---|---|---|---|
| ×2 (step-up) | 2 | "1:2" | 0.6 – 1.2 V |
| ×1 (charge bucket) | 1 | "1:1" | 1.2 – 2.4 V |
| ×½ (step-down) | ½ | "2:1" | 2.4 – 3.0 V |

> ⚠️ **Naming:** the whiteboard named modes by *ratio* (its "2:1" is ×½). This repo always uses **gain** (×2, ×1, ×½), as the design notes do ([DEC-003](../process/DECISIONS.md#dec-003)).

**Regulation:** an error amplifier compares Vout with a reference and outputs **vctrl**. vctrl sets the frequency of a ring-oscillator **VCO**. A higher switching frequency lowers the converter's output resistance and pushes more current. At light load the VCO cannot slow down enough, so a **hold comparator** stops the clock inside a dead-time gap and the converter runs in **bursts**.

## Specifications

| Spec | Value | Status |
|---|---|---|
| Output voltage | 1 V | Adopted (professor feedback) |
| Input range | 0.6 – 3 V | Adopted |
| Max output current | 20 mA | Adopted, may go lower |
| Max output power | 20 mW | Derived |
| Efficiency anchor | 75 % at Vin = 2.4 V → 1 V | Whiteboard, can change. See [OPEN-03](../process/OPEN_ISSUES.md#open-03) |
| Output ripple | 10 mV (1 %), 50 mV fallback | Whiteboard |
| Regulation | VCO sets fsw from the error amp; hold gate at light load | Team choice |
| Mode switching | Hysteresis on Vin thresholds | Whiteboard |
| Transient | Qualitative, no number yet | Open ([OPEN-07](../process/OPEN_ISSUES.md#open-07)) |

## What the 1 V process changes (design notes p.2)

- Vin reaches 3 V on devices tuned for about 1 V. The PDK's **thick-oxide devices and their max Vds/Vgs** decide the switch and driver topology. That makes the PDK device list the first task ([OPEN-01](../process/OPEN_ISSUES.md#open-01)).
- **Gate drive must exceed Vin.** An nMOS switch referenced to Vin needs its gate at about Vin + Vth, roughly 3.4–4 V at Vin = 3 V.
- **Vin = 0.6 V is below the nominal supply.** The VCO, logic and drivers must start from 0.6 V and then switch over to a rail made from Vout.
- A classic 1.2 V bandgap does not fit a 1 V rail, so Alex needs a **sub-1 V reference**.
- Standard cells must be checked at 0.6 V in slow corners.

## Top-level block diagram

Power flows left to right along the bottom; control closes the loop along the top.

```
        vin_sense                    mode_target                 vctrl, hold_req
  +------------------+   (mt_half, mt_x2)   +-------------------+   <------   +---------------------+
  |   Mode select    | ------------------> |  Clock generation | <---------- | Error amp + hold cmp |
  |   (Sam)          |                     |  (Sam, 5 stages)  |             | (Brandon)            |
  +------------------+                     +-------------------+             +---------------------+
          ^                                         | ctl_a..ctl_e                    ^ vout_sense
          |                                         v                                 |
          |                                +-------------------+                      |
          |                                | Gate drivers /    |                      |
          |                                | level shifters    |                      |
          |                                | (Nathaniel)       |                      |
          |                                +-------------------+                      |
          |                                         | gate_a..gate_e                  |
   +-------------+                         +-------------------+   Vout   +--------+  |   +---------+
   | Vin 0.6-3 V |------------------------>| Switch network    |--------->|  Cout  |--+-->|  Load   |
   +-------------+                         | 5 switches + Cfly |          | ~1.5uF |      | <=20 mA |
                                           | (Nathaniel)       |          +--------+      +---------+
                                           +-------------------+

  Support (Alex): bandgap (vref), LDO + bias (vdd_logic, vdd_drv, ibias), UVLO, soft-start, overcurrent -> en/fault
```

How the loop responds to load: load current pulls Vout down, the error amp raises vctrl, the VCO speeds up, and Vout recovers. When Vout rises above target at light load, `hold_req` stops the clock.

## Owners

| Block | Owner | Real-circuit job |
|---|---|---|
| Switch network and Cfly | **Nathaniel** | Five switches + flying capacitor |
| Gate drivers and level shifters | **Nathaniel** | Boosted drive for a, b, d; plain drive for c, e |
| Clock generation (5 stages) | **Sam** | VCO, ÷2, non-overlap, hold gate, mode latch + routing |
| Mode select | **Sam** | Vin thresholds with hysteresis → mode_target |
| Error amp + compensation, hold comparator | **Brandon** | vctrl and hold_req from Vout and Vref |
| Bandgap, LDO, UVLO, soft-start, overcurrent | **Alex** | Support circuits. Any of them can be cut but kept as a Verilog-A model |

The whiteboard's "Natsu" is Nathaniel, and the clock-gen board's "me" is Sam (matches the PDF owner table).

## Where to read next

| If you are… | Read |
|---|---|
| Anyone, first time | this file → [01_interfaces](01_interfaces.md) → [06_modeling_levels_and_swap_plan](06_modeling_levels_and_swap_plan.md) |
| Nathaniel (switches/drivers) | [02_power_stage](02_power_stage.md), `veriloga/power_stage/` |
| Sam (clock gen, mode select) | [03_clock_chain](03_clock_chain.md), `veriloga/clock_chain/`, `veriloga/control/mode_sel.va` |
| Brandon (error amp) | [04_control_loop](04_control_loop.md), `veriloga/control/`, `sim/spectre/tb_L1_*` |
| Alex (support) | [05_support_circuits](05_support_circuits.md), `veriloga/support/` |
| Setting up Cadence | [08_cadence_workflow](08_cadence_workflow.md) |
| Running tests | [07_verification_plan](07_verification_plan.md), [`sim/README.md`](../../sim/README.md) |

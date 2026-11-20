# PM28 requirements

Rev A. One page on purpose. If a number here changes, everything downstream
(simulation limits, derating sheet, firmware thresholds) gets re-checked.

## What it is

A small board that takes a dirty 28 V vehicle/industrial bus and hands clean
5 V and 3.3 V to a microcontroller and its peripherals. It has to survive
being wired backwards, survive the bus doing ugly things, and report what it
is doing over a header.

Test levels are borrowed from ISO 16750-2 and ISO 7637-2 at their 24 V system
severities, which is the usual stand-in for a 28 V bus outside of aerospace.

## Input

| Item | Requirement |
|---|---|
| Nominal input | 28 V |
| Continuous operating range | 16 V to 36 V, both outputs in regulation |
| Turn-on threshold (UVLO) | 15 V ±1 V rising |
| Reverse polarity | -30 V continuous, indefinitely, no damage, < 1 mA drawn |
| Surge (suppressed load dump) | 58 V, 400 ms, 1 Ω source. Outputs stay in regulation through it |
| Fast spike | +112 V, 50 µs, 2 Ω source (ISO 7637-2 pulse 2a). No damage, outputs stay in regulation |
| Protected bus clamp | 38 V ±1 V during any overvoltage |
| Electronic breaker | Trips at 2.5 A ±20 %, auto-retry, folds back into a dead short |
| Resettable fuse | PTC, 2.5 A hold / 5 A trip, 72 V rated. Backup for faults the breaker cannot see |

## Outputs

| Rail | Voltage | Continuous current | Ripple | Load step | Short circuit |
|---|---|---|---|---|---|
| 5V0 | 5.00 V ±2 % | 2.0 A | < 20 mVpp | 25→100 % in 1 µs: < ±5 %, settled < 200 µs | Indefinite, recovers on release |
| 3V3 | 3.30 V ±2 % | 1.0 A | < 20 mVpp | 25→100 % in 1 µs: < ±5 %, settled < 200 µs | Indefinite, recovers on release |

- Startup: both rails monotonic, no overshoot above 3 %, in regulation within 10 ms of the input crossing UVLO.
- Rails only start once the input switch is fully on, so inrush and buck soft-start don't stack.
- Efficiency at 28 V in, both rails at full load: ≥ 85 % overall.

## Telemetry header (to an STM32)

All analog signals are scaled to 0–3.3 V full scale and safe to connect to a 3.3 V MCU pin directly.

| Signal | Scale |
|---|---|
| VBUS_MON | Protected bus voltage, 0–49.5 V |
| IIN_MON | Input current, 0–2.7 A |
| V5_MON, V3_MON | Rail voltages, 0–6.6 V |
| PG5, PG3 | Open drain, low = rail out of regulation |
| FLT | Open drain, low = breaker tripped or timed out |

Firmware reports all of these over UART at 10 Hz and flags anything outside this sheet.

## Environment and build

- Ambient -40 °C to +85 °C. No forced air.
- 4-layer FR-4, 1.6 mm, 1 oz copper, 2 internal ground planes. Target ≤ 60 × 40 mm.
- Every part runs at 50–80 % of its rating or less at worst case (see the derating sheet).
- Every IC has a vendor LTspice model, so every line on this page can be checked in simulation before the board exists.

## Out of scope for Rev A

ISO 7637-2 pulse 1 at the 24 V level (-600 V). It needs a bigger TVS and a
different front end, and the input clamp would dominate the board. Conducted
EMI compliance is designed for (Silent Switcher regulators, input filter
footprint) but not verified until hardware exists.

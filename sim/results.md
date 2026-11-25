| Area | Check | Simulated | Limit | Result |
|---|---|---|---|---|
| Startup | 5V0 in regulation after UVLO crossing | 7.16 ms | ≤ 10 ms | Pass |
| Startup | 5V0 overshoot | +0.09 % | ≤ 3 % | Pass |
| Startup | 5V0 monotonic (largest dip during rise) | 11.8 mV | ≤ 1 % of rail | Pass |
| Startup | 5V0 starts after input switch is fully on | +0.12 ms after ENOUT | after ENOUT | Pass |
| Outputs | 5V0 ripple at full load | 7.7 mVpp | < 20 mVpp | Pass |
| Outputs | 5V0 DC at 28 V, full load | 5.001 V | 5.00 V ± 2 % | Pass |
| Startup | 3V3 in regulation after UVLO crossing | 7.15 ms | ≤ 10 ms | Pass |
| Startup | 3V3 overshoot | +0.16 % | ≤ 3 % | Pass |
| Startup | 3V3 monotonic (largest dip during rise) | 20.3 mV | ≤ 1 % of rail | Pass |
| Startup | 3V3 starts after input switch is fully on | +0.11 ms after ENOUT | after ENOUT | Pass |
| Outputs | 3V3 ripple at full load | 4.7 mVpp | < 20 mVpp | Pass |
| Outputs | 3V3 DC at 28 V, full load | 3.303 V | 3.30 V ± 2 % | Pass |
| Outputs | Efficiency, 28 V in, both rails full load | 94.9 % (13.31 W / 14.02 W) | ≥ 85 % | Pass |
| Input | Inrush peak (bus caps charging) | 0.63 A | < 2.5 A breaker | Pass |
| Telemetry | IIN_MON reading vs actual bus current | 0.500 A vs 0.500 A (-0.0 %) | ± 3 % | Pass |
| Telemetry | Highest voltage on any telemetry pin | 2.50 V | ≤ 3.3 V (+0.3 V) | Pass |
| Input | Pulse 2a: TVS clamp (FET drain) | 98.9 V, 19.4 A peak | Q1 ≤ 150 V | Pass |
| Input | Pulse 2a: protected bus peak | 28.3 V | ≤ 39 V | Pass |
| Input | Pulse 2a: LTC4364 VCC peak | 39.6 V | ≤ 80 V (100 V abs max) | Pass |
| Input | Pulse 2a: 5V0 during the spike | 4.996–5.005 V (0.10 %) | ± 2 % | Pass |
| Input | Pulse 2a: 3V3 during the spike | 3.300–3.305 V (0.16 %) | ± 2 % | Pass |
| Input | Load dump: bus clamp | 38.09–38.09 V | 38 V ± 1 V | Pass |
| Input | Load dump: bus never drops out | min 27.3 V | ≥ 16 V (rails' range) | Pass |
| Input | Load dump: fault timer margin | TMR peak 0.81 V | < 1.25 V fault threshold | Pass |
| Input | Load dump: FLT stays high | min 3.30 V | > 2 V | Pass |
| Input | Turn-on threshold (UVLO rising) | 15.59 V | 15 V ± 1 V | Pass |
| Input | Turn-off threshold (UVLO falling) | 14.97 V | below turn-on | Pass |
| Input | Reverse polarity −30 V: current drawn | 10.1 mA | < 15 mA (Rev B) | Pass |
| Input | Reverse polarity: bus voltage | 0.0 mV | ≈ 0 (loads never see it) | Pass |
| Input | Electronic breaker trip current | 2.54 A | 2.5 A ± 20 % | Pass |
| Input | Folds back into a dead short | 1.29 A | < trip current | Pass |
| Input | Dead short: fault timer turns Q1 off | after 94 ms (3.4 J) | turns off | Pass |
| Input | Dead short: FLT asserts | 87 ms after short | asserts | Pass |
| Input | Dead short: auto-retry | every 260 s | retries | Pass |
| Outputs | 5V0 load step 25 → 100 % → 25 % | 4.07 %, settled in 53 µs | < ± 5 %, < 200 µs | Pass |
| Outputs | 5V0 across 16–38 V input at full load | 4.945–5.007 V (1.10 %) | ± 2 % | Pass |
| Outputs | 3V3 load step 25 → 100 % → 25 % | 2.64 %, settled in 37 µs | < ± 5 %, < 200 µs | Pass |
| Outputs | 3V3 across 16–38 V input at full load | 3.294–3.306 V (0.19 %) | ± 2 % | Pass |
| Outputs | 5V0 short circuit and release | 5.6 A peak; recovers in 0.05 ms, peaks at +2 % | recovers, peak ≤ 110 % | Pass |
| Outputs | 3V3 short circuit and release | 5.6 A peak; recovers in 0.07 ms, peaks at +9 % | recovers, peak ≤ 110 % | Pass |

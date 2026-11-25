# Derating

Requirement: every part at or below 80 % of its rating at worst case. Stresses
come from [`calc/sizing.json`](../calc/sizing.json) and the LTspice results
([`sim/results.json`](../sim/results.json)). [`calc/derating.py`](../calc/derating.py)
generates the table and chart.

![Derating chart](img/derating.png)

| Ref | Part | Stress | Worst case | Rating | Use |
|---|---|---|---|---|---|
| Q1 | IPB072N15N3 | V_DS, TVS clamp with Q1 off | 99.1 V | 150 V | 66% |
| Q1 | IPB072N15N3 | T_j, worst fault pulse (est.) | 130 °C | 175 °C | 74% |
| Q2 | BSC060N10NS3 | V_DS, input reversed | 29.5 V | 100 V | 29% |
| D1 | SMCJ58CA | peak power, pulse 2a (50 µs) | 1.98 kW | 6.7 kW * | 30% |
| F1 | MF-RX250/72 | hold current at 85 °C | 0.978 A | 1.375 A | 71% |
| F1 | MF-RX250/72 | voltage while tripped (load dump) | 58 V | 72 V | 81% |
| U1 | LTC4364 | VCC, load dump | 57.6 V | 100 V | 58% |
| U1 | LTC4364 | SOURCE, input reversed | 29.5 V | 40 V | 74% |
| U2, U3 | LT8641 | V_IN, bus clamp max | 39 V | 65 V | 60% |
| U2 | LT8641 | output current, 5V0 | 2 A | 3.5 A | 57% |
| U4 | LTC6101 | supply, bus clamp max | 39 V | 60 V * | 65% |
| L1 | SRP7028A-4R7M | peak current vs I_sat | 2.46 A | 10 A * | 25% |
| RSNS | 20 mΩ 1206 | power held at current limit | 0.129 W | 0.5 W * | 26% |
| C_BUS | 47 µF 63 V hybrid | voltage, bus clamp max | 39 V | 63 V | 62% |
| C_IN | 1 µF / 4.7 µF 100 V X7R | voltage, bus clamp max | 39 V | 100 V | 39% |
| C_OUT | 22 µF 10 V X7R | voltage, 5V0 rail | 5 V | 10 V | 50% |
| D2 | BAS21 | reverse voltage, pulse 2a | 99.1 V | 250 V | 40% |

\* Rating not yet verified against the datasheet.

## Q1 junction temperature

The LTspice FET models do not include self-heating. Q1 junction temperature is
estimated from the simulated power waveform with a two-element thermal model:
die drop P × R_th(j-c), with R_th(j-c) derived from rated P_tot, plus the pulse
energy absorbed by the tab and adjacent copper. The worst pulse is the partial
short (bench `partial`).

| | Worst pulse | R_th(j-c) | Tab + copper | T_j at 85 °C ambient |
|---|---|---|---|---|
| **IPB072N15N3 G** (D²PAK, used) | 64 W, 6.6 J, 103 ms | 0.5 K/W | 0.5 J/K | **130 °C** |
| IPD200N15N3 G (DPAK, Rev A) | same | 1.0 K/W | 0.15 J/K | 193 °C |

For comparison, the load dump is 8.0 W, 3.23 J over 400 ms, and a dead short
is 32 W for 94 ms (3.4 J).

Estimated accuracy is ±30 %. At the upper bound the D²PAK remains below 175 °C
and the DPAK does not. To be refined with the Infineon Z_th(j-c) curve and a
board-level thermal simulation after layout.

## Exceptions

- **F1 voltage while tripped:** 58 V on a 72 V rating (81 %). Only occurs if
  the PTC has already tripped when a load dump arrives. Accepted.
- **D1 standoff:** the 58 V standoff equals the load-dump level. Minimum
  breakdown is 64.4 V, so D1 does not conduct during the surge, but leakage is
  higher than at 28 V. The table uses peak pulse power as the D1 stress.

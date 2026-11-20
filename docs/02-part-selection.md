# Part selection and sizing

Numbers in this file come from [`calc/sizing.py`](../calc/sizing.py). Change the
spec or a constant there, rerun, and this table is what changes.

## How the parts were picked

The brief said to size the bucks in TI WEBENCH and pick parts with LTspice
models. Those two pull in different directions: WEBENCH only offers TI silicon,
and TI regulators don't ship inside LTspice. I went with the LTspice side,
because every bench test in this project is a simulation, and a regulator
without a vendor model would turn "simulated" into "guessed".

So: Analog Devices ICs throughout, sized by hand from datasheet equations (the
same equations WEBENCH and LTpowerCAD use), then checked in LTspice against the
vendor models. MOSFETs are Infineon parts whose models ship in LTspice's
`standard.mos`. The TVS model is written from the datasheet table because LTspice
only ships two TVS parts and neither fits.

## Block diagram

```
          F1          D1            Q1 (surge)   Q2 (reverse)   RSNS
 28 V ──[PTC 2.5A]──┬─[TVS]─┐  ──┤ IPD200N15N3 ├┤ BSC060N10NS3 ├──/\/\──┬── VBUS (≤ 38 V)
                    │       │         └──────── LTC4364-2 ──────┘        │
 GND ───────────────┴───────┴──────────────────────────────────────────┤
                                                                         ├── LT8641 ── 5V0 / 2 A
                                                                         ├── LT8641 ── 3V3 / 1 A
                                                                         └── LTC6101 + dividers ── telemetry header
```

## Front end

| Ref | Part | Why this one |
|---|---|---|
| U1 | LTC4364HMS-2 | Surge stopper and ideal diode controller in one package. It linearly clamps the bus during a surge instead of disconnecting, so the loads ride through a load dump. Its second gate drives a reverse-blocking FET, and its current limit plus fault timer make the electronic breaker. The -2 suffix auto-retries after a fault, where the -1 latches off. H grade (-40 to 125 °C) because the I grade tops out at our 85 °C ambient. |
| Q1 | Infineon IPD200N15N3 G | The surge pass FET. It sits in linear mode for the whole load dump: 8.4 W for 400 ms, 3.4 J. DPAK for the thermal mass, 150 V because its drain sees the TVS clamp voltage (88 V) during a spike. A 100 V part would run at 88 % of rating there. |
| Q2 | Infineon BSC060N10NS3 G | Reverse-blocking FET. It only ever switches fully on or off, so it doesn't need SOA. 6 mΩ keeps the forward drop small. 100 V covers a reversed supply plus the TVS clamp on a negative spike. |
| D1 | Littelfuse SMCJ58CA | Bidirectional, so a reversed supply doesn't forward-bias it. The 58 V standoff equals the suppressed load-dump level, so it stays off during the 400 ms surge (the FET handles that) and only catches the fast 112 V spike. |
| F1 | Bourns MF-RX250/72 | Resettable backup fuse. Rated 72 V so it can hold off a load dump while tripped. Hold current at 85 °C is about 1.38 A against a 0.98 A worst-case load (71 %). The smaller 1.85 A part would sit at 96 % and could nuisance-trip hot. |
| RSNS | 20 mΩ, 1206, 1 % | LTC4364 limits at 50 mV across it, giving 2.5 A. Folds back to 25 mV (1.25 A) when the output is shorted. The LTC6101 reads the same resistor for telemetry. |
| D_VCC, Z_VCC | BAS21 + 62 V zener | Feeds the LTC4364 VCC pin. The series diode blocks reverse polarity at that pin, and the zener holds VCC below 62 V when the 88 V spike arrives. The UV divider hangs off this protected node too, so a reversed input can't drag the UV pin negative. |

## Regulators

| Ref | Part | Why this one |
|---|---|---|
| U2, U3 | LT8641 | 65 V input, so it runs at about 60 % of its voltage rating with the bus clamped at 38 V. 3.5 A switches loaded to 2 A and 1 A. Silent Switcher layout (split input caps, mirrored hot loops) is the cheapest way to make a 1 MHz buck quiet on a small board. One part number for both rails. |
| L1, L2 | Bourns SRP7028A-4R7M | Same inductor on both rails. 4.7 µH is above the datasheet's 0.7·(Vout+0.1)/f rule for 5 V (3.6 µH). Peak current is 2.5 A against a 10 A saturation rating. |
| — | 1 MHz, RT = 41.2 kΩ | High enough for small passives, low enough that the 3.3 V rail's on-time at 38 V in (87 ns) stays clear of the 50 ns worst-case minimum. |

## Telemetry

| Signal | Circuit | Scale |
|---|---|---|
| VBUS_MON | 140k / 10k divider | 49.5 V full scale |
| IIN_MON | LTC6101 on RSNS, Rin 100 Ω, Rout 6.04 kΩ | 1.208 V/A, 2.73 A full scale |
| V5_MON, V3_MON | 10k / 10k dividers | 6.6 V full scale |
| PG5, PG3, FLT | Open drain, 100k pull-up to 3V3 | Logic |

## Sizing output

```
Front end  FB divider (clamp)  147k / 4.99k          Vclamp 38.07 V nom, 37.2-39.0 V over FB tolerance
Front end  UV divider          1.05M / 100k          turn-on 14.97 V at the connector
Front end  Sense resistor      20 mΩ 1 % 1206        breaker 2.50 A, folds back to 1.25 A into a short
Budget     Output power        13.3 W                5 V x 2 A + 3.3 V x 1 A
Budget     Input current       0.56 A @ 28 V, 0.98 A @ 16 V   assumes 85% worst-case efficiency
Front end  PTC                 MF-RX250/72           hold 1.38 A at 85 C vs 0.98 A worst load (71%)
Front end  TVS                 SMCJ58CA              pulse 2a: 11.8 A, clamps at 87.8 V (worst-case part)
Front end  Surge FET           IPD200N15N3 G         load dump: 20.4 V x 0.41 A = 8.4 W for 400 ms (3.36 J)
Bucks      RT                  41.2k                 1 MHz
5V0 buck   FB divider          887k / 169k           Vout 4.999 V
5V0 buck   Min on-time check   132 ns at 38 V in     limit 50 ns worst case: OK
5V0 buck   Inductor            SRP7028A-4R7M         ripple 0.92 App (46%), peak 2.46 A vs Isat 10 A, DCR loss 151 mW
3V3 buck   FB divider          357k / 115k           Vout 3.283 V
3V3 buck   Min on-time check   87 ns at 38 V in      limit 50 ns worst case: OK
3V3 buck   Inductor            SRP7028A-4R7M         ripple 0.64 App (64%), peak 1.32 A vs Isat 10 A, DCR loss 38 mW
Telemetry  IIN_MON             LTC6101               1.208 V/A, full scale 2.73 A
```

## Things I'm not sure about yet

- The LT8641 feedback reference (0.800 V) is back-solved from ADI's own example
  schematic (1 MΩ / 191 kΩ for a 5 V output), not read off the datasheet. The
  simulation will confirm it.
- The PTC hold-current derating at 85 °C (55 %) is a typical polymer-PTC curve.
  It needs checking against the Bourns MF-RX table.
- The 3.3 V rail's 64 % inductor ripple is high but fine for a current-mode
  part. If the ripple measurement comes in hot, the fix is a 6.8 µH part on
  that rail only.

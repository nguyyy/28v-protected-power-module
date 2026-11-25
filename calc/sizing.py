"""
PM28 component sizing.

Every value that ends up on the schematic is computed here from the spec
(docs/01-spec.md) and the datasheet constants listed at the top. Run it and it
prints the table that docs/02-part-selection.md is built from, and writes
calc/sizing.json for the derating sheet and the firmware scale factors.

    python calc/sizing.py
"""
import json
import sys
import math
from pathlib import Path

# ---------------------------------------------------------------- spec ----
VIN_NOM, VIN_MIN, VIN_MAX = 28.0, 16.0, 36.0
V_LOADDUMP, RI_LOADDUMP, T_LOADDUMP = 58.0, 1.0, 0.400
# ISO 7637-2 pulse 2a rides on top of the 28 V bus (UA), so the open-circuit peak is UA + Us.
V_SPIKE, RI_SPIKE = VIN_NOM + 112.0, 2.0
V_REVERSE = -30.0
V_CLAMP_TARGET = 38.0
V_UVLO_TARGET = 15.0
I_BREAKER_TARGET = 2.5
RAILS = {"5V0": dict(v=5.0, i=2.0), "3V3": dict(v=3.3, i=1.0)}
FSW = 1.0e6
T_AMB_MAX = 85.0

# -------------------------------------------- datasheet / model constants ----
LTC4364_VFB = 1.25          # FB servo, V (1.22..1.28)
LTC4364_VUV = 1.25          # UV comparator threshold, V
LTC4364_VSNS = 0.050        # current-limit sense voltage, V (25 mV foldback)
LT8641_VFB = 0.809          # FB reference, V. Measured on the LTspice vendor model (FB node, steady
                            # state). The 0.800 V back-solved from ADI's demo divider was 1.1 % low.
LT8641_TON_MIN = 50e-9      # worst-case minimum on-time, s
LT8641_VSW_BOT = 0.1        # bottom switch drop at load, V (approx)
LT8641_ILIM = 3.5           # rated output current, A

TVS = dict(pn="SMCJ58CA", vrwm=58.0, vbr_min=64.4, vbr_max=71.2, vc=93.6, ipp=16.0)
PTC = dict(pn="MF-RX250/72", ihold=2.5, itrip=5.0, vmax=72.0, imax=40.0, rmin=0.05, r1max=0.13)
# MF-RX hold-current derating (fraction of 23 C rating). Typical radial PPTC curve;
# confirm against the Bourns MF-RX table before release.
PTC_DERATE = {-40: 1.45, 0: 1.18, 23: 1.00, 50: 0.80, 60: 0.73, 70: 0.66, 85: 0.55}

L_CHOSEN = dict(pn="Bourns SRP7028A-4R7M", L=4.7e-6, dcr=0.037, isat=10.0)

E96 = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33,
       1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74, 1.78, 1.82,
       1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49,
       2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 3.16, 3.24, 3.32, 3.40,
       3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42, 4.53, 4.64,
       4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34,
       6.49, 6.65, 6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66,
       8.87, 9.09, 9.31, 9.53, 9.76]


# E192 (0.1 % parts) for the buck FB dividers. IEC 60063 rounds 9.19 up to 9.20.
E192 = [9.20 if v == 9.19 else v for v in (round(10 ** (i / 192), 2) for i in range(192))]


def e96(x, series=E96):
    dec = 10 ** math.floor(math.log10(x))
    return min((v * dec for v in series + [10.0]), key=lambda v: abs(v - x))


def fmt_r(r):
    for unit, k in (("M", 1e6), ("k", 1e3)):
        if r >= k:
            return f"{r / k:g}{unit}"
    return f"{r:g}"


sys.stdout.reconfigure(encoding="utf-8")
out = {}
rows = []


def row(block, item, value, note=""):
    rows.append((block, item, value, note))


# ---------------------------------------------------- front end: clamp ----
R6 = 4.99e3
R5 = e96(R6 * (V_CLAMP_TARGET / LTC4364_VFB - 1))
vclamp = LTC4364_VFB * (1 + R5 / R6)
vclamp_lo = 1.22 * (1 + R5 / R6)
vclamp_hi = 1.28 * (1 + R5 / R6)
row("Front end", "FB divider (clamp)", f"{fmt_r(R5)} / {fmt_r(R6)}",
    f"Vclamp {vclamp:.2f} V nom, {vclamp_lo:.1f}-{vclamp_hi:.1f} V over FB tolerance")
out["clamp"] = dict(R_top=R5, R_bot=R6, v_nom=vclamp, v_min=vclamp_lo, v_max=vclamp_hi)

# -------------------------------------------------------- front end: UV ----
# UV divider hangs off the protected VCC node (after D_VCC), so a reversed
# input can't pull the UV pin negative. Account for the diode drop.
VD_VCC = 0.6
RUV_BOT = 100e3
RUV_TOP = e96(RUV_BOT * ((V_UVLO_TARGET - VD_VCC) / LTC4364_VUV - 1))
v_uv = LTC4364_VUV * (1 + RUV_TOP / RUV_BOT) + VD_VCC
row("Front end", "UV divider", f"{fmt_r(RUV_TOP)} / {fmt_r(RUV_BOT)}",
    f"turn-on {v_uv:.2f} V at the connector")
out["uv"] = dict(R_top=RUV_TOP, R_bot=RUV_BOT, v_on=v_uv)

# --------------------------------------------- front end: current limit ----
RSNS = 0.020
i_lim = LTC4364_VSNS / RSNS
i_fold = 0.025 / RSNS
row("Front end", "Sense resistor", "20 mΩ 1 % 1206",
    f"breaker {i_lim:.2f} A, folds back to {i_fold:.2f} A into a short")
out["rsns"] = dict(R=RSNS, i_lim=i_lim, i_fold=i_fold)

# --------------------------------------- input current / power budget ----
p_out = sum(r["v"] * r["i"] for r in RAILS.values())
eta_worst = 0.85
p_in = p_out / eta_worst
i_in_min_v = p_in / VIN_MIN
i_in_nom = p_in / VIN_NOM
row("Budget", "Output power", f"{p_out:.1f} W", "5 V x 2 A + 3.3 V x 1 A")
row("Budget", "Input current", f"{i_in_nom:.2f} A @ 28 V, {i_in_min_v:.2f} A @ 16 V",
    f"assumes {eta_worst:.0%} worst-case efficiency")
out["budget"] = dict(p_out=p_out, p_in=p_in, i_in_16=i_in_min_v, i_in_28=i_in_nom)

# --------------------------------------------------------------- PTC ----
ihold_hot = PTC["ihold"] * PTC_DERATE[85]
row("Front end", "PTC", PTC["pn"],
    f"hold {ihold_hot:.2f} A at 85 C vs {i_in_min_v:.2f} A worst load "
    f"({i_in_min_v / ihold_hot:.0%})")
out["ptc"] = dict(ihold_85=ihold_hot, load_frac=i_in_min_v / ihold_hot)

# --------------------------------------------------------------- TVS ----
rd = (TVS["vc"] - TVS["vbr_max"]) / TVS["ipp"]  # dynamic resistance, worst part
# Pulse 2a into the TVS through 2 ohm source + ~0.1 ohm PTC
i_tvs = (V_SPIKE - TVS["vbr_max"]) / (RI_SPIKE + PTC["rmin"] + rd)
v_tvs = TVS["vbr_max"] + i_tvs * rd
row("Front end", "TVS", TVS["pn"],
    f"pulse 2a ({V_SPIKE:.0f} V peak): {i_tvs:.1f} A, clamps at {v_tvs:.1f} V (worst-case part)")
out["tvs"] = dict(rd=rd, i_spike=i_tvs, v_spike=v_tvs)

# ---------------------------------------- surge FET energy in load dump ----
i_bus = p_in / vclamp
vds_ld = V_LOADDUMP - RI_LOADDUMP * i_bus - vclamp_lo
p_fet = vds_ld * i_bus
e_fet = p_fet * T_LOADDUMP
row("Front end", "Surge FET", "Infineon IPB072N15N3 G (150 V, D2PAK)",
    f"load dump: {vds_ld:.1f} V x {i_bus:.2f} A = {p_fet:.1f} W for {T_LOADDUMP * 1e3:.0f} ms "
    f"({e_fet:.2f} J)")
row("Front end", "Reverse FET", "Infineon BSC060N10NS3 G (100 V, SuperSO8)",
    f"sees at most {abs(V_REVERSE):.0f} V reverse DC, {TVS['vbr_max']:.0f} V on a negative spike")
out["surge_fet"] = dict(vds=vds_ld, i=i_bus, p=p_fet, e=e_fet)

# ------------------------------------------------------------- bucks ----
RT = e96(46.5 / (FSW / 1e6) - 5.2) * 1e3
row("Bucks", "RT", fmt_r(RT), f"{FSW / 1e6:g} MHz (46.5/f - 5.2 kΩ fit to ADI RT table)")
out["bucks"] = {"rt": RT, "fsw": FSW}
for name, r in RAILS.items():
    vo, io = r["v"], r["i"]
    # best E192 (0.1 %) pair, bottom 49.9k..995k (FB divider current <= 16 uA), top <= 1M
    rt, rb = min(((e96(b * (vo / LT8641_VFB - 1), E192), b)
                  for b in (v * d for d in (1e4, 1e5) for v in E192)
                  if b >= 49.9e3 and e96(b * (vo / LT8641_VFB - 1), E192) <= 1.0e6),
                 key=lambda p: abs(LT8641_VFB * (1 + p[0] / p[1]) - vo))
    v_set = LT8641_VFB * (1 + rt / rb)
    d_max = vo / VIN_MIN
    ton_hi = vo / V_CLAMP_TARGET / FSW
    l_rec = 0.7 * (vo + LT8641_VSW_BOT) / (FSW / 1e6) * 1e-6
    di = (vo / (FSW * L_CHOSEN["L"])) * (1 - vo / VIN_MAX)
    ipk = io + di / 2
    p_dcr = (io ** 2 + di ** 2 / 12) * L_CHOSEN["dcr"]
    row(f"{name} buck", "FB divider", f"{fmt_r(rt)} / {fmt_r(rb)} 0.1 %", f"Vout {v_set:.3f} V")
    row(f"{name} buck", "Min on-time check", f"{ton_hi * 1e9:.0f} ns at 38 V in",
        f"limit {LT8641_TON_MIN * 1e9:.0f} ns worst case: OK" if ton_hi > LT8641_TON_MIN
        else "TOO SHORT")
    row(f"{name} buck", "Inductor", L_CHOSEN["pn"],
        f"datasheet rule {l_rec * 1e6:.1f} µH; ripple {di:.2f} App "
        f"({di / io:.0%} of load), peak {ipk:.2f} A vs Isat {L_CHOSEN['isat']:.0f} A, "
        f"DCR loss {p_dcr * 1e3:.0f} mW")
    out["bucks"][name] = dict(r_top=rt, r_bot=rb, v_set=v_set, di=di, ipk=ipk,
                              p_dcr=p_dcr, ton_38=ton_hi)

# ----------------------------------------------------------- telemetry ----
ADC_FS = 3.3
tele = {}
for sig, (rt, rb) in {"VBUS_MON": (140e3, 10e3), "V5_MON": (10e3, 10e3),
                      "V3_MON": (10e3, 10e3)}.items():
    fs = ADC_FS * (rt + rb) / rb
    tele[sig] = dict(r_top=rt, r_bot=rb, full_scale=fs, gain=rb / (rt + rb))
    row("Telemetry", sig, f"{fmt_r(rt)} / {fmt_r(rb)}", f"full scale {fs:.1f} V")
RIN, ROUT = 100.0, 6.04e3
g = ROUT / RIN
i_fs = ADC_FS / (g * RSNS)
tele["IIN_MON"] = dict(r_in=RIN, r_out=ROUT, gain=g, v_per_a=g * RSNS, full_scale=i_fs)
row("Telemetry", "IIN_MON", f"LTC6101, Rin {RIN:g} Ω, Rout {fmt_r(ROUT)}",
    f"{g * RSNS:.3f} V/A, full scale {i_fs:.2f} A")
out["telemetry"] = tele

# ------------------------------------------- values tuned in simulation ----
# These aren't derived from a closed-form equation; each one was picked by
# running the LTspice suite (sim/run.py) and is justified in docs/03-simulation.md.
out["tuned"] = dict(
    c_tmr=6.8e-6,    # load dump peaks at 0.80 V of 1.25 V; caps the worst fault pulse at ~100 ms
    c_hgate=2.2e-9,  # HGATE ramp ~8 V/ms: bus up in ~4 ms, inrush ~0.6 A
    r_vcc=1e3, c_vcc=100e-9,   # VCC filter: 100 us RC rides through pulse 2a without the zener
    c_ss=4.7e-9,     # LT8641 soft-start ~2 ms
    c_ff=22e-12,     # FB feed-forward; 4.7 pF gave -6.1 % on the 5 V load step
    c_out=22e-6, n_out=2, c_out_eff={"5V0": 13e-6, "3V3": 15e-6},  # 22 uF 10 V X7R 1210 after DC bias
    c_in=1e-6, c_in_bulk=4.7e-6, c_bus=47e-6, r_bus_esr=0.3,
)
row("Tuned", "C_TMR / C_HGATE", "6.8 µF / 2.2 nF", "set in simulation (docs/03-simulation.md)")
row("Tuned", "C_SS / C_FF", "4.7 nF / 22 pF", "set in simulation (docs/03-simulation.md)")

# -------------------------------------------------------------- report ----
w = [max(len(str(r[i])) for r in rows) for i in range(3)]
for b, it, v, n in rows:
    print(f"{b:<{w[0]}}  {it:<{w[1]}}  {v:<{w[2]}}  {n}")

Path(__file__).with_name("sizing.json").write_text(json.dumps(out, indent=2))

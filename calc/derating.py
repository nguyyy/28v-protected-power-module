"""
PM28 derating sheet. Worst-case stress on each part, from calc/sizing.json and
sim/results.json, divided by its rating. Writes docs/img/derating.png.

Usage: python calc/derating.py
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "calc/sizing.json").read_text())
R = {r["item"]: r for r in json.loads((ROOT / "sim/results.json").read_text(encoding="utf-8"))}
T_AMB = 85.0
TJ_MAX = 175.0


def num(item, key):
    return float(R[item][key])


FETS = {
    "IPB072N15N3 G (D²PAK, used)": dict(rjc=150 / 300, c=0.50),
    "IPD200N15N3 G (DPAK, Rev A)": dict(rjc=150 / 150, c=0.15),
}
pulse = R["Q1 partial short pulse (worst case)"]
tj = {k: T_AMB + pulse["q1_peak_w"] * f["rjc"] + pulse["q1_energy_j"] / f["c"] for k, f in FETS.items()}

b = S["bucks"]
rows = [
    ("Q1", "IPB072N15N3", "V_DS, TVS clamp with Q1 off", S["tvs"]["v_spike"], 150, "V", False),
    ("Q1", "IPB072N15N3", "T_j, worst fault pulse (est.)", tj["IPB072N15N3 G (D²PAK, used)"], TJ_MAX, "°C", False),
    ("Q2", "BSC060N10NS3", "V_DS, input reversed", num("Q2 reverse blocking", "q2_vds"), 100, "V", False),
    ("D1", "SMCJ58CA", "peak power, pulse 2a (50 µs)", S["tvs"]["v_spike"] * S["tvs"]["i_spike"] / 1e3, 6.7, "kW", True),
    ("F1", "MF-RX250/72", "hold current at 85 °C", S["budget"]["i_in_16"], S["ptc"]["ihold_85"], "A", False),
    ("F1", "MF-RX250/72", "voltage while tripped (load dump)", 58, 72, "V", False),
    ("U1", "LTC4364", "VCC, load dump", 57.6, 100, "V", False),
    ("U1", "LTC4364", "SOURCE, input reversed", -num("Q2 reverse blocking", "src_min"), 40, "V", False),
    ("U2, U3", "LT8641", "V_IN, bus clamp max", S["clamp"]["v_max"], 65, "V", False),
    ("U2", "LT8641", "output current, 5V0", 2.0, 3.5, "A", False),
    ("U4", "LTC6101", "supply, bus clamp max", S["clamp"]["v_max"], 60, "V", True),
    ("L1", "SRP7028A-4R7M", "peak current vs I_sat", b["5V0"]["ipk"], 10, "A", True),
    ("RSNS", "20 mΩ 1206", "power held at current limit", 2.54 ** 2 * 0.02, 0.5, "W", True),
    ("C_BUS", "47 µF 63 V hybrid", "voltage, bus clamp max", S["clamp"]["v_max"], 63, "V", False),
    ("C_IN", "1 µF / 4.7 µF 100 V X7R", "voltage, bus clamp max", S["clamp"]["v_max"], 100, "V", False),
    ("C_OUT", "22 µF 10 V X7R", "voltage, 5V0 rail", 5.0, 10, "V", False),
    ("D2", "BAS21", "reverse voltage, pulse 2a", S["tvs"]["v_spike"], 250, "V", False),
]

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("| Ref | Part | Stress | Worst case | Rating | Use |\n|---|---|---|---|---|---|")
    for ref, part, what, s, r, u, mem in rows:
        print(f"| {ref} | {part} | {what} | {s:.3g} {u} | {r:g} {u}{' *' if mem else ''} | {s / r:.0%} |")
    print(f"\nQ1 worst pulse: {pulse['q1_peak_w']:.0f} W peak, {pulse['q1_energy_j']:.2f} J over "
          f"{pulse['q1_time_s'] * 1e3:.0f} ms")
    for k, v in tj.items():
        print(f"  T_j estimate {k}: {v:.0f} °C")

    INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    BLUE, RED = "#2a78d6", "#d03b3b"
    labels = [f"{ref}  {what}" for ref, _, what, *_ in rows][::-1]
    frac = [s / r for _, _, _, s, r, *_ in rows][::-1]
    fig, ax = plt.subplots(figsize=(9, 0.32 * len(rows) + 1.2), dpi=150)
    fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
    bars = ax.barh(labels, [f * 100 for f in frac], color=[RED if f > 0.8 else BLUE for f in frac],
                   height=0.62, edgecolor=SURF, linewidth=2)
    for bar, f in zip(bars, frac):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2, f"{f:.0%}", va="center",
                fontsize=8.5, color=INK)
    ax.axvline(80, color=INK2, lw=1, ls=(0, (4, 3)))
    ax.text(80.5, len(rows) - 0.4, "80 % guideline", fontsize=8, color=INK2, va="bottom")
    ax.set_xlim(0, 105); ax.set_xlabel("worst-case stress, % of rating", color=INK2)
    ax.tick_params(colors=INK2, labelsize=8.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(GRID)
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
    fig.suptitle("Derating: every part at its worst simulated or calculated stress", x=0.01, ha="left",
                 fontsize=12, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(ROOT / "docs/img/derating.png", facecolor=SURF)

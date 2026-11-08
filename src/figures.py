"""Figures for the slide deck (written to slides/fig_*.png)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "slides"
OUT.mkdir(exist_ok=True)
df = pd.read_csv(ROOT / "data" / "results.csv")
val = json.loads((ROOT / "data" / "validation.json").read_text())
TC = ["#CFC8B8", "#9C978C", "#4A4843", "#111111"]
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": "#FBF8F2", "axes.facecolor": "#FBF8F2", "savefig.facecolor": "#FBF8F2", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False})

# 1. evidence map
fig, ax = plt.subplots(figsize=(8, 4.4), dpi=200)
x, y = np.log10(df.pair_all + 1), np.log10(df.pair_clinical + 1)
ax.axvspan(np.log10(21), x.max() + 0.2, ymax=0.1, color="#E8590C", alpha=0.10)
cols = ["#E8590C" if s == "Translational gap" else TC[t] for s, t in zip(df.status, df.modern_tier)]
ax.scatter(x, y, s=40 + df.certainty * 160, c=cols, edgecolor="white", lw=1, zorder=3)
for _, r in df[df.pair_clinical >= 17].iterrows():
    ax.annotate(f"{r.candidate_binomial} ({r.indication_category.split('/')[0]})",
                (np.log10(r.pair_all + 1), np.log10(r.pair_clinical + 1)), fontsize=7,
                xytext=(-6, 6), textcoords="offset points", ha="right")
gl = df[df.status == "Translational gap"].sort_values("pair_all")
for k, (_, r) in enumerate(gl.iterrows()):
    ax.annotate(f"{r.candidate_binomial} ({r.indication_category.split('/')[0]})",
                (np.log10(r.pair_all + 1), 0), xytext=(2.3, 0.1 + 0.15 * k),
                fontsize=7, color="#E8590C", arrowprops=dict(arrowstyle="-", color="#E8590C", lw=0.6))
ticks = [0, 1, 10, 100, 1000]
ax.set_xticks(np.log10(np.array(ticks) + 1), ticks)
ax.set_yticks(np.log10(np.array([0, 1, 10, 50]) + 1), [0, 1, 10, 50])
ax.set_xlabel("PubMed records: taxon + Dioscoridean use")
ax.set_ylabel("Clinical trials / RCTs")
for t, lab in enumerate(["0 none", "1 preclinical", "2 trial", "3 trial + SR/MA"]):
    ax.scatter([], [], c=TC[t], s=50, label=lab)
ax.scatter([], [], c="#E8590C", s=50, label="translational gap")
ax.legend(title="Evidence tier", frameon=False, fontsize=8, loc="upper left")
fig.tight_layout(); fig.savefig(OUT / "fig_map.png"); plt.close(fig)

# 2. claims vs negative controls
v = df[df.indication_category != "toxicity"].sort_values("lift")
fig, ax = plt.subplots(figsize=(8, 5.2), dpi=200)
yy = np.arange(len(v))
ax.hlines(yy, v.background_specificity * 100, v.specificity * 100, color="#ccc", lw=1.5)
ax.scatter(v.background_specificity * 100, yy, c="#B5AE9F", s=22, label="negative controls (same taxon, unrelated use)", zorder=3)
ax.scatter(v.specificity * 100, yy, c="#111111", s=22, label="Dioscoridean claim", zorder=3)
ax.set_yticks(yy, [f"{r.candidate_binomial} · {r.indication_category}" for _, r in v.iterrows()], fontsize=6)
ax.set_xscale("symlog", linthresh=0.1)
ax.set_xlabel("% of the taxon's PubMed literature that mentions the use")
ax.legend(frameon=False, fontsize=8, loc="lower right")
ax.set_title(f"{val['claims_more_specific_than_controls']}/{val['n_claims']} claims beat their controls · "
             f"permutation p = {val['signflip_permutation_p']:.4f}", fontsize=10)
fig.tight_layout(); fig.savefig(OUT / "fig_controls.png"); plt.close(fig)

# 3. top gaps
g = df[~df.status.isin(["Translated via compound", "Post-Dioscoridean use"])].nlargest(8, "translational_gap").iloc[::-1]
fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
ax.barh([f"{r.greek_name} → {r.candidate_binomial}\n{r.indication_category}" for _, r in g.iterrows()],
        g.translational_gap, color=["#E8590C" if s == "Translational gap" else "#4A4843" for s in g.status])
for i, (_, r) in enumerate(g.iterrows()):
    ax.text(r.translational_gap, i, f"  {int(r.pair_all)} papers · {int(r.pair_clinical)} trials", va="center", fontsize=8)
ax.set_xlabel("Translational-gap score")
ax.set_xlim(0, g.translational_gap.max() * 1.6)
ax.tick_params(axis="y", labelsize=8)
fig.tight_layout(); fig.savefig(OUT / "fig_gaps.png"); plt.close(fig)
print("figures written")

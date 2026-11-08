"""Score every Dioscoridean claim and validate the scoring.

Outputs
  data/results.csv        one row per claim with evidence tier, specificity, certainty, gap score
  data/validation.json    statistical checks (negative-control permutation test, HMPC concordance)
  docs/data.js            the same results for the static dashboard

Scoring (transparent, rule-based, every term is shown on the dashboard):
  specificity        = pair_all / taxon_total   (share of a taxon's literature about the claim;
                        corrects for "famous plant" popularity bias)
  lift               = specificity / background specificity from negative controls of the same taxon
  modern_tier        0 = no co-occurring literature
                     1 = literature but no clinical trial (preclinical / observational only)
                     2 = >=1 clinical trial or RCT
                     3 = >=1 clinical trial AND >=1 systematic review / meta-analysis
  certainty          = name_certainty x claim_confidence x GBIF match confidence
  translational_gap  = signal x (1 - clinical saturation) x certainty
                        signal  = min(1, log1p(preclinical records) / log1p(200))
                        clinical saturation = min(1, log1p(trials) / log1p(30))
                       High = a historically attested use with a real preclinical signal
                       but few human trials -> a candidate for a clinical study.
  sustainability flag from GBIF occurrences (records are a sampling proxy, not abundance).
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA, DOCS = ROOT / "data", ROOT / "docs"
NAME_W = {"high": 1.0, "medium": 0.6, "low": 0.3}
CLAIM_W = {"high": 1.0, "medium": 0.7}
RNG = np.random.default_rng(42)
# Claims whose modern clinical use runs through an isolated compound rather than the plant name
# ("Papaver paradox"): plant-name queries undercount their evidence, so they are not called gaps.
COMPOUND_TRANSLATED = {"D02", "D03", "D04", "D32"}


def tier(r):
    if r.pair_all == 0:
        return 0
    if r.pair_clinical == 0:
        return 1
    return 3 if r.pair_synthesis > 0 else 2


def status(r):
    if r.indication_category == "toxicity":
        return "Post-Dioscoridean use"
    if isinstance(r.compound_route, str) and r.compound_route and r.modern_tier <= 2 \
            and r.id in COMPOUND_TRANSLATED:
        return "Translated via compound"
    if r.modern_tier == 3:
        return "Clinically explored"
    if r.modern_tier == 2:
        return "Early clinical"
    if r.pair_all >= 20:
        return "Translational gap"
    if r.pair_all > 0:
        return "Weak signal"
    return "Historical only"


def supply(r):
    if r.occ_global < 1000:
        return "data-poor / possible supply risk"
    if r.occ_greece == 0:
        return "no Greek records in GBIF"
    return "widely recorded"


def main():
    seed = pd.read_csv(DATA / "dioscorides_seed.csv")
    gbif = json.loads((DATA / "raw_gbif.json").read_text())
    pub = json.loads((DATA / "raw_pubmed.json").read_text())
    ctrl = pd.DataFrame(json.loads((DATA / "raw_controls.json").read_text()))

    df = seed.copy()
    for col in ["taxon_total", "pair_all", "pair_clinical", "pair_synthesis"]:
        df[col] = df.id.map(lambda i: pub[i][col])
    for col in ["gbif_scientific_name", "gbif_status", "gbif_match_type", "gbif_confidence",
                "family", "occ_global", "occ_greece", "gbif_key"]:
        df[col] = df.candidate_binomial.map(lambda b: gbif[b].get(col))

    ctrl = ctrl.merge(df[["id", "taxon_total"]], on="id")
    ctrl["spec"] = ctrl.pair_all / ctrl.taxon_total.clip(lower=1)
    bg = ctrl.groupby("id").spec.mean()

    df["specificity"] = df.pair_all / df.taxon_total.clip(lower=1)
    df["background_specificity"] = df.id.map(bg).fillna(0)
    df["lift"] = (df.specificity + 1e-3) / (df.background_specificity + 1e-3)
    df["modern_tier"] = df.apply(tier, axis=1)
    df["certainty"] = (df.name_certainty.map(NAME_W) * df.claim_confidence.map(CLAIM_W)
                       * df.gbif_confidence.fillna(0) / 100).round(3)
    pre = (df.pair_all - df.pair_clinical).clip(lower=0)
    signal = np.minimum(1, np.log1p(pre) / math.log1p(200))
    sat = np.minimum(1, np.log1p(df.pair_clinical) / math.log1p(30))
    df["translational_gap"] = (signal * (1 - sat) * df.certainty).round(3)
    df["status"] = df.apply(status, axis=1)
    df["supply_flag"] = df.apply(supply, axis=1)

    # ---------------- validation ----------------
    v = df[df.indication_category != "toxicity"].copy()
    # (a) paired test: are Dioscoridean claims more specific than the same taxon's control claims?
    diff = (np.log1p(v.specificity * 1000) - np.log1p(v.background_specificity * 1000)).to_numpy()
    w = stats.wilcoxon(diff, alternative="greater")
    # sign-flip permutation test on the mean paired difference
    obs = diff.mean()
    perm = np.array([(diff * RNG.choice([-1, 1], size=len(diff))).mean() for _ in range(20000)])
    p_perm = float((np.sum(perm >= obs) + 1) / (len(perm) + 1))
    # (b) concordance with EMA/HMPC monograph indications (independent regulatory reference)
    pos, neg = v[v.ema_hmpc_overlap == 1], v[v.ema_hmpc_overlap == 0]
    mw = stats.mannwhitneyu(pos.modern_tier, neg.modern_tier, alternative="greater")
    auc = mw.statistic / (len(pos) * len(neg))
    # (c) robustness: does the conclusion survive dropping low-certainty identifications?
    hi = v[v.name_certainty != "low"]
    dhi = (np.log1p(hi.specificity * 1000) - np.log1p(hi.background_specificity * 1000)).to_numpy()
    w_hi = stats.wilcoxon(dhi, alternative="greater")

    validation = {
        "n_claims": int(len(v)),
        "claims_more_specific_than_controls": int((diff > 0).sum()),
        "median_lift": float(v.lift.median()),
        "wilcoxon_p": float(w.pvalue),
        "signflip_permutation_p": p_perm,
        "hmpc_overlap_n": int(len(pos)),
        "hmpc_tier_auc": float(auc),
        "hmpc_mannwhitney_p": float(mw.pvalue),
        "robust_high_medium_names_n": int(len(hi)),
        "robust_wilcoxon_p": float(w_hi.pvalue),
        "tier_counts": {str(k): int(c) for k, c in v.modern_tier.value_counts().sort_index().items()},
        "status_counts": {k: int(c) for k, c in df.status.value_counts().items()},
    }
    (DATA / "validation.json").write_text(json.dumps(validation, indent=1))
    df.to_csv(DATA / "results.csv", index=False)
    DOCS.mkdir(exist_ok=True)
    payload = {"rows": json.loads(df.to_json(orient="records")), "validation": validation}
    (DOCS / "data.js").write_text("window.RHIZO = " + json.dumps(payload) + ";\n", encoding="utf-8")
    print(json.dumps(validation, indent=1))
    print(df.sort_values("translational_gap", ascending=False)[
        ["id", "candidate_binomial", "indication_category", "pair_all", "pair_clinical",
         "pair_synthesis", "lift", "modern_tier", "translational_gap", "status"]].to_string())


if __name__ == "__main__":
    main()

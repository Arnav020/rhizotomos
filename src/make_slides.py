"""Build the 10-slide pitch deck from the pipeline outputs (numbers are never typed by hand)."""
import json
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "slides"
df = pd.read_csv(ROOT / "data" / "results.csv")
V = json.loads((ROOT / "data" / "validation.json").read_text())
INK, MUTE, ACC, GAP, BG = (RGBColor(0x1D, 0x2B, 0x22), RGBColor(0x5D, 0x6B, 0x61),
                           RGBColor(0x2F, 0x6B, 0x45), RGBColor(0xC0, 0x53, 0x2D), RGBColor(0xF7, 0xF5, 0xEF))
URL = "arnav020.github.io/rhizotomos"
REPO = "github.com/Arnav020/rhizotomos"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def p(x):
    return "< 0.001" if x < 0.001 else f"{x:.3f}"


def slide(title, kicker=None, notes=""):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = BG
    if kicker:
        tb = s.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12), Inches(0.4)).text_frame
        tb.text = kicker.upper(); r = tb.paragraphs[0].runs[0]
        r.font.size, r.font.bold, r.font.color.rgb = Pt(12), True, ACC
    tb = s.shapes.add_textbox(Inches(0.6), Inches(0.7), Inches(12.2), Inches(1)).text_frame
    tb.word_wrap = True; tb.text = title; r = tb.paragraphs[0].runs[0]
    r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(30), True, INK, "Georgia"
    s.notes_slide.notes_text_frame.text = notes
    return s


def bullets(s, items, x=0.6, y=1.9, w=12, h=5, size=18):
    tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        bold, _, rest = it.partition("|") if "|" in it else ("", "", it)
        if bold:
            r = para.add_run(); r.text = bold; r.font.bold = True; r.font.size = Pt(size); r.font.color.rgb = INK
        r = para.add_run(); r.text = rest; r.font.size = Pt(size); r.font.color.rgb = INK
        para.space_after = Pt(10)
    return tf


def big(s, x, y, num, label, color=ACC):
    tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(3), Inches(1.4)).text_frame
    tf.word_wrap = True; tf.text = str(num)
    r = tf.paragraphs[0].runs[0]; r.font.size, r.font.bold, r.font.color.rgb = Pt(40), True, color
    q = tf.add_paragraph(); q.text = label; q.runs[0].font.size = Pt(13); q.runs[0].font.color.rgb = MUTE


n = len(df)
trial = int((df.modern_tier >= 2).sum())
gaps = df[df.status == "Translational gap"]
top = df[df.indication_category != "toxicity"].nlargest(3, "translational_gap")

# 1 title
s = slide("Rhizotomos", "EthnoHack 2026 · Track 1 · Traditional knowledge",
          "Rhizotomos was the Greek name for root-cutters, the herb gatherers whose knowledge Dioscorides recorded. "
          "This project asks which of his claims modern science has actually tested.")
bullets(s, ["A translational-gap atlas of Dioscorides' De Materia Medica",
            "Which 2,000-year-old therapeutic claims has modern science tested, which only in the lab, and which never?",
            f"Live demo: {URL}    Code: {REPO}", "Arnav Joshi"], y=2.0, size=22)

# 2 problem
s = slide("\"Ancient remedies validated by science\": which ones, though?", "Problem",
          "De Materia Medica was the reference text for about 1,500 years. Claims about it are anecdotal. Three technical obstacles stop a systematic answer.")
bullets(s, ["Names drift.|  Greek thymon ≠ garden thyme; 'white hellebore' is Veratrum; silphion is extinct.",
            "Popularity bias.|  Garlic or cannabis appear in thousands of papers, so raw counts make every claim look 'supported'.",
            "Evidence ≠ evidence.|  100 in-vitro papers are not one clinical trial.",
            "Result:|  nobody can list the documented uses that have a real lab signal but have never been tested in humans. That is where a trial would be most justified."])

# 3 data
s = slide("Data: one ancient text, three open APIs, one regulatory reference", "Data",
          "All API responses are cached so the analysis reruns offline. Counts only, no abstracts stored.")
bullets(s, [f"De Materia Medica (public domain)|  {n} curated claims: Greek name, candidate taxon, paraphrased use, name and reading certainty, curator notes",
            "GBIF Backbone Taxonomy (CC BY 4.0)|  name resolution with match confidence; occurrences worldwide and in Greece",
            "PubMed E-utilities|  for every claim: all records, clinical trials/RCTs, systematic reviews/meta-analyses, and the taxon's total literature",
            f"Negative controls|  {2*n} extra queries: the same taxon paired with unrelated uses (fixed seed)",
            "EMA/HMPC monographs|  an independent reference: does the claim overlap a current EU herbal monograph indication?"])

# 4 method
s = slide("Method: claim → taxon → evidence → gap", "Approach",
          "Every formula is in src/score.py and shown per claim on the dashboard. Nothing is a black box.")
bullets(s, ["Specificity|  = claim records ÷ the taxon's total records, which corrects popularity bias",
            "Lift|  = specificity ÷ specificity of the same taxon's negative controls",
            "Evidence tier|  0 none · 1 preclinical only · 2 ≥1 clinical trial · 3 trial + systematic review/meta-analysis",
            "Certainty|  = name certainty × reading certainty × GBIF match confidence; uncertain identifications are down-weighted, not hidden",
            "Translational-gap score|  = preclinical signal × (1 − clinical saturation) × certainty"])

# 5 map
s = slide(f"Only {trial} of {n} claims ever reached a human trial", "Results · evidence map",
          "Each point is one claim. Bottom right means lots of laboratory work and no trials: the translational gap.")
s.shapes.add_picture(str(S / "fig_map.png"), Inches(0.6), Inches(1.7), height=Inches(5.5))
big(s, 9.6, 2.0, trial, "claims with ≥1 clinical trial")
big(s, 9.6, 3.6, len(gaps), "translational gaps (≥20 papers, 0 trials)", GAP)
big(s, 9.6, 5.2, V["tier_counts"].get("0", 0), "claims with no modern literature at all", MUTE)

# 6 validation
s = slide("The signal is real, not an artefact of famous plants", "Validation",
          "Each taxon's own unrelated-use queries are its control, so popularity cancels out. Robust to dropping uncertain names.")
s.shapes.add_picture(str(S / "fig_controls.png"), Inches(0.4), Inches(1.6), height=Inches(5.7))
bullets(s, [f"{V['claims_more_specific_than_controls']}/{V['n_claims']}|  claims are more specific than their own negative controls (median lift {V['median_lift']:.1f}×)",
            f"Wilcoxon p {p(V['wilcoxon_p'])}|  · sign-flip permutation p {p(V['signflip_permutation_p'])}",
            f"Without low-certainty names|  p {p(V['robust_wilcoxon_p'])}",
            f"EMA/HMPC concordance|  AUC {V['hmpc_tier_auc']:.2f} (p {p(V['hmpc_mannwhitney_p'])}): claims matching EU monographs sit in higher evidence tiers"],
        x=9.2, y=1.8, w=3.8, size=13)

# 7 gaps
lines = [f"{r.greek_name} → {r.candidate_binomial}|  {r.dmm_indication}: {int(r.pair_all)} papers, {int(r.pair_clinical)} trials"
         for _, r in top.iterrows()]
s = slide("Where 2,000 years of use never met a clinical trial", "Results · research priorities",
          "These are hypotheses for clinical research prioritisation, not recommendations. Toxicity and quality of the preclinical data must be assessed first.")
s.shapes.add_picture(str(S / "fig_gaps.png"), Inches(0.5), Inches(1.7), height=Inches(4.3))
bullets(s, lines, x=8.2, y=1.9, w=4.8, size=13)
bullets(s, ["Hypotheses for trial prioritisation, not medical claims."], x=0.6, y=6.3, size=13)

# 8 demo
s = slide("Demo: the interactive atlas", "Prototype",
          "Walk through: click the top gap; show the Greek name, GBIF resolution, certainty, controls, then open the exact PubMed query.")
pic = S / "dashboard.png"
if pic.exists():
    s.shapes.add_picture(str(pic), Inches(0.6), Inches(1.7), height=Inches(5.4))
bullets(s, ["Every claim → Greek name, resolved taxon, certainty, evidence tier, lift, gap score",
            "One click opens the exact PubMed query: fully auditable",
            "Biodiversity layer: GBIF records worldwide and in Greece",
            "Static site, no server, opens offline", URL], x=8.6 if pic.exists() else 0.6, y=1.9,
        w=4.4 if pic.exists() else 12, size=14 if pic.exists() else 20)

# 9 limits
s = slide("Limits and responsible research", "Uncertainty",
          "We state uncertainty in the data itself: certainty flags, curator notes and deliberate hard cases (thymon, silphion, white hellebore, colchicum).")
bullets(s, ["Co-occurrence ≠ efficacy:|  tiers count whether trials exist, not their results or quality",
            "The seed table is a curated prototype:|  identifications and readings need verification against the Wellmann edition",
            "Query noise:|  title/abstract matching, synonyms missed; every query is stored for audit",
            "GBIF counts measure sampling, not abundance;|  IUCN is the next step",
            "Public-domain text, no living-community knowledge taken;|  extending to community knowledge requires consent and Nagoya benefit-sharing",
            "Toxic taxa flagged;|  nothing here is medical advice"], size=16)

# 10 impact
s = slide("Impact and what comes next", "Impact · future",
          "The method generalises to any historical pharmacopoeia: Byzantine, Arabic, Ayurvedic, Chinese.")
bullets(s, ["For researchers:|  a ranked, auditable list of historically grounded hypotheses for clinical study",
            "For historians:|  a quantitative view of which ancient knowledge survived into modern pharmacology",
            "For conservation:|  ties demand signals to occurrence data (e.g. lost silphion, Greek endemics)",
            "Next:|  Greek NLP over all ~800 chapters · diachronic names via Byzantine, Arabic and Latin traditions · trial-outcome grading (ClinicalTrials.gov) · compound links (LOTUS/Wikidata) · IUCN",
            f"{URL}  ·  {REPO}"], size=17)

prs.save(S / "Rhizotomos_EthnoHack2026.pptx")
print("deck written:", len(prs.slides), "slides")

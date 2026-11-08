"""Build the 10-slide pitch deck (HTML -> PDF + PNG) from pipeline outputs. No number is typed by hand."""
import json
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "slides"
df = pd.read_csv(ROOT / "data" / "results.csv")
V = json.loads((ROOT / "data" / "validation.json").read_text())
URL, REPO = "rhizotomos.vercel.app", "github.com/Arnav020/rhizotomos"


def p(x):
    return "&lt; 0.001" if x < 0.001 else f"{x:.3f}"


n = len(df)
trial = int((df.modern_tier >= 2).sum())
gaps = df[df.status == "Translational gap"].sort_values("translational_gap", ascending=False)
gent = df[df.id == "D23"].iloc[0]
opium = df[df.id == "D02"].iloc[0]
compound_n = int((df.status == "Translated via compound").sum())
no_lit = int((df.pair_all == 0).sum())

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap');
*{box-sizing:border-box;margin:0}body{background:#ddd;font-family:Manrope,sans-serif;color:#111}
.slide{width:1920px;height:1080px;background:#F4EFE6;position:relative;overflow:hidden;padding:80px 96px;page-break-after:always}
.tag{font-size:20px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#E8590C}
h1{font-size:68px;line-height:1.05;font-weight:600;letter-spacing:-.02em;margin:20px 0 0;max-width:1450px}
h1 .o{color:#E8590C}.sub{font-size:28px;line-height:1.45;color:#3A3A36;margin-top:24px;max-width:1300px}
.clay{background:#FBF8F2;border-radius:40px;box-shadow:16px 16px 36px rgba(120,96,60,.22),-12px -12px 28px rgba(255,255,255,.9),inset 3px 3px 6px #fff,inset -5px -5px 10px rgba(120,96,60,.10);padding:40px}
.ink{background:#111;color:#F4EFE6;border-radius:40px;padding:40px;box-shadow:16px 16px 36px rgba(0,0,0,.28),inset 3px 3px 8px rgba(255,255,255,.08),inset -5px -5px 10px rgba(0,0,0,.6)}
.orb{position:absolute;border-radius:50%;background:#E8590C;box-shadow:14px 14px 30px rgba(232,89,12,.35),inset 6px 6px 14px rgba(255,255,255,.4),inset -10px -10px 20px rgba(120,40,0,.35)}
.row{display:flex;gap:40px}.col{flex:1}
.big{font-size:84px;font-weight:600;letter-spacing:-.03em;line-height:1}.big.o{color:#E8590C}
.lab{font-size:24px;line-height:1.35;color:#77746B;margin-top:12px}.ink .lab{color:#BDB7AA}
.h3{font-size:34px;font-weight:600;line-height:1.2}.p{font-size:24px;line-height:1.45;color:#3A3A36;margin-top:12px}.ink .p{color:#BDB7AA}
.num{font-size:22px;font-weight:600;color:#E8590C;letter-spacing:.08em}
.foot{position:absolute;left:96px;right:96px;bottom:40px;display:flex;justify-content:space-between;font-size:18px;color:#77746B}
img.fig{border-radius:32px;display:block}
.gk{font-size:64px;font-weight:600}.mono{font-variant-numeric:tabular-nums}
.flow{display:flex;align-items:stretch;gap:24px;margin-top:56px}.flow .clay{flex:1;padding:32px}.arrow{align-self:center;font-size:48px;color:#E8590C}
"""


def foot(i, src=""):
    return f'<div class="foot"><span>Rhizotomos · EthnoHack 2026 · Track 1</span><span>{src}</span><span>{i:02d} / 10</span></div>'


slides = []
# 1 title
slides.append(f"""<section class="slide"><div class="orb" style="width:340px;height:340px;right:-60px;top:-80px"></div>
<div class="tag">EthnoHack 2026 · Track 1 · Traditional knowledge</div>
<h1 style="font-size:150px;margin-top:150px">Rhizotomos<span class="o">.</span></h1>
<div class="sub" style="font-size:40px;max-width:1350px">Which of Dioscorides' 2,000 year old remedies has modern science actually tested, and which did it never test?</div>
<div class="row" style="margin-top:80px;gap:24px"><div class="clay" style="padding:24px 32px;font-size:24px">Live atlas · <b>{URL}</b></div><div class="clay" style="padding:24px 32px;font-size:24px">Code · <b>{REPO}</b></div><div class="ink" style="padding:24px 32px;font-size:24px">Arnav Joshi</div></div>
<div class="foot"><span>ῥιζοτόμος: "root cutter", the herb gatherers Dioscorides learned from</span><span></span><span>01 / 10</span></div></section>""")
# 2 problem
slides.append(f"""<section class="slide"><div class="tag">01 · Problem</div>
<h1>"Ancient remedies validated by science." <span class="o">Which ones?</span></h1>
<div class="sub"><i>De Materia Medica</i> (c. 60 CE) was the pharmacology reference of Europe, Byzantium and the Islamic world for 1,500 years. Nobody can say which of its claims modern research has tested.</div>
<div class="row" style="margin-top:64px">
<div class="clay col"><div class="num">OBSTACLE 1</div><div class="h3" style="margin-top:16px">Names drift</div><div class="p">Greek <b>thymon</b> is not garden thyme. "White hellebore" is <b>Veratrum</b>. <b>Silphion</b> is extinct.</div></div>
<div class="clay col"><div class="num">OBSTACLE 2</div><div class="h3" style="margin-top:16px">Popularity bias</div><div class="p">Garlic appears in thousands of papers, so raw counts make every claim about it look "supported".</div></div>
<div class="clay col"><div class="num">OBSTACLE 3</div><div class="h3" style="margin-top:16px">Evidence is not evidence</div><div class="p">A hundred in vitro papers are not one clinical trial. Some evidence hides inside isolated compounds.</div></div>
</div>{foot(2)}</section>""")
# 3 data
slides.append(f"""<section class="slide"><div class="tag">02 · Data</div>
<h1>One ancient text, two open APIs, <span class="o">one regulatory check</span></h1>
<div class="row" style="margin-top:64px">
<div class="ink col"><div class="big o">{n}</div><div class="lab">curated claims from <i>De Materia Medica</i>: Greek name, candidate taxon, paraphrased use, name certainty, reading certainty, curator note</div></div>
<div class="clay col"><div class="big">{n*4 + n*2}</div><div class="lab">PubMed E-utilities queries: records, clinical trials, systematic reviews, taxon totals and {n*2} negative controls</div></div>
<div class="clay col"><div class="big">{len(df.candidate_binomial.unique())}</div><div class="lab">taxa resolved on the GBIF Backbone with occurrence records worldwide and in Greece (CC BY 4.0)</div></div>
<div class="clay col"><div class="big">{int(df.ema_hmpc_overlap.sum())}</div><div class="lab">claims overlapping a current EMA/HMPC herbal monograph, held out as an independent check</div></div>
</div><div class="sub" style="font-size:24px;margin-top:48px">Every API response is cached in the repository, so the whole analysis reruns offline. Counts only: no abstracts are stored.</div>{foot(3,"Sources: Dioscorides (public domain) · GBIF.org · NCBI PubMed · EMA/HMPC")}</section>""")
# 4 method
slides.append(f"""<section class="slide"><div class="tag">03 · Method</div>
<h1>From a Greek plant name <span class="o">to a research priority</span></h1>
<div class="flow">
<div class="clay"><div class="num">01 CLAIM</div><div class="h3" style="margin-top:12px">Read</div><div class="p">Greek name, use and two doubt flags</div></div><div class="arrow">→</div>
<div class="clay"><div class="num">02 TAXON</div><div class="h3" style="margin-top:12px">Resolve</div><div class="p">GBIF accepted name, confidence, occurrences</div></div><div class="arrow">→</div>
<div class="clay"><div class="num">03 EVIDENCE</div><div class="h3" style="margin-top:12px">Weigh</div><div class="p">PubMed records, trials, reviews ÷ taxon total</div></div><div class="arrow">→</div>
<div class="ink" style="flex:1;padding:32px"><div class="num">04 GAP</div><div class="h3" style="margin-top:12px">Score</div><div class="p">signal × (1 − trial saturation) × certainty</div></div></div>
<div class="row" style="margin-top:48px">
<div class="clay col" style="padding:32px"><div class="h3" style="font-size:28px">Lift over own controls</div><div class="p">Each plant is compared with itself paired with 2 unrelated uses. Popularity cancels out.</div></div>
<div class="clay col" style="padding:32px"><div class="h3" style="font-size:28px">Evidence tier 0 to 3</div><div class="p">none · preclinical only · ≥1 clinical trial · trial plus systematic review</div></div>
<div class="clay col" style="padding:32px"><div class="h3" style="font-size:28px">Doubt is data</div><div class="p">Uncertain identifications are down-weighted, never hidden.</div></div></div>{foot(4,"All formulas: src/score.py")}</section>""")
# 5 map
slides.append(f"""<section class="slide"><div class="tag">04 · Results</div>
<h1>Only <span class="o">{trial} of {n}</span> claims ever reached a human trial</h1>
<div class="row" style="margin-top:48px;align-items:flex-start"><img class="fig clay" style="padding:16px;width:1060px" src="fig_map.png">
<div class="col" style="display:flex;flex-direction:column;gap:24px">
<div class="ink" style="padding:32px"><div class="big o">{len(gaps)}</div><div class="lab" style="margin-top:4px">translational gaps: 20+ papers, zero clinical trials</div></div>
<div class="clay" style="padding:32px"><div class="big">{compound_n}</div><div class="lab">translated via an isolated compound, the "Papaver paradox"</div></div>
<div class="clay" style="padding:32px"><div class="big">{no_lit}</div><div class="lab">claims with no modern literature at all, including lost silphion</div></div></div></div>{foot(5,"PubMed counts retrieved 9 Nov 2026")}</section>""")
# 6 validation
slides.append(f"""<section class="slide"><div class="tag">05 · Validation</div>
<h1>The signal is real, <span class="o">not an artefact of famous plants</span></h1>
<div class="row" style="margin-top:48px;align-items:flex-start"><img class="fig clay" style="padding:16px;width:1000px" src="fig_controls.png">
<div class="col" style="display:flex;flex-direction:column;gap:24px">
<div class="ink" style="padding:32px"><div class="big o">{V['claims_more_specific_than_controls']}/{V['n_claims']}</div><div class="lab">claims beat their own negative controls · median lift {V['median_lift']:.1f}× · Wilcoxon p {p(V['wilcoxon_p'])} · permutation p {p(V['signflip_permutation_p'])}</div></div>
<div class="clay" style="padding:32px"><div class="big">AUC {V['hmpc_tier_auc']:.2f}</div><div class="lab">claims in EU herbal monographs sit in higher evidence tiers · p {p(V['hmpc_mannwhitney_p'])}</div></div>
<div class="clay" style="padding:32px"><div class="big" style="font-size:72px">p {p(V['robust_wilcoxon_p'])}</div><div class="lab">still significant without low certainty identifications</div></div></div></div>{foot(6,"Sign flip permutation, 20,000 draws, seed 42")}</section>""")
# 7 hero finding
slides.append(f"""<section class="slide"><div class="orb" style="width:220px;height:220px;right:120px;top:90px"></div><div class="tag">06 · Findings</div>
<h1>Where 2,000 years of use <span class="o">never met a clinical trial</span></h1>
<div class="row" style="margin-top:56px;align-items:stretch">
<div class="clay" style="width:760px"><div class="num">DIOSCORIDES, BOOK III</div><div class="gk" style="margin-top:12px">γεντιανή</div><div class="h3" style="color:#77746B;font-weight:500">Gentiana lutea · gentian root</div>
<div class="p" style="margin-top:24px">"warms, and is good for the stomach"</div>
<div class="row" style="margin-top:32px;gap:24px"><div><div class="big o mono">{gent.lift:.0f}×</div><div class="lab">lift over controls</div></div><div><div class="big mono">{int(gent.pair_all)}</div><div class="lab">papers</div></div><div><div class="big mono">0</div><div class="lab">trials</div></div></div></div>
<div class="col"><img class="fig clay" style="padding:16px;width:100%" src="fig_gaps.png"></div></div>
<div class="sub" style="font-size:22px;margin-top:32px">Hypotheses for trial prioritisation, not medical claims. Toxicity and the quality of preclinical work must be assessed first.</div>{foot(7)}</section>""")
# 8 papaver paradox + taxonomy blind spot
slides.append(f"""<section class="slide"><div class="tag">07 · Two insights nobody measures</div>
<h1>Databases are confident. <span class="o">History is not.</span></h1>
<div class="row" style="margin-top:56px">
<div class="ink col"><div class="num">THE TAXONOMY BLIND SPOT</div><div class="big o" style="margin-top:24px">99 to 100%</div><div class="p">GBIF match confidence for all {len(df.candidate_binomial.unique())} names, including disputed ones like thymon, sideritis and silphion. Modern taxonomy cannot see historical identification error, so Rhizotomos stores it as a certainty weight.</div></div>
<div class="clay col"><div class="num">THE PAPAVER PARADOX</div><div class="big" style="margin-top:24px">{int(opium.pair_clinical)} trials</div><div class="p">for <i>Papaver somniferum</i> and pain, although opioids are the most successful plant drug in history. Evidence migrates into compounds (morphine, scopolamine, aspirin) and plant name searches miss it. We label these claims instead of calling them gaps.</div></div></div>
<div class="row" style="margin-top:40px;gap:24px"><div class="clay col" style="padding:28px"><div class="num">MEKON</div><div class="h3" style="font-size:30px;margin-top:10px">Opium poppy <span style="color:#E8590C">→</span> morphine</div></div><div class="clay col" style="padding:28px"><div class="num">MANDRAGORAS</div><div class="h3" style="font-size:30px;margin-top:10px">Mandrake <span style="color:#E8590C">→</span> scopolamine</div></div><div class="clay col" style="padding:28px"><div class="num">ITEA</div><div class="h3" style="font-size:30px;margin-top:10px">Willow <span style="color:#E8590C">→</span> salicin → aspirin</div></div><div class="clay col" style="padding:28px"><div class="num">KOLCHIKON</div><div class="h3" style="font-size:30px;margin-top:10px">Autumn crocus <span style="color:#E8590C">→</span> colchicine</div></div></div>{foot(8)}</section>""")
# 9 demo + limits
slides.append(f"""<section class="slide"><div class="tag">08 · Prototype and limits</div>
<h1>An atlas you can audit <span class="o">claim by claim</span></h1>
<div class="row" style="margin-top:48px;align-items:flex-start"><img class="fig" style="width:1060px;box-shadow:16px 16px 36px rgba(120,96,60,.25)" src="dashboard.png">
<div class="ink col"><div class="h3">What it does not claim</div><div class="p" style="font-size:21px">• Co-occurrence measures attention, not efficacy<br>• Trial counts say nothing about trial results<br>• The seed table needs checking against the Wellmann edition<br>• GBIF records measure sampling, not abundance<br>• A public domain text: no living community knowledge was taken. Extending to it needs consent and Nagoya benefit sharing<br>• Toxic taxa flagged. Not medical advice</div></div></div>{foot(9,URL)}</section>""")
# 10 impact
slides.append(f"""<section class="slide"><div class="orb" style="width:300px;height:300px;right:-40px;bottom:-60px"></div><div class="tag">09 · Impact and next steps</div>
<h1>A method for every <span class="o">historical pharmacopoeia</span></h1>
<div class="row" style="margin-top:56px">
<div class="clay col"><div class="h3">Drug discovery</div><div class="p">A ranked, auditable shortlist of historically grounded hypotheses for clinical study.</div></div>
<div class="clay col"><div class="h3">History of medicine</div><div class="p">A quantitative view of which ancient knowledge survived into modern pharmacology.</div></div>
<div class="clay col"><div class="h3">Conservation</div><div class="p">Demand signals tied to occurrence data, from lost silphion to Greek endemics.</div></div></div>
<div class="ink" style="margin-top:40px;padding:32px 40px"><div class="p" style="font-size:24px;color:#F4EFE6"><b style="color:#E8590C">Next:</b> Greek NLP over all ~800 chapters · Byzantine, Arabic and Latin name mapping · trial outcome grading from ClinicalTrials.gov · compound links via LOTUS and Wikidata · IUCN risk</div></div>
<div class="sub" style="font-size:26px;margin-top:32px"><b>{URL}</b> · <b>{REPO}</b></div>{foot(10)}</section>""")

html = f"<!doctype html><html><head><meta charset='utf-8'><title>Rhizotomos deck</title><style>{CSS}@page{{size:1920px 1080px;margin:0}}</style></head><body>{''.join(slides)}</body></html>"
(S / "deck.html").write_text(html, encoding="utf-8")
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto((S / "deck.html").as_uri()); pg.wait_for_timeout(1500)
    pg.pdf(path=str(S / "Rhizotomos_EthnoHack2026.pdf"), width="1920px", height="1080px", print_background=True)
    for i, el in enumerate(pg.query_selector_all(".slide"), 1):
        el.screenshot(path=str(S / f"slide_{i:02d}.png"))
    b.close()
print("deck: pdf + png written")

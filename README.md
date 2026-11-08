# Rhizotomos: a translational-gap atlas of Dioscorides' *De Materia Medica*

**EthnoHack 2026, Track 1: Traditional knowledge** (with a biodiversity layer for Track 3)

> *Rhizotomos* (ῥιζοτόμος, "root-cutter") was the Greek name for the herb gatherers whose field knowledge Dioscorides wrote down. This tool does their job in reverse: it digs up the roots of each claim in modern evidence.

**Live atlas:** https://rhizotomos.vercel.app (mirror: https://arnav020.github.io/rhizotomos/) (static, also works offline by opening `docs/index.html`)

## Problem

*De Materia Medica* (c. 50–70 CE) was the main pharmacological reference in Europe and the Byzantine and Islamic worlds for about 1,500 years. People often say that "ancient remedies are being validated by modern science", but nobody can say **which** Dioscoridean claims modern science has actually tested, which it has tested only in the lab, and which it has ignored. Three problems get in the way:

1. **Names.** A Greek plant name is not a modern species. *Thymon* is usually *Thymbra capitata*, not garden thyme. "White hellebore" is *Veratrum*, not *Helleborus*. Silphion is lost.
2. **Popularity bias.** Famous plants (garlic, cannabis) appear in thousands of papers, so raw counts make every claim about them look "supported".
3. **Evidence quality.** A pile of in-vitro papers is not a clinical trial.

## Approach

```
Dioscorides claim (Greek name + use)
      │  curated seed table with name- and reading-certainty flags
      ▼
GBIF Backbone Taxonomy ──► accepted name, family, match confidence, occurrences (global / Greece)
      ▼
PubMed E-utilities ──► records, clinical trials/RCTs, systematic reviews/meta-analyses
      │               + the taxon's total literature (specificity, against popularity bias)
      │               + 2 negative-control indications per taxon (background rate)
      ▼
Scoring ──► evidence tier 0–3 · lift over controls · certainty · translational-gap score
      ▼
Validation ──► paired Wilcoxon + sign-flip permutation vs controls · concordance with EMA/HMPC
      ▼
Interactive atlas (docs/index.html)
```

**Translational-gap score** = preclinical signal × (1 − clinical saturation) × certainty. It is high when a use was documented 2,000 years ago, has a real body of laboratory work behind it, and has almost no human trials. Those claims are where a clinical study is most justified. All formulas are in [`src/score.py`](src/score.py).

## Results

All numbers below come from `data/validation.json` and `data/results.csv` (PubMed counts retrieved 9 Nov 2026).

| Result | Value |
|---|---|
| Claims audited | 34 (33 therapeutic + 1 negative-control case, *Colchicum*) |
| Claims with at least one clinical trial | 17 / 34 |
| **Translational gaps** (≥ 20 papers, 0 trials) | 4: *Gentiana lutea* (digestive), *Punica granatum* (anthelmintic), *Nigella sativa* (headache), *Salvia officinalis* (wounds) |
| Translated via an isolated compound | 3 (opium → morphine; mandrake, henbane → scopolamine) |
| Claims more specific than their own negative controls | 21 / 33, median lift 1.7× |
| Paired Wilcoxon / sign-flip permutation (20,000 draws) | p = 0.011 / p = 0.015 |
| Same test without low-certainty identifications (n = 30) | p = 0.019 |
| Concordance with EMA/HMPC monograph indications | AUC = 0.82, Mann-Whitney p < 0.001 |

**Headline finding:** Dioscorides' gentian root "for the stomach" is 12× more specific than gentian's unrelated uses in PubMed, with 20 papers and **zero clinical trials**.

**Two unexpected insights**
1. *The taxonomy blind spot.* GBIF matched all 34 names with 99–100 % confidence, including disputed identifications (thymon, sideritis, silphion). Modern taxonomy cannot see historical identification error, so Rhizotomos records it explicitly as a certainty weight.
2. *The Papaver paradox.* *Papaver somniferum* + pain has 0 plant-level trials, although opioids are among the most successful plant-derived drugs. Evidence migrates into isolated compounds, so these claims are labelled "translated via compound" rather than counted as gaps.

Slides: [`slides/Rhizotomos_EthnoHack2026.pdf`](slides/Rhizotomos_EthnoHack2026.pdf) · Video: [`video/Rhizotomos_pitch.mp4`](video/Rhizotomos_pitch.mp4)

## Reproduce

```bash
pip install -r requirements.txt
python src/pipeline.py          # uses cached raw_*.json; add --refresh to re-query GBIF/PubMed live
python src/score.py             # scores, validation, docs/data.js
python src/figures.py           # figures for the slides
python src/make_deck.py         # 10-slide deck -> PDF + PNG (needs: playwright install chromium)
python video/make_video.py      # narrated pitch video (needs ffmpeg + Kokoro ONNX model files, voice am_fenrir)
python video/add_captions.py    # burn in captions
```

API results are cached in `data/raw_*.json`, so the analysis can be rerun offline exactly. Running `--refresh` gives today's PubMed counts, which grow over time.

## Repository layout

| Path | Content |
|---|---|
| `data/dioscorides_seed.csv` | 34 curated claims: Greek name, compound route, candidate binomial, paraphrased use, category, certainty flags, PubMed query, curator note |
| `data/raw_*.json` | Cached API responses (GBIF, PubMed, negative controls) |
| `data/results.csv` | Scored claims |
| `data/validation.json` | Statistical validation |
| `src/` | Pipeline, scoring, figures, deck generator |
| `docs/` | Static interactive atlas (GitHub Pages / Vercel) |
| `slides/` | Pitch deck (PDF) and figures |
| `video/` | Narrated pitch video and its generator (Kokoro TTS + ffmpeg) |

## Data sources and licences

| Source | Use | Licence / terms |
|---|---|---|
| Dioscorides, *De Materia Medica* | Claims paraphrased by the team (no translation text copied) | Original text public domain |
| [GBIF Backbone Taxonomy](https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c) and occurrence API | Name resolution, occurrence counts | CC BY 4.0, cite GBIF.org |
| [NCBI PubMed E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/) | Record counts only (no abstracts stored) | NCBI usage policy |
| EMA/HMPC herbal monographs | Binary overlap flag (`ema_hmpc_overlap`) used as an external reference | Public regulatory documents |

Code: MIT (see `LICENSE`).

## Assumptions, limitations, uncertainty

- **The seed table is a curated prototype, not a critical edition.** Uses are paraphrased and grouped into categories. Candidate identifications follow commonly proposed modern identifications. `name_certainty` and `claim_confidence` record doubt, and every row needs line-by-line verification against the Wellmann edition and a scholarly translation. We would welcome historians of medicine to do this.
- **Co-occurrence is not efficacy.** Tiers count whether trials exist, not whether they were positive or well run. A "Clinically explored" claim may have negative trials.
- **Query noise.** Binomials are matched in title/abstract only, so synonyms and older names are missed. Indication queries are hand-written and kept in the seed file for audit.
- **The HMPC flags were curated by the team** from monograph indications and should be checked against the current EMA documents.
- **GBIF occurrence counts measure sampling effort, not abundance or conservation status.** IUCN assessments are the next step.
- **Toxicity.** Several taxa (Mandragora, Hyoscyamus, Veratrum, Colchicum) are dangerous. No output here is medical advice or a treatment recommendation.

## Responsible use of traditional knowledge

*De Materia Medica* is a published, public-domain text, so this project does not take knowledge from living Indigenous communities. The method (claim → taxon → evidence → gap) could be applied to community knowledge, but that would need prior informed consent and benefit-sharing under the Nagoya Protocol. We deliberately did not build that without community partners.

## Future development

- Full-text extraction of all ~800 plant chapters with a Greek NLP model, aligned to the Wellmann chapter numbering.
- Diachronic name mapping through Byzantine, Arabic and Latin translations (e.g. the Vienna Dioscorides, Ibn al-Baytar).
- Trial-outcome extraction (ClinicalTrials.gov, Cochrane) to grade evidence direction, not just existence.
- Compound-aware queries (morphine, scopolamine, salicin) to close the Papaver paradox automatically.
- Linking taxa to compounds (LOTUS / Wikidata) for Track 2 screening, and to IUCN for conservation risk.

## Team

Arnav Joshi

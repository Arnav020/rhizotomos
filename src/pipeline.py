"""Rhizotomos pipeline: De Materia Medica claims -> resolved taxa -> modern evidence -> gap scores.

Steps
  1. Resolve each candidate binomial against the GBIF Backbone Taxonomy (match confidence,
     accepted name, family) and fetch occurrence counts (global and Greece).
  2. Query PubMed (NCBI E-utilities) for every (taxon, historical indication) pair:
     all records, clinical trials / RCTs, systematic reviews / meta-analyses, plus the
     taxon's total literature (for a specificity ratio that corrects popularity bias).
  3. Build a negative-control set: each taxon paired with 2 indications drawn from OTHER
     rows (fixed seed) to estimate the background co-occurrence rate.
  4. Write raw results to data/raw_*.json (cached, so reruns are offline and reproducible).

Run:  python src/pipeline.py            (uses cache when present)
      python src/pipeline.py --refresh  (re-queries the APIs)
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
GBIF = "https://api.gbif.org/v1"
HEADERS = {"User-Agent": "rhizotomos-ethnohack/1.0 (research prototype)"}
SEED = 42

CLINICAL = '("clinical trial"[pt] OR "randomized controlled trial"[pt])'
SYNTHESIS = '("meta-analysis"[pt] OR "systematic review"[pt])'


def pubmed_count(term: str, retries: int = 4) -> int:
    for attempt in range(retries):
        try:
            r = requests.get(EUTILS, params={"db": "pubmed", "term": term, "retmode": "json",
                                             "rettype": "count", "tool": "rhizotomos"},
                             headers=HEADERS, timeout=30)
            if r.status_code == 429:
                time.sleep(1.5 * (attempt + 1))
                continue
            r.raise_for_status()
            time.sleep(0.36)  # stay under 3 requests/s without an API key
            return int(r.json()["esearchresult"]["count"])
        except Exception as exc:  # noqa: BLE001
            print(f"  retry {attempt + 1} for {term[:60]}: {exc}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"PubMed query failed: {term}")


def taxon_clause(binomial: str) -> str:
    return f'"{binomial}"[tiab]'


def resolve_gbif(binomial: str) -> dict:
    m = requests.get(f"{GBIF}/species/match", params={"name": binomial, "kingdom": "Plantae"},
                     headers=HEADERS, timeout=30).json()
    key = m.get("acceptedUsageKey") or m.get("usageKey")
    out = {
        "gbif_key": key,
        "gbif_scientific_name": m.get("scientificName"),
        "gbif_status": m.get("status"),
        "gbif_match_type": m.get("matchType"),
        "gbif_confidence": m.get("confidence", 0),
        "family": m.get("family"),
    }
    if key:
        for label, extra in (("occ_global", {}), ("occ_greece", {"country": "GR"})):
            r = requests.get(f"{GBIF}/occurrence/search",
                             params={"taxonKey": key, "limit": 0, **extra},
                             headers=HEADERS, timeout=30).json()
            out[label] = r.get("count", 0)
    else:
        out["occ_global"] = out["occ_greece"] = 0
    return out


def main(refresh: bool) -> None:
    seed = pd.read_csv(DATA / "dioscorides_seed.csv")
    gbif_cache = DATA / "raw_gbif.json"
    pub_cache = DATA / "raw_pubmed.json"
    ctrl_cache = DATA / "raw_controls.json"

    if refresh or not gbif_cache.exists():
        print("[1/3] GBIF taxonomic resolution + occurrences")
        gbif = {}
        for b in seed["candidate_binomial"].unique():
            gbif[b] = resolve_gbif(b)
            print(f"  {b}: conf={gbif[b]['gbif_confidence']} occ={gbif[b]['occ_global']}")
        gbif_cache.write_text(json.dumps(gbif, indent=1))

    if refresh or not pub_cache.exists():
        print("[2/3] PubMed evidence for historical claims")
        pub = {}
        for _, row in seed.iterrows():
            t, ind = taxon_clause(row.candidate_binomial), row.pubmed_indication_query
            rec = {
                "taxon_total": pubmed_count(t),
                "pair_all": pubmed_count(f"{t} AND {ind}"),
                "pair_clinical": pubmed_count(f"{t} AND {ind} AND {CLINICAL}"),
                "pair_synthesis": pubmed_count(f"{t} AND {ind} AND {SYNTHESIS}"),
            }
            pub[row.id] = rec
            print(f"  {row.id} {row.candidate_binomial}: {rec}")
        pub_cache.write_text(json.dumps(pub, indent=1))

    if refresh or not ctrl_cache.exists():
        print("[3/3] Negative controls (taxon x indication from other rows)")
        rng = random.Random(SEED)
        ctrl = []
        for _, row in seed.iterrows():
            pool = seed[seed.indication_category != row.indication_category]
            for _, other in pool.sample(2, random_state=rng.randint(0, 10**6)).iterrows():
                t = taxon_clause(row.candidate_binomial)
                ctrl.append({"id": row.id, "control_from": other.id,
                             "control_category": other.indication_category,
                             "pair_all": pubmed_count(f"{t} AND {other.pubmed_indication_query}")})
        ctrl_cache.write_text(json.dumps(ctrl, indent=1))
    print("done.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    main(ap.parse_args().refresh)

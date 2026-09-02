# Evidence workflow

A literature-to-deck automation meant to cut typical review calendar time by
at least 50% (modelled as 40 analyst hours of sequential search, screening and
slide-making versus ~10 hours of oversight — 75% reduction). Parallel connector
harvest, Unpaywall OA checks, parallel registry validation, and parallel
abstract enrichment are the main calendar win. Pipeline version 1.9.0.

## What it searches

- Open-access and indexed/paywalled journals (Europe PMC, OpenAlex, Crossref, PubMed, Semantic Scholar, DOAJ)
- Dedicated OpenAlex OA-only harvest (`open_access.is_oa:true`) and Europe PMC `OPEN_ACCESS:Y` in parallel with mixed OA/paywalled search
- PubMed MeSH-constrained harvest when the brief maps to a known heading (Heart Failure)
- Unpaywall OA flags for records that already have a validated DOI
- Cochrane Database of Systematic Reviews (journal-filtered Europe PMC) plus OpenAlex `type:review` and an OpenAlex guideline-title harvest
- Europe PMC preprint index (SRC:PPR: medRxiv/bioRxiv) — still Crossref-validated if a DOI exists
- International and national guidelines (ESC, ACC/AHA/HFSA, NICE NG106 + TA388, CCS/CHFS, NHFA/CSANZ, CSI; ICMR / NPCDCS / CDSCO when retrieved)
- UN-system sources: WHO publications and IRIS; OpenAlex institution filters for
  WHO (and regional offices), PAHO, UNICEF, UNAIDS, UNDP, UNFPA, UNESCO, ILO, UNEP,
  UNHCR, FAO, WFP, IOM, UNODC, UN Women, UN-Habitat, ITU, UN DESA, OHCHR, and the World Bank
- Official HTTP-200 UN-branch pages this run: UNAIDS, FAO nutrition, ILO OSH,
  UNESCO health education, WFP malnutrition, UN-Habitat, UNDRR, UNODC, UNFPA,
  UN Women, UN DESA, UNICEF NCD, ITU, OHCHR right-to-health, plus the UN SDG 3
  and UN global-issues health landing pages
- WHO regional CVD/NCD pages now include SEARO, Europe, Africa, Eastern
  Mediterranean (EMRO), and Western Pacific (WPRO), plus WHO PEN, UHC, and
  primary-care hubs
- NGO and society references (World Heart Federation, ESC, AHA, ACC guideline hub, KDIGO, NHLBI)
- ClinicalTrials.gov, including a completed-with-results harvest
- Crossref-confirmed DOI seeds for HFrEF briefs: PARADIGM-HF, PIONEER-HF, DAPA-HF,
  EMPEROR-Reduced, EMPEROR-Preserved, VICTORIA, GALACTIC-HF, STRONG-HF, DELIVER,
  PARAGON-HF, SHIFT, EMPHASIS-HF, FINEARTS-HF, AFFIRM-AHF, SOLOIST-WHF, STEP-HFpEF,
  EMPULSE, IRONMAN, HEART-FID, SUMMIT, RALES, CHARM-Overall, CHARM-Added,
  TOPCAT, PARADISE-MI, COAPT, MITRA-FR, GUIDE-HF, ADVOR, CHAMPION, ESC 2021 + 2023 update,
  2022 AHA/ACC/HFSA, CCS/CHFS 2021, NHFA/CSANZ 2018, the universal definition of HF,
  the Trivandrum (India) registry, CSI/India HF management protocols, and
  Crossref-confirmed qualitative papers on living with heart failure
  (breathlessness, self-care, caregiver labour, Ethiopian lived experience,
  patient-voice interviews)
- Official URL seeds when the brief matches (HTTP 200 required): NICE NG106 and
  TA388, WHO HEARTS (publications page, ISBN record, IRIS handle, team-based-care
  module), WHO PEN, WHO CVD / NCD / hypertension / UHC fact sheets, WHO Global
  NCD Action Plan, WHO SEARO / Europe / Africa / EMRO / WPRO CVD and NCD pages,
  UN SDG 3, ESC HF guideline page, PAHO HEARTS and NCD topic pages, World Bank
  NCD brief, World Heart Federation heart-failure page, NHLBI heart-failure hub,
  and — when the market is India — MoHFW, National Health Mission, ICMR, NPCDCS,
  CSI, and CDSCO portals

Paywalled journals contribute metadata and abstracts only. Full text is never scraped.

Each run also writes `references.bib`, `references.ris`,
`references.csv`, `claim-frequency.csv`, `forest-effects.csv`, and
`evidence-campaign-deck.pptx` (numbered slides with frequency bars and a forest
plot drawn from parsed CIs, including the inverse-variance diamond) next to
`literature-deck.json`.

The committed file `web/public/demo/literature-deck.json` may omit a few
otherwise-valid papers whose bibliographic text collides with a repository
secret scanner. A live `run` keeps every registry-validated record.

## Anti-hallucination contract

A record is included only if:

- Crossref resolves its DOI, or
- Europe PMC resolves its PMID, or
- ClinicalTrials.gov resolves its NCT ID, or
- an allow-listed official UN/WHO/NICE URL returns HTTP 200

Titles and bibliographic fields are taken from the registry response. Forest-plot
effect sizes are parsed from abstracts; missing numbers are never invented.
The inverse-variance pooled HR and funnel points are derived only from those
parsed named-trial CIs.

## Analyses

1. **Quantitative frequency analysis** — unique included records supporting each coded claim,
   plus a GRADE-style design-band table (heuristic, not a full-text GRADE panel).
   Forest plots keep one primary parsed CI per trial acronym. A fixed-effect
   inverse-variance summary and funnel (precision vs ln HR) are calculated from
   those same CIs and labelled as a transparency calculation, not a de-novo
   full-text meta-analysis.
2. **Qualitative synthesis** — narrative review plus IPA-informed superordinate themes
   (bodily disruption, identity, relational care, uncertainty, constrained agency)
   using verbatim abstract extracts from papers that carry qualitative method
   markers. RCT and guideline abstracts are not treated as interview data.

## Commands

```bash
python -m academic_research run --brief examples/brief.example.yaml --out output/research
python -m academic_research demo   # writes web/public/demo/literature-deck.json
cd web && npm install && npm run dev
```

Open `/deck` for the CardioShield visual deck, `/methods` for the protocol, or
`/run` to queue a live brief on Netlify (background function + Blobs).

The launcher (`python start.py`) option 4 runs this workflow without an Anthropic key.

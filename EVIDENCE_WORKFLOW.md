# Evidence workflow

A literature-to-deck automation meant to cut typical review calendar time by
at least 50% (modelled as 40 analyst hours of sequential search, screening and
slide-making versus ~10 hours of oversight — 75% reduction). Parallel connector
harvest, parallel registry checks, and parallel abstract enrichment are the main
calendar win. Pipeline version 1.4.0.

## What it searches

- Open-access and indexed/paywalled journals (Europe PMC, OpenAlex, Crossref, PubMed)
- International and national guidelines (ESC, ACC/AHA/HFSA, NICE; ICMR when retrieved)
- UN-system sources: WHO publications and IRIS; OpenAlex institution filters for
  WHO (and regional offices), PAHO, UNICEF, UNAIDS, UNDP, UNFPA, UNESCO, ILO, UNEP,
  UNHCR, FAO, WFP, IOM, UNODC, UN Women, UN-Habitat, ITU, UN DESA, and the World Bank
- NGO and society references (World Heart Federation, ESC, AHA)
- ClinicalTrials.gov
- Crossref-confirmed DOI seeds for HFrEF briefs: PARADIGM-HF, PIONEER-HF, DAPA-HF,
  EMPEROR-Reduced, EMPEROR-Preserved, VICTORIA, GALACTIC-HF, STRONG-HF, ESC 2021 +
  2023 update, 2022 AHA/ACC/HFSA, the Trivandrum (India) registry, CSI/India HF
  management protocols, and Crossref-confirmed qualitative papers on living with
  heart failure (breathlessness, self-care, caregiver labour)
- Official URL seeds when the brief matches (HTTP 200 required): NICE NG106,
  WHO HEARTS, WHO CVD fact sheet, WHO Global NCD Action Plan, ESC HF guideline
  page, PAHO HEARTS in the Americas, World Heart Federation heart-failure page

Paywalled journals contribute metadata and abstracts only. Full text is never scraped.

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

## Analyses

1. **Quantitative frequency analysis** — unique included records supporting each coded claim.
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

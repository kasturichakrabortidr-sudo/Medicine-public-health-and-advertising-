# Example science-viz blocks (CardioShield / illustrative)

These blocks are the visual grammar the agent emits. They are **illustrative
scaffolds** from `brief.example.yaml`, not promotional claims. Run:

```bash
python -m medicomarketing_agent render-visuals --input examples/science-viz.example.md --out output/
```

```science-viz
{
  "id": "hfref-patient-impact",
  "type": "patient_impact",
  "title": "What the pivotal evidence represents for 100 similar patients",
  "subtitle": "Absolute translation of the composite endpoint — the bedside so-what, not the p-value",
  "source": "PARADIGM-HF style pivotal RCT cited in the example brief — illustrative pending full extraction",
  "mlr": "required",
  "of": 100,
  "horizon": "Over the trial follow-up, compared with an ACE inhibitor",
  "items": [
    {"label": "avoid a cardiovascular death or heart-failure hospitalisation", "value": 5, "tone": "positive"},
    {"label": "still experience the composite event — residual risk the campaign must not over-claim", "value": 22, "tone": "caution"}
  ]
}
```

```science-viz
{
  "id": "composite-effect-size",
  "type": "effect_size",
  "title": "Decision-critical endpoints versus the ACE-inhibitor comparator",
  "subtitle": "Relative effect the medical director will be asked to believe — ratios below 1 favour the brand",
  "source": "PARADIGM-HF style composite as described in the example brief — illustrative",
  "mlr": "required",
  "unit": "hazard ratio",
  "comparator": "enalapril-class ACE inhibitor",
  "items": [
    {"label": "CV death or HF hospitalisation", "value": 0.80, "ci": "0.73–0.87", "direction": "favours brand", "note": "illustrative"},
    {"label": "Cardiovascular death", "value": 0.80, "ci": "0.71–0.89", "direction": "favours brand", "note": "illustrative"}
  ]
}
```

```science-viz
{
  "id": "evidence-stream-mix",
  "type": "evidence_mix",
  "title": "Where the story currently lives",
  "subtitle": "How much of the argument is brand-generated versus independently owned versus still evolving",
  "source": "Example brief streams A–E — counts are a scaffold until Phase 3 extraction",
  "mlr": "not-promotional",
  "items": [
    {"label": "Brand-generated", "value": 3, "grade": "A"},
    {"label": "Independent published", "value": 2, "grade": "A/B"},
    {"label": "Evolving / emerging", "value": 2, "grade": "B"},
    {"label": "Guidelines", "value": 3, "grade": "A"},
    {"label": "Health-economic", "value": 1, "grade": "B pending"}
  ]
}
```

```science-viz
{
  "id": "early-initiation-alignment",
  "type": "comparison_matrix",
  "title": "Does every stream support early initiation?",
  "subtitle": "Alignment is the only safe promotional territory; clashes become education or silence",
  "source": "Example brief: ESC / ACC-AHA-HFSA / CSI plus evolving in-hospital initiation data",
  "mlr": "required",
  "columns": ["Brand", "Independent", "Evolving", "Guidelines"],
  "rows": [
    {"question": "Early initiation after stability", "cells": ["supportive", "supportive", "supportive", "supportive"]},
    {"question": "Indian-patient tolerability", "cells": ["supportive", "silent", "neutral", "silent"]},
    {"question": "Cost / readmission offset", "cells": ["neutral", "silent", "supportive", "silent"]}
  ]
}
```

```science-viz
{
  "id": "science-to-solution-cascade",
  "type": "cascade",
  "title": "Science to solution through strategy execution",
  "subtitle": "Each row is a contract: the picture, the practice change, the field move, the proof",
  "source": "Phases 4, 6, 7 of the example pipeline — illustrative cascade",
  "mlr": "not-promotional",
  "steps": ["Science", "Implication", "Solution", "Execution", "Metric"],
  "rows": [
    {
      "id": "C1",
      "cells": [
        "Composite benefit vs ACEI (patient-impact visual)",
        "Delaying ARNI leaves preventable events on the table",
        "Initiate foundational ARNI once haemodynamically stable — not after a long ACEI chapter",
        "Launch ward-to-clinic initiation protocol + KOL case reviews",
        "Share of new HFrEF starts on ARNI within 30 days of index visit"
      ]
    },
    {
      "id": "C2",
      "cells": [
        "Guideline Class I / four-pillar alignment",
        "Peers already have cover; the habit is the barrier",
        "Replace 'stabilise first on ACEI' with 'stabilise on the indicated pillar'",
        "Peer-to-peer 'stabilise first' myth-bust using the discordance visual",
        "% of target HCPs who self-report first-line (not late) ARNI use"
      ]
    },
    {
      "id": "C3",
      "cells": [
        "Cost 8–10x generic ARB; PAP under-used",
        "Tier-2 physicians are not refusing the science — they are refusing the bill",
        "Make the health-economic and affordability path as visible as the HR",
        "Rep + PAP walkthrough for high cost-concern segments (UCPMP-safe)",
        "PAP enrolment per 100 eligible starts; 90-day persistency"
      ]
    }
  ]
}
```

```science-viz
{
  "id": "lead-callout-rrr",
  "type": "callout_stat",
  "title": "The number the campaign will be asked to stand behind",
  "subtitle": "A relative risk reduction is not a promise to an individual patient",
  "source": "Illustrative 20% RRR on the composite — pending locked CSR extraction",
  "mlr": "required",
  "stat": "20%",
  "unit": "relative reduction in CV death or HF hospitalisation vs ACE inhibitor",
  "meaning": "What it represents: fewer composite events in a treated population — not a cure, and not a substitute for the other pillars."
}
```

```science-viz
{
  "id": "adoption-funnel",
  "type": "funnel",
  "title": "How execution will be proven",
  "subtitle": "The cascade closes when an aware cardiologist becomes a repeating, advocating initiator",
  "source": "Phase 12 measurement scaffold — targets are planning figures, not forecasts",
  "mlr": "not-promotional",
  "items": [
    {"label": "Aware of early-initiation position", "value": 100},
    {"label": "Engaged with a named visual", "value": 55},
    {"label": "Trialled in eligible HFrEF", "value": 28},
    {"label": "Repeating at 90 days", "value": 16},
    {"label": "Advocating to peers", "value": 6}
  ]
}
```

```science-viz
{
  "id": "key-driver-map",
  "type": "driver_map",
  "title": "The levers the cascade must pull",
  "subtitle": "Science changes minds only when it hits a named COM-B barrier",
  "source": "Example brief HCP insights — advisory board, field notes, survey",
  "mlr": "not-promotional",
  "items": [
    {"driver": "Confidence to initiate once stable, not after a long ACEI chapter", "lever": "Motivation + Capability", "barrier": "'Stabilise first' habit"},
    {"driver": "Visible local tolerability", "lever": "Capability", "barrier": "KOLs waiting for Indian RWE before public advocacy"},
    {"driver": "A workable answer to monthly cost", "lever": "Opportunity", "barrier": "8–10x generic ARB; PAP unused"}
  ]
}
```

```science-viz
{
  "id": "execution-timeline",
  "type": "timeline",
  "title": "When each cascade row enters the field",
  "subtitle": "Execution is sequenced, not a launch-day dump of every visual",
  "source": "Phase 10 journey scaffold",
  "mlr": "not-promotional",
  "items": [
    {"stage": "Pre-launch", "objective": "KOL lock the position", "cascade_ids": ["C1", "C2"]},
    {"stage": "Launch", "objective": "Put the patient-impact visual in the room", "cascade_ids": ["C1"]},
    {"stage": "Adoption", "objective": "Cost path + first starts", "cascade_ids": ["C3"]},
    {"stage": "Reinforce", "objective": "90-day persistency + peer proof", "cascade_ids": ["C1", "C2"]},
    {"stage": "Beyond", "objective": "Local RWE feedback loop", "cascade_ids": ["C2"]}
  ]
}
```

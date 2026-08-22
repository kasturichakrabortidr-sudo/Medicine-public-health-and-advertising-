"""Phase definitions for the medicomarketing strategy pipeline.

Each phase encodes one step of the working process, in order. The pipeline
runs them sequentially as a single growing conversation, so every phase can
see and build on the output of all the phases before it.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Phase:
    id: str
    title: str
    prompt: str


SYSTEM_PROMPT = """\
You are a senior medicomarketing strategy director working inside a healthcare
communications agency. You build evidence-led, ethically sound marketing
strategies for pharmaceutical brands, medical products, and health services,
always targeted at healthcare professionals (HCPs).

Operating principles you must follow in every output:

1. Evidence first. Every strategic claim must be traceable to a piece of
   evidence (trial, real-world study, guideline, HCP insight) named in the
   working context. When evidence is missing, say so explicitly and record it
   as an evidence gap rather than inventing data. Never fabricate trial names,
   effect sizes, citations, or guideline recommendations.
2. Scientific rigour. Distinguish clearly between: brand-generated evidence,
   independent published evidence, evolving/emerging evidence, and guideline
   positions. Grade the strength of evidence when you compare sources.
3. Compliance awareness. All recommendations must be compatible with
   pharmaceutical promotion codes (e.g. local equivalents of ABPI/UCPMP/PhRMA
   codes). Flag any claim or tactic that would need medical-legal-regulatory
   (MLR) review before use. Never propose off-label promotion, inducements to
   prescribe, or disguised promotion.
4. HCP respect. Doctors change behaviour on the basis of evidence, peer
   influence, patient benefit, and practical feasibility — not pressure.
   Frame every tactic around genuine clinical value.
5. Client-ready output. Write in clean Markdown with clear headings, and use
   tables wherever the content is comparative or enumerable. Each phase output
   must stand alone as a client-facing document section while staying
   consistent with the phases before it.
6. Show your working process. Begin each phase output with a short
   "How this section was built" note (2-4 sentences) describing the reasoning
   steps taken, so the client can audit the process.
7. Visual evidence translation. Do not leave scientific findings trapped in
   prose or tables. Translate them into decision-useful visuals that show what
   the data means clinically, not merely what the numbers are. Chart only
   supplied or retrieved values, retain the stated population, comparator,
   endpoint, timepoint, denominator, and uncertainty, and never turn a
   qualitative grade into a made-up number. When comparable quantitative data
   are unavailable, draw an evidence-state or causal diagram and label the
   missing data rather than simulating a quantitative chart.
8. Science-to-execution traceability. Preserve one explicit chain through the
   strategy:
   EV-### evidence -> CM-### clinical meaning -> HI-### HCP insight or
   BD-### behavioural driver -> SC-### strategic choice -> SOL-### solution or
   message -> EX-### execution -> KPI-### measure.
   Assign these stable IDs when each item is first created and cite upstream
   IDs in every downstream recommendation. A proposal without adequate
   evidence must point to a GAP-### item and be labelled
   "HYPOTHESIS — REQUIRES VALIDATION"; never disguise a gap as scientific
   support.
"""


VISUAL_OUTPUT_CONTRACT = """\
## Required visual synthesis

Include a section headed **Visual synthesis** containing the phase-specific
visual requested below.

- Write the visual as a valid Mermaid fenced block. Prefer `flowchart` for
  pathways, causal systems, journeys, and infographics. Use `xychart-beta`
  only when the underlying numeric values are comparable and share a meaningful
  scale. Keep the exact-value table beside a quantitative chart.
- Make evidence status visible: supported, mixed, unsupported, or evidence
  gap. Do not use visual size, colour, or position to imply an effect or ranking
  that the source data does not support.
- Immediately below every visual add an accessible text caption with exactly
  these labels: **What it shows**, **So what**, **Evidence anchors**, and
  **Decision enabled**. Evidence anchors must cite the relevant stable IDs.
- Keep node labels concise and put detailed claims, values, caveats, and source
  information in the surrounding text or table. The diagram is a synthesis,
  not a substitute for evidence disclosure.

Phase-specific visual:
{visual_brief}
"""


PHASE_VISUAL_BRIEFS: dict[str, str] = {
    "01-critical-thinking": (
        "Draw a causal problem map from the clinical/patient problem through "
        "the HCP decision and current behaviour to the business consequence. "
        "Show assumptions and unknowns as visibly separate branches."
    ),
    "02-scientific-criteria": (
        "Draw the research-and-appraisal funnel from each PICO(S) question to "
        "search, screening, quality appraisal, extraction, synthesis, and the "
        "specific strategic decision that the evidence will inform."
    ),
    "03-evidence-forefront": (
        "Create an evidence dashboard with (1) a quantitative clinical-outcome "
        "chart when comparable numeric data exist, otherwise an explicit "
        "data-gap panel; (2) an evidence-strength landscape by stream; and "
        "(3) an EV-### -> CM-### bridge that states what each major result "
        "means for patients and clinical practice. Multiple Mermaid blocks are "
        "expected when one chart cannot represent these honestly."
    ),
    "04-hcp-insights": (
        "Draw an evidence-versus-perception map showing concordance, "
        "discordance, and silent zones. Connect every HCP belief to its EV-### "
        "or GAP-### anchor and show the resulting opportunity or risk."
    ),
    "05-behavioural-drivers": (
        "Draw a COM-B causal system map linking evidence and HCP insights to "
        "capability, opportunity, and motivation barriers, then to the target "
        "behaviour. Label the highest-leverage BD-### nodes."
    ),
    "06-evidence-position": (
        "Draw the defensible claim-territory map. Show where brand, independent, "
        "evolving, and guideline evidence align, conflict, or remain silent, "
        "and connect each territory to an SC-### strategic choice."
    ),
    "07-core-messaging": (
        "Draw the science-to-solution blueprint: EV-### -> CM-### -> HI-###/"
        "BD-### -> SC-### -> SOL-###. Every proposed solution or message must "
        "have an unbroken upstream path or a clearly labelled GAP-### path."
    ),
    "08-hcp-engagement": (
        "Draw the HCP journey from pre-launch through beyond-campaign. Put the "
        "SOL-### used, EX-### touchpoint, intended behaviour shift, feedback "
        "loop, and exit criterion at each stage."
    ),
    "09-activation-ideas": (
        "Draw the prioritised execution portfolio by segment. Connect each "
        "EX-### activation to its SOL-###, BD-###, target segment, expected "
        "effect, and the Q1 or Q2-Q4 deployment window."
    ),
    "10-measurement": (
        "Draw the causal measurement tree from EX-### delivery through leading "
        "behaviour indicators to adoption, clinical/social outcomes, and "
        "quarterly business outcomes. Label each measure KPI-### and show "
        "where attribution is direct, contributory, or unknown."
    ),
    "11-executive-summary": (
        "Produce a one-page executive infographic with selected, decision-"
        "critical paths across the full EV-### -> CM-### -> HI-###/BD-### -> "
        "SC-### -> SOL-### -> EX-### -> KPI-### chain. Include no orphan "
        "tactics and retain major GAP-### and MLR gates."
    ),
}


def build_phase_prompt(phase: Phase) -> str:
    """Combine a phase instruction with its mandatory visual output contract."""
    try:
        visual_brief = PHASE_VISUAL_BRIEFS[phase.id]
    except KeyError as exc:  # fail closed if a new phase omits visual synthesis
        raise ValueError(f"Phase {phase.id!r} has no visual brief") from exc
    return f"{phase.prompt}\n\n{VISUAL_OUTPUT_CONTRACT.format(visual_brief=visual_brief)}"


PHASES: list[Phase] = [
    Phase(
        id="01-critical-thinking",
        title="Strategic Framing & Insightful Critical Thinking",
        prompt="""\
Phase 1 — Insightful critical thinking on the brief.

Deconstruct the client brief before any research is planned. Produce:

1. **Restated challenge** — the real commercial and clinical problem in one
   paragraph, separating what the client asked for from what the brand needs.
2. **First-principles questions** — the 8-12 questions that must be answered
   for this strategy to succeed (clinical, behavioural, market, access).
3. **Assumptions register** — a table of assumptions hidden in the brief:
   assumption | why it matters | risk if wrong | how we will test it.
4. **Known / unknown map** — what we know with evidence, what we believe
   without evidence, what we don't know at all.
5. **Working hypotheses** — 3-5 falsifiable hypotheses about why target HCPs
   do or do not currently adopt the product/recommendation. Assign each a
   HYP-### ID and link it to the research it will need. Assign GAP-### IDs to
   material unknowns so later recommendations cannot mistake them for facts.

This phase sets the intellectual frame every later phase must answer to.""",
    ),
    Phase(
        id="02-scientific-criteria",
        title="Medical & Scientific Criteria for the Research Process",
        prompt="""\
Phase 2 — Define the medical and scientific criteria that will govern the
research process, with explicit sub-steps.

Produce:

1. **Research questions in PICO(S) format** — for each working hypothesis from
   Phase 1, a structured question: Population | Intervention | Comparator |
   Outcomes | Setting. Assign each question an RQ-### ID and cite the HYP-###
   or GAP-### item it resolves.
2. **Evidence inclusion / exclusion criteria** — study designs accepted,
   minimum quality thresholds, date limits, populations, endpoints that count
   (clinical, patient-reported, health-economic, safety).
3. **Evidence hierarchy** — the grading scheme to be applied (e.g. systematic
   reviews/meta-analyses > RCTs > large cohort/RWE > case series > expert
   opinion), and how brand-generated vs independent evidence will be weighted.
4. **Research process sub-steps** — a numbered, executable plan: sources to
   search (databases, congress abstracts, guideline bodies, registries, RWE
   sources), search strings/concepts, screening steps, extraction fields,
   quality-appraisal step, and synthesis step. Present as a table:
   sub-step | purpose | source/tool | output artefact | owner.
5. **Guideline scope** — which national and international guidelines are in
   scope and why.
6. **Safety and pharmacovigilance criteria** — what safety evidence must be
   captured alongside efficacy.

These criteria are the contract the evidence phase must honour.""",
    ),
    Phase(
        id="03-evidence-forefront",
        title="Evidence Analysis, Collation & the Client Forefront Table",
        prompt="""\
Phase 3 — Analyse and collate the relevant evidence in parallel stacked
streams, then build the Evidence Forefront Table for the client.

Work stream by stream, in parallel structure (same extraction fields for
each so they stack cleanly):

- Stream A: Brand-generated evidence (pivotal trials, brand RWE, post-hoc).
- Stream B: Independent existing published evidence.
- Stream C: Evolving / emerging new evidence (recent publications, congress
  data, ongoing trials of note).
- Stream D: Guidelines and consensus statements.
- Stream E: Health-economic and access evidence (cost, budget impact, QoL).

For each stream: summarise what exists (from the brief and working context),
apply the Phase 2 criteria, grade the evidence, and note gaps. Assign every
evidence item an EV-### ID. For each decision-relevant result, create a
CM-### "clinical meaning" statement that explains the implication for the
defined patient, comparator, endpoint, timepoint, and practice decision without
overstating causality. If the brief does not supply enough detail for a stream,
list precisely what the research team must retrieve, using the Phase 2 search
plan, and retain or create a GAP-### ID.

Then produce the **EVIDENCE FOREFRONT TABLE** — the single client-facing
table that stacks all streams side by side. Columns:

| ID | Evidence item | Stream | Design & N | Key finding (with effect size where known) | Clinical meaning ID | Evidence grade | Relevance to strategy | Message potential | Gap / caveat / MLR flag |

Close with: (a) the 5 strongest evidence-backed strategic assets, and
(b) the 5 most important evidence gaps with a recommendation for each.""",
    ),
    Phase(
        id="04-hcp-insights",
        title="In-House HCP Insight Analysis vs. the Evidence",
        prompt="""\
Phase 4 — Analyse the insights gathered from our in-house HCPs and compare
them against what the evidence shows.

Using the HCP insights supplied in the brief (advisory boards, field notes,
interviews, surveys — whatever is provided; if thin, infer carefully-labelled
provisional insights typical for this specialty and flag them for validation):

1. **Insight inventory** — table: HI-### ID | insight | source (who/where) |
   strength of signal (how many HCPs, how consistent) | theme | EV-### or
   GAP-### anchor.
2. **Concordance map** — where HCP beliefs AGREE with the evidence forefront
   table: these are amplification opportunities.
3. **Discordance map** — where HCP beliefs CONTRADICT or lag the evidence:
   perception gaps. For each: the belief | what the evidence actually shows |
   likely origin of the gap (old data, competitor messaging, habit, access
   experience) | strategic implication.
4. **Silent zones** — evidence the HCPs never mention (unexploited assets) and
   HCP concerns the evidence never answers (evidence gaps to escalate).
5. **Validation plan** — which provisional insights need confirming, with whom,
   and by what method, before major spend is committed.""",
    ),
    Phase(
        id="05-behavioural-drivers",
        title="HCP Behaviours, Concerns, Motivations & Key Behavioural Drivers",
        prompt="""\
Phase 5 — List and analyse the main behaviours, concerns, motivations, and
key behavioural drivers that determine whether target doctors adopt the
product or recommendation-related change.

Structure the analysis with a recognised behavioural framework (COM-B:
Capability, Opportunity, Motivation → Behaviour) and produce:

1. **Current behaviour baseline** — what target HCPs actually do today in the
   relevant clinical decision moment (diagnosis, initiation, switch,
   adherence support), by segment where behaviour differs.
2. **Behaviours table** — behaviour we need | current behaviour | the change
   required | size of the leap (small habit tweak vs. major practice change).
3. **Concerns register** — clinical concerns (efficacy, safety, interactions),
   practical concerns (workflow, monitoring burden, referral pathways),
   economic concerns (patient cost, reimbursement, hospital budget),
   professional concerns (guideline cover, peer opinion, medico-legal).
4. **Motivations map** — what genuinely moves these doctors: better patient
   outcomes, confidence/certainty, peer recognition, efficiency, scientific
   curiosity, patient demand. Rank by segment.
5. **KEY BEHAVIOURAL DRIVERS** — the 4-6 levers with the highest leverage.
   Assign each a BD-### ID and state: driver | EV-###/CM-###/HI-### evidence
   it rests on | barrier it overcomes | how the campaign will pull it. These
   drivers must be traceable to Phases 3 and 4.""",
    ),
    Phase(
        id="06-evidence-position",
        title="Comparative Evidence Position: Brand vs. Existing vs. Evolving vs. Guidelines",
        prompt="""\
Phase 6 — Compare the evidence we hold on the brand/product/service against
the existing evidence base within the brand, the evolving new evidence, and
the supporting guidelines — and convert that comparison into a strategic
evidence position.

Produce:

1. **Four-way comparison table** — for each key clinical question / claim
   territory: what brand evidence says | what the established independent
   evidence says | what the newest/evolving evidence says | what guidelines
   currently say. Mark each cell as supportive / neutral / unsupportive /
   silent.
2. **Alignment analysis** — where all four columns align (safe, powerful
   message territory); where brand evidence leads guidelines (education
   opportunity, handle with MLR care); where guidelines lead brand evidence
   (vulnerability); where evolving evidence may shift the picture within the
   campaign window (watch-list with trigger events).
3. **Competitive shadow** — how the comparator/standard-of-care evidence sits
   against ours in the same table logic.
4. **Strategic evidence position statement** — one tight paragraph stating
   the defensible scientific ground the campaign will stand on.
5. **Strategic choices** — assign SC-### IDs to the choices this evidence
   supports. For each: EV-###/CM-### basis | opportunity or problem selected |
   what the strategy will do | what it will deliberately not claim or do.
6. **Evidence roadmap** — data generation or publication moves (RWE, ISS,
   post-hoc, congress presence) that would strengthen the position during and
   after the campaign.""",
    ),
    Phase(
        id="07-core-messaging",
        title="Core Messaging Theme, Key Drivers & Behaviour-Change Adaptation",
        prompt="""\
Phase 7 — Build the core messaging platform and define the behavioural change
adaptation required to successfully launch and sustain the campaign.

Produce:

1. **Core messaging theme** — the single organising idea of the campaign,
   in one sentence, grounded in the strategic evidence position (Phase 6) and
   the key behavioural drivers (Phase 5). Give 2 alternative framings and
   recommend one, with rationale. Assign a SOL-### ID to each candidate.
2. **Message house** — table: SOL-### | pillar | core message | supporting
   EV-###/CM-### evidence | SC-### strategic choice | BD-### driver it pulls |
   proof points | MLR risk level.
3. **Segment adaptations** — how the same message house flexes for each HCP
   segment identified earlier (wording, lead evidence, channel emphasis).
4. **Objection-handling grid** — top concerns from Phase 5 | response |
   evidence anchor | what NOT to say (compliance boundary).
5. **Behaviour-change adaptation plan** — what has to change and hold:
   launch phase (breaking the old habit: triggers, education, trial
   experiences) vs. sustain phase (embedding the new habit: reinforcement,
   feedback loops, peer norms, system prompts in workflow). Map each element
   to the COM-B lever it works on.""",
    ),
    Phase(
        id="08-hcp-engagement",
        title="HCP Engagement Plan: Campaign Start to End and Beyond",
        prompt="""\
Phase 8 — Design how we engage HCPs from the beginning of the campaign to its
end — and beyond it.

Produce a staged engagement journey:

1. **Stage map** — table across the arc: Pre-launch (KOL & steering) →
   Launch (awareness & credibility) → Adoption (first prescriptions / first
   recommendations) → Reinforcement (habit & advocacy) → Beyond campaign
   (community, data feedback, lifecycle). For each stage: objective | target
   segments | EX-### activities | SOL-### and EV-###/CM-### used | channels |
   who leads (medical vs. commercial) | stage exit criteria.
2. **Touchpoint choreography** — the sequence and cadence of contacts a
   single HCP experiences (rep visits, med-ed events, digital, peer-to-peer,
   congress), with rules to avoid fatigue.
3. **KOL and peer-influence plan** — identification criteria, roles
   (steering, speaking, authorship within compliance), and how peer proof is
   cascaded to the wider base.
4. **Two-way engagement** — how HCP feedback, objections, and real-world
   experience flow back into the campaign (advisory loops, insight capture at
   every touchpoint) and trigger adaptations.
5. **Beyond-the-campaign plan** — what stays alive after the funded period:
   communities, registries/data collaborations, education platforms, and the
   handover into the next cycle's strategy.""",
    ),
    Phase(
        id="09-activation-ideas",
        title="Activation Ideas by Specialty, Status, City, Patient Mix & Cost Sensitivity",
        prompt="""\
Phase 9 — Generate activation idea options tailored to the HCP target's
specialty, professional status, city/geography tier, the type of patients they
encounter, and their sensitivity to treatment cost.

Produce:

1. **Segmentation grid** — build the practical activation segments by
   crossing: specialty (as per the brief) x status (KOL / senior consultant /
   early-career / GP-referrer as relevant) x city tier (metro / tier-2 /
   tier-3-rural or the local equivalent) x dominant patient profile (payer
   mix, disease severity mix) x cost-of-treatment concern (low / medium /
   high).
   Collapse to the 6-10 segments that actually matter commercially.
2. **Activation menu per segment** — for each retained segment, 3-5 concrete
   activation ideas. Assign each an EX-### ID. For every idea: what it is
   (2-3 sentences) | SOL-### and EV-###/CM-### it carries | channel & format |
   why it fits THIS segment (tie explicitly to specialty, status, city,
   patient type, cost concern) | effort/cost level (L/M/H) | expected effect
   on BD-### | compliance note.
3. **Cost-concern adaptations** — specific mechanics for high cost-concern
   segments: patient-affordability communication (within code), health-economic
   evidence use, payer/formulary engagement, generics/biosimilar defence if
   relevant.
4. **Prioritisation matrix** — impact vs. feasibility plot (as a table) across
   all ideas, and the recommended activation mix for quarter 1 vs. quarters
   2-4.""",
    ),
    Phase(
        id="10-measurement",
        title="Measurement Framework: Engagement, Uptake, Revenue & Popularity",
        prompt="""\
Phase 10 — Provide the measurable metric tools to assess continuous HCP
engagement and uptake of the campaign, in terms of quarterly revenue growth
and the clinical and social popularity of the campaign.

Produce:

1. **KPI tree** — from business goal down: quarterly revenue growth →
   prescription/recommendation volume & share → HCP adoption funnel
   (aware → engaged → trialling → repeating → advocating) → engagement
   activity metrics. Show the causal chain so every metric has a parent.
2. **Metric definition table** — assign every measure a KPI-### ID and state:
   metric | exact definition & formula | EX-###/BD-###/SC-### parent |
   data source (sales data, CRM, med-ed platform, social listening, market
   research waves) | baseline | quarterly target Q1-Q4 | owner | review cadence.
3. **Continuous HCP engagement metrics** — reach, frequency, depth (time,
   interaction quality), rep call quality, event attendance & repeat
   attendance, digital engagement (open/CTR/dwell), advisory participation,
   share-of-voice with target HCPs.
4. **Clinical popularity metrics** — guideline citations, congress mentions,
   publication momentum, KOL sentiment, inclusion in local protocols and
   formularies, peer-to-peer recommendation rates from market research.
5. **Social popularity metrics** — HCP social channels (medical Twitter/X,
   LinkedIn, physician communities), sentiment and advocacy tracking,
   patient-community spillover where compliant to monitor.
6. **Revenue linkage model** — how engagement metrics will be correlated to
   quarterly revenue (test-control geographies, pre-post cohorts, marketing
   mix logic), with honest notes on attribution limits.
7. **Dashboard & governance** — the quarterly review pack: leading vs lagging
   indicators, thresholds that trigger course-correction, and who decides.""",
    ),
    Phase(
        id="11-executive-summary",
        title="Executive Strategy Summary",
        prompt="""\
Phase 11 — Compile the executive strategy summary.

Condense the entire pipeline into a client-ready executive document
(2-3 pages equivalent):

1. The challenge and the insight (Phases 1, 4, 5).
2. The evidence position in one table (Phases 3, 6), retaining EV-###,
   CM-###, and SC-### identifiers.
3. The core theme and message house top line (Phase 7).
4. The engagement and activation plan on one page (Phases 8, 9).
5. The measurement commitments and quarterly targets (Phase 10).
6. Risks, dependencies, and MLR items to clear before launch.
7. **Science-to-solution execution spine** — one traceability table with:
   EV-### | CM-### | HI-###/BD-### | SC-### | SOL-### | EX-### | KPI-### |
   owner | next decision. Include all priority executions; any broken link is
   a GAP-### and a pre-launch decision gate.
8. Immediate next steps: the first 30 days.

Write it so a client CEO and a medical director both sign off on it.""",
    ),
]


EXPAND_PROMPT = """\
You are developing detail for one point of a medicomarketing strategy outline
supplied by the strategy lead.

For the outline point below, produce a fully developed section:

- Restate the point as a clear objective.
- Develop it in depth using the same operating principles (evidence-first,
  compliance-aware, HCP-respectful, client-ready Markdown, tables for
  comparative content).
- Where it touches research, define criteria and sub-steps.
- Where it touches evidence, distinguish brand / independent / evolving /
  guideline sources and flag gaps rather than inventing data.
- Where it touches behaviour, name the behavioural drivers explicitly.
- Where it touches execution, segment by specialty, status, geography,
  patient mix, and cost sensitivity as relevant.
- Where it touches measurement, give metric definitions, sources, and targets.
- Assign and preserve the applicable traceability IDs: EV-### evidence,
  CM-### clinical meaning, HI-### HCP insight, BD-### behavioural driver,
  SC-### strategic choice, SOL-### solution, EX-### execution, and KPI-###
  measure. If an upstream link is missing, use GAP-### and label the proposal
  "HYPOTHESIS — REQUIRES VALIDATION".
- Include a **Visual synthesis** section with a valid Mermaid flowchart that
  connects the scientific basis to the proposed solution and its execution.
  Below it, add an accessible caption labelled **What it shows**, **So what**,
  **Evidence anchors**, and **Decision enabled**. Never invent numeric chart
  values; use an explicitly labelled evidence-gap node when data are absent.
- Include a traceability table with the applicable columns from:
  EV-### | CM-### | HI-###/BD-### | SC-### | SOL-### | EX-### | KPI-###.
- End with: dependencies on other outline points, open questions for the
  strategy lead, and MLR/compliance flags.

OUTLINE POINT TO DEVELOP:
{point}
"""

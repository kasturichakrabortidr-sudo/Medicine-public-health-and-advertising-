"""Phase definitions for the medicomarketing strategy pipeline.

Each phase encodes one step of the working process, in order. The pipeline
runs them sequentially as a single growing conversation, so every phase can
see and build on the output of all the phases before it.
"""

from dataclasses import dataclass

from .visuals import VISUAL_GRAMMAR


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
7. Visualise what the science represents. Tables collate data; they do not
   show meaning. Whenever you present a scientific finding, endpoint, evidence
   mix, perception gap, behavioural driver, or KPI, also emit a graphical
   representation (a `science-viz` infographic and, where a process is being
   described, a Mermaid diagram). Every visual must state the source, the
   plain-language "so what", and an MLR flag. Never invent numbers.
8. Connect science to the solution through execution. Do not leave evidence
   as a research appendix. Every material finding must travel a named
   cascade row: scientific finding → clinical implication → the solution it
   implies → the execution move that delivers it → the metric that proves it.
   Later phases must cite those cascade IDs (C1, C2, …). A tactic with no
   cascade parent is incomplete.

""" + VISUAL_GRAMMAR


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
   do or do not currently adopt the product/recommendation, each linked to the
   research it will need.

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
   Outcomes | Setting.
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
apply the Phase 2 criteria, grade the evidence, and note gaps. If the brief
does not supply enough detail for a stream, list precisely what the research
team must retrieve, using the Phase 2 search plan.

Then produce the **EVIDENCE FOREFRONT TABLE** — the single client-facing
table that stacks all streams side by side. Columns:

| Evidence item | Stream | Design & N | Key finding (with effect size where known) | Evidence grade | Relevance to strategy | Message potential | Gap / caveat / MLR flag |

Close with: (a) the 5 strongest evidence-backed strategic assets, and
(b) the 5 most important evidence gaps with a recommendation for each.

Then draw the data, do not only tabulate it. Emit at least:
- one `evidence_mix` science-viz of the five streams (counts + grades)
- one `effect_size` science-viz for every endpoint whose effect size is known
- one `patient_impact` science-viz translating the strongest finding into
  "out of 100 patients like yours" language
- one `callout_stat` for the single number a medical director must remember
If a number is missing, render the visual with a pending-retrieval placeholder
rather than skipping the graphic.""",
    ),
    Phase(
        id="04-science-infographics",
        title="Scientific Data Visualization: What the Evidence Represents",
        prompt="""\
Phase 4 — Draw what the scientific data represents.

Phase 3 collated evidence. This phase is the visual translation: every
material finding becomes an infographic that a medical director can read
in seconds and that a brand team can carry into execution. Tables may
support the pictures; they must not replace them.

Produce:

1. **Visual thesis** — one paragraph: what the body of evidence *means*
   clinically, in language a treating physician would recognise. Not a
   recitation of study names.
2. **Infographic set** — emit at least five `science-viz` blocks that
   together tell the scientific story:
   - `patient_impact`: the lead endpoint as "out of N patients"
   - `effect_size`: brand vs comparator on the decision-critical endpoints
   - `evidence_mix`: how much of the story is brand-generated vs independent
     vs evolving vs guideline
   - `comparison_matrix` or a second `effect_size`: where streams agree / clash
   - `callout_stat`: the one figure the campaign will be remembered for
   Each visual's `subtitle` must state what the figure represents (the so-what),
   not the method. Each must carry `source` and `mlr`.
3. **Meaning captions** — under each visual (in prose, 3-5 lines): the
   bedside implication, the HCP belief it confirms or contradicts, and the
   solution-space it opens. Flag any caption that would need MLR before use
   with HCPs.
4. **Un-drawable gaps** — a table of findings that cannot yet be visualised
   because a number is missing: finding | missing datum | retrieval task
   from the Phase 2 plan | risk of designing execution without it.
5. **Handoff to strategy** — the 3-5 visualised findings that *must* become
   cascade rows in the science-to-solution-to-execution phase. Give each a
   proposed ID (C1, C2, …).

Mermaid is welcome for process (e.g. how an endpoint maps to a clinical
decision), but the data itself must be `science-viz` infographics, not a
flowchart of adjectives.""",
    ),
    Phase(
        id="05-hcp-insights",
        title="In-House HCP Insight Analysis vs. the Evidence",
        prompt="""\
Phase 5 — Analyse the insights gathered from our in-house HCPs and compare
them against what the evidence shows (including the Phase 4 visuals).

Using the HCP insights supplied in the brief (advisory boards, field notes,
interviews, surveys — whatever is provided; if thin, infer carefully-labelled
provisional insights typical for this specialty and flag them for validation):

1. **Insight inventory** — table: insight | source (who/where) | strength of
   signal (how many HCPs, how consistent) | theme.
2. **Concordance map** — where HCP beliefs AGREE with the evidence forefront
   table: these are amplification opportunities.
3. **Discordance map** — where HCP beliefs CONTRADICT or lag the evidence:
   perception gaps. For each: the belief | what the evidence actually shows |
   likely origin of the gap (old data, competitor messaging, habit, access
   experience) | strategic implication.
4. **Silent zones** — evidence the HCPs never mention (unexploited assets) and
   HCP concerns the evidence never answers (evidence gaps to escalate).
5. **Validation plan** — which provisional insights need confirming, with whom,
   and by what method, before major spend is committed.
6. **Visual concordance** — emit a `comparison_matrix` science-viz of
   belief vs evidence (supportive / clash / silent) and a Mermaid diagram of
   the discordance origins. Each discordant belief must name the Phase 4
   visual it contradicts.""",
    ),
    Phase(
        id="06-behavioural-drivers",
        title="HCP Behaviours, Concerns, Motivations & Key Behavioural Drivers",
        prompt="""\
Phase 6 — List and analyse the main behaviours, concerns, motivations, and
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
5. **KEY BEHAVIOURAL DRIVERS** — the 4-6 levers with the highest leverage,
   each stated as: driver | evidence/insight it rests on | barrier it
   overcomes | how the campaign will pull it. These drivers must be traceable
   to Phases 3, 4 and 5.
6. **Driver infographic** — emit a `driver_map` science-viz of the 4-6 key
   drivers (driver / COM-B lever / barrier). This picture is an input to the
   science-to-solution cascade, not a decoration.""",
    ),
    Phase(
        id="07-evidence-position",
        title="Comparative Evidence Position: Brand vs. Existing vs. Evolving vs. Guidelines",
        prompt="""\
Phase 7 — Compare the evidence we hold on the brand/product/service against
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
5. **Evidence roadmap** — data generation or publication moves (RWE, ISS,
   post-hoc, congress presence) that would strengthen the position during and
   after the campaign.
6. **Position visual** — emit a `comparison_matrix` science-viz of the
   four-way table. This picture, plus the Phase 4 infographics and Phase 6
   drivers, is the input to the next phase.""",
    ),
    Phase(
        id="08-science-to-solution",
        title="Science to Solution through Strategy Execution",
        prompt="""\
Phase 8 — Connect the science to the solution through strategy execution.

This is the spine of the strategy. Evidence that is not converted into a
named execution move is research, not medicomarketing. Do not start
messaging or tactics until every material scientific finding has a path
from the infographic to the field.

Produce:

1. **Solution thesis** — one tight paragraph: given what the science
   *represents* (Phase 4), what HCP beliefs do (Phase 5), and which
   behavioural levers move them (Phase 6), what is the clinical-behavioural
   solution this campaign exists to deliver? Separate the medical solution
   (the practice change) from the commercial objective.
2. **SCIENCE → SOLUTION → EXECUTION CASCADE** — a table and a matching
   `cascade` science-viz. Rows are C1, C2, C3… (use the IDs proposed in
   Phase 4; add more if the position in Phase 7 created new ones). Columns:
   scientific finding (name the evidence and the visual) | what it represents
   clinically | the solution it implies (practice or belief change) |
   execution move (the concrete engagement / activation / content action) |
   owner (medical vs commercial) | proof metric.
   Every later tactic in Phases 9–12 must cite one of these IDs. A row
   without a feasible execution move is an evidence-to-strategy gap — say so.
3. **Execution blueprint** — for each cascade row, specify how it will be
   delivered across the campaign arc: the Phase 9 message pillar it owns,
   the Phase 10 journey stage it enters, the Phase 11 activation formats
   that carry it, the Phase 12 KPI that proves it. This is a map, not a
   slogan.
4. **Mermaid through-line** — a flowchart from the lead scientific visual
   to the solution thesis to the first-quarter execution mix to the
   quarterly proof metric.
5. **Failure modes** — where the science-to-execution link is weakest
   (missing number, MLR-blocked claim, access barrier, HCP disbelief) and
   the workaround that still honours the evidence.

If you cannot draw a straight line from a finding to a field action, do
not bury it in the forefront table — escalate it here as a gap.""",
    ),
    Phase(
        id="09-core-messaging",
        title="Core Messaging Theme, Key Drivers & Behaviour-Change Adaptation",
        prompt="""\
Phase 9 — Build the core messaging platform and define the behavioural change
adaptation required to successfully launch and sustain the campaign.

Messaging is how the cascade is *said*. Every pillar must execute one or
more Phase 8 cascade IDs; a beautiful message with no cascade parent is
incomplete.

Produce:

1. **Core messaging theme** — the single organising idea of the campaign,
   in one sentence, grounded in the solution thesis (Phase 8), the strategic
   evidence position (Phase 7) and the key behavioural drivers (Phase 6).
   Give 2 alternative framings and recommend one, with rationale.
2. **Message house** — table: pillar | cascade ID(s) | core message |
   supporting evidence (named, from the forefront table and Phase 4 visual) |
   behavioural driver it pulls | proof points | MLR risk level.
3. **Segment adaptations** — how the same message house flexes for each HCP
   segment identified earlier (wording, lead evidence, channel emphasis).
4. **Objection-handling grid** — top concerns from Phase 6 | response |
   evidence anchor | Phase 4 visual to put in front of the HCP |
   what NOT to say (compliance boundary).
5. **Behaviour-change adaptation plan** — what has to change and hold:
   launch phase (breaking the old habit: triggers, education, trial
   experiences) vs. sustain phase (embedding the new habit: reinforcement,
   feedback loops, peer norms, system prompts in workflow). Map each element
   to the COM-B lever it works on and the cascade row it executes.
6. **Message visual** — a Mermaid message-house diagram plus a `callout_stat`
   science-viz of the theme's lead figure.""",
    ),
    Phase(
        id="10-hcp-engagement",
        title="HCP Engagement Plan: Campaign Start to End and Beyond",
        prompt="""\
Phase 10 — Design how we engage HCPs from the beginning of the campaign to its
end — and beyond it. Engagement is how the cascade is *delivered over time*.

Produce a staged engagement journey:

1. **Stage map** — table across the arc: Pre-launch (KOL & steering) →
   Launch (awareness & credibility) → Adoption (first prescriptions / first
   recommendations) → Reinforcement (habit & advocacy) → Beyond campaign
   (community, data feedback, lifecycle). For each stage: objective | cascade
   IDs delivered | target segments | key activities | content/evidence used
   (name the Phase 4 visual) | channels | who leads (medical vs. commercial)
   | stage exit criteria.
2. **Touchpoint choreography** — the sequence and cadence of contacts a
   single HCP experiences (rep visits, med-ed events, digital, peer-to-peer,
   congress), with rules to avoid fatigue. Each contact must carry a named
   cascade row and a named visual, not a generic brand story.
3. **KOL and peer-influence plan** — identification criteria, roles
   (steering, speaking, authorship within compliance), and how peer proof is
   cascaded to the wider base.
4. **Two-way engagement** — how HCP feedback, objections, and real-world
   experience flow back into the campaign (advisory loops, insight capture at
   every touchpoint) and trigger adaptations.
5. **Beyond-the-campaign plan** — what stays alive after the funded period:
   communities, registries/data collaborations, education platforms, and the
   handover into the next cycle's strategy.
6. **Journey visual** — emit a `timeline` science-viz of the stages with
   cascade IDs, and a Mermaid journey for one representative HCP.""",
    ),
    Phase(
        id="11-activation-ideas",
        title="Activation Ideas by Specialty, Status, City, Patient Mix & Cost Sensitivity",
        prompt="""\
Phase 11 — Generate activation idea options tailored to the HCP target's
specialty, professional status, city/geography tier, the type of patients they
encounter, and their sensitivity to treatment cost.

Activation is how the cascade is *made concrete for a named doctor*.
Every idea must cite a Phase 8 cascade ID and the Phase 4 visual it puts
in the room.

Produce:

1. **Segmentation grid** — build the practical activation segments by
   crossing: specialty (as per the brief) x status (KOL / senior consultant /
   early-career / GP-referrer as relevant) x city tier (metro / tier-2 /
   tier-3-rural or the local equivalent) x dominant patient profile (payer
   mix, disease severity mix) x cost-of-treatment concern (low / medium /
   high).
   Collapse to the 6-10 segments that actually matter commercially.
2. **Activation menu per segment** — for each retained segment, 3-5 concrete
   activation ideas. For every idea: what it is (2-3 sentences) | cascade
   ID(s) | Phase 4 visual it uses | evidence & message pillar it carries |
   channel & format | why it fits THIS segment (tie explicitly to specialty,
   status, city, patient type, cost concern) | effort/cost level (L/M/H) |
   expected effect on the key behavioural driver | compliance note.
3. **Cost-concern adaptations** — specific mechanics for high cost-concern
   segments: patient-affordability communication (within code), health-economic
   evidence use, payer/formulary engagement, generics/biosimilar defence if
   relevant.
4. **Prioritisation matrix** — impact vs. feasibility plot (as a table) across
   all ideas, and the recommended activation mix for quarter 1 vs. quarters
   2-4, grouped by cascade ID so Q1 spend clearly executes the spine.""",
    ),
    Phase(
        id="12-measurement",
        title="Measurement Framework: Engagement, Uptake, Revenue & Popularity",
        prompt="""\
Phase 12 — Provide the measurable metric tools to assess continuous HCP
engagement and uptake of the campaign, in terms of quarterly revenue growth
and the clinical and social popularity of the campaign.

Measurement is how we prove the cascade worked. Every KPI must name the
cascade row it closes.

Produce:

1. **KPI tree** — from business goal down: quarterly revenue growth →
   prescription/recommendation volume & share → HCP adoption funnel
   (aware → engaged → trialling → repeating → advocating) → engagement
   activity metrics. Show the causal chain so every metric has a parent
   *and* a cascade ID.
2. **Metric definition table** — for every KPI: metric | cascade ID | exact
   definition & formula | data source (sales data, CRM, med-ed platform,
   social listening, market research waves) | baseline | quarterly target
   Q1-Q4 | owner | review cadence.
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
   indicators, thresholds that trigger course-correction, and who decides.
8. **Proof visuals** — emit a `funnel` science-viz of the adoption cascade
   and a Mermaid KPI tree. If a cascade row has no KPI, that is a design
   defect — call it out.""",
    ),
    Phase(
        id="13-executive-summary",
        title="Executive Strategy Summary",
        prompt="""\
Phase 13 — Compile the executive strategy summary.

Condense the entire pipeline into a client-ready executive document
(2-3 pages equivalent) that a CEO and a medical director can sign. Lead
with pictures of the science and the cascade, then the words.

1. The challenge and the insight (Phases 1, 5, 6).
2. What the science represents — restated visual thesis plus the 2-3
   strongest Phase 4 infographics (re-emit the `science-viz` blocks so they
   render in this document).
3. The evidence position in one table *and* the Phase 7 comparison visual
   (Phases 3, 7).
4. The science-to-solution-to-execution cascade (Phase 8) — the cascade
   visual is the page the sign-off meeting should stay on.
5. The core theme and message house top line, each pillar tagged with a
   cascade ID (Phase 9).
6. The engagement and activation plan on one page, tagged with cascade IDs
   (Phases 10, 11).
7. The measurement commitments and quarterly targets that close each
   cascade row (Phase 12).
8. Risks, dependencies, and MLR items to clear before launch — including
   which visuals are illustrative pending retrieval.
9. Immediate next steps: the first 30 days.

Write it so the medical director can audit the science and the CEO can
see how that science becomes next quarter's execution.""",
    ),
]


EXPAND_PROMPT = """\
You are developing detail for one point of a medicomarketing strategy outline
supplied by the strategy lead.

For the outline point below, produce a fully developed section:

- Restate the point as a clear objective.
- Develop it in depth using the same operating principles (evidence-first,
  compliance-aware, HCP-respectful, client-ready Markdown, tables for
  comparative content, visuals for scientific meaning, cascade IDs for
  science-to-execution traceability).
- Where it touches research, define criteria and sub-steps.
- Where it touches evidence, distinguish brand / independent / evolving /
  guideline sources and flag gaps rather than inventing data. Also emit at
  least one `science-viz` infographic of what the data represents
  (patient_impact, effect_size, evidence_mix, or callout_stat).
- Where it touches behaviour, name the behavioural drivers explicitly and
  emit a `driver_map` if drivers are the subject.
- Where it touches execution, segment by specialty, status, geography,
  patient mix, and cost sensitivity as relevant, and name the cascade row
  (science → implication → solution → execution → metric) each tactic
  delivers.
- Where it touches measurement, give metric definitions, sources, and
  targets, each closing a named cascade row.
- End with: dependencies on other outline points, open questions for the
  strategy lead, and MLR/compliance flags.

OUTLINE POINT TO DEVELOP:
{point}
"""

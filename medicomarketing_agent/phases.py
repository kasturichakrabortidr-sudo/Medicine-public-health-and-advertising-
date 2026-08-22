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
7. Visualise the science. Every phase output must include the visuals that
   phase asks for (and add more where they genuinely aid understanding) as
   Mermaid code blocks (```mermaid ... ```), so the data is shown graphically
   and infographically, not only in tables. Choose the form that fits the
   data:
   - `flowchart LR`/`flowchart TD` for causal chains, trees, and traceability
     threads;
   - `xychart-beta` (bar/line) for magnitudes such as effect sizes, evidence
     volume, baselines vs. quarterly targets;
   - `quadrantChart` for 2x2 positioning (e.g. impact vs. feasibility,
     belief vs. evidence);
   - `timeline` for staged journeys and campaign arcs;
   - `pie` for share/mix breakdowns;
   - `mindmap` for structural overviews.
   Mermaid syntax safety rules (follow strictly so every diagram renders):
   keep node and axis labels short (under ~40 characters); wrap every label
   that contains spaces or punctuation in double quotes; never use
   parentheses, square brackets, curly braces, semicolons, or the `#`
   character inside label text; use simple alphanumeric node ids; put one
   statement per line; do not use Mermaid comments. Introduce each visual
   with one sentence stating what it shows and the take-away. Visuals must be
   faithful to the evidence: chart only numbers that appear in the working
   context, and if a magnitude is unknown, represent the item qualitatively
   (e.g. in a flowchart or quadrant) rather than inventing a number.
8. Keep the science-to-solution thread visible. Whenever you introduce a
   strategic element (an insight, behavioural driver, message, engagement
   stage, activation idea, or metric), name the upstream evidence item(s) it
   rests on, so any reader can trace every executional choice back to the
   science and forward to the measurable outcome it is expected to move.
"""


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

**Visuals for this phase** — (a) a `quadrantChart` mapping the known/unknown
items on axes "evidence we hold" vs. "importance to the strategy", so the
client sees at a glance where the dangerous unknowns sit; (b) a
`flowchart LR` linking each working hypothesis to the research stream that
will test it.

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

**Visuals for this phase** — (a) a `flowchart TD` of the evidence hierarchy
as a pyramid (top grade at the top, arrows showing how weight decreases);
(b) a `flowchart LR` of the research process funnel: sources → search →
screening → extraction → appraisal → synthesis, with the output artefact
named at each step.

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

**Visuals for this phase** — the scientific data in this phase must also be
shown graphically: (a) an `xychart-beta` bar chart of the key quantified
findings (effect sizes, response rates, risk reductions — whatever numbers
the evidence actually provides), clearly labelled per evidence item, so the
client sees the magnitude of the science, not just prose (chart only numbers
present in the working context; omit items with no stated magnitude);
(b) a `quadrantChart` positioning each evidence item on "evidence strength"
vs. "strategic relevance", which makes the forefront assets and the weak
spots visible in one picture; (c) a `pie` chart of the evidence base mix by
stream (how much of the case rests on brand-generated vs. independent vs.
evolving vs. guideline vs. health-economic evidence).

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

**Visuals for this phase** — a `quadrantChart` plotting each major HCP belief
on axes "strength of HCP belief" vs. "strength of supporting evidence": the
top-right quadrant is amplify, the top-left (strong belief, weak evidence) is
correct, the bottom-right (weak belief, strong evidence) is educate, the
bottom-left is monitor. This single infographic is the centrepiece of the
perception-gap story.""",
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
5. **KEY BEHAVIOURAL DRIVERS** — the 4-6 levers with the highest leverage,
   each stated as: driver | evidence/insight it rests on | barrier it
   overcomes | how the campaign will pull it. These drivers must be traceable
   to Phases 3 and 4.

**Visuals for this phase** — (a) a `flowchart LR` of the COM-B model applied
to this brief: capability, opportunity, and motivation factors as nodes
flowing into the target behaviour, with barriers marked; (b) a
`flowchart LR` tracing each key behavioural driver back to the named evidence
item or insight it rests on (science on the left, driver on the right), so
the drivers are visibly anchored in the data.""",
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
5. **Evidence roadmap** — data generation or publication moves (RWE, ISS,
   post-hoc, congress presence) that would strengthen the position during and
   after the campaign.

**Visuals for this phase** — (a) a `quadrantChart` positioning each claim
territory on "our evidence strength" vs. "guideline and independent support",
so safe ground, education opportunities, and vulnerabilities are visible in
one picture; (b) a `timeline` of the evidence roadmap showing when each data
generation or publication move lands relative to the campaign window.""",
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
   recommend one, with rationale.
2. **Message house** — table: pillar | core message | supporting evidence
   (named, from the forefront table) | behavioural driver it pulls | proof
   points | MLR risk level.
3. **Segment adaptations** — how the same message house flexes for each HCP
   segment identified earlier (wording, lead evidence, channel emphasis).
4. **Objection-handling grid** — top concerns from Phase 5 | response |
   evidence anchor | what NOT to say (compliance boundary).
5. **Behaviour-change adaptation plan** — what has to change and hold:
   launch phase (breaking the old habit: triggers, education, trial
   experiences) vs. sustain phase (embedding the new habit: reinforcement,
   feedback loops, peer norms, system prompts in workflow). Map each element
   to the COM-B lever it works on.

**Visuals for this phase** — a `flowchart TD` of the message house as an
infographic: the core theme as the roof node, the message pillars beneath it,
and under each pillar the named evidence items that hold it up — so the
client sees the messaging literally standing on the science.""",
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
   segments | key activities | content/evidence used | channels | who leads
   (medical vs. commercial) | stage exit criteria.
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
   handover into the next cycle's strategy.

**Visuals for this phase** — (a) a `timeline` of the full engagement arc from
pre-launch to beyond-campaign with the headline activities per stage; (b) a
`flowchart LR` of the single-HCP touchpoint journey showing the sequence of
contacts and the feedback loop flowing back into the campaign.""",
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
   activation ideas. For every idea: what it is (2-3 sentences) | evidence &
   message pillar it carries | channel & format | why it fits THIS segment
   (tie explicitly to specialty, status, city, patient type, cost concern) |
   effort/cost level (L/M/H) | expected effect on the key behavioural driver |
   compliance note.
3. **Cost-concern adaptations** — specific mechanics for high cost-concern
   segments: patient-affordability communication (within code), health-economic
   evidence use, payer/formulary engagement, generics/biosimilar defence if
   relevant.
4. **Prioritisation matrix** — impact vs. feasibility plot across all ideas:
   present it both as a table and as a `quadrantChart` (impact on the y-axis,
   feasibility on the x-axis, every activation idea plotted by short name),
   and give the recommended activation mix for quarter 1 vs. quarters 2-4.

**Visuals for this phase** — the impact-vs-feasibility `quadrantChart` from
point 4 is mandatory; additionally include a `pie` chart of the recommended
Q1 activation mix by effort/cost so the client sees where the early budget
goes.""",
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
2. **Metric definition table** — for every KPI: metric | exact definition &
   formula | data source (sales data, CRM, med-ed platform, social listening,
   market research waves) | baseline | quarterly target Q1-Q4 | owner |
   review cadence.
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

**Visuals for this phase** — (a) a `flowchart TD` of the KPI tree from
quarterly revenue growth at the top down to engagement activity metrics at
the leaves, so every metric's parent is visible; (b) an `xychart-beta` bar
chart of the quarterly targets Q1-Q4 for the 2-3 headline KPIs (use the
target numbers defined in the metric table; if targets are still to be
baselined, show only the KPIs with agreed numbers).""",
    ),
    Phase(
        id="11-science-to-solution",
        title="Science-to-Solution Thread: Connecting the Evidence to the Execution",
        prompt="""\
Phase 11 — Connect the science to the solution through the strategy
execution, explicitly and in one place. This phase is the strategy's
integrity check: every executional choice must be traceable back to the
scientific data, and every strong piece of science must have an execution
vehicle carrying it to HCPs.

Produce:

1. **GOLDEN-THREAD DIAGRAM** — the centrepiece: a `flowchart LR` that runs
   left to right in labelled columns — Evidence (Phase 3) → Insight or
   perception gap (Phase 4) → Behavioural driver (Phase 5) → Message pillar
   (Phase 7) → Engagement stage and activation tactic (Phases 8-9) → KPI
   (Phase 10) → Quarterly revenue growth. Draw the 5-8 strongest threads as
   connected paths, using the named evidence items, drivers, pillars,
   tactics, and metrics from the earlier phases. This is the single picture
   that shows the science becoming the solution through the execution.
2. **Traceability matrix** — one row per thread: evidence item (named, with
   grade) | what the science shows | insight or gap it meets | behavioural
   driver it powers | core message it becomes | execution vehicle (stage +
   tactic + segment) | metric that proves it worked | contribution to
   quarterly revenue growth.
3. **Orphan check** — two honest lists: (a) execution elements (messages,
   tactics, metrics) that do NOT trace back to named evidence — each must be
   re-anchored, re-scoped, or cut; (b) strong evidence assets with NO
   execution vehicle — each gets a recommendation (activate, hold, or
   publish first).
4. **Thread risk register** — for each golden thread: its weakest link
   (evidence grade, perception gap depth, tactic feasibility, or metric
   attribution), what would break it, and the mitigation.

This phase must read as proof that the strategy is one continuous chain from
scientific data to commercial outcome, not a collection of parallel ideas.""",
    ),
    Phase(
        id="12-executive-summary",
        title="Executive Strategy Summary",
        prompt="""\
Phase 12 — Compile the executive strategy summary.

Condense the entire pipeline into a client-ready executive document
(2-3 pages equivalent):

1. The challenge and the insight (Phases 1, 4, 5).
2. The evidence position in one table (Phases 3, 6).
3. The core theme and message house top line (Phase 7).
4. The engagement and activation plan on one page (Phases 8, 9).
5. The measurement commitments and quarterly targets (Phase 10).
6. The science-to-solution golden thread (Phase 11), condensed to a single
   `flowchart LR` showing the top 3-4 threads from evidence to revenue —
   the one visual a CEO should remember.
7. Risks, dependencies, and MLR items to clear before launch.
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
- Include at least one Mermaid visual (chart, quadrant, flowchart, or
  timeline per the visual operating principles) wherever the section contains
  comparative data, magnitudes, a process, or a prioritisation — the science
  and the plan must be shown graphically, not only described.
- State the science-to-solution thread for this point: which named evidence
  it rests on, and which executional element and metric it feeds.
- End with: dependencies on other outline points, open questions for the
  strategy lead, and MLR/compliance flags.

OUTLINE POINT TO DEVELOP:
{point}
"""

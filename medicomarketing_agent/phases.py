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
7. Visualise the data, don't just describe it. Whenever a phase instructs you
   to produce a chart, include it as a machine-readable chart spec (see CHART
   SPEC FORMAT below), placed directly after the table or section it
   visualises. A chart must encode the exact same real labels and numbers as
   the surrounding text — never a generic, placeholder, or decorative
   diagram. If the working context genuinely lacks enough detail to populate
   a required chart honestly, still output it using your best evidence-based
   estimate, and add one line directly above it: "*Chart uses provisional
   estimates pending confirmed data — see gap register.*" Never skip a
   required chart silently — a client-ready strategy is judged on its
   visuals as much as its tables and prose.

CHART SPEC FORMAT
Whenever a phase asks for a chart, emit it as a fenced code block whose
language tag is exactly `chart`, containing exactly one JSON object and
nothing else (no comments, no trailing commas, no surrounding prose inside
the block). A downstream Python renderer turns this JSON into a real PNG
image, so it must match one of these five schemas exactly:

- bar      {"type":"bar","id":"kebab-id","title":"...","x_label":"...",
            "y_label":"...","categories":["A","B",...],
            "series":[{"name":"...","values":[n,n,...]}, ...]}
            (every series' values array must be the same length as
            categories; use one series for a simple bar chart, several for a
            grouped comparison)
- pie      {"type":"pie","id":"kebab-id","title":"...",
            "labels":["A","B",...],"values":[n,n,...]}
- quadrant {"type":"quadrant","id":"kebab-id","title":"...",
            "x_label":"what low..high means","y_label":"what low..high means",
            "x_range":[0,10],"y_range":[0,10],
            "quadrant_labels":{"top_left":"...","top_right":"...",
                                 "bottom_left":"...","bottom_right":"..."},
            "points":[{"label":"...","x":n,"y":n}, ...]}
- funnel   {"type":"funnel","id":"kebab-id","title":"...",
            "stages":[{"label":"...","value":n}, ...]}
            (ordered top to bottom; value is a count or a percentage)
- tree     {"type":"tree","id":"kebab-id","title":"...",
            "orientation":"vertical"|"horizontal",
            "nodes":[{"id":"a","label":"...","level":0}, ...],
            "edges":[{"from":"a","to":"b"}, ...]}
            (edges are optional — omitting them auto-connects every node at
            level N to every node at level N+1, which is only correct for a
            simple chain; supply explicit edges whenever the real
            relationships are not a full mesh, which is the normal case,
            e.g. a KPI tree, a message house, or an evidence-to-execution
            bridge)

Use short, unique, kebab-case `id` values within each chart. Keep every
chart to the smallest, clearest slice of real data that makes the point —
4-10 categories/points/nodes is normally right; never fabricate extra ones
just to fill the chart.
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
5. **Known/unknown snapshot chart** — a `bar` chart (see CHART SPEC FORMAT)
   with one category per bucket in point 4 (know with evidence / believe
   without evidence / don't know at all) and the number of items you placed
   in each, so the client can see at a glance how evidence-backed the
   starting position really is.
6. **Working hypotheses** — 3-5 falsifiable hypotheses about why target HCPs
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
7. **Evidence hierarchy chart** — a `tree` chart (orientation vertical) with
   one node per grading level from point 3, level 0 = strongest, increasing
   level number as strength decreases, chained top to bottom, so the grading
   scheme itself reads as a diagram, not only a sentence.

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

Then add two charts built from the real rows of the table you just produced
(see CHART SPEC FORMAT):

1. A `pie` chart titled "Evidence grade distribution" — one slice per
   evidence grade you used, sized by how many table rows carry that grade.
2. A `bar` chart titled "Evidence volume by stream" — one category per
   stream (A-E), one series, valued by how many items you collated in that
   stream. This is the first graphical picture of how the scientific data is
   actually distributed, not just a table of it.""",
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
6. **Concordance/discordance chart** — a `quadrant` chart plotting every
   insight from the inventory: x = strength of the evidence behind the
   related claim (0 = none/contradicted, 10 = strong independent + guideline
   support), y = strength/consistency of the HCP signal (0 = isolated/weak,
   10 = near-universal and consistent). Label the four quadrants with what a
   point landing there means, e.g. top-right = "confirmed belief — amplify",
   bottom-right = "evidence exists, HCPs unaware — silent zone to close",
   top-left = "strong belief, weak evidence — perception gap to correct",
   bottom-left = "low current priority". This turns the concordance and
   discordance maps into one picture instead of two separate lists.""",
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
6. **COM-B driver map chart** — a `tree` chart (orientation vertical),
   level 0 = the three COM-B levers (Capability, Opportunity, Motivation),
   level 1 = the key behavioural drivers from point 5, level 2 = the single
   target-behaviour-change node. Use explicit `edges` connecting each driver
   only to the lever(s) it genuinely operates on and on to the target
   behaviour — not a full mesh — so the diagram shows real mechanism, not
   decoration.
7. **Driver leverage chart** — a `bar` chart, one category per key
   behavioural driver from point 5, one series scoring its leverage/priority
   (highest first), so the ranking in point 5 is also visible at a glance.""",
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
6. **Alignment scorecard chart** — a `bar` chart, one category per key
   clinical question/claim territory from the four-way comparison table,
   with four series (Brand, Independent, Evolving, Guidelines) each scored
   numerically for that row (supportive = 1, neutral = 0, unsupportive = -1,
   silent = 0 — and say in the text which cells were silent so the zero isn't
   mistaken for neutrality), so the alignment pattern across all four sources
   is visible as one chart instead of only a table.""",
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
6. **Message house chart** — a `tree` chart (orientation vertical),
   level 0 = the core messaging theme, level 1 = the message pillars from
   point 2, level 2 = the single lead proof point for each pillar. This makes
   the campaign's argument structure visible as one diagram, directly reusing
   the real pillar names and proof points from point 2.""",
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
6. **Engagement arc chart** — a `tree` chart (orientation horizontal), one
   node per stage from point 1 in order (Pre-launch → Launch → Adoption →
   Reinforcement → Beyond campaign), with `edges` chaining each stage to the
   next, so the journey reads left to right as a single flow diagram rather
   than only a table row.""",
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
4. **Prioritisation matrix** — impact vs. feasibility plot (as a table) across
   all ideas, and the recommended activation mix for quarter 1 vs. quarters
   2-4.
5. **Prioritisation chart** — the same impact-vs-feasibility view as a
   `quadrant` chart: one point per activation idea (label = short idea name),
   x = feasibility (0-10), y = impact (0-10). Quadrant labels:
   top_right = "do now", top_left = "hard wins — needs investment",
   bottom_right = "quick wins — lower impact", bottom_left = "deprioritise".
   This gives the client a genuine plotted matrix, not only a text table.""",
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
8. **Adoption funnel chart** — a `funnel` chart with one stage per step of
   the HCP adoption funnel from point 1 (aware → engaged → trialling →
   repeating → advocating), valued with your best current-state or Q4-target
   estimate for each, so the funnel is a real picture, not only a phrase.
9. **KPI tree chart** — a `tree` chart (orientation horizontal) mirroring
   point 1: level 0 = quarterly revenue growth, level 1 = prescription/
   recommendation volume & share, level 2 = the adoption funnel stages,
   level 3 = the engagement activity metrics that feed them. Use explicit
   `edges` to show the true causal parents of each metric, not a full mesh.""",
    ),
    Phase(
        id="11-science-to-execution-bridge",
        title="Science-to-Solution Bridge: Evidence → Strategy → Execution Traceability",
        prompt="""\
Phase 11 — Build the explicit bridge that connects the science to the
solution through the strategy's execution. Every earlier phase produced one
link in this chain; this phase makes the whole chain visible and auditable
in a single place, so no strategic or executional element is left floating
free of the evidence that is supposed to justify it.

Produce:

1. **Traceability matrix** — one row per key evidence item carried into the
   Evidence Forefront Table (Phase 3). Columns: evidence item | strategic
   evidence position it supports (Phase 6) | behavioural driver it fuels
   (Phase 5) | message pillar it proves (Phase 7) | engagement stage(s) that
   carry it to HCPs (Phase 8) | activation tactic(s) that operationalise it
   (Phase 9) | the KPI it should move (Phase 10). If a cell has no honest
   answer, write "no link yet" and add it to the broken-link register in
   point 4 — never invent a link just to fill the cell.
2. **Reverse check** — for every activation tactic (Phase 9) and every
   message pillar (Phase 7), confirm it traces back to at least one named
   evidence item, or flag it "evidence-light — tone/credibility risk, needs
   MLR and medical sign-off before use."
3. **Bridge diagram** — a `tree` chart (orientation horizontal) with level 0
   = the evidence streams/items driving the strategy, level 1 = the
   strategic evidence position statement, level 2 = the key behavioural
   drivers, level 3 = the core message pillars, level 4 = the activation
   tactics that carry them to HCPs, level 5 = the KPI each ultimately moves.
   Use real, named labels taken from the phases above (never generic
   placeholders like "Evidence 1") and explicit `edges` so the diagram shows
   the true chain for each item, not a full mesh between every node in
   adjacent levels.
4. **Broken-link register** — every place in the traceability matrix or the
   reverse check where the chain is missing, weak, or evidence-light, with a
   recommendation: generate more evidence, soften the claim, re-route to a
   better-supported message/tactic, or hold for MLR review.
5. **One-paragraph bridge statement** — in plain language, how the science in
   this brief becomes the specific tactics on the ground and the revenue
   result the client is asking for. This paragraph is the direct answer to
   "how does the evidence actually turn into the campaign and the number."

This phase is the spine of the whole document: everything before it is
science and strategy; everything after it (the executive summary) is the
sign-off. Nothing in the executive summary may claim a connection that this
phase's traceability matrix does not support.""",
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
6. **Strategy-on-a-page chart** — a single condensed `tree` chart
   (orientation horizontal), 4-6 nodes per level, distilling the Phase 11
   bridge diagram down to only the headline evidence, the strategic
   position, the core theme, the lead activation motion, and the top KPI —
   the one visual a CEO could screenshot and remember.
7. Risks, dependencies, and MLR items to clear before launch, drawn from the
   Phase 11 broken-link register as well as compliance considerations.
8. Immediate next steps: the first 30 days.

Write it so a client CEO and a medical director both sign off on it, and so
neither of them has to take the evidence-to-execution connection on faith —
point them at Phase 11 for the full traceability if they want to audit it.""",
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
- Wherever the point has comparative, hierarchical, sequential, or
  quantitative content, add at least one chart in the CHART SPEC FORMAT
  defined in the system prompt (bar / pie / quadrant / funnel / tree) built
  from the real data in this section — never a decorative placeholder.
- If the point sits between science and execution (evidence, insight, or
  behavioural content feeding into a tactic, message, or metric), make that
  link explicit in the text: name which evidence/insight justifies which
  tactic, and show that link in the chart wherever a `tree` chart is the
  right fit for it.
- End with: dependencies on other outline points, open questions for the
  strategy lead, and MLR/compliance flags.

OUTLINE POINT TO DEVELOP:
{point}
"""

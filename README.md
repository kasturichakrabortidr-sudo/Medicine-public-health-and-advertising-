# Medicomarketing Strategy Agent

An AI agent that builds a complete, evidence-led **medicomarketing strategy from
scratch** — and can also take an outline you write and **develop every outline
point in full detail**. It is built for healthcare-professional (HCP) targeted
campaigns: pharmaceutical brands, medical products, and health services.

The agent runs on the Claude API (`claude-opus-5` by default) and encodes the
entire working process as an explicit, auditable pipeline. Every phase writes a
client-ready Markdown document, and each phase builds on all the phases before
it in a single continuous reasoning thread.

---

## Easiest way to run it (no technical knowledge needed)

1. **Install Python** from [python.org/downloads](https://www.python.org/downloads/)
   — on Windows, tick **"Add Python to PATH"** during install.
2. **Download this project**: on the GitHub page, pick the branch, click the
   green **Code** button → **Download ZIP**, and unzip it anywhere.
3. **Start it**:
   - Windows: double-click **`Start-Windows.bat`**
   - Mac: double-click **`Start-Mac.command`** (if blocked, right-click → Open)

That's it. The launcher installs everything itself, walks you through getting
an API key the first time, asks you plain-English questions about your brand,
and then builds the strategy while you watch. Your finished documents appear
in the `output` folder, and your answers are remembered for next time.

---

## The working process — fully outlined

This is the exact process the agent executes, phase by phase. Each phase is a
step you can run, inspect, and hand to a client.

| # | Phase | What it produces |
|---|-------|------------------|
| 1 | **Strategic framing & insightful critical thinking** | Restated challenge, first-principles questions, assumptions register, known/unknown map, falsifiable working hypotheses |
| 2 | **Medical & scientific criteria for research** | PICO(S) research questions, evidence inclusion/exclusion criteria, evidence-grading hierarchy, and a numbered research plan with sub-steps (sources, search strings, screening, extraction, appraisal, synthesis) |
| 3 | **Evidence analysis & collation** | Five evidence streams analysed in parallel with identical extraction fields — brand-generated, independent published, evolving/new, guidelines, health-economic — stacked into the client-facing **Evidence Forefront Table**, plus top strategic assets and evidence gaps |
| 4 | **In-house HCP insight analysis vs. evidence** | Insight inventory, concordance map (where HCP beliefs agree with evidence), discordance map (perception gaps and their origins), silent zones, validation plan |
| 5 | **Behaviours, concerns, motivations & key behavioural drivers** | COM-B based analysis of what target doctors do today, the change required, their clinical/practical/economic/professional concerns, ranked motivations, and the 4–6 **key behavioural drivers** for adopting the product or recommendation change |
| 6 | **Comparative evidence position** | Four-way comparison — brand evidence vs. existing evidence within the brand vs. evolving new evidence vs. supporting guidelines — alignment analysis, competitive shadow, strategic evidence position statement, evidence roadmap |
| 7 | **Core messaging & behaviour-change adaptation** | Core messaging theme, message house tied to named evidence and behavioural drivers, segment adaptations, objection-handling grid, and the launch-vs-sustain **behaviour-change adaptation plan** required to launch and sustain the campaign |
| 8 | **HCP engagement plan — start to end and beyond** | Staged journey (pre-launch → launch → adoption → reinforcement → beyond-campaign), touchpoint choreography, KOL/peer-influence plan, two-way feedback loops, post-campaign continuity |
| 9 | **Activation ideas by segment** | Activation menu tailored to HCP **specialty × status × city tier × patient types encountered × cost-of-treatment concern**, with cost-concern adaptations and an impact/feasibility prioritisation for Q1 vs. Q2–Q4 |
| 10 | **Measurement framework** | KPI tree from **quarterly revenue growth** down to engagement activity, metric definition tables with formulas/sources/targets, continuous HCP engagement metrics, **clinical popularity** and **social popularity** metrics, revenue-linkage model, and quarterly dashboard governance |
| 11 | **Executive strategy summary** | The whole strategy condensed into a sign-off document for the client CEO and medical director |

Every phase output begins with a short *"How this section was built"* note so
the critical-thinking process behind each step stays visible and auditable.

### Built-in guardrails

- **Evidence first** — claims are traced to named evidence; missing evidence is
  logged as a gap, never invented.
- **Evidence separation** — brand-generated vs. independent vs. evolving vs.
  guideline sources are always distinguished and graded.
- **Compliance aware** — outputs flag anything needing medical-legal-regulatory
  (MLR) review and stay inside pharmaceutical promotion codes.

---

## Literature-to-deck evidence workflow

A second automation (`python -m academic_research`) searches open-access and
indexed journals, Cochrane reviews, national/international guidelines, UN-system
and NGO pages (including WHO regional offices and additional UN branches), and
ClinicalTrials.gov. A record is kept only when Crossref,
Europe PMC, ClinicalTrials.gov, or an allow-listed official URL resolves. It
then runs claim-frequency analysis, GRADE-style design bands, and IPA on
qualitative papers, and writes a numbered visual deck plus BibTeX/RIS/CSV/PPTX.

```bash
python -m academic_research demo
cd web && npm install && npm run dev
```

Open `/deck`. The launcher option **4** runs the same workflow without an
Anthropic key. See [`EVIDENCE_WORKFLOW.md`](EVIDENCE_WORKFLOW.md).

---

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # or use `ant auth login`
```

## Usage

### 1. Build a full strategy from scratch

Write a client brief (see [`examples/brief.example.yaml`](examples/brief.example.yaml)
— only `brand` and `therapy_area` are required), then:

```bash
python -m medicomarketing_agent run --brief examples/brief.example.yaml --out output/
```

The agent streams each phase to your terminal and writes:

```
output/
  01-critical-thinking.md
  02-scientific-criteria.md
  03-evidence-forefront.md
  ...
  11-executive-summary.md
  medicomarketing-strategy.md   <- the combined strategy document
```

Run only selected phases:

```bash
python -m medicomarketing_agent run --brief brief.yaml --phases 01,02,03
```

### 2. Develop details for every point of *your* outline

Put one outline point per line/bullet in a file (see
[`examples/outline.example.md`](examples/outline.example.md)), then:

```bash
python -m medicomarketing_agent expand --brief brief.yaml --outline my-outline.md
```

Each point is developed into a full section — with research criteria,
evidence handling, behavioural drivers, segmentation, and metrics as relevant —
plus dependencies, open questions, and MLR flags. Output:
`output/outline-expansion.md`.

### 3. Options

| Flag | Effect |
|------|--------|
| `--web-search` | Lets the model search the web for current guidelines and emerging evidence (server-side web search tool) |
| `--model` | Override the model (default `claude-opus-5`) |
| `--out` | Output directory (default `output/`) |
| `--quiet` | Suppress streaming output |
| `phases` subcommand | List all pipeline phases |

## How it works technically

- **One continuous conversation** — phases run as sequential turns, so Phase 7
  messaging can cite the exact evidence rows from Phase 3 and the drivers from
  Phase 5.
- **Prompt caching** — the conversation prefix is cached between phases, so
  each phase re-reads earlier phases at ~10% of the token price.
- **Streaming** — long outputs stream token-by-token; the pipeline handles
  server-tool pauses (`pause_turn`) and surfaces model refusals cleanly.
- **Everything is a file** — briefs in, Markdown out; nothing hidden in state.

## Important note

This tool produces *strategy drafts*. All medical claims, promotional
materials, and tactics derived from its output must pass your organisation's
medical-legal-regulatory review and comply with local pharmaceutical promotion
codes before any use with healthcare professionals.

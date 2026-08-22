# Medicomarketing Strategy Agent

An AI agent that builds a complete, evidence-led **medicomarketing strategy from
scratch** — and can also take an outline you write and **develop every outline
point in full detail**. It is built for healthcare-professional (HCP) targeted
campaigns: pharmaceutical brands, medical products, and health services.

The agent runs on the Claude API (`claude-opus-5` by default) and encodes the
entire working process as an explicit, auditable pipeline. Every phase writes a
client-ready Markdown document, and each phase builds on all the phases before
it in a single continuous reasoning thread.

Every phase that presents comparative, hierarchical, sequential, or
quantitative data also ships a **real chart image** — evidence-grade pie
charts, behavioural-driver rankings, concordance/discordance quadrant maps,
prioritisation matrices, adoption funnels, KPI trees — rendered straight from
the same data as the tables next to them, not decorative filler. And one
phase exists purely to connect the dots: the **Science-to-Solution Bridge**
traces every piece of evidence all the way through the strategic position,
the behavioural drivers, the core messages, the activation tactics, and into
the KPI it's meant to move — as both a table and a diagram — so the strategy
never floats free of the science it's supposed to be built on.

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

| # | Phase | What it produces | Charts it ships |
|---|-------|------------------|------------------|
| 1 | **Strategic framing & insightful critical thinking** | Restated challenge, first-principles questions, assumptions register, known/unknown map, falsifiable working hypotheses | Known/unknown snapshot (bar) |
| 2 | **Medical & scientific criteria for research** | PICO(S) research questions, evidence inclusion/exclusion criteria, evidence-grading hierarchy, and a numbered research plan with sub-steps (sources, search strings, screening, extraction, appraisal, synthesis) | Evidence hierarchy (tree) |
| 3 | **Evidence analysis & collation** | Five evidence streams analysed in parallel with identical extraction fields — brand-generated, independent published, evolving/new, guidelines, health-economic — stacked into the client-facing **Evidence Forefront Table**, plus top strategic assets and evidence gaps | Evidence grade distribution (pie), evidence volume by stream (bar) |
| 4 | **In-house HCP insight analysis vs. evidence** | Insight inventory, concordance map (where HCP beliefs agree with evidence), discordance map (perception gaps and their origins), silent zones, validation plan | Concordance/discordance map (quadrant) |
| 5 | **Behaviours, concerns, motivations & key behavioural drivers** | COM-B based analysis of what target doctors do today, the change required, their clinical/practical/economic/professional concerns, ranked motivations, and the 4–6 **key behavioural drivers** for adopting the product or recommendation change | COM-B driver map (tree), driver leverage ranking (bar) |
| 6 | **Comparative evidence position** | Four-way comparison — brand evidence vs. existing evidence within the brand vs. evolving new evidence vs. supporting guidelines — alignment analysis, competitive shadow, strategic evidence position statement, evidence roadmap | Alignment scorecard (bar) |
| 7 | **Core messaging & behaviour-change adaptation** | Core messaging theme, message house tied to named evidence and behavioural drivers, segment adaptations, objection-handling grid, and the launch-vs-sustain **behaviour-change adaptation plan** required to launch and sustain the campaign | Message house (tree) |
| 8 | **HCP engagement plan — start to end and beyond** | Staged journey (pre-launch → launch → adoption → reinforcement → beyond-campaign), touchpoint choreography, KOL/peer-influence plan, two-way feedback loops, post-campaign continuity | Engagement arc (tree) |
| 9 | **Activation ideas by segment** | Activation menu tailored to HCP **specialty × status × city tier × patient types encountered × cost-of-treatment concern**, with cost-concern adaptations and an impact/feasibility prioritisation for Q1 vs. Q2–Q4 | Impact/feasibility prioritisation (quadrant) |
| 10 | **Measurement framework** | KPI tree from **quarterly revenue growth** down to engagement activity, metric definition tables with formulas/sources/targets, continuous HCP engagement metrics, **clinical popularity** and **social popularity** metrics, revenue-linkage model, and quarterly dashboard governance | HCP adoption funnel (funnel), KPI tree (tree) |
| 11 | **Science-to-Solution Bridge — evidence → strategy → execution traceability** | A row-by-row **traceability matrix** linking every key evidence item to the strategic position, behavioural driver, message pillar, engagement stage, activation tactic, and KPI it feeds; a reverse check flagging any tactic/message that doesn't trace back to evidence; a broken-link register; and a one-paragraph plain-language bridge statement | Full evidence-to-KPI bridge diagram (tree) |
| 12 | **Executive strategy summary** | The whole strategy condensed into a sign-off document for the client CEO and medical director, pointing back at Phase 11 for the full audit trail | Strategy-on-a-page (tree) |

Every phase output begins with a short *"How this section was built"* note so
the critical-thinking process behind each step stays visible and auditable.

### Visuals, not just tables

Every phase above renders its own real chart images — bar, pie, quadrant,
funnel, and tree/flow diagrams — built with matplotlib from the exact same
labels and numbers as the surrounding tables (never decorative placeholders).
The model emits a small structured chart spec per chart; the pipeline turns
each one into a PNG under `output/charts/` and embeds it directly into the
Markdown, so the scientific and strategic data is genuinely visualised, not
only described in prose and tables.

The centrepiece is **Phase 11 — the Science-to-Solution Bridge**: a single
diagram and matrix that trace every piece of evidence through the strategic
position, the behavioural drivers, and the core messages, all the way to the
activation tactics on the ground and the KPI each one is meant to move — so
the connection from science to solution to execution is explicit and
auditable, not implied.

### Built-in guardrails

- **Evidence first** — claims are traced to named evidence; missing evidence is
  logged as a gap, never invented.
- **Evidence separation** — brand-generated vs. independent vs. evolving vs.
  guideline sources are always distinguished and graded.
- **Compliance aware** — outputs flag anything needing medical-legal-regulatory
  (MLR) review and stay inside pharmaceutical promotion codes.

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
  11-science-to-execution-bridge.md
  12-executive-summary.md
  medicomarketing-strategy.md   <- the combined strategy document
  charts/                       <- every chart, as a PNG (+ its JSON source)
    03-evidence-forefront-01-evidence-grade-distribution.png
    03-evidence-forefront-02-evidence-volume-by-stream.png
    ...
```

Open any `.md` file (or the combined document) in a Markdown viewer — VS
Code, GitHub, Obsidian, Typora — and the chart images render inline
alongside the tables and prose.

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
- **Everything is a file** — briefs in, Markdown + PNGs out; nothing hidden in
  state.
- **Charts are rendered, not requested from the reader's imagination** — each
  phase emits a small `chart` JSON block (bar/pie/quadrant/funnel/tree)
  next to the table it visualises; `medicomarketing_agent/visuals.py` turns
  every one of those into a real PNG with matplotlib and swaps it into the
  Markdown. If a chart spec is malformed or unrenderable, that one block is
  left as-is with a logged warning — never enough to break the rest of the
  strategy document.

## Important note

This tool produces *strategy drafts*. All medical claims, promotional
materials, and tactics derived from its output must pass your organisation's
medical-legal-regulatory review and comply with local pharmaceutical promotion
codes before any use with healthcare professionals.

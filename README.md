# Medicomarketing Strategy Agent

An AI agent that builds a complete, evidence-led **medicomarketing strategy from
scratch** — and can also take an outline you write and **develop every outline
point in full detail**. It is built for healthcare-professional (HCP) targeted
campaigns: pharmaceutical brands, medical products, and health services.

The agent runs on the Claude API (`claude-opus-5` by default) and encodes the
entire working process as an explicit, auditable pipeline. Every phase writes a
client-ready Markdown document, and each phase builds on all the phases before
it in a single continuous reasoning thread.

Every phase also **visualises its data** — evidence-magnitude charts,
belief-vs-evidence quadrants, message-house diagrams, journey timelines,
impact/feasibility plots, and KPI trees — and the pipeline ends with a
**science-to-solution golden thread** that connects each piece of evidence,
through insight, driver, message, and execution, to the metric and revenue
outcome it is expected to move. Alongside the Markdown, the agent writes an
HTML report that renders all of these as real graphics in any web browser.

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
in the `output` folder — double-click the `.html` one to see the full report
with all charts and diagrams in your web browser — and your answers are
remembered for next time.

---

## The working process — fully outlined

This is the exact process the agent executes, phase by phase. Each phase is a
step you can run, inspect, and hand to a client.

| # | Phase | What it produces |
|---|-------|------------------|
| 1 | **Strategic framing & insightful critical thinking** | Restated challenge, first-principles questions, assumptions register, known/unknown map, falsifiable working hypotheses |
| 2 | **Medical & scientific criteria for research** | PICO(S) research questions, evidence inclusion/exclusion criteria, evidence-grading hierarchy, and a numbered research plan with sub-steps (sources, search strings, screening, extraction, appraisal, synthesis) |
| 3 | **Evidence analysis & collation** | Five evidence streams analysed in parallel with identical extraction fields — brand-generated, independent published, evolving/new, guidelines, health-economic — stacked into the client-facing **Evidence Forefront Table**, plus top strategic assets, evidence gaps, and **infographics of the science**: an effect-magnitude chart, an evidence strength-vs-relevance quadrant, and the evidence-mix breakdown |
| 4 | **In-house HCP insight analysis vs. evidence** | Insight inventory, concordance map (where HCP beliefs agree with evidence), discordance map (perception gaps and their origins), silent zones, validation plan |
| 5 | **Behaviours, concerns, motivations & key behavioural drivers** | COM-B based analysis of what target doctors do today, the change required, their clinical/practical/economic/professional concerns, ranked motivations, and the 4–6 **key behavioural drivers** for adopting the product or recommendation change |
| 6 | **Comparative evidence position** | Four-way comparison — brand evidence vs. existing evidence within the brand vs. evolving new evidence vs. supporting guidelines — alignment analysis, competitive shadow, strategic evidence position statement, evidence roadmap |
| 7 | **Core messaging & behaviour-change adaptation** | Core messaging theme, message house tied to named evidence and behavioural drivers, segment adaptations, objection-handling grid, and the launch-vs-sustain **behaviour-change adaptation plan** required to launch and sustain the campaign |
| 8 | **HCP engagement plan — start to end and beyond** | Staged journey (pre-launch → launch → adoption → reinforcement → beyond-campaign), touchpoint choreography, KOL/peer-influence plan, two-way feedback loops, post-campaign continuity |
| 9 | **Activation ideas by segment** | Activation menu tailored to HCP **specialty × status × city tier × patient types encountered × cost-of-treatment concern**, with cost-concern adaptations and an impact/feasibility **quadrant plot** for Q1 vs. Q2–Q4 prioritisation |
| 10 | **Measurement framework** | KPI tree (drawn as a **tree diagram** from **quarterly revenue growth** down to engagement activity), metric definition tables with formulas/sources/targets, continuous HCP engagement metrics, **clinical popularity** and **social popularity** metrics, quarterly-target charts, revenue-linkage model, and quarterly dashboard governance |
| 11 | **Science-to-solution thread** | The strategy's integrity check: a **golden-thread diagram** and traceability matrix connecting each named evidence item → insight → behavioural driver → message → engagement/activation tactic → KPI → quarterly revenue, plus an orphan check (execution without evidence, evidence without execution) and a per-thread risk register |
| 12 | **Executive strategy summary** | The whole strategy condensed into a sign-off document for the client CEO and medical director, closing with the condensed golden-thread visual |

Every phase output begins with a short *"How this section was built"* note so
the critical-thinking process behind each step stays visible and auditable.

### Visual, infographic output

Each phase is required to represent its data graphically, not only in prose
and tables. The visuals are written as [Mermaid](https://mermaid.js.org/)
blocks inside the Markdown — bar/line charts for effect sizes and quarterly
targets, quadrant plots for prioritisation and belief-vs-evidence gaps,
flowcharts for COM-B, message houses, KPI trees and golden threads, timelines
for journeys and evidence roadmaps, and pies for evidence and budget mix.
They render natively on GitHub and in most Markdown editors, and the pipeline
also writes **`medicomarketing-strategy.html`** — open it in any web browser
to see the full report with every chart and diagram drawn out (client-ready,
printable).

### Built-in guardrails

- **Evidence first** — claims are traced to named evidence; missing evidence is
  logged as a gap, never invented.
- **Evidence separation** — brand-generated vs. independent vs. evolving vs.
  guideline sources are always distinguished and graded.
- **Compliance aware** — outputs flag anything needing medical-legal-regulatory
  (MLR) review and stay inside pharmaceutical promotion codes.
- **Honest visuals** — charts may only plot numbers present in the working
  context; items without a known magnitude are shown qualitatively instead of
  being given invented values.
- **Traceable execution** — every strategic element names the evidence it
  rests on, and Phase 11 audits the whole strategy for execution without
  evidence and evidence without execution.

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
  11-science-to-solution.md
  12-executive-summary.md
  medicomarketing-strategy.md     <- the combined strategy document
  medicomarketing-strategy.html   <- the same report with all charts/diagrams
                                     rendered - open in a web browser
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
evidence handling, behavioural drivers, segmentation, visuals, and metrics as
relevant — plus its science-to-solution thread, dependencies, open questions,
and MLR flags. Output: `output/outline-expansion.md` and the browser-rendered
`output/outline-expansion.html`.

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
- **Everything is a file** — briefs in, Markdown and a self-rendering HTML
  report out; nothing hidden in state. The HTML report fetches its Markdown
  and diagram renderers (marked, Mermaid) from a CDN, so it needs an internet
  connection the first time it is opened; offline it falls back to plain text.

## Important note

This tool produces *strategy drafts*. All medical claims, promotional
materials, and tactics derived from its output must pass your organisation's
medical-legal-regulatory review and comply with local pharmaceutical promotion
codes before any use with healthcare professionals.

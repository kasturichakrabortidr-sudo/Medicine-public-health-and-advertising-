# Medicomarketing Strategy Agent

An AI agent that builds a complete, evidence-led **medicomarketing strategy from
scratch** — and can also take an outline you write and **develop every outline
point in full detail**. It is built for healthcare-professional (HCP) targeted
campaigns: pharmaceutical brands, medical products, and health services.

The agent runs on the Claude API (`claude-opus-5` by default) and encodes the
entire working process as an explicit, auditable pipeline. Every phase writes a
client-ready Markdown document, and each phase builds on all the phases before
it in a single continuous reasoning thread.

Scientific findings are not left as tables. The pipeline **draws what the
data represents** (patient-impact grids, effect-size charts, evidence-mix
donuts) and then **connects each finding to the solution through strategy
execution** — a named cascade from the infographic to the field tactic to
the proof metric.

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
| 3 | **Evidence analysis & collation** | Five evidence streams analysed in parallel with identical extraction fields — brand-generated, independent published, evolving/new, guidelines, health-economic — stacked into the client-facing **Evidence Forefront Table**, plus the first science infographics (evidence mix, effect sizes, patient impact) |
| 4 | **Scientific data visualization** | Infographic set of **what the data represents**: patient-impact grids, effect-size charts, evidence-mix donuts, callout stats, plus meaning captions and a handoff of findings that must become cascade rows |
| 5 | **In-house HCP insight analysis vs. evidence** | Insight inventory, concordance / discordance maps against the visuals, silent zones, validation plan, belief-vs-evidence graphic |
| 6 | **Behaviours, concerns, motivations & key behavioural drivers** | COM-B analysis, ranked motivations, 4–6 **key behavioural drivers**, and a driver-map infographic |
| 7 | **Comparative evidence position** | Four-way comparison — brand vs independent vs evolving vs guidelines — plus a comparison-matrix visual and the strategic evidence position statement |
| 8 | **Science → solution → execution cascade** | The strategy spine: solution thesis and named cascade rows (C1, C2, …) from scientific finding → clinical implication → implied solution → execution move → proof metric. Later tactics without a cascade parent are incomplete |
| 9 | **Core messaging & behaviour-change adaptation** | Core theme and message house, each pillar tagged with cascade IDs and the Phase 4 visual it carries |
| 10 | **HCP engagement plan — start to end and beyond** | Staged journey that *delivers* named cascade rows over time, with a timeline visual |
| 11 | **Activation ideas by segment** | Activation menu tailored to HCP **specialty × status × city tier × patient types × cost concern**, each idea citing a cascade ID and the visual it puts in the room |
| 12 | **Measurement framework** | KPI tree from **quarterly revenue growth** down to activity, every metric closing a cascade row, plus funnel / KPI-tree visuals |
| 13 | **Executive strategy summary** | Sign-off document that leads with the science pictures and the cascade, then the words — for the client CEO and medical director |

Every phase output begins with a short *"How this section was built"* note so
the critical-thinking process behind each step stays visible and auditable.

### Built-in guardrails

- **Evidence first** — claims are traced to named evidence; missing evidence is
  logged as a gap, never invented.
- **Evidence separation** — brand-generated vs. independent vs. evolving vs.
  guideline sources are always distinguished and graded.
- **Compliance aware** — outputs flag anything needing medical-legal-regulatory
  (MLR) review and stay inside pharmaceutical promotion codes.
- **Drawn, not only tabulated** — scientific data is rendered as infographics
  (`output/visuals/*.svg` and `output/visual-strategy-brief.html`).
- **Science through to the field** — every material finding travels a cascade
  ID from the picture to the tactic to the KPI.

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
  04-science-infographics.md
  ...
  08-science-to-solution.md
  ...
  13-executive-summary.md
  medicomarketing-strategy.md      <- the combined strategy document
  visual-strategy-brief.html       <- open in a browser: the science pictures
  visuals/*.svg                    <- individual infographics
```

Re-render infographics from an existing Markdown file (no API call):

```bash
python -m medicomarketing_agent render-visuals --input examples/science-viz.example.md --out output/
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

## Testing the visuals (no API key)

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

This renders the example CardioShield infographics from
[`examples/science-viz.example.md`](examples/science-viz.example.md) and checks
that the 13-phase spine still carries science → solution → execution.

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

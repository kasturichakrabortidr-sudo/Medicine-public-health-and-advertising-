# STRATA — AI Strategy Director

A presentation-ready **strategy director** for HCP medicomarketing. Upload a
client brief in **any format**, extract the working file, and get a visual
strategy deck plus a measurement dashboard.

The director does not write a generic funnel. It picks a **doctrine** from the
tension in the brief. Interventions, charts, and kill-criteria all serve that bet.

The app does **not** preload a sample brand. Upload your brief, or open a pack
from **Projects**.

### Run the app on your computer

```bash
pip install -r requirements.txt
python start_director.py
```

Opens `http://127.0.0.1:5173`

| Tab | What it does |
|---|---|
| **Brief** | Upload or paste a client brief. Nothing is preloaded. |
| **Projects** | **Ongoing** working files from Generate, and **Saved** packs you pin. Open, save, or delete them here. |
| **Working file** | The eleven-step strategy for the open pack. |
| **Papers** | Validated citation register (DOI/PMID). Uncited brief items stay gaps. |
| **Deck** | Client-ready slides. **Download PPTX**. Print to PDF. |
| **Measurement** | KPI room, funnel, evidence mix, intervention board, governance. |

`examples/brief.example.yaml` is a CLI fixture only. It is not opened by the app.
Planning numbers are labelled illustrative until you replace them with audit /
CRM baselines. All claims still need MLR.

### Live website

Use the **manual Web Service** path below. Do not type a guessed
`strata-director.onrender.com` URL — that host does not exist. Render only
makes a URL after the service is **Live**, and the hostname is whatever Render
prints on the service page.

GitHub’s default branch in this repo is the old CLI launcher. It has **no
website**. If you leave **Branch** on the default, the deploy has nothing to
serve and the URL shows as not available.

The director website does **not** need an Anthropic API key.

#### Manual path (Render Dashboard)

1. Open [https://dashboard.render.com](https://dashboard.render.com) and sign in
   with GitHub.
2. Top right: **New** → **Web Service**.
3. Stay on **Git Provider**. Connect GitHub if asked, and allow
   `Medicine-public-health-and-advertising-`.
4. Click that repository. Do **not** pick **Existing Image**.
5. Fill the form exactly:

   | Field | Set to |
   |---|---|
   | **Name** | anything you like (this becomes part of the URL) |
   | **Region** | Oregon, or the region closest to you |
   | **Branch** | `cursor/live-working-app-8da2` |
   | **Language** | **Docker** (not Python) |
   | **Dockerfile Path** | `./Dockerfile` |
   | **Root Directory** | leave blank |
   | **Instance type** | **Free** to try, or **Starter** if you want it always on |

6. Open **Advanced**:
   - **Health Check Path:** `/api/health`
   - Leave **Docker Command** empty (the Dockerfile already starts uvicorn)
   - Do **not** add a disk on the Free instance (Render rejects it)
7. Click **Create Web Service** (some accounts say **Deploy Web Service**).
8. Open **Logs** / **Events**. Wait until the deploy status is **Live**. First
   Docker build takes several minutes. Opening the URL before **Live** is what
   produces “URL not available”.
9. On the service page, copy the `https://….onrender.com` link next to the
   service name. Open **that** URL, not a name you invent.
10. Confirm `https://YOUR-HOST.onrender.com/api/health` shows `"ok": true` and
    `"web": true`.

**If the browser still says the URL is not available**

- Confirm **Events** says **Live**, then wait one minute and refresh.
- Free instances sleep after 15 minutes idle. The first request after that can
  take about a minute. Keep the tab open; do not treat the wait page as a dead
  link.
- Use `https://`, not `http://`.
- Try an incognito window or another network (some VPNs break `onrender.com`).

**Free vs always-on:** Free is fine to test. For a URL that stays up, change
the instance type to **Starter** on the service **Settings** page.

Do **not** use **New → Blueprint** unless you first set the Blueprint branch to
`cursor/live-working-app-8da2`. A Blueprint against the default GitHub branch
will not find this app.

#### Other hosts

**Your own server (VPS):**

```bash
pip install -r requirements.txt
python start_live.py
```

Then open `http://YOUR-SERVER:8080`. Point Nginx or Caddy at that port for HTTPS.

**Docker Compose (on a machine with Docker):**

```bash
docker compose up --build
```

Opens `http://127.0.0.1:8080`.

**Fly.io:** install [flyctl](https://fly.io/docs/flyctl/install/), then:

```bash
fly auth login
fly launch --copy-config --yes
fly volumes create strata_data --region iad --size 1
fly deploy
```

Change `app = "strata-director"` in `fly.toml` if that name is taken.

Do **not** deploy the `netlify.toml` frontend as the live app. That file only
builds the Vite site. Without the Python API, Brief, Projects, and PPTX download
will fail.

The original 11-phase Claude pipeline (Markdown documents) is unchanged below.

---

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

# STRATA — AI Strategy Director

A presentation-ready **strategy director** for HCP medicomarketing. Upload a
client brief in **any format**, extract the working file, and get a visual
strategy deck plus a measurement dashboard.

The director does not write a generic funnel. It picks a **doctrine** from the
tension in the brief — for the CardioShield example, **The First-Touch
Doctrine**: the enemy is the *stabilise-first* ritual, not the comparator
molecule. Interventions, charts, and kill-criteria all serve that bet.

### Run the app

```bash
pip install -r requirements.txt
python start_director.py
```

Opens `http://127.0.0.1:8080` — one link for the app and the API. Phone and laptop
both use that address. `python start_director.py --dev` still splits Vite (`5173`)
and the API (`8787`) for live reload.

### Public rollout — a shareable link that stays up

A `*.trycloudflare.com` workbench URL is **not** a product host. Cloudflare's own quick tunnels have no uptime guarantee, the hostname changes if the tunnel restarts, and this development machine goes away when the session stops. That is why a shared preview link becomes inactive.

To give people a link that is ready at all times, run STRATA on a host you keep running and point a real hostname at it:

```bash
cp .env.example .env   # add Stripe keys and PUBLIC_BASE_URL=https://your-domain
docker build -t strata .
docker run --restart unless-stopped --env-file .env -p 8080:8080 strata
```

Set `PUBLIC_BASE_URL` to that domain, then run `PYTHONPATH=. python scripts/bootstrap_stripe.py` so Checkout and the webhook point at it. Netlify can serve the static UI, but generate, credits, and Stripe need this Python process.

A named Cloudflare tunnel (`CLOUDFLARE_TUNNEL_TOKEN` plus `CLOUDFLARE_TUNNEL_HOST`) keeps one hostname across process restarts. A quick tunnel does not.

While you are on this machine, `PYTHONPATH=. python scripts/keep_public.py` watches the local app and restarts the public tunnel if it drops. The live hostname is written to `.strata-public-url`. That still only lasts as long as this machine is up.

| Tab | What it does |
|---|---|
| **Brief** | Upload PDF/PPT/DOC/YAML or paste text. The working file is built from **your** files, not from the demo. |
| **Evidence** | Validated citation register (DOI/PMID). The campaign lead is the highest-leverage published source, not a slogan. Uncited brief items stay gaps. PubMed hits are retrieved but cannot silently become the lead. |
| **Strat deck** | Client-ready slides: forest plots, box plots, bars, lines, pies, impact matrix. **Download PPTX** for an editable PowerPoint (native text, tables, Office charts). Print to PDF. |
| **Dashboard** | KPI room, funnel, evidence mix, intervention board, governance. |
| **Plans** | Free / Practice / Agency credit allowances. Writing a working file costs 8 credits. A user PPTX costs 3. The demo is free. |

### Paid plans

Without Stripe keys the Plans tab can start Practice, Agency, or a 50-credit pack on this machine so the meter works. To take real cards, copy `.env.example` to `.env` (never commit it) and:

1. Prefer a restricted key (`rk_test_` / `rk_live_`) over a secret key. Never commit `.env`.
2. Run `PYTHONPATH=. python scripts/bootstrap_stripe.py` to create one Product per plan and the webhook, or set `STRIPE_PRICE_PRACTICE`, `STRIPE_PRICE_AGENCY`, and `STRIPE_PRICE_CREDITS_50` yourself.
3. Keep `STRIPE_WEBHOOK_SECRET` pointed at `/api/billing/webhook` for `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, and `customer.subscription.deleted`.
4. Set `PUBLIC_BASE_URL` to the public site URL used in Checkout success/cancel. After Checkout, the app also claims `session_id` so credits land even if the webhook is late.

If you will charge US or EU customers, enable Stripe Tax and add a registration before turning tax on. Stripe collects no tax until a registration is active.

The CardioShield HFrEF pack in `examples/brief.example.yaml` is an **optional demo** (button: “Open the CardioShield demo”). It does not load on startup, and it is never returned from `/api/generate`. Planning numbers are labelled illustrative until you replace them with audit / CRM baselines. All claims still need MLR.

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

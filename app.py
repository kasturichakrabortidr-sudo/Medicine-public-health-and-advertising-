"""Gradio web interface for the medicomarketing strategy agent."""

import os
import queue
import tempfile
import threading
from pathlib import Path

import gradio as gr

from medicomarketing_agent.engine import StrategyEngine
from medicomarketing_agent.phases import PHASES

ENV_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


class _QueueWriter:
    def __init__(self, q: queue.Queue):
        self._q = q

    def write(self, text: str):
        if text:
            self._q.put(text)


def _build_brief(brand, therapy_area, product, indication, market,
                 business_goal, target_specialties, brand_evidence,
                 hcp_insights, competitors, constraints):
    brief = {"brand": brand.strip(), "therapy_area": therapy_area.strip()}
    for key, val in [
        ("product", product), ("indication", indication),
        ("market", market), ("business_goal", business_goal),
    ]:
        if val and val.strip():
            brief[key] = val.strip()
    for key, val in [
        ("target_specialties", target_specialties),
        ("brand_evidence", brand_evidence),
        ("hcp_insights", hcp_insights),
        ("competitors", competitors),
        ("constraints", constraints),
    ]:
        items = [ln.strip() for ln in (val or "").splitlines() if ln.strip()]
        if items:
            brief[key] = items
    return brief


def run_strategy(api_key, brand, therapy_area, product, indication, market,
                 business_goal, target_specialties, brand_evidence, hcp_insights,
                 competitors, constraints, mode):

    if not api_key or not api_key.strip().startswith("sk-ant-"):
        yield "⚠  Please enter a valid Anthropic API key (starts with sk-ant-).", None
        return
    if not brand.strip() or not therapy_area.strip():
        yield "⚠  Brand name and Therapy area are required.", None
        return

    brief = _build_brief(brand, therapy_area, product, indication, market,
                         business_goal, target_specialties, brand_evidence,
                         hcp_insights, competitors, constraints)

    phases_to_run = PHASES[:1] if mode.startswith("Quick") else None

    out_dir = Path(tempfile.mkdtemp()) / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    q: queue.Queue = queue.Queue()
    done = threading.Event()
    result_holder: list[Path] = []
    error_holder: list[str] = []

    def _run():
        try:
            engine = StrategyEngine(
                brief,
                out_dir=out_dir,
                api_key=api_key.strip(),
                writer=_QueueWriter(q),
            )
            combined = engine.run_pipeline(phases_to_run)
            result_holder.append(combined)
        except Exception as exc:
            error_holder.append(str(exc))
            q.put(f"\n\n⚠  ERROR: {exc}")
        finally:
            done.set()

    threading.Thread(target=_run, daemon=True).start()

    accumulated = ""
    while True:
        try:
            chunk = q.get(timeout=0.25)
            accumulated += chunk
            yield accumulated, None
        except queue.Empty:
            if done.is_set() and q.empty():
                break
            yield accumulated, None

    if result_holder:
        accumulated += "\n\n✅  Done! Download your strategy document below."
        yield accumulated, str(result_holder[0])
    else:
        yield accumulated, None


# ------------------------------------------------------------------ UI

with gr.Blocks(
    title="Medicomarketing Strategy Agent",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="indigo"),
    css=".gradio-container { max-width: 760px !important; margin: auto; }",
) as demo:

    gr.Markdown(
        "# 💊 Medicomarketing Strategy Agent\n"
        "Build an evidence-led HCP marketing strategy — powered by Claude AI.\n"
        "Fill in the form and press **Run**."
    )

    api_key = gr.Textbox(
        label="Anthropic API Key",
        placeholder="sk-ant-...",
        type="password",
        value=ENV_KEY,
        info="Get one free at platform.anthropic.com → API Keys (pay-as-you-go, ~$1-3 per full run)",
    )

    gr.Markdown("### Brand brief")
    with gr.Row():
        brand = gr.Textbox(label="Brand name *", placeholder="e.g. CardioShield")
        therapy_area = gr.Textbox(label="Therapy area *", placeholder="e.g. Cardiology – heart failure")

    with gr.Accordion("Optional details — more detail = better output", open=False):
        product = gr.Textbox(label="Product / molecule", placeholder="e.g. sacubitril/valsartan")
        indication = gr.Textbox(label="Indication / patient group", placeholder="e.g. HFrEF, NYHA class II–IV")
        market = gr.Textbox(label="Market / country / cities", placeholder="e.g. India (metro + tier-2/3)")
        business_goal = gr.Textbox(
            label="Business goal",
            placeholder="e.g. Grow prescriptions 15% per quarter",
            lines=2,
        )
        target_specialties = gr.Textbox(
            label="Target specialties (one per line)",
            placeholder="Cardiologists\nConsultant physicians\nGP referrers",
            lines=3,
        )
        brand_evidence = gr.Textbox(
            label="Key evidence you hold (one per line)",
            placeholder="PARADIGM-HF RCT: CV death reduction vs enalapril\nLocal RWE study (n=1,200)",
            lines=4,
        )
        hcp_insights = gr.Textbox(
            label="HCP insights from advisors / field (one per line)",
            placeholder="Advisory board: agree with early initiation but wait to stabilise first\nField notes: monthly cost is top barrier in tier-2",
            lines=4,
        )
        competitors = gr.Textbox(
            label="Competitors (one per line)",
            placeholder="Generic ACE inhibitors / ARBs\nSGLT2 inhibitors",
            lines=2,
        )
        constraints = gr.Textbox(
            label="Constraints (one per line)",
            placeholder="Full UCPMP compliance required\n4-quarter campaign, 60 reps across 22 cities",
            lines=2,
        )

    mode = gr.Radio(
        choices=[
            "Quick test — Phase 1 only (~2–3 min, pennies)",
            "Full strategy — all 11 phases (~30–40 min, ~$1–3)",
        ],
        value="Quick test — Phase 1 only (~2–3 min, pennies)",
        label="Run mode",
    )

    run_btn = gr.Button("▶  Run Strategy", variant="primary", size="lg")

    output_box = gr.Textbox(
        label="Live output (streams as it generates)",
        lines=25,
        interactive=False,
        show_copy_button=True,
    )
    download_file = gr.File(label="Download combined strategy (.md)", visible=True)

    run_btn.click(
        fn=run_strategy,
        inputs=[
            api_key, brand, therapy_area,
            product, indication, market, business_goal,
            target_specialties, brand_evidence, hcp_insights,
            competitors, constraints, mode,
        ],
        outputs=[output_box, download_file],
    )

    gr.Markdown(
        "---\n"
        "*Output is a strategy draft. All claims and tactics must pass your organisation's "
        "medical-legal-regulatory review before use with HCPs.*"
    )

demo.queue().launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))

"""Pipeline spine tests — new visual + cascade phases stay wired."""

from medicomarketing_agent.cli import select_phases
from medicomarketing_agent.phases import PHASES, SYSTEM_PROMPT, EXPAND_PROMPT
from medicomarketing_agent.visuals import CHART_TYPES, VISUAL_GRAMMAR


def test_thirteen_phases_in_order():
    ids = [p.id for p in PHASES]
    assert ids == [
        "01-critical-thinking",
        "02-scientific-criteria",
        "03-evidence-forefront",
        "04-science-infographics",
        "05-hcp-insights",
        "06-behavioural-drivers",
        "07-evidence-position",
        "08-science-to-solution",
        "09-core-messaging",
        "10-hcp-engagement",
        "11-activation-ideas",
        "12-measurement",
        "13-executive-summary",
    ]


def test_system_prompt_requires_visuals_and_cascade():
    assert VISUAL_GRAMMAR in SYSTEM_PROMPT
    assert "science-viz" in SYSTEM_PROMPT
    assert "Connect science to the solution through execution" in SYSTEM_PROMPT
    for viz_type in CHART_TYPES:
        assert viz_type in SYSTEM_PROMPT


def test_science_and_cascade_phases_name_the_through_line():
    viz = next(p for p in PHASES if p.id == "04-science-infographics")
    cascade = next(p for p in PHASES if p.id == "08-science-to-solution")
    assert "patient_impact" in viz.prompt
    assert "what the scientific data represents" in viz.prompt.lower()
    assert "SCIENCE → SOLUTION → EXECUTION CASCADE" in cascade.prompt
    assert "C1, C2" in cascade.prompt
    assert "execution move" in cascade.prompt.lower()


def test_later_phases_must_cite_cascade_ids():
    for pid in (
        "09-core-messaging",
        "10-hcp-engagement",
        "11-activation-ideas",
        "12-measurement",
        "13-executive-summary",
    ):
        prompt = next(p for p in PHASES if p.id == pid).prompt
        assert "cascade" in prompt.lower(), pid


def test_expand_prompt_asks_for_visuals_and_cascade():
    assert "science-viz" in EXPAND_PROMPT
    assert "cascade" in EXPAND_PROMPT


def test_select_phases_prefix_hits_new_ids():
    selected = select_phases("04,08")
    assert [p.id for p in selected] == [
        "04-science-infographics",
        "08-science-to-solution",
    ]

import json

from director_api.agent import run_director
from director_api.extract import ExtractedBrief
from director_api.generate import generate_pack


def _helix() -> ExtractedBrief:
    return ExtractedBrief(
        brand="Helix",
        therapy_area="Oncology",
        indication="metastatic NSCLC",
        business_goal="Move first-eligible starts this quarter",
        hcp_insights=["Most wait until the patient is stable in clinic"],
        constraints=["No comparative claim without a numbered paper"],
    )


def test_think_then_execute_on_every_step():
    events = []
    pack = run_director(_helix(), pubmed=False, emit=events.append)
    assert pack["meta"]["brand"] == "Helix"
    assert pack["agent"]["llm"] is False
    assert pack["agent"]["model"] == "director-workflow"
    assert pack["slides"]
    assert events
    seen_think: set[str] = set()
    last_kind_for: dict[str, str] = {}
    for event in events:
        assert event["type"] in {"think", "execute"}
        step = event["step"]
        if event["type"] == "think":
            seen_think.add(step)
            last_kind_for[step] = "think"
        else:
            assert step in seen_think, f"EXECUTE {step} ran before THINK"
            last_kind_for[step] = "execute"
    for step in ("brief", "evidence", "doctrine", "workfile", "deck", "take"):
        assert last_kind_for.get(step) == "execute"
    kinds = [e["type"] for e in events]
    assert kinds[0] == "think"
    wrapped = generate_pack(_helix(), pubmed=False)
    assert wrapped["agent"]["log"]
    assert wrapped["meta"]["brand"] == "Helix"


def test_mocked_llm_patches_prose_only():
    patch = {
        "doctrine": {"bet": "Start Helix at the first eligible visit."},
        "slides": [{"id": "problem", "title": "The wait is the disease.", "soWhat": "Start at the eligible visit."}],
    }

    class _Block:
        type = "text"
        text = json.dumps(patch)

    class _Msg:
        content = [_Block()]

    class _Messages:
        @staticmethod
        def create(**kwargs):
            return _Msg()

    class _Client:
        messages = _Messages()

    pack = run_director(_helix(), pubmed=False, llm=_Client())
    assert pack["agent"]["llm"] is True
    assert pack["doctrine"]["bet"] == "Start Helix at the first eligible visit."
    problem = next(s for s in pack["slides"] if s["id"] == "problem")
    assert problem["title"] == "The wait is the disease."


def test_mocked_llm_refuses_invented_pmid_and_hr():
    patch = {
        "doctrine": {"bet": "Helix beats control HR 0.41 (PMID 99999999)."},
        "slides": [{"id": "problem", "title": "NNT 3.14 from a paper we do not have.", "soWhat": "PMID 8888888 says so."}],
    }

    class _Block:
        type = "text"
        text = json.dumps(patch)

    class _Msg:
        content = [_Block()]

    class _Messages:
        @staticmethod
        def create(**kwargs):
            return _Msg()

    class _Client:
        messages = _Messages()

    pack = run_director(_helix(), pubmed=False, llm=_Client())
    assert "99999999" not in pack["doctrine"]["bet"]
    problem = next(s for s in pack["slides"] if s["id"] == "problem")
    assert "3.14" not in problem["title"]
    assert "8888888" not in (problem.get("soWhat") or "")

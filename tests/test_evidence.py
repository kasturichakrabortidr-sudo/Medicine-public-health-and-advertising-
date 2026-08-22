from director_api.app import _brief_from_mapping
from director_api.evidence import resolve_evidence
from director_api.extract import ExtractedBrief
from director_api.generate import generate_pack
from medicomarketing_agent.config import load_brief


def _visual_cards(slide: dict) -> list[dict]:
    out = list((slide.get("board") or {}).get("cards") or [])
    split = slide.get("split") or {}
    out.extend(split.get("heroes") or [])
    out.extend(split.get("rail") or [])
    out.extend((slide.get("flow") or {}).get("steps") or [])
    return out


def test_cardioshield_lead_is_cited_first_eligible_science():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    ledger = resolve_evidence(brief, pubmed=False)
    pmids = {r["pmid"] for r in ledger["records"]}
    assert "25176015" in pmids  # PARADIGM-HF McMurray 2014 NEJM
    assert "30415601" in pmids  # PIONEER-HF
    assert "34447992" in pmids  # ESC 2021
    assert ledger["lead"]["directs"] == "first-eligible-start"
    assert "25176015" in " ".join(c["pmid"] or "" for c in ledger["lead"]["citations"]) or any(
        c["id"] == "paradigm-hf-2014" or c["id"] == "pioneer-hf-2019" for c in ledger["lead"]["citations"]
    )
    assert all(r.get("doi") and r.get("citation") for r in ledger["records"])
    assert "keynote-189-2018" not in {r["id"] for r in ledger["records"]}
    assert "keynote-024-2016" not in {r["id"] for r in ledger["records"]}
    assert any("local" in g["item"].lower() or "rwe" in g["item"].lower() or "indian" in g["item"].lower()
               for g in ledger["gaps"]) or ledger["gaps"]


def test_pack_exposes_science_slides_and_anchors():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    pack = generate_pack(brief, mode="demo", pubmed=False)
    ids = [s["id"] for s in pack["slides"]]
    assert "science-meaning" in ids
    assert "science-compare" in ids
    assert "science-execute" in ids
    assert "pack" in ids
    assert "how-built" not in ids
    assert "references" in ids
    assert pack["workfile"]["phases"][0]["id"] == "01"
    assert len(pack["workfile"]["phases"]) == 11
    assert pack["references"][0]["n"] == 1
    assert pack["references"][0]["pmid"] == "25176015"
    assert "PMID: 25176015" in pack["references"][0]["citation"]
    meaning = next(s for s in pack["slides"] if s["id"] == "science-meaning")
    assert "[1]" in meaning["subtitle"] or "[1]" in meaning["narrative"]
    pack_slide = next(s for s in pack["slides"] if s["id"] == "pack")
    pack_text = " ".join(
        f"{c.get('title')} {c.get('body')} {c.get('ref')}" for c in _visual_cards(pack_slide)
    )
    assert "[" in pack_text or "PMID" in pack_text or pack_slide.get("refs")
    refs_slide = next(s for s in pack["slides"] if s["id"] == "references")
    assert refs_slide["layout"] == "references"
    assert "McMurray" in refs_slide["table"]["rows"][0][1]
    forest = next(s for s in pack["slides"] if s["id"] == "forest")
    names = [row["name"] for row in forest["chart"]["data"]]
    assert any("PARADIGM-HF" in n for n in names)
    assert any("PIONEER-HF" in n for n in names)
    assert pack["doctrine"]["scienceAnchor"]
    assert "PMID" in pack["doctrine"]["scienceAnchor"]
    house = next(s for s in pack["slides"] if s["id"] == "house")
    house_text = " ".join(
        f"{c.get('title')} {c.get('body')} {c.get('ref')}" for c in _visual_cards(house)
    ) + " ".join(house.get("bullets") or []) + str(house.get("table") or "")
    assert "[1]" in house_text or "[2]" in house_text or "PMID" in house_text
    assert pack["interventions"][0]["evidenceAnchor"]


def test_people_infographic_uses_published_paradigm_rates():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    pack = generate_pack(brief, mode="demo", pubmed=False)
    meaning = next(s for s in pack["slides"] if s["id"] == "science-meaning")
    assert meaning["layout"] == "visual"
    assert meaning["chart"]["kind"] == "people"
    row = meaning["chart"]["data"][0]
    assert row["pmid"] == "25176015"
    assert row["nnt"] == 21
    assert row["control"] == 26.5
    assert row["treat"] == 21.8
    assert pack["dashboard"]["meaning"][0]["nnt"] == 21


def test_spine_connects_pioneer_to_first_touch():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    pack = generate_pack(brief, mode="demo", pubmed=False)
    execute = next(s for s in pack["slides"] if s["id"] == "science-execute")
    assert execute["chart"]["kind"] == "spine"
    names = " ".join(str(r.get("name")) for r in execute["chart"]["data"])
    moves = " ".join(f"{r.get('move')} {r.get('execute')}" for r in execute["chart"]["data"])
    assert "PIONEER-HF" in names
    assert "First-Touch" in moves
    paradigm = next(r for r in execute["chart"]["data"] if "PARADIGM" in str(r.get("name")))
    pioneer = next(r for r in execute["chart"]["data"] if "PIONEER" in str(r.get("name")))
    assert "First-Touch" in str(paradigm.get("move"))
    assert "First-Touch" in str(pioneer.get("move"))
    assert any("30415601" in str(r.get("pmid")) for r in execute["chart"]["data"])
    compare = next(s for s in pack["slides"] if s["id"] == "science-compare")
    assert compare["chart"]["kind"] == "compare"
    assert compare["chart"]["data"][0]["pmid"] == "30415601"
    iv = next(s for s in pack["slides"] if s["id"] == "interventions")
    iv_text = " ".join(
        f"{c.get('title')} {c.get('body')} {c.get('ref')}" for c in _visual_cards(iv)
    ) + " ".join(iv.get("bullets") or [])
    assert "[" in iv_text and "PMID" in iv_text


def test_oncology_brief_matches_keynote_not_hf():
    brief = ExtractedBrief(
        brand="HelixOne",
        therapy_area="Oncology - NSCLC",
        indication="first-line NSCLC",
        business_goal="Grow first-line share. Cost of IO combo is the main barrier.",
    )
    ledger = resolve_evidence(brief, pubmed=False)
    ids = {r["id"] for r in ledger["records"]}
    assert "keynote-189-2018" in ids
    assert "paradigm-hf-2014" not in ids
    assert ledger["lead"]["citations"][0]["pmid"] == "29658856"
    pack = generate_pack(brief, pubmed=False)
    meaning = next(s for s in pack["slides"] if s["id"] == "science-meaning")
    assert meaning["chart"]["data"][0]["pmid"] == "29658856"
    assert meaning["chart"]["data"][0]["nnt"] == 5


def test_respiratory_without_catalog_does_not_invent_trials():
    brief = ExtractedBrief(
        brand="Aero",
        therapy_area="Respiratory",
        access_and_cost=["High out-of-pocket cost is the only stated barrier"],
        business_goal="Grow reimbursed volume",
    )
    pack = generate_pack(brief, pubmed=False)
    assert pack["doctrine"]["id"] == "affordability-confidence"
    assert pack["evidence"]["records"] == []
    assert "do not lock" in pack["evidence"]["lead"]["statement"].lower()
    assert pack["meta"]["brand"] == "Aero"
    assert pack["meta"]["demo"] is False
    assert "CardioShield" not in pack["slides"][0]["title"]
    assert pack["interventions"][0]["id"] == "afford-kit"


def test_unrelated_india_brief_does_not_get_cardioshield_science():
    brief = ExtractedBrief(
        brand="LumenDerm",
        therapy_area="Dermatology - psoriasis",
        market="India",
        business_goal="Grow related clinic starts among related specialists.",
        hcp_insights=["Doctors want a template they can use in clinic."],
    )
    pack = generate_pack(brief, pubmed=False)
    ids = {r["id"] for r in pack["evidence"]["records"]}
    assert "paradigm-hf-2014" not in ids
    assert "pioneer-hf-2019" not in ids
    assert "trivandrum-hf-2015" not in ids
    assert pack["meta"]["brand"] == "LumenDerm"
    assert pack["doctrine"]["id"] != "first-touch"
    assert "CardioShield" not in str(pack["doctrine"])
    assert pack["interventions"][0]["name"] != "First-Touch Protocol"


def test_hf_sglt2_brief_does_not_attach_arni_trials():
    brief = ExtractedBrief(
        brand="GlucoHeart",
        product="dapagliflozin",
        therapy_area="Cardiology - chronic heart failure",
        indication="HFrEF",
        market="India",
        business_goal="Grow SGLT2 foundational use.",
    )
    ledger = resolve_evidence(brief, pubmed=False)
    ids = {r["id"] for r in ledger["records"]}
    assert "paradigm-hf-2014" not in ids
    assert "pioneer-hf-2019" not in ids
    assert "keynote-189-2018" not in ids


def test_product_without_trial_names_still_gets_catalog():
    brief = ExtractedBrief(
        brand="HelixOne",
        product="sacubitril",
        therapy_area="Cardiology — HFrEF",
        market="India",
        business_goal="Grow ARNI initiation in metro clinics",
        hcp_insights=["Cost is the veto at the desk"],
    )
    ledger = resolve_evidence(brief, pubmed=False)
    ids = {r["id"] for r in ledger["records"]}
    assert "paradigm-hf-2014" in ids
    assert ledger["lead"]["citations"][0]["pmid"]


def test_brief_without_paper_links_gets_pubmed_records(monkeypatch):
    def fake_search(term, retmax=8):
        assert "lumetinib" in term.lower() or "psoriasis" in term.lower() or "dermatology" in term.lower()
        return ["39001111"]

    def fake_summary(pmids):
        return {
            "39001111": {
                "title": "Lumetinib in moderate-to-severe plaque psoriasis: a randomized trial",
                "fulljournalname": "N Engl J Med",
                "pubdate": "2024 Jan",
                "authors": [{"name": "Chen L"}, {"name": "Rao P"}, {"name": "Singh A"}, {"name": "Other"}],
                "articleids": [{"idtype": "doi", "value": "10.1056/NEJMoa9999999"}],
                "pubtype": ["Randomized Controlled Trial"],
            }
        }

    def fake_fetch(pmids):
        return {
            "39001111": {
                "abstract": (
                    "METHODS: We randomized n=840 adults with moderate-to-severe plaque psoriasis. "
                    "RESULTS: PASI 90 at week 16 was achieved by 74.1% of lumetinib patients versus 5.8% of placebo (p<0.001). "
                    "CONCLUSIONS: Lumetinib was superior to placebo for PASI 90 at week 16 in plaque psoriasis."
                ),
                "sections": {},
                "pubtypes": ["Randomized Controlled Trial"],
                "pages": "12-24",
            }
        }

    monkeypatch.setattr("director_api.evidence._esearch", fake_search)
    monkeypatch.setattr("director_api.evidence._esummary", fake_summary)
    monkeypatch.setattr("director_api.evidence.fetch_abstracts", fake_fetch)
    brief = ExtractedBrief(
        brand="LumenDerm",
        product="lumetinib",
        therapy_area="Dermatology",
        indication="plaque psoriasis",
        market="India",
        business_goal="Grow first-line share among metro dermatologists",
        hcp_insights=["Cost is the veto at the desk"],
    )
    ledger = resolve_evidence(brief, pubmed=True)
    pmids = {r["pmid"] for r in ledger["records"]}
    assert "39001111" in pmids
    assert len(ledger["records"]) <= 4
    rec = ledger["records"][0]
    assert "PASI 90" in rec["claim_permitted"]
    assert rec["treat_event"] == 74.1
    assert rec["spine_means"]
    assert "Cost is the veto" in rec["spine_barrier"]
    assert "paradigm-hf-2014" not in {r["id"] for r in ledger["records"]}
    assert "PASI 90" in ledger["lead"]["statement"]
    assert "paper links" not in ledger["lead"]["statement"].lower()
    pack = generate_pack(brief, pubmed=True)
    assert pack["references"][0]["pmid"] == "39001111"
    assert "PASI 90" in pack["evidence"]["lead"]["statement"]
    assert "CardioShield" not in pack["slides"][0]["title"]
    house = next(p for p in pack["workfile"]["phases"] if p["id"] == "07")["house"]["rows"]
    joined = " ".join(" ".join(str(c) for c in row) for row in house)
    assert "PASI 90" in joined
    assert "74.1" in joined
    assert "guideline encounter" not in joined
    assert "Cost is the veto" in joined
    assert "first eligible encounter (citation pending)" not in " ".join(pack["slides"][0].get("bullets") or [])


def test_sglt2_pubmed_does_not_steal_arni_catalog(monkeypatch):
    def fake_search(term, retmax=8):
        return ["31535829"]

    def fake_summary(pmids):
        return {
            "31535829": {
                "title": "Dapagliflozin in patients with heart failure and reduced ejection fraction",
                "fulljournalname": "N Engl J Med",
                "pubdate": "2019",
                "authors": [{"name": "McMurray JJV"}],
                "articleids": [{"idtype": "doi", "value": "10.1056/NEJMoa1911303"}],
                "pubtype": ["Randomized Controlled Trial"],
            }
        }

    monkeypatch.setattr("director_api.evidence._esearch", fake_search)
    monkeypatch.setattr("director_api.evidence._esummary", fake_summary)
    monkeypatch.setattr(
        "director_api.evidence.fetch_abstracts",
        lambda pmids: {
            "31535829": {
                "abstract": (
                    "METHODS: 4744 patients were randomized. "
                    "RESULTS: The primary composite occurred in 16.3% with dapagliflozin and in 21.2% with placebo "
                    "(hazard ratio 0.74; 95% CI 0.65 to 0.85). "
                    "CONCLUSIONS: Dapagliflozin reduced worsening heart failure or cardiovascular death."
                ),
                "pubtypes": ["Randomized Controlled Trial"],
                "pages": "",
            }
        },
    )
    brief = ExtractedBrief(
        brand="GlucoHeart",
        product="dapagliflozin",
        therapy_area="Cardiology - chronic heart failure",
        indication="HFrEF",
        market="India",
    )
    ledger = resolve_evidence(brief, pubmed=True)
    ids = {r["id"] for r in ledger["records"]}
    pmids = {r["pmid"] for r in ledger["records"]}
    assert "paradigm-hf-2014" not in ids
    assert "31535829" in pmids
    rec = next(r for r in ledger["records"] if r["pmid"] == "31535829")
    assert rec["hr"] == 0.74
    assert "0.74" in rec["claim_permitted"]
    assert "16.3" in rec["claim_permitted"]
    assert "0.74" in ledger["lead"]["statement"]


def test_each_paper_owns_a_distinct_strategy_line(monkeypatch):
    def fake_search(term, retmax=8):
        return ["111", "222", "333"]

    def fake_summary(pmids):
        return {
            "111": {
                "title": "Lumetinib versus placebo in plaque psoriasis (BEAM-1)",
                "fulljournalname": "N Engl J Med",
                "pubdate": "2024",
                "authors": [{"name": "Chen L"}],
                "articleids": [{"idtype": "doi", "value": "10.1056/a"}],
                "pubtype": ["Randomized Controlled Trial"],
            },
            "222": {
                "title": "Lumetinib versus secukinumab in plaque psoriasis (BEAM-HEAD)",
                "fulljournalname": "Br J Dermatol",
                "pubdate": "2025",
                "authors": [{"name": "Rao P"}],
                "articleids": [{"idtype": "doi", "value": "10.1111/b"}],
                "pubtype": ["Randomized Controlled Trial"],
            },
            "333": {
                "title": "Long-term lumetinib open-label extension (BEAM-EXT)",
                "fulljournalname": "J Am Acad Dermatol",
                "pubdate": "2025",
                "authors": [{"name": "Singh A"}],
                "articleids": [{"idtype": "doi", "value": "10.1016/c"}],
                "pubtype": ["Randomized Controlled Trial"],
            },
        }

    def fake_fetch(pmids):
        return {
            "111": {
                "abstract": (
                    "METHODS: BEAM-1 randomized 840 adults. "
                    "RESULTS: PASI 90 at week 16 was 74.1% versus 5.8% placebo. "
                    "CONCLUSIONS: Lumetinib was superior to placebo."
                ),
                "pubtypes": ["Randomized Controlled Trial"],
            },
            "222": {
                "abstract": (
                    "METHODS: BEAM-HEAD compared lumetinib with secukinumab. "
                    "RESULTS: PASI 90 at week 52 was 86.6% versus 57.1% secukinumab. "
                    "CONCLUSIONS: Lumetinib was superior to secukinumab."
                ),
                "pubtypes": ["Randomized Controlled Trial"],
            },
            "333": {
                "abstract": (
                    "METHODS: BEAM-EXT open-label extension enrolled 897 patients. "
                    "RESULTS: At week 256, 85.1%/52.3% of patients achieved PASI 90/100. "
                    "CONCLUSIONS: Durable PASI 90 responses were maintained."
                ),
                "pubtypes": ["Randomized Controlled Trial"],
            },
        }

    monkeypatch.setattr("director_api.evidence._esearch", fake_search)
    monkeypatch.setattr("director_api.evidence._esummary", fake_summary)
    monkeypatch.setattr("director_api.evidence.fetch_abstracts", fake_fetch)
    brief = ExtractedBrief(
        brand="LumenDerm",
        product="lumetinib",
        therapy_area="Dermatology",
        indication="plaque psoriasis",
        hcp_insights=["Cost is the veto at the desk"],
    )
    pack = generate_pack(brief, pubmed=True)
    lead = pack["evidence"]["lead"]["statement"]
    assert "74.1" in lead
    assert "86.6" in lead or "57.1" in lead
    assert "85.1" in lead
    assert lead.count("74.1") == 1
    house = next(p for p in pack["workfile"]["phases"] if p["id"] == "07")["house"]["rows"]
    lines = [row[1] for row in house]
    assert any("74.1" in str(line) for line in lines)
    assert any("86.6" in str(line) or "57.1" in str(line) for line in lines)
    assert any("85.1" in str(line) for line in lines)
    assert len({str(line) for line in lines}) == len(lines)
    executes = {r.get("spine_execute") for r in pack["evidence"]["records"]}
    assert len(executes) >= 2
    objections = next(p for p in pack["workfile"]["phases"] if p["id"] == "07")["objections"]["rows"]
    obj_refs = [row[2] for row in objections if row[2] not in ("gap", "pending", "brief", "—")]
    assert len(set(obj_refs)) >= 2
    p05 = next(p for p in pack["workfile"]["phases"] if p["id"] == "05")
    driver_refs = [row[1] for row in p05["drivers"]["rows"] if str(row[1]).startswith("[")]
    assert len(set(driver_refs)) >= 3
    assert "the sourced finding" not in (p05.get("required") or "").lower()
    p06 = next(p for p in pack["workfile"]["phases"] if p["id"] == "06")
    standing = " ".join(str(x) for row in p06["fourway"]["rows"] for x in row)
    assert "Indian RWE" not in standing
    assert "ACEI" not in standing
    assert "first-eligible" not in standing.lower()
    assert "[1]" in standing and "[2]" in standing
    assert "74.1" in standing
    assert "86.6" in standing or "57.1" in standing


def test_cost_arni_brief_does_not_clone_cardioshield_playbook():
    """HelixOne / sacubitril + a cost insight is not the CardioShield first-touch file."""
    brief = ExtractedBrief(
        brand="HelixOne",
        product="sacubitril",
        therapy_area="Cardiology — HFrEF",
        indication="HFrEF",
        market="India",
        business_goal="Grow ARNI initiation in metro clinics",
        hcp_insights=["Cost is the veto at the desk"],
        guidelines=["ESC HF 2021"],
    )
    pack = generate_pack(brief, pubmed=False)
    lead = pack["evidence"]["lead"]["statement"]
    assert "Lead the campaign with first-eligible" not in lead
    assert "25176015" in lead  # PARADIGM-HF
    house = next(p for p in pack["workfile"]["phases"] if p["id"] == "07")["house"]["rows"]
    refs = [row[2] for row in house]
    assert len(set(r for r in refs if str(r).startswith("["))) >= 3
    p05 = next(p for p in pack["workfile"]["phases"] if p["id"] == "05")
    assert "first eligible encounter" not in (p05.get("required") or "").lower()
    p06 = next(p for p in pack["workfile"]["phases"] if p["id"] == "06")
    blob = str(p06)
    assert "Indian RWE" not in blob
    assert pack["doctrine"]["id"] == "affordability-confidence"
    demo = generate_pack(
        _brief_from_mapping(load_brief("examples/brief.example.yaml")),
        mode="demo",
        pubmed=False,
    )
    assert "Lead the campaign with first-eligible" in demo["evidence"]["lead"]["statement"]


def test_fictional_hfpef_brief_gets_a_paper_pack_not_one_reprint():
    """Cardiava / Velmecor HFpEF must not collapse to Trivandrum or a single PMID."""
    from director_api.evidence import _pubmed_queries
    from director_api.paper_read import search_product_name, _mentions_product

    brief = ExtractedBrief(
        brand="Cardiava™ (fictional brand)",
        product="Velmecor 10 mg / 20 mg (fictional once-daily oral therapy)",
        therapy_area="Heart Failure with Preserved Ejection Fraction (HFpEF",
        hcp_insights=["simply an insight,", "or just another campaign line."],
    )
    assert search_product_name(brief.product) == ""
    assert _mentions_product(
        "Empagliflozin in Heart Failure with a Preserved Ejection Fraction",
        "",
        brief.product,
    )
    queries = _pubmed_queries(brief)
    blob = " ".join(queries).lower()
    assert queries
    assert "velmecor" not in blob
    assert "fictional" not in blob
    assert "hfpef" in blob
    assert "(" not in brief.product or all("(" not in q.split("AND")[0] or "HFpEF" in q for q in queries)

    ledger = resolve_evidence(brief, pubmed=False)
    ids = {r["id"] for r in ledger["records"]}
    pmids = {r["pmid"] for r in ledger["records"]}
    assert len(ledger["records"]) >= 3
    assert "trivandrum-hf-2015" not in ids
    assert "paradigm-hf-2014" not in ids
    assert "pioneer-hf-2019" not in ids
    assert "34449189" in pmids  # EMPEROR-Preserved
    assert "36027570" in pmids  # DELIVER
    assert "31475794" in pmids  # PARAGON-HF
    lead = ledger["lead"]["statement"].lower()
    assert "one paper is not a case" in lead
    assert len(ledger["lead"]["citations"]) >= 3

    pack = generate_pack(brief, pubmed=False)
    assert pack["meta"]["brand"].startswith("Cardiava")
    assert pack["meta"].get("molecule") in ("", None)
    p02 = next(p for p in pack["workfile"]["phases"] if p["id"] == "02")
    intervention = " ".join(str(c) for c in p02["pico"]["rows"][1]).lower()
    assert "velmecor" not in intervention
    assert "cardiava" not in intervention
    how = (pack["workfile"].get("howBuilt") or "").lower()
    assert "velmecor" not in how
    assert "cardiava" not in how or "brief for" in how
    papers_blob = " ".join(
        f"{r.get('claim_permitted')} {r.get('title')}" for r in pack["evidence"]["records"]
    ).lower()
    assert "empagliflozin" in papers_blob
    assert "dapagliflozin" in papers_blob
    assert "jardiance" not in papers_blob
    assert "farxiga" not in papers_blob
    assert pack["doctrine"]["id"] != "first-touch"
    assert "Lead the campaign with first-eligible" not in pack["evidence"]["lead"]["statement"]
    house = next(p for p in pack["workfile"]["phases"] if p["id"] == "07")["house"]["rows"]
    joined = " ".join(" ".join(str(c) for c in row) for row in house)
    assert "not enough to convince" in joined.lower()
    refs = [row[2] for row in house]
    assert any("–" in str(r) or str(r).count("[") == 1 and "," in str(r) or str(r) in ("[1–3]", "[1–4]", "[1,2,3]") for r in refs) or (
        len(set(r for r in refs if str(r).startswith("["))) >= 3
    )
    p05 = next(p for p in pack["workfile"]["phases"] if p["id"] == "05")
    assert "one paper is not a case" in (p05.get("required") or "").lower()
    standing = next(p for p in pack["workfile"]["phases"] if p["id"] == "06")
    standing_blob = str(standing)
    assert "ACEI" not in standing_blob
    assert "first-eligible" not in standing_blob.lower()
    papers = next(p for p in pack["workfile"]["phases"] if p["id"] == "03")
    forefront = " ".join(str(x) for row in papers["forefront"]["rows"] for x in row)
    assert "[1]" in forefront and "[2]" in forefront and "[3]" in forefront


def test_pubmed_keeps_searching_until_a_pack_is_filled(monkeypatch):
    calls: list[str] = []

    def fake_search(term, retmax=8):
        calls.append(term)
        if "hfpef" in term.lower() or "preserved" in term.lower():
            return ["999111", "999222", "999333"]
        return []

    def fake_summary(pmids):
        catalog = {
            "999111": "Empagliflozin in heart failure with a preserved ejection fraction (copy)",
            "999222": "Dapagliflozin in heart failure with mildly reduced or preserved ejection fraction (copy)",
            "999333": "Finerenone in heart failure with preserved ejection fraction",
        }
        return {
            pmid: {
                "title": catalog[pmid],
                "fulljournalname": "N Engl J Med",
                "pubdate": "2021",
                "authors": [{"name": "Anker SD"}],
                "articleids": [{"idtype": "doi", "value": "10.1056/x"}],
                "pubtype": ["Randomized Controlled Trial"],
            }
            for pmid in pmids
            if pmid in catalog
        }

    monkeypatch.setattr("director_api.evidence._esearch", fake_search)
    monkeypatch.setattr("director_api.evidence._esummary", fake_summary)
    from director_api.evidence import _pubmed_enrich

    brief = ExtractedBrief(
        brand="Cardiava™ (fictional brand)",
        product="Velmecor 10 mg / 20 mg (fictional once-daily oral therapy)",
        therapy_area="Heart Failure with Preserved Ejection Fraction (HFpEF",
    )
    hits = _pubmed_enrich(brief, set())
    assert any("hfpef" in c.lower() or "preserved" in c.lower() for c in calls)
    assert len(calls) >= 2
    titles = " ".join(h["title"] for h in hits).lower()
    assert "preserved" in titles
    assert not any("velmecor" in (h.get("title") or "").lower() for h in hits)

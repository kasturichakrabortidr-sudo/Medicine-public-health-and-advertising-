from director_api.extract import ExtractedBrief
from director_api.paper_read import extract_finding, select_papers


def test_extracts_pasi_response_from_abstract():
    parsed = extract_finding(
        "Lumetinib in moderate-to-severe plaque psoriasis: a randomized trial",
        "METHODS: We randomized n=840 adults. "
        "RESULTS: PASI 90 at week 16 was achieved by 74.1% of lumetinib patients versus 5.8% of placebo (p<0.001). "
        "CONCLUSIONS: Lumetinib was superior to placebo for PASI 90 at week 16 in plaque psoriasis.",
        product="lumetinib",
    )
    assert parsed["n"] == 840
    assert "PASI 90" in parsed["claim"]
    assert parsed["treat_event"] == 74.1
    assert parsed["control_event"] == 5.8
    assert parsed["hr"] is None
    assert parsed["numeric"] is True


def test_extracts_hazard_ratio_and_event_rates():
    parsed = extract_finding(
        "Dapagliflozin in patients with heart failure and reduced ejection fraction",
        "METHODS: 4744 patients were randomized. "
        "RESULTS: The primary composite occurred in 16.3% with dapagliflozin and in 21.2% with placebo "
        "(hazard ratio 0.74; 95% CI 0.65 to 0.85). "
        "CONCLUSIONS: Dapagliflozin reduced worsening heart failure or cardiovascular death.",
        product="dapagliflozin",
    )
    assert parsed["hr"] == 0.74
    assert parsed["low"] == 0.65
    assert parsed["high"] == 0.85
    assert parsed["treat_event"] == 16.3
    assert parsed["control_event"] == 21.2
    assert "0.74" in parsed["claim"]
    assert "16.3" in parsed["claim"]


def test_unicode_decimal_does_not_split_pasi_rates():
    """NCBI abstracts often use a middle-dot (73·8%) instead of 73.8%."""
    results = (
        "Risankizumab was noninferior to secukinumab in the proportion of patients "
        "achieving PASI 90 at week 16 [73·8% vs. 65·6%; difference of 8·2%] and "
        "superior to secukinumab at week 52 (86·6% vs. 57·1%; difference of 29·8%)."
    )
    parsed = extract_finding(
        "Efficacy and safety of risankizumab vs. secukinumab in patients with plaque psoriasis (IMMerge)",
        "METHODS: IMMerge randomized 327 patients. RESULTS: " + results + " "
        "CONCLUSIONS: At week 52, risankizumab demonstrated superior efficacy compared with secukinumab.",
        product="risankizumab",
    )
    assert parsed["trial"] == "IMMerge"
    assert parsed["treat_event"] == 86.6
    assert parsed["control_event"] == 57.1
    assert parsed["treat_event"] != 8.0
    assert "86.6" in parsed["claim"]
    assert "8%" not in parsed["claim"]


def test_lancet_parenthetical_pasi_rates():
    parsed = extract_finding(
        "Risankizumab versus ustekinumab for plaque psoriasis (UltIMMa-1 and UltIMMa-2)",
        "FINDINGS: At week 16 of UltIMMa-1, PASI 90 was achieved by 229 (75·3%) patients "
        "receiving risankizumab versus five (4·9%) receiving placebo "
        "(placebo-adjusted difference 70·3% [95% CI 64·0-76·7]). "
        "INTERPRETATION: Risankizumab showed superior efficacy to both placebo and ustekinumab.",
        product="risankizumab",
    )
    assert parsed["trial"].startswith("UltIMMa")
    assert parsed["treat_event"] == 75.3
    assert parsed["control_event"] == 4.9
    assert parsed["treat_event"] != 9.0
    assert "75.3" in parsed["claim"]


def test_open_label_extension_single_arm_pasi():
    parsed = extract_finding(
        "Long-term safety and efficacy of risankizumab for psoriasis: LIMMitless",
        "METHODS: LIMMitless enrolled 897 patients. "
        "RESULTS: At week 304, 86.0% of patients achieved PASI 90, 54.2% achieved PASI 100. "
        "CONCLUSIONS: Long-term risankizumab demonstrated high and durable efficacy.",
        product="risankizumab",
    )
    assert parsed["trial"] == "LIMMitless"
    assert parsed["treat_event"] == 86.0
    assert parsed["control_event"] is None
    assert "86" in parsed["claim"]
    assert "PASI 90" in parsed["claim"]


def test_pasi_90_100_slash_uses_the_pasi_90_rate():
    parsed = extract_finding(
        "Long-term risankizumab: LIMMitless interim",
        "METHODS: LIMMitless enrolled 897 patients. "
        "RESULTS: At week 256, 85.1%/52.3% of patients achieved PASI 90/100, respectively. "
        "CONCLUSIONS: Durable PASI 90 responses were maintained.",
        product="risankizumab",
    )
    assert parsed["treat_event"] == 85.1
    assert parsed["treat_event"] != 52.3
    assert "PASI 90" in parsed["claim"]


def test_does_not_use_clinicaltrials_gov_as_the_trial_name():
    parsed = extract_finding(
        "Efficacy of risankizumab vs placebo in plaque psoriasis",
        "RESULTS: At week 16, 298 patients (73.2%) in the treatment group vs 2 patients (2.0%) "
        "receiving placebo achieved a PASI 90 response, and 340 patients (83.5%) receiving "
        "risankizumab vs 7 patients (7.0%) receiving placebo achieved sPGA 0/1 scores. "
        "CONCLUSIONS: Risankizumab was efficacious. TRIAL REGISTRATION: ClinicalTrials.gov Identifier: NCT02672852.",
        product="risankizumab",
    )
    assert parsed["trial"] != "ClinicalTrials"
    assert parsed["treat_event"] == 73.2
    assert parsed["control_event"] == 2.0
    assert "placebo" in parsed["claim"]


def test_select_papers_prefers_numeric_rct_and_drops_duplicates():
    hits = [
        {"pmid": "1", "title": "Systemic treatments for chronic plaque psoriasis: a network meta-analysis", "year": 2022, "design": "Meta-Analysis"},
        {"pmid": "2", "title": "Systemic treatments for chronic plaque psoriasis: a network meta-analysis", "year": 2023, "design": "Meta-Analysis"},
        {
            "pmid": "ole-a",
            "title": "Long-term safety of lumetinib: the BEAM-EXT open-label extension",
            "year": 2025,
            "design": "Randomized Controlled Trial",
        },
        {
            "pmid": "ole-b",
            "title": "Final analysis of lumetinib in the BEAM-EXT open-label extension",
            "year": 2025,
            "design": "Randomized Controlled Trial",
        },
        {
            "pmid": "4",
            "title": "Efficacy and safety of lumetinib in moderate-to-severe plaque psoriasis (BEAM-1)",
            "year": 2024,
            "design": "Randomized Controlled Trial",
        },
        {
            "pmid": "noise",
            "title": "Angio-IMR validation in coronary microvascular dysfunction",
            "year": 2024,
            "design": "Validation Study",
        },
    ]
    brief = ExtractedBrief(product="lumetinib", therapy_area="Dermatology")
    readings = {
        "4": {
            "abstract": "RESULTS: PASI 90 at week 16 was 74% versus 6% placebo.",
            "pubtypes": ["Randomized Controlled Trial"],
        },
        "ole-a": {
            "abstract": "BEAM-EXT open-label extension. RESULTS: 81% of patients achieved PASI 90 at week 52.",
            "pubtypes": ["Randomized Controlled Trial"],
        },
        "ole-b": {
            "abstract": "BEAM-EXT open-label extension. RESULTS: 82% of patients achieved PASI 90 at week 104.",
            "pubtypes": ["Randomized Controlled Trial"],
        },
        "noise": {"abstract": "Angio-IMR correlated moderately with invasive IMR.", "pubtypes": ["Validation Study"]},
        "1": {"abstract": "Network meta-analysis of systemic treatments.", "pubtypes": ["Meta-Analysis"]},
        "2": {"abstract": "Updated network meta-analysis of systemic treatments.", "pubtypes": ["Meta-Analysis"]},
    }
    chosen = select_papers(hits, brief, readings, limit=4)
    pmids = [h["pmid"] for h in chosen]
    assert "4" in pmids
    assert pmids[0] == "4"
    assert sum(1 for p in pmids if p in {"ole-a", "ole-b"}) <= 1
    assert "noise" not in pmids
    assert sum(1 for p in pmids if p in {"1", "2"}) <= 1
    assert len(chosen) <= 4

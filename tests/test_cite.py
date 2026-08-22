from director_api.cite import attach_references, format_marks, mark, vancouver


def test_format_marks_compresses_ranges():
    assert format_marks([1, 2, 3, 5]) == "[1–3,5]"
    assert mark({"ref": 2}, {"ref": 1}) == "[1–2]"


def test_vancouver_has_pmid_and_doi():
    text = vancouver({
        "authors": "McMurray JJV, et al.",
        "title": "Angiotensin–neprilysin inhibition versus enalapril in heart failure",
        "journal": "N Engl J Med",
        "year": 2014,
        "pages": "371:993-1004",
        "doi": "10.1056/NEJMoa1409077",
        "pmid": "25176015",
    })
    assert "PMID: 25176015" in text
    assert "doi:10.1056/NEJMoa1409077" in text


def test_attach_references_numbers_in_order():
    ledger = {
        "records": [{"id": "a", "short": "A", "authors": "A", "title": "T", "journal": "J", "year": 2020, "pmid": "1"}],
        "pubmed": [{"pmid": "9", "title": "Hit", "authors": "B", "journal": "K", "year": 2021}],
        "lead": {"citations": [{"id": "a"}]},
    }
    attach_references(ledger)
    assert ledger["records"][0]["ref"] == 1
    assert ledger["pubmed"][0]["ref"] == 2
    assert ledger["lead"]["citations"][0]["ref"] == 1
    assert ledger["references"][1]["status"] == "retrieved"

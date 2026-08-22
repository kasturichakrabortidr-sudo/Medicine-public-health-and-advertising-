from director_api.links import paper_href


def test_paper_href_prefers_https_url():
    assert paper_href({"url": "https://example.com/p", "pmid": "1"}) == "https://example.com/p"


def test_paper_href_pubmed_then_doi():
    assert paper_href({"pmid": "25176015"}) == "https://pubmed.ncbi.nlm.nih.gov/25176015/"
    assert paper_href({"doi": "10.1056/NEJMoa1409077"}) == "https://doi.org/10.1056/NEJMoa1409077"
    assert paper_href({"doi": "doi:10.1/abc"}) == "https://doi.org/10.1/abc"


def test_paper_href_empty():
    assert paper_href({}) == ""
    assert paper_href(None) == ""

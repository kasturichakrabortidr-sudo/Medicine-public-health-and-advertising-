"""Live connectors for scholarly, guideline, UN, and trial sources."""

from __future__ import annotations

from urllib.parse import quote, urlencode

from .extract import strip_text
from .http_client import get_json
from .models import EvidenceRecord
from .validate import normalize_doi

UN_INSTITUTIONS = [
    ("I4210105654", "World Health Organization", "un_agency"),
    ("I4210112062", "WHO SEARO", "un_agency"),
    ("I4210099008", "WHO Europe", "un_agency"),
    ("I4210139943", "WHO AFRO", "un_agency"),
    ("I112289208", "UNICEF", "un_agency"),
    ("I145388677", "UNAIDS", "un_agency"),
    ("I107145371", "UNDP", "un_agency"),
    ("I78934096", "UNFPA", "un_agency"),
    ("I1293226324", "UNESCO", "un_agency"),
    ("I1285985921", "ILO", "un_agency"),
    ("I202262619", "UNEP", "un_agency"),
    ("I1337769664", "UNHCR", "un_agency"),
    ("I1320745970", "FAO", "un_agency"),
    ("I1295768896", "WFP", "un_agency"),
    ("I1315501941", "IOM", "un_agency"),
    ("I32579530", "UNODC", "un_agency"),
    ("I1334329717", "World Bank", "un_agency"),
    ("I4210089393", "PAHO / WHO Americas", "un_agency"),
    ("I4405272890", "UN Women", "un_agency"),
    ("I2801717407", "UN-Habitat", "un_agency"),
    ("I1303371618", "ITU", "un_agency"),
    ("I90130731", "UN DESA", "un_agency"),
    ("I90810661", "World Heart Federation", "ngo"),
]

SOCIETY_INSTITUTIONS = [
    ("I308269434", "European Society of Cardiology", "international_guideline"),
    ("I1281833243", "American Heart Association", "international_guideline"),
    ("I37048141", "Indian Council of Medical Research", "national_guideline"),
]

# Registry-known DOIs used only as search seeds. Titles/authors/years are
# overwritten from Crossref or Europe PMC during validation. Each DOI was
# confirmed live against Crossref before being listed here.
ANCHOR_DOI_SEEDS = {
    "heart failure": [
        "10.1056/NEJMoa1409077",  # PARADIGM-HF
        "10.1056/NEJMoa1812851",  # PIONEER-HF
        "10.1056/NEJMoa1911303",  # DAPA-HF
        "10.1056/NEJMoa2022190",  # EMPEROR-Reduced
        "10.1056/NEJMoa2107038",  # EMPEROR-Preserved
        "10.1016/S0140-6736(22)02076-1",  # STRONG-HF
        "10.1056/NEJMoa1915928",  # VICTORIA
        "10.1056/NEJMoa2025797",  # GALACTIC-HF
        "10.1056/NEJMoa2206286",  # DELIVER (HFmrEF/HFpEF)
        "10.1056/NEJMoa1908655",  # PARAGON-HF
        "10.1093/eurheartj/ehab368",  # ESC 2021 HF guideline
        "10.1093/eurheartj/ehad195",  # ESC 2023 focused update
        "10.1016/j.jacc.2021.12.012",  # 2022 AHA/ACC/HFSA (JACC)
        "10.1161/CIR.0000000000001063",  # 2022 AHA/ACC/HFSA (Circulation)
        "10.1002/ejhf.283",  # Trivandrum Heart Failure Registry
        "10.1016/j.ijcard.2020.10.012",  # 5-year Trivandrum / India outcomes
        "10.1016/j.ihj.2017.11.015",  # CSI/India HF management protocols
        "10.1111/jocn.13615",  # qualitative: living with breathlessness
        "10.1186/1472-6963-10-77",  # qualitative narrative review, living with CHF
        "10.1186/2193-1801-2-320",  # qualitative meta-synthesis, self-care barriers
        "10.1097/jcn.0b013e3182076a69",  # caregiver experiences, qualitative review
        "10.1016/S0140-6736(10)61198-1",  # SHIFT
        "10.1056/NEJMoa1009492",  # EMPHASIS-HF
        "10.1056/NEJMoa2407107",  # FINEARTS-HF
        "10.1016/S0140-6736(20)32339-4",  # AFFIRM-AHF
        "10.1056/NEJMoa2030183",  # SOLOIST-WHF
        "10.1056/NEJMoa2306963",  # STEP-HFpEF
        "10.1038/s41591-021-01659-1",  # EMPULSE
        "10.1016/S0140-6736(22)02083-9",  # IRONMAN
        "10.1056/NEJMoa2304968",  # HEART-FID
        "10.1056/NEJMoa2410027",  # SUMMIT
        "10.1056/NEJM199909023411001",  # RALES
        "10.1016/S0140-6736(03)14282-1",  # CHARM-Overall
        "10.1016/S0140-6736(03)14283-3",  # CHARM-Added
        "10.1056/NEJMoa1313731",  # TOPCAT
        "10.1056/NEJMoa2104508",  # PARADISE-MI
        "10.1056/NEJMoa1806640",  # COAPT
        "10.1056/NEJMoa2203094",  # ADVOR
        "10.1016/S0140-6736(11)60101-3",  # CHAMPION
        "10.1177/1474515117707666",  # qualitative: caregiver phenomenology
        "10.2147/RMHP.S443475",  # qualitative: lived experience, Ethiopia
        "10.5837/bjc.2012.004",  # qualitative: patient voice interviews
        "10.1016/j.hrtlng.2021.05.002",  # qualitative: family caregiving
    ],
}


def _authors_from_epmc(hit: dict) -> list[str]:
    raw = hit.get("authorString") or ""
    return [a.strip() for a in raw.split(",") if a.strip()][:12]


def _year(value) -> int | None:
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None


def europe_pmc(query: str, page_size: int = 12) -> list[EvidenceRecord]:
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode(
        {
            "query": query,
            "format": "json",
            "pageSize": page_size,
            "resultType": "core",
            "sort": "CITED desc",
        }
    )
    data = get_json(url)
    out: list[EvidenceRecord] = []
    for hit in (data.get("resultList") or {}).get("result") or []:
        doi = normalize_doi(hit.get("doi"))
        pmid = str(hit.get("pmid") or "") or None
        is_oa = str(hit.get("isOpenAccess") or "").upper() in {"Y", "TRUE", "1"}
        family = "open_access" if is_oa else "paywalled_journal"
        title = strip_text(hit.get("title") or "")
        if not title:
            continue
        out.append(
            EvidenceRecord(
                key=doi or (f"pmid:{pmid}" if pmid else f"epmc:{hit.get('id')}"),
                title=title,
                url=(
                    f"https://doi.org/{doi}"
                    if doi
                    else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    if pmid
                    else f"https://europepmc.org/article/MED/{hit.get('id')}"
                ),
                source_connector="europe_pmc",
                source_family=family,
                issuing_body=hit.get("journalTitle") or "Indexed journal",
                doi=doi,
                pmid=pmid,
                pmcid=hit.get("pmcid"),
                authors=_authors_from_epmc(hit),
                year=_year(hit.get("pubYear")),
                venue=hit.get("journalTitle"),
                is_oa=is_oa,
                abstract=strip_text(hit.get("abstractText") or ""),
            )
        )
    return out


def openalex(search: str, page_size: int = 10, extra_filter: str | None = None) -> list[EvidenceRecord]:
    params = {
        "search": search,
        "per-page": str(page_size),
        "sort": "cited_by_count:desc",
        "mailto": "research@localhost",
    }
    if extra_filter:
        params["filter"] = extra_filter
    url = "https://api.openalex.org/works?" + urlencode(params)
    data = get_json(url)
    out: list[EvidenceRecord] = []
    for work in data.get("results") or []:
        doi = normalize_doi((work.get("doi") or "").replace("https://doi.org/", ""))
        loc = work.get("primary_location") or {}
        src = loc.get("source") or {}
        oa = (work.get("open_access") or {}).get("is_oa") is True
        authors = []
        for auth in (work.get("authorships") or [])[:12]:
            name = ((auth.get("author") or {}).get("display_name")) or ""
            if name:
                authors.append(name)
        abstract = _openalex_abstract(work.get("abstract_inverted_index"))
        title = strip_text(work.get("display_name") or "")
        if not title:
            continue
        landing = loc.get("landing_page_url") or (f"https://doi.org/{doi}" if doi else work.get("id"))
        out.append(
            EvidenceRecord(
                key=doi or work.get("id"),
                title=title,
                url=landing,
                source_connector="openalex",
                source_family="open_access" if oa else "paywalled_journal",
                issuing_body=src.get("display_name") or "Indexed journal",
                doi=doi,
                authors=authors,
                year=work.get("publication_year"),
                venue=src.get("display_name"),
                is_oa=oa,
                abstract=abstract,
            )
        )
    return out


def _openalex_abstract(inverted: dict | None) -> str:
    if not inverted:
        return ""
    positions: dict[int, str] = {}
    for word, idxs in inverted.items():
        for i in idxs:
            positions[int(i)] = word
    return " ".join(positions[i] for i in sorted(positions))[:4000]


def openalex_societies(search: str, page_size: int = 8) -> list[EvidenceRecord]:
    return _openalex_by_institutions(search, SOCIETY_INSTITUTIONS, page_size)


def openalex_un_ngo(search: str, page_size: int = 8) -> list[EvidenceRecord]:
    return _openalex_by_institutions(search, UN_INSTITUTIONS, page_size)


def _openalex_by_institutions(
    search: str,
    institutions: list[tuple[str, str, str]],
    page_size: int,
) -> list[EvidenceRecord]:
    ids = "|".join(i for i, _, _ in institutions)
    family_by_id = {i: fam for i, _, fam in institutions}
    body_by_id = {i: name for i, name, _ in institutions}
    params = {
        "search": search,
        "per-page": str(page_size),
        "sort": "cited_by_count:desc",
        "mailto": "research@localhost",
        "filter": f"authorships.institutions.id:{ids}",
    }
    url = "https://api.openalex.org/works?" + urlencode(params)
    data = get_json(url)
    out: list[EvidenceRecord] = []
    for work in data.get("results") or []:
        doi = normalize_doi((work.get("doi") or "").replace("https://doi.org/", ""))
        inst_ids = []
        for auth in work.get("authorships") or []:
            for inst in auth.get("institutions") or []:
                oid = (inst.get("id") or "").split("/")[-1]
                if oid:
                    inst_ids.append(oid)
        family = institutions[0][2] if institutions else "un_agency"
        body = "Institutional author"
        for oid in inst_ids:
            if oid in family_by_id:
                family = family_by_id[oid]
                body = body_by_id[oid]
                break
        loc = work.get("primary_location") or {}
        title = strip_text(work.get("display_name") or "")
        if not title:
            continue
        out.append(
            EvidenceRecord(
                key=doi or work.get("id"),
                title=title,
                url=loc.get("landing_page_url")
                or (f"https://doi.org/{doi}" if doi else work.get("id")),
                source_connector="openalex_institutions",
                source_family=family,
                issuing_body=body,
                doi=doi,
                authors=[
                    ((a.get("author") or {}).get("display_name") or "")
                    for a in (work.get("authorships") or [])[:8]
                    if (a.get("author") or {}).get("display_name")
                ],
                year=work.get("publication_year"),
                venue=body,
                is_oa=(work.get("open_access") or {}).get("is_oa") is True,
                abstract=_openalex_abstract(work.get("abstract_inverted_index")),
            )
        )
    return out


def crossref_search(query: str, rows: int = 8) -> list[EvidenceRecord]:
    """Bibliographic search of Crossref (OA and paywalled journals)."""
    if not query.strip():
        return []
    url = "https://api.crossref.org/works?" + urlencode(
        {
            "query": query,
            "rows": str(rows),
            "select": "DOI,title,author,issued,container-title,URL,abstract,type",
            "mailto": "research@localhost",
        }
    )
    data = get_json(url)
    out: list[EvidenceRecord] = []
    for item in (data.get("message") or {}).get("items") or []:
        doi = normalize_doi(item.get("DOI"))
        title = strip_text(" ".join(item.get("title") or []))
        if not doi or not title:
            continue
        authors = []
        for a in (item.get("author") or [])[:12]:
            name = f"{a.get('given') or ''} {a.get('family') or ''}".strip() or a.get("name")
            if name:
                authors.append(name)
        year = None
        parts = (item.get("issued") or {}).get("date-parts") or [[]]
        if parts and parts[0]:
            year = parts[0][0]
        venue = (item.get("container-title") or [None])[0]
        out.append(
            EvidenceRecord(
                key=doi,
                title=title,
                url=f"https://doi.org/{doi}",
                source_connector="crossref",
                source_family="paywalled_journal",
                issuing_body=venue or "Indexed journal",
                doi=doi,
                authors=authors,
                year=year,
                venue=venue,
                is_oa=False,
                abstract=strip_text(item.get("abstract") or ""),
            )
        )
    return out


def pubmed(query: str, page_size: int = 8) -> list[EvidenceRecord]:
    """NCBI E-utilities search (MEDLINE). Abstracts filled later via Europe PMC."""
    if not query.strip():
        return []
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urlencode(
        {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": str(page_size),
            "sort": "relevance",
            "tool": "evidenceworkflow",
            "email": "research@localhost",
        }
    )
    data = get_json(search_url)
    ids = (data.get("esearchresult") or {}).get("idlist") or []
    if not ids:
        return []
    sum_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urlencode(
        {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json",
            "tool": "evidenceworkflow",
            "email": "research@localhost",
        }
    )
    summary = get_json(sum_url)
    result = summary.get("result") or {}
    out: list[EvidenceRecord] = []
    for pmid in ids:
        hit = result.get(pmid) or {}
        title = strip_text(hit.get("title") or "")
        if not title:
            continue
        doi = None
        for ident in hit.get("articleids") or []:
            if ident.get("idtype") == "doi":
                doi = normalize_doi(ident.get("value"))
                break
        year = _year(hit.get("pubdate") or hit.get("sortpubdate"))
        out.append(
            EvidenceRecord(
                key=doi or f"pmid:{pmid}",
                title=title,
                url=f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                source_connector="pubmed",
                source_family="paywalled_journal",
                issuing_body=hit.get("fulljournalname") or hit.get("source") or "MEDLINE",
                doi=doi,
                pmid=str(pmid),
                authors=[a.get("name") for a in (hit.get("authors") or [])[:12] if a.get("name")],
                year=year,
                venue=hit.get("source"),
                is_oa=False,
                abstract="",
            )
        )
    return out


def unpaywall_is_oa(doi: str) -> bool | None:
    """Return True/False from Unpaywall, or None if the lookup fails."""
    norm = normalize_doi(doi)
    if not norm:
        return None
    url = (
        "https://api.unpaywall.org/v2/"
        + quote(norm)
        + "?email=research@localhost"
    )
    try:
        data = get_json(url, timeout=20, retries=2)
    except Exception:
        return None
    flag = data.get("is_oa")
    if flag is True:
        return True
    if flag is False:
        return False
    return None


def europe_pmc_reviews(query: str, page_size: int = 8) -> list[EvidenceRecord]:
    """Systematic reviews and Cochrane records via Europe PMC."""
    q = f"({query}) AND (systematic review OR meta-analysis OR Cochrane)"
    return europe_pmc(q, page_size)


def europe_pmc_cochrane(query: str, page_size: int = 6) -> list[EvidenceRecord]:
    """Cochrane Database of Systematic Reviews only."""
    q = (
        f'({query}) AND (JOURNAL:"Cochrane Database Syst Rev" OR '
        f'JOURNAL:"Cochrane Database of Systematic Reviews")'
    )
    return europe_pmc(q, page_size)


def semantic_scholar(query: str, page_size: int = 8) -> list[EvidenceRecord]:
    """Semantic Scholar Graph API — OA and paywalled bibliographic hits."""
    if not query.strip():
        return []
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urlencode(
        {
            "query": query,
            "limit": str(page_size),
            "fields": "title,year,authors,abstract,externalIds,isOpenAccess,url,venue",
        }
    )
    try:
        data = get_json(url, timeout=25, retries=2)
    except Exception:
        return []
    out: list[EvidenceRecord] = []
    for hit in data.get("data") or []:
        title = strip_text(hit.get("title") or "")
        if not title:
            continue
        ids = hit.get("externalIds") or {}
        doi = normalize_doi(ids.get("DOI"))
        pmid = str(ids.get("PubMed") or "") or None
        authors = [a.get("name") for a in (hit.get("authors") or [])[:12] if a.get("name")]
        is_oa = hit.get("isOpenAccess") is True
        out.append(
            EvidenceRecord(
                key=doi or (f"pmid:{pmid}" if pmid else hit.get("paperId") or title),
                title=title,
                url=(
                    f"https://doi.org/{doi}"
                    if doi
                    else hit.get("url")
                    or (f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "")
                ),
                source_connector="semantic_scholar",
                source_family="open_access" if is_oa else "paywalled_journal",
                issuing_body=hit.get("venue") or "Indexed journal",
                doi=doi,
                pmid=pmid,
                authors=authors,
                year=_year(hit.get("year")),
                venue=hit.get("venue"),
                is_oa=is_oa,
                abstract=strip_text(hit.get("abstract") or ""),
            )
        )
    return out


def europe_pmc_preprints(query: str, page_size: int = 5) -> list[EvidenceRecord]:
    """Server-side preprint index (medRxiv/bioRxiv via Europe PMC SRC:PPR)."""
    q = f"({query}) AND SRC:PPR"
    rows = europe_pmc(q, page_size)
    for rec in rows:
        rec.source_connector = "europe_pmc_preprints"
        rec.source_family = "open_access"
        rec.is_oa = True
    return rows


def doaj(query: str, page_size: int = 6) -> list[EvidenceRecord]:
    """Directory of Open Access Journals article search."""
    if not query.strip():
        return []
    url = (
        "https://doaj.org/api/search/articles/"
        + quote(query)
        + "?"
        + urlencode({"pageSize": str(page_size), "page": "1"})
    )
    try:
        data = get_json(url, timeout=25, retries=2)
    except Exception:
        return []
    out: list[EvidenceRecord] = []
    for hit in data.get("results") or []:
        bib = hit.get("bibjson") or {}
        title = strip_text(bib.get("title") or "")
        if not title:
            continue
        doi = None
        html_url = ""
        for ident in bib.get("identifier") or []:
            if str(ident.get("type") or "").lower() == "doi":
                doi = normalize_doi(ident.get("id"))
        for link in bib.get("link") or []:
            if link.get("url"):
                html_url = link["url"]
                break
        year = _year(bib.get("year"))
        journal = (bib.get("journal") or {}).get("title") or "DOAJ journal"
        authors = []
        for a in (bib.get("author") or [])[:12]:
            name = a.get("name") or ""
            if name:
                authors.append(name)
        abstract = strip_text(bib.get("abstract") or "")
        out.append(
            EvidenceRecord(
                key=doi or hit.get("id") or title,
                title=title,
                url=f"https://doi.org/{doi}" if doi else html_url,
                source_connector="doaj",
                source_family="open_access",
                issuing_body=journal,
                doi=doi,
                authors=authors,
                year=year,
                venue=journal,
                is_oa=True,
                abstract=abstract,
            )
        )
    return out


def records_from_dois(dois: list[str]) -> list[EvidenceRecord]:
    """Seed records by DOI only; bibliographic fields come from validation."""
    out: list[EvidenceRecord] = []
    for doi in dois:
        norm = normalize_doi(doi)
        if not doi:
            continue
        if not norm:
            continue
        out.append(
            EvidenceRecord(
                key=norm,
                title=f"DOI seed {norm}",
                url=f"https://doi.org/{norm}",
                source_connector="doi_seed",
                source_family="paywalled_journal",
                issuing_body="Indexed journal",
                doi=norm,
                is_oa=False,
            )
        )
    return out


def who_publications(query: str, top: int = 10) -> list[EvidenceRecord]:
    # WHO's query= param is noisy; constrain via OData contains on title words.
    words = [w for w in query.replace(",", " ").split() if len(w) > 4][:3]
    if not words:
        words = ["cardiovascular"]
    clause = " or ".join(f"contains(tolower(Title),'{w.lower()}')" for w in words)
    url = (
        "https://www.who.int/api/hubs/publications?"
        + urlencode({"$filter": clause, "$top": str(top)})
    )
    try:
        data = get_json(url)
    except Exception:
        return []
    out: list[EvidenceRecord] = []
    for item in data.get("value") or []:
        title = strip_text(item.get("Title") or "")
        path = item.get("ItemDefaultUrl") or ""
        if not title or not path:
            continue
        url_full = "https://www.who.int" + path
        year = _year(item.get("PublicationDate"))
        abstract = strip_text(
            item.get("MetaDescription") or item.get("Summary") or item.get("Overview") or ""
        )
        out.append(
            EvidenceRecord(
                key=item.get("Id") or url_full,
                title=title,
                url=url_full,
                source_connector="who_publications",
                source_family="un_agency",
                issuing_body="World Health Organization",
                handle=item.get("IRISID") or None,
                year=year,
                venue="WHO",
                is_oa=True,
                abstract=abstract,
            )
        )
    return out


def who_iris(query: str, size: int = 8) -> list[EvidenceRecord]:
    url = (
        "https://iris.who.int/server/api/discover/search/objects?"
        + urlencode({"query": query, "size": str(size)})
    )
    try:
        data = get_json(url)
    except Exception:
        return []
    objects = (
        ((data.get("_embedded") or {}).get("searchResult") or {})
        .get("_embedded") or {}
    ).get("objects") or []
    out: list[EvidenceRecord] = []
    for obj in objects:
        idx = (obj.get("_embedded") or {}).get("indexableObject") or {}
        handle = idx.get("handle")
        meta = idx.get("metadata") or {}
        title = idx.get("name")
        if not title:
            titles = meta.get("dc.title") or []
            title = titles[0].get("value") if titles else None
        abstract = ""
        for key in ("dc.description.abstract", "dc.description"):
            if meta.get(key):
                abstract = meta[key][0].get("value") or ""
                break
        if not title or not handle:
            continue
        year = None
        dates = meta.get("dc.date.issued") or meta.get("dc.date.available") or []
        if dates:
            year = _year(dates[0].get("value"))
        url_full = f"https://iris.who.int/handle/{handle}"
        out.append(
            EvidenceRecord(
                key=f"iris:{handle}",
                title=strip_text(title),
                url=url_full,
                source_connector="who_iris",
                source_family="un_agency",
                issuing_body="World Health Organization",
                handle=handle,
                year=year,
                venue="WHO IRIS",
                is_oa=True,
                abstract=strip_text(abstract),
            )
        )
    return out


def clinical_trials(query: str, page_size: int = 6) -> list[EvidenceRecord]:
    url = "https://clinicaltrials.gov/api/v2/studies?" + urlencode(
        {"query.term": query, "pageSize": str(page_size)}
    )
    try:
        data = get_json(url)
    except Exception:
        return []
    out: list[EvidenceRecord] = []
    for study in data.get("studies") or []:
        prot = study.get("protocolSection") or {}
        ident = prot.get("identificationModule") or {}
        status = prot.get("statusModule") or {}
        desc = prot.get("descriptionModule") or {}
        nct = ident.get("nctId")
        title = ident.get("briefTitle")
        if not nct or not title:
            continue
        year = _year((status.get("startDateStruct") or {}).get("date"))
        abstract = strip_text(desc.get("briefSummary") or ident.get("officialTitle") or "")
        out.append(
            EvidenceRecord(
                key=nct,
                title=strip_text(title),
                url=f"https://clinicaltrials.gov/study/{nct}",
                source_connector="clinicaltrials",
                source_family="trial_registry",
                issuing_body="ClinicalTrials.gov",
                nct_id=nct,
                year=year,
                venue="ClinicalTrials.gov",
                is_oa=True,
                abstract=abstract,
            )
        )
    return out


def official_document(
    *,
    key: str,
    title: str,
    url: str,
    year: int,
    body: str,
    family: str,
    abstract: str = "",
) -> EvidenceRecord:
    """Seed an allow-listed official URL. Inclusion still requires HTTP 200."""
    return EvidenceRecord(
        key=key,
        title=title,
        url=url,
        source_connector="official_url_seed",
        source_family=family,
        issuing_body=body,
        year=year,
        venue=body,
        is_oa=True,
        abstract=abstract or title,
        is_guideline=True,
    )


def hf_official_seeds() -> list[EvidenceRecord]:
    """Allow-listed official pages for HFrEF briefs. Inclusion still needs HTTP 200."""
    return [
        nice_guideline(
            "ng106",
            "Chronic heart failure in adults: diagnosis and management (NICE NG106)",
            2018,
        ),
        official_document(
            key="who:hearts",
            title="HEARTS technical package for cardiovascular disease management in primary health care",
            url="https://www.who.int/publications/i/item/hearts-technical-package",
            year=2020,
            body="World Health Organization",
            family="un_agency",
            abstract=(
                "WHO HEARTS package for hypertension and cardiovascular disease "
                "in primary care: protocols, medicines, team-based care, and systems."
            ),
        ),
        official_document(
            key="esc:hf-guidelines",
            title="ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure",
            url="https://www.escardio.org/Guidelines/Clinical-Practice-Guidelines/Acute-and-Chronic-Heart-Failure",
            year=2021,
            body="European Society of Cardiology",
            family="international_guideline",
            abstract=(
                "ESC clinical practice guidelines covering diagnosis and treatment "
                "of acute and chronic heart failure, including foundational therapy."
            ),
        ),
        official_document(
            key="who:cvd-factsheet",
            title="Cardiovascular diseases (CVDs) fact sheet",
            url="https://www.who.int/news-room/fact-sheets/detail/cardiovascular-diseases-(cvds)",
            year=2021,
            body="World Health Organization",
            family="un_agency",
            abstract=(
                "WHO fact sheet on the global burden of cardiovascular diseases, "
                "risk factors, prevention, and health-system response."
            ),
        ),
        official_document(
            key="who:ncd-gap",
            title="Global action plan for the prevention and control of noncommunicable diseases 2013-2020",
            url="https://www.who.int/publications/i/item/9789241506236",
            year=2013,
            body="World Health Organization",
            family="un_agency",
            abstract=(
                "WHO Global NCD Action Plan covering cardiovascular disease, "
                "risk-factor targets, and health-system response through 2020 and beyond."
            ),
        ),
        official_document(
            key="paho:hearts",
            title="HEARTS in the Americas",
            url="https://www.paho.org/en/hearts-americas",
            year=2021,
            body="PAHO / WHO Americas",
            family="un_agency",
            abstract=(
                "PAHO HEARTS in the Americas initiative to improve hypertension "
                "and cardiovascular disease management in primary care."
            ),
        ),
        official_document(
            key="whf:heart-failure",
            title="World Heart Federation — Heart Failure",
            url="https://world-heart-federation.org/what-we-do/heart-failure/",
            year=2023,
            body="World Heart Federation",
            family="ngo",
            abstract=(
                "World Heart Federation programme page on the global heart-failure "
                "burden and advocacy for better prevention, diagnosis, and care."
            ),
        ),
        official_document(
            key="who:ncd-factsheet",
            title="Noncommunicable diseases fact sheet",
            url="https://www.who.int/news-room/fact-sheets/detail/noncommunicable-diseases",
            year=2023,
            body="World Health Organization",
            family="un_agency",
            abstract=(
                "WHO fact sheet on the global burden of noncommunicable diseases, "
                "including cardiovascular disease, and the health-system response."
            ),
        ),
        official_document(
            key="who:hearts-iris",
            title="HEARTS technical package (WHO IRIS)",
            url="https://iris.who.int/handle/10665/333221",
            year=2020,
            body="World Health Organization",
            family="un_agency",
            abstract=(
                "WHO IRIS handle for the HEARTS technical package for cardiovascular "
                "disease management in primary health care."
            ),
        ),
        official_document(
            key="worldbank:ncd",
            title="Noncommunicable diseases — World Bank brief",
            url="https://www.worldbank.org/en/topic/health/brief/noncommunicable-diseases",
            year=2024,
            body="World Bank",
            family="un_agency",
            abstract=(
                "World Bank brief on noncommunicable diseases, including cardiovascular "
                "disease, as a development and health-system financing issue."
            ),
        ),
        official_document(
            key="who:cvd-topics",
            title="Cardiovascular diseases — WHO health topic",
            url="https://www.who.int/health-topics/cardiovascular-diseases",
            year=2024,
            body="World Health Organization",
            family="un_agency",
            abstract=(
                "WHO health-topic hub for cardiovascular diseases, linking HEARTS, "
                "hypertension, and NCD programme pages."
            ),
        ),
        official_document(
            key="who:ncd-department",
            title="WHO Department of Noncommunicable Diseases",
            url="https://www.who.int/teams/noncommunicable-diseases",
            year=2024,
            body="World Health Organization",
            family="un_agency",
            abstract="WHO NCD department page covering CVD, hypertension, and HEARTS delivery.",
        ),
    ]


def un_cvd_official_seeds() -> list[EvidenceRecord]:
    """Allow-listed UN-system CVD/NCD pages. Inclusion still needs HTTP 200."""
    return [
        official_document(
            key="un:sdg3",
            title="Sustainable Development Goal 3 — Good health and well-being",
            url="https://sdgs.un.org/goals/goal3",
            year=2015,
            body="United Nations DESA",
            family="un_agency",
            abstract=(
                "UN SDG 3 target page covering NCD mortality reduction, UHC, and "
                "access to essential medicines — the UN framing for CVD programmes."
            ),
        ),
        official_document(
            key="who:searo-cvd",
            title="Cardiovascular diseases — WHO South-East Asia",
            url="https://www.who.int/southeastasia/health-topics/cardiovascular-diseases",
            year=2023,
            body="WHO SEARO",
            family="un_agency",
            abstract=(
                "WHO South-East Asia regional page on the cardiovascular-disease "
                "burden and programme response, including HEARTS implementation."
            ),
        ),
        official_document(
            key="who:euro-cvd",
            title="Cardiovascular diseases — WHO Europe",
            url="https://www.who.int/europe/health-topics/cardiovascular-diseases",
            year=2023,
            body="WHO Europe",
            family="un_agency",
            abstract=(
                "WHO Europe health-topic page on cardiovascular diseases, prevention, "
                "and health-system action."
            ),
        ),
        official_document(
            key="who:afro-cvd",
            title="Cardiovascular diseases — WHO Regional Office for Africa",
            url="https://www.afro.who.int/health-topics/cardiovascular-diseases",
            year=2023,
            body="WHO AFRO",
            family="un_agency",
            abstract=(
                "WHO Africa regional page on cardiovascular diseases and the "
                "regional NCD response."
            ),
        ),
        official_document(
            key="who:searo-ncd",
            title="Noncommunicable diseases — WHO South-East Asia",
            url="https://www.who.int/southeastasia/health-topics/noncommunicable-diseases",
            year=2023,
            body="WHO SEARO",
            family="un_agency",
            abstract="WHO South-East Asia NCD programme page, including CVD.",
        ),
        official_document(
            key="who:euro-ncd",
            title="Noncommunicable diseases — WHO Europe",
            url="https://www.who.int/europe/health-topics/noncommunicable-diseases",
            year=2023,
            body="WHO Europe",
            family="un_agency",
            abstract="WHO Europe NCD health-topic page covering CVD and risk factors.",
        ),
        official_document(
            key="paho:ncd",
            title="Noncommunicable diseases — PAHO",
            url="https://www.paho.org/en/topics/noncommunicable-diseases",
            year=2023,
            body="PAHO / WHO Americas",
            family="un_agency",
            abstract="PAHO topic page on noncommunicable diseases in the Americas.",
        ),
        official_document(
            key="who:hypertension-team",
            title="WHO NCD department — Hypertension",
            url="https://www.who.int/teams/noncommunicable-diseases/hypertension",
            year=2023,
            body="World Health Organization",
            family="un_agency",
            abstract=(
                "WHO NCD department hypertension programme, the HEARTS delivery "
                "channel for blood-pressure and CVD risk management."
            ),
        ),
        official_document(
            key="who:hypertension-factsheet",
            title="Hypertension fact sheet",
            url="https://www.who.int/news-room/fact-sheets/detail/hypertension",
            year=2023,
            body="World Health Organization",
            family="un_agency",
            abstract=(
                "WHO fact sheet on the global burden of hypertension and the "
                "health-system response, including HEARTS."
            ),
        ),
        official_document(
            key="who:hypertension-guideline-2021",
            title="Guideline for the pharmacological treatment of hypertension in adults",
            url="https://www.who.int/publications/i/item/9789240033986",
            year=2021,
            body="World Health Organization",
            family="international_guideline",
            abstract=(
                "WHO guideline on pharmacological treatment of hypertension in "
                "adults, the medicines pillar that HEARTS implements in primary care."
            ),
        ),
        official_document(
            key="who:hearts-package-pub",
            title="HEARTS: Technical package for cardiovascular disease management in primary health care",
            url="https://www.who.int/publications/i/item/9789241511377",
            year=2018,
            body="World Health Organization",
            family="un_agency",
            abstract=(
                "WHO HEARTS technical package publication record for CVD management "
                "in primary health care."
            ),
        ),
        official_document(
            key="who:hearts-teambased-iris",
            title="Technical package for cardiovascular disease management in primary health care: team-based care",
            url="https://iris.who.int/handle/10665/260424",
            year=2018,
            body="World Health Organization",
            family="un_agency",
            abstract=(
                "WHO IRIS handle for the HEARTS team-based care module — how primary "
                "care teams deliver CVD and hypertension protocols."
            ),
        ),
        official_document(
            key="un:sdg3-unorg",
            title="Good health and well-being — United Nations Sustainable Development Goal 3",
            url="https://www.un.org/sustainabledevelopment/health/",
            year=2015,
            body="United Nations",
            family="un_agency",
            abstract=(
                "UN SDG 3 landing page on NCD mortality reduction, UHC, and access "
                "to essential medicines."
            ),
        ),
        official_document(
            key="unaids:home",
            title="UNAIDS — Joint United Nations Programme on HIV/AIDS",
            url="https://www.unaids.org/en",
            year=2024,
            body="UNAIDS",
            family="un_agency",
            abstract="UNAIDS official programme page; UN-system health mandate (HIV/AIDS).",
        ),
        official_document(
            key="fao:nutrition",
            title="FAO — Nutrition",
            url="https://www.fao.org/nutrition/en",
            year=2024,
            body="Food and Agriculture Organization",
            family="un_agency",
            abstract="FAO nutrition programme page, the UN food-system counterpart to NCD diets.",
        ),
        official_document(
            key="ilo:osh",
            title="ILO — Safety and health at work",
            url="https://www.ilo.org/topics-and-sectors/safety-and-health-work",
            year=2024,
            body="International Labour Organization",
            family="un_agency",
            abstract="ILO occupational safety and health topic page (UN labour agency).",
        ),
        official_document(
            key="unesco:health-ed",
            title="UNESCO — Health education",
            url="https://www.unesco.org/en/health-education",
            year=2024,
            body="UNESCO",
            family="un_agency",
            abstract="UNESCO health-education topic page (UN education agency).",
        ),
        official_document(
            key="wfp:nutrition",
            title="WFP — Ending malnutrition",
            url="https://www.wfp.org/ending-malnutrition",
            year=2024,
            body="World Food Programme",
            family="un_agency",
            abstract="World Food Programme malnutrition page (UN food-assistance agency).",
        ),
        official_document(
            key="unhabitat:home",
            title="UN-Habitat",
            url="https://unhabitat.org/",
            year=2024,
            body="UN-Habitat",
            family="un_agency",
            abstract="UN-Habitat official site — urban health and liveable cities mandate.",
        ),
        official_document(
            key="undrr:home",
            title="UNDRR — United Nations Office for Disaster Risk Reduction",
            url="https://www.undrr.org/",
            year=2024,
            body="UNDRR",
            family="un_agency",
            abstract="UNDRR official site, including disaster-risk and health-system resilience.",
        ),
        official_document(
            key="unodc:home",
            title="UNODC — United Nations Office on Drugs and Crime",
            url="https://www.unodc.org/",
            year=2024,
            body="UNODC",
            family="un_agency",
            abstract="UNODC official site (UN-system health-adjacent mandate: drugs and crime).",
        ),
        official_document(
            key="unfpa:home",
            title="UNFPA — United Nations Population Fund",
            url="https://www.unfpa.org/",
            year=2024,
            body="UNFPA",
            family="un_agency",
            abstract="UNFPA official site — UN population and reproductive-health mandate.",
        ),
        official_document(
            key="unwomen:home",
            title="UN Women",
            url="https://www.unwomen.org/en",
            year=2024,
            body="UN Women",
            family="un_agency",
            abstract="UN Women official site — gender equality and health-related mandate.",
        ),
        official_document(
            key="undesa:home",
            title="UN Department of Economic and Social Affairs",
            url="https://www.un.org/development/desa/en/",
            year=2024,
            body="United Nations DESA",
            family="un_agency",
            abstract="UN DESA portal hosting SDG follow-up, including SDG 3 health targets.",
        ),
        official_document(
            key="who:emro-ncd",
            title="Noncommunicable diseases — WHO Eastern Mediterranean",
            url="https://www.emro.who.int/noncommunicable-diseases/index.html",
            year=2023,
            body="WHO EMRO",
            family="un_agency",
            abstract=(
                "WHO Eastern Mediterranean NCD programme page, including the regional "
                "cardiovascular-disease response."
            ),
        ),
        official_document(
            key="who:wpro-cvd",
            title="Cardiovascular diseases — WHO Western Pacific",
            url="https://www.who.int/westernpacific/health-topics/cardiovascular-diseases",
            year=2023,
            body="WHO Western Pacific",
            family="un_agency",
            abstract="WHO Western Pacific cardiovascular-disease health-topic page.",
        ),
        official_document(
            key="who:euro-hypertension",
            title="Hypertension — WHO Europe",
            url="https://www.who.int/europe/health-topics/hypertension",
            year=2023,
            body="WHO Europe",
            family="un_agency",
            abstract="WHO Europe hypertension health-topic page, the HEARTS risk-factor counterpart.",
        ),
        official_document(
            key="who:ncd-surveillance",
            title="WHO NCD department — Surveillance, monitoring and reporting",
            url="https://www.who.int/teams/noncommunicable-diseases/surveillance",
            year=2024,
            body="World Health Organization",
            family="un_agency",
            abstract="WHO NCD surveillance page for global CVD/NCD monitoring frameworks.",
        ),
        official_document(
            key="acc:guidelines",
            title="ACC Guidelines and Clinical Documents",
            url="https://www.acc.org/Guidelines",
            year=2024,
            body="American College of Cardiology",
            family="international_guideline",
            abstract="American College of Cardiology clinical guideline and consensus-document hub.",
        ),
        official_document(
            key="kdigo:guidelines",
            title="KDIGO Clinical Practice Guidelines",
            url="https://kdigo.org/guidelines/",
            year=2024,
            body="KDIGO",
            family="international_guideline",
            abstract=(
                "KDIGO international kidney-disease guidelines, including CKD–CVD overlap "
                "relevant to heart-failure comorbidity."
            ),
        ),
    ]


def india_official_seeds() -> list[EvidenceRecord]:
    """National India health-system pages. Inclusion still needs HTTP 200."""
    return [
        official_document(
            key="india:mohfw",
            title="Ministry of Health and Family Welfare, Government of India",
            url="https://www.mohfw.gov.in/",
            year=2024,
            body="Ministry of Health and Family Welfare (India)",
            family="national_guideline",
            abstract=(
                "Official portal of India's health ministry, the national authority "
                "for NCD and cardiovascular programme guidance."
            ),
        ),
        official_document(
            key="india:nhm",
            title="National Health Mission, Government of India",
            url="https://nhm.gov.in/",
            year=2024,
            body="National Health Mission (India)",
            family="national_guideline",
            abstract=(
                "National Health Mission portal hosting NPCDCS and other national "
                "NCD / cardiovascular programme materials."
            ),
        ),
        official_document(
            key="india:icmr",
            title="Indian Council of Medical Research",
            url="https://www.icmr.gov.in/",
            year=2024,
            body="Indian Council of Medical Research",
            family="national_guideline",
            abstract="ICMR official portal — India's national biomedical research and guidance body.",
        ),
        official_document(
            key="india:npcdcs",
            title="National Programme for Prevention and Control of NCDs (NPCDCS) — NHM",
            url="https://nhm.gov.in/index1.php?lang=1&level=2&sublinkid=1048&lid=611",
            year=2024,
            body="National Health Mission (India)",
            family="national_guideline",
            abstract=(
                "NHM NPCDCS programme page for national NCD and cardiovascular "
                "prevention and control in India."
            ),
        ),
    ]


def official_seeds_for_brief(brief: dict) -> list[EvidenceRecord]:
    """Topic-matched official URL seeds. Validation still requires HTTP 200."""
    blob = " ".join(
        str(brief.get(k) or "")
        for k in ("therapy_area", "indication", "product", "brand", "market")
    ).lower()
    rows: list[EvidenceRecord] = []
    if any(
        tok in blob
        for tok in ("heart failure", "hfref", "hfpef", "cardiology", "cardiovascular")
    ):
        rows += hf_official_seeds()
        rows += un_cvd_official_seeds()
    if "india" in blob:
        rows += india_official_seeds()
    return rows


def nice_guideline(path: str, title: str, year: int) -> EvidenceRecord:
    url = f"https://www.nice.org.uk/guidance/{path}"
    return EvidenceRecord(
        key=f"nice:{path}",
        title=title,
        url=url,
        source_connector="nice",
        source_family="national_guideline",
        issuing_body="NICE (UK)",
        year=year,
        venue="NICE",
        is_oa=True,
        abstract=title,
        is_guideline=True,
    )


def classify_guideline_family(record: EvidenceRecord) -> str:
    blob = f"{record.title} {record.issuing_body} {record.venue or ''}".lower()
    national_markers = (
        "nice",
        "india",
        "csi",
        "icmr",
        "aha/acc",
        "acc/aha",
        "nhs",
        "ministry",
        "national institute",
    )
    international_markers = (
        "esc ",
        "esc guideline",
        "who ",
        "world health",
        "ish ",
        "universal definition",
        "heart failure association",
    )
    if any(m in blob for m in international_markers) or record.source_family == "un_agency":
        if "guideline" in blob or "technical package" in blob or "consensus" in blob:
            return "international_guideline"
    if any(m in blob for m in national_markers) and (
        "guideline" in blob or "nice" in blob or "position" in blob
    ):
        return "national_guideline"
    if "guideline" in blob:
        return "international_guideline"
    return record.source_family

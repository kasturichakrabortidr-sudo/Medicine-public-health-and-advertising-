"""Live connectors for scholarly, guideline, UN, and trial sources."""

from __future__ import annotations

from urllib.parse import urlencode

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
    ("I90810661", "World Heart Federation", "ngo"),
]


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


def openalex_un_ngo(search: str, page_size: int = 8) -> list[EvidenceRecord]:
    ids = "|".join(i for i, _, _ in UN_INSTITUTIONS)
    family_by_id = {i: fam for i, _, fam in UN_INSTITUTIONS}
    body_by_id = {i: name for i, name, _ in UN_INSTITUTIONS}
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
        family = "un_agency"
        body = "UN system"
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
                source_connector="openalex_un",
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

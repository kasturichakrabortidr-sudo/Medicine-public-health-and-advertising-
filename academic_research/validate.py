"""Registry validation — refuse any record that cannot be resolved."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

from .extract import strip_text
from .http_client import get_json, head_ok
from .models import EvidenceRecord, Validation

OFFICIAL_HOSTS = (
    "who.int",
    "iris.who.int",
    "un.org",
    "unicef.org",
    "unaids.org",
    "undp.org",
    "unhcr.org",
    "unfpa.org",
    "unep.org",
    "unwomen.org",
    "unhabitat.org",
    "undrr.org",
    "itu.int",
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "crossref.org",
    "unesco.org",
    "ilo.org",
    "fao.org",
    "wfp.org",
    "iom.int",
    "unodc.org",
    "worldbank.org",
    "paho.org",
    "cdc.gov",
    "nih.gov",
    "nice.org.uk",
    "escardio.org",
    "heart.org",
    "world-heart-federation.org",
    "clinicaltrials.gov",
    "gov.in",
    "mohfw.gov.in",
    "doi.org",
    "ahajournals.org",
    "acc.org",
    "nejm.org",
    "thelancet.com",
    "bmj.com",
    "nature.com",
    "springer.com",
    "wiley.com",
    "oup.com",
)


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = doi.strip()
    value = re_sub_doi(value)
    return value.lower() if value else None


def re_sub_doi(value: str) -> str:
    value = value.replace("https://doi.org/", "").replace("http://doi.org/", "")
    value = value.replace("doi:", "").strip().strip("/")
    return value


def doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}"


def validate_record(record: EvidenceRecord) -> EvidenceRecord | None:
    """Return a copy annotated with Validation, or None if it cannot be proven."""
    doi = normalize_doi(record.doi)
    if doi:
        try:
            data = get_json(f"https://api.crossref.org/works/{quote(doi, safe='/')}")
            msg = data.get("message") or {}
            title = " ".join(msg.get("title") or []) or record.title
            year = None
            parts = (msg.get("issued") or {}).get("date-parts") or [[]]
            if parts and parts[0]:
                year = parts[0][0]
            authors = []
            for a in (msg.get("author") or [])[:12]:
                given = a.get("given") or ""
                family = a.get("family") or ""
                name = f"{given} {family}".strip() or a.get("name")
                if name:
                    authors.append(name)
            venue = None
            ct = msg.get("container-title") or []
            if ct:
                venue = ct[0]
            record.doi = doi
            record.title = strip_text(title or record.title)
            record.year = year or record.year
            if authors:
                record.authors = authors
            record.venue = venue or record.venue
            record.url = doi_url(doi)
            record.validation = Validation(
                status="verified",
                via="crossref",
                identifier=doi,
                retrieved_at=utcnow(),
                canonical_url=doi_url(doi),
            )
            return record
        except Exception:
            # Fall through to PMID / URL validators
            pass

    if record.pmid:
        try:
            from urllib.parse import urlencode

            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode(
                {
                    "query": f"EXT_ID:{record.pmid} AND SRC:MED",
                    "format": "json",
                    "pageSize": 1,
                    "resultType": "core",
                }
            )
            data = get_json(url)
            hits = (data.get("resultList") or {}).get("result") or []
            if hits:
                hit = hits[0]
                record.title = strip_text(hit.get("title") or record.title)
                record.year = _safe_year(hit.get("pubYear")) or record.year
                if hit.get("doi"):
                    record.doi = normalize_doi(hit.get("doi"))
                    record.url = doi_url(record.doi) if record.doi else record.url
                record.validation = Validation(
                    status="verified",
                    via="europe_pmc",
                    identifier=str(record.pmid),
                    retrieved_at=utcnow(),
                    canonical_url=record.url
                    or f"https://pubmed.ncbi.nlm.nih.gov/{record.pmid}/",
                )
                if not record.url:
                    record.url = f"https://pubmed.ncbi.nlm.nih.gov/{record.pmid}/"
                return record
        except Exception:
            pass

    if record.nct_id:
        nct = record.nct_id.upper()
        try:
            data = get_json(
                "https://clinicaltrials.gov/api/v2/studies/"
                + nct
                + "?fields=NCTId,BriefTitle,OfficialTitle"
            )
            prot = (data.get("protocolSection") or {}).get("identificationModule") or {}
            title = prot.get("briefTitle") or prot.get("officialTitle")
            if title:
                record.title = title
            record.url = f"https://clinicaltrials.gov/study/{nct}"
            record.validation = Validation(
                status="verified",
                via="clinicaltrials.gov",
                identifier=nct,
                retrieved_at=utcnow(),
                canonical_url=record.url,
            )
            return record
        except Exception:
            pass

    if record.url and _allowlisted(record.url) and head_ok(record.url):
        record.validation = Validation(
            status="verified",
            via="official_url",
            identifier=record.url,
            retrieved_at=utcnow(),
            canonical_url=record.url,
        )
        return record

    return None


def _allowlisted(url: str) -> bool:
    host = url.lower()
    return any(h in host for h in OFFICIAL_HOSTS)


def _safe_year(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

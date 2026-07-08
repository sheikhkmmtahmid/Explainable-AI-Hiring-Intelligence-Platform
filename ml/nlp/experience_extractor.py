"""
Extracts structured work-history entries (job title, company, start/end
dates) from raw CV text, using a date-range regex plus spaCy's ORG entity
recognition to help separate "job title" from "company" on each entry line.

This is heuristic, not a trained model -- real resumes vary enormously in
layout. It is designed to do well on the common "Title — Company (Date -
Date)" style (which is what most resume templates, including this
project's own synthetic CVs, actually use), and to fail safely (return
nothing for that entry) rather than guess wrongly when a line doesn't
match a recognisable pattern.
"""
import logging
import re
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

EXPERIENCE_HEADERS = [
    "experience", "work experience", "professional experience",
    "employment history", "work history",
]
NEXT_SECTION_HEADERS = [
    "education", "skills", "projects", "certifications", "certification",
    "summary", "professional summary", "references", "publications",
    "awards", "languages",
]

DATE_TOKEN = r"(?:[A-Za-z]{3,9}\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4})"
DATE_RANGE_RE = re.compile(
    rf"(?P<start>{DATE_TOKEN})\s*(?:[-–—]|\bto\b)\s*(?P<end>{DATE_TOKEN}|Present|Current|Now)",
    re.IGNORECASE,
)


def _parse_date_token(token: str) -> Optional[date]:
    token = token.strip()
    if re.fullmatch(r"\d{1,2}/\d{4}", token):
        month, year = token.split("/")
        try:
            return date(int(year), int(month), 1)
        except ValueError:
            return None
    if re.fullmatch(r"\d{4}", token):
        return date(int(token), 1, 1)
    try:
        from dateutil import parser as dateutil_parser
        dt = dateutil_parser.parse(token, default=date(1900, 1, 1))
        return date(dt.year, dt.month, 1)
    except (ValueError, OverflowError, TypeError):
        return None


def _extract_experience_section(text: str) -> str:
    """Return just the EXPERIENCE section of the CV, or the whole text if
    no recognisable section header is found."""
    lines = text.splitlines()
    start_idx = None
    end_idx = len(lines)

    for i, line in enumerate(lines):
        stripped = line.strip().strip(":").lower()
        if stripped in EXPERIENCE_HEADERS:
            start_idx = i + 1
            break

    if start_idx is None:
        logger.debug("No explicit EXPERIENCE header found; scanning whole text")
        return text

    for j in range(start_idx, len(lines)):
        stripped = lines[j].strip().strip(":").lower()
        if stripped in NEXT_SECTION_HEADERS:
            end_idx = j
            break

    return "\n".join(lines[start_idx:end_idx])


def _split_company_location(company: str, nlp_doc=None) -> tuple[str, str]:
    """If `company` looks like "Company, City" (common in real resumes),
    split the trailing city out as a location using spaCy's GPE entity."""
    if "," not in company or nlp_doc is None:
        return company, ""

    head, _, tail = company.rpartition(",")
    tail = tail.strip()
    for ent in nlp_doc.ents:
        if ent.label_ == "GPE" and ent.text.strip() == tail:
            return head.strip(), tail
    return company, ""


def _split_title_company(header_line: str, nlp_doc=None) -> tuple[str, str, str]:
    """Best-effort split of a job-entry header line (with the date range
    already removed) into (job_title, company, location)."""
    line = header_line.strip(" -–—,|")
    if not line:
        return "", "", ""

    for sep in ("—", "–", "|", " - ", ","):
        if sep in line:
            parts = [p.strip() for p in line.split(sep, 1)]
            if len(parts) == 2 and parts[0] and parts[1]:
                company, location = _split_company_location(parts[1], nlp_doc)
                return parts[0], company, location

    # No clean separator -- fall back to spaCy ORG entity as the company
    if nlp_doc is not None:
        for ent in nlp_doc.ents:
            if ent.label_ == "ORG" and ent.text.strip() in line:
                title = line.replace(ent.text, "").strip(" -–—,|")
                return (title or line), ent.text.strip(), ""

    return line, "", ""


def extract_experience_entries(text: str) -> list[dict]:
    """
    Return a list of {job_title, company, start_date, end_date, is_current,
    description} dicts parsed from the CV's experience section.

    Entries with a start_date but no parseable end_date are skipped rather
    than guessed -- an experience entry with a wrong date range is worse
    for downstream years-of-experience math than simply not extracting it.
    """
    section = _extract_experience_section(text)
    if not section.strip():
        return []

    from .spacy_loader import get_nlp
    nlp = get_nlp()

    lines = section.splitlines()
    header_idxs = [i for i, line in enumerate(lines) if DATE_RANGE_RE.search(line)]
    if not header_idxs:
        return []

    entries = []
    for pos, idx in enumerate(header_idxs):
        line = lines[idx]
        match = DATE_RANGE_RE.search(line)
        if not match:
            continue

        start_date = _parse_date_token(match.group("start"))
        end_token = match.group("end")
        is_current = end_token.strip().lower() in ("present", "current", "now")
        end_date = None if is_current else _parse_date_token(end_token)

        if start_date is None or (end_date is None and not is_current):
            logger.debug("Skipping unparseable date range: %r", line)
            continue

        header_text = line[:match.start()] + line[match.end():]
        header_text = re.sub(r"[()]", "", header_text).strip()
        doc = nlp(header_text) if header_text else None
        job_title, company, location = _split_title_company(header_text, doc)

        next_header_idx = header_idxs[pos + 1] if pos + 1 < len(header_idxs) else len(lines)
        description = "\n".join(
            l.strip() for l in lines[idx + 1:next_header_idx] if l.strip()
        )

        entries.append({
            "job_title": job_title or "Unknown Role",
            "company": company,
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "is_current": is_current,
            "description": description,
        })

    return entries

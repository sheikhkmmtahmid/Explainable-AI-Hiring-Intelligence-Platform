"""CV and job description parsing using spaCy NER + regex heuristics."""
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SKILL_PATTERNS = [
    "python", "java", "javascript", "typescript", "react", "django", "flask",
    "fastapi", "node.js", "sql", "postgresql", "mysql", "mongodb", "redis",
    "docker", "kubernetes", "aws", "gcp", "azure", "machine learning", "deep learning",
    "pytorch", "tensorflow", "scikit-learn", "nlp", "computer vision", "data analysis",
    "pandas", "numpy", "spark", "kafka", "git", "ci/cd", "agile", "scrum",
]


def extract_text_from_file(file_path: str) -> str:
    """Extract raw text from PDF, DOCX, or TXT file."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    if ext == ".pdf":
        try:
            import pdfminer.high_level as pdfminer
            return pdfminer.extract_text(file_path)
        except ImportError:
            logger.warning("pdfminer not available, falling back to empty text")
            return ""

    if ext in (".docx", ".doc"):
        try:
            import docx
            doc = docx.Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            logger.warning("python-docx not available, falling back to empty text")
            return ""

    logger.warning("Unsupported file extension: %s", ext)
    return ""


def extract_email(text: str) -> Optional[str]:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    match = re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text)
    return match.group(0).strip() if match else None


def extract_skills_from_text(text: str) -> list[dict]:
    """Simple pattern-based skill extractor. Will be augmented by NER in ml layer."""
    text_lower = text.lower()
    found = []
    for skill in SKILL_PATTERNS:
        if skill in text_lower:
            found.append({"skill_name": skill, "category": "technical"})
    return found


def extract_years_of_experience(text: str) -> float:
    """Heuristic: look for patterns like '5 years of experience'."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?experience", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 0.0


def parse_cv_text(raw_text: str) -> dict:
    """Return structured data extracted from raw CV text."""
    return {
        "email": extract_email(raw_text),
        "phone": extract_phone(raw_text),
        "skills": extract_skills_from_text(raw_text),
        "years_of_experience": extract_years_of_experience(raw_text),
    }

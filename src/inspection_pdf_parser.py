from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

from .data_models import TABLE_SCHEMAS


AUTO_EXTRACT_REMARK = "Auto extracted from Inspection Standard PDF. Need human confirmation."

DIAMETER_CHARS = "ØøΦφ⌀"
NUMBER_PATTERN = r"\d+(?:\.\d+)?"
SPEC_TEXT_PATTERN = re.compile(
    rf"""
    (?P<spec>
        [3]?\s*-\s*[{DIAMETER_CHARS}]?\s*{NUMBER_PATTERN}\s*(?:±|\+/-)\s*{NUMBER_PATTERN}
        |[{DIAMETER_CHARS}]?\s*{NUMBER_PATTERN}\s*\+\s*{NUMBER_PATTERN}\s*/\s*-\s*{NUMBER_PATTERN}
        |(?:MAX|MIN|max|min)\s+{NUMBER_PATTERN}
        |[{DIAMETER_CHARS}]\s*{NUMBER_PATTERN}(?:\s*\|\s*[A-Z])*
        |{NUMBER_PATTERN}\s*(?:±|\+/-)\s*{NUMBER_PATTERN}
        |{NUMBER_PATTERN}
    )
    """,
    re.VERBOSE,
)
DIMENSION_ROW_PATTERN = re.compile(
    rf"""
    (?P<drawing_no>1\s*-\s*(?P<no>\d{{1,2}}))
    (?P<context>.{{0,260}}?)
    Dimension
    (?P<after>.{{0,260}}?)
    (?P<spec>
        [3]?\s*-\s*[{DIAMETER_CHARS}]?\s*{NUMBER_PATTERN}\s*(?:±|\+/-)\s*{NUMBER_PATTERN}
        |[{DIAMETER_CHARS}]?\s*{NUMBER_PATTERN}\s*\+\s*{NUMBER_PATTERN}\s*/\s*-\s*{NUMBER_PATTERN}
        |(?:MAX|MIN|max|min)\s+{NUMBER_PATTERN}
        |[{DIAMETER_CHARS}]\s*{NUMBER_PATTERN}(?:\s*\|\s*[A-Z])*
        |{NUMBER_PATTERN}\s*(?:±|\+/-)\s*{NUMBER_PATTERN}
        |{NUMBER_PATTERN}
    )
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)
SAMPLE_QTY_PATTERN = re.compile(r"\b(?P<qty>\d+\s*EA(?:\s*/\s*Lot)?)\b", re.IGNORECASE)


def _round(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _decimal(value: str) -> Decimal:
    return Decimal(value.strip())


def _clean_spec(spec_text: str) -> str:
    text = str(spec_text or "").strip()
    text = text.replace("＋", "+").replace("－", "-").replace("–", "-")
    text = re.sub(r"\s+", "", text)
    return text


def _strip_prefix_and_diameter(spec_text: str) -> str:
    text = _clean_spec(spec_text)
    text = re.sub(r"^\d+\-", "", text)
    return text.lstrip(DIAMETER_CHARS)


def method_tool_for_no(no: int) -> tuple[str, str]:
    if 1 <= no <= 4:
        return "Distance", "V/C"
    if 5 <= no <= 7:
        return "Position", "GO-NO JIG"
    if 8 <= no <= 10:
        return "Diameter", "V/C"
    if 11 <= no <= 13:
        return "Position", "GO-NO JIG"
    if no == 14:
        return "Diameter", "V/C"
    if no == 15:
        return "Position", "GO-NO JIG"
    if no == 16:
        return "Flatness", "CMM"
    if 17 <= no <= 20:
        return "Distance", "V/C"
    if no == 21:
        return "Distance", "JIG"
    if 22 <= no <= 24:
        return "Distance", "GO-NO JIG"
    return "", ""


def parse_dimension_spec(spec_text: str, inspection_no: int | None = None) -> dict[str, object]:
    original = str(spec_text or "").strip()
    text = _clean_spec(original)
    lower_text = text.lower()
    symbol_type = "Dimension"

    if not text:
        return {"nominal": "", "upper": "", "lower": "", "unit": "mm", "symbol_type": symbol_type}

    if inspection_no == 16:
        symbol_type = "Flatness"
    elif text[0] in DIAMETER_CHARS:
        symbol_type = "Diameter" if ("±" in text or "+/-" in text or "+" in text) else "Position"

    asymmetric = re.search(rf"^[{DIAMETER_CHARS}]?(?P<nom>{NUMBER_PATTERN})\+(?P<plus>{NUMBER_PATTERN})/(?P<minus>-?{NUMBER_PATTERN})$", text)
    if asymmetric:
        nominal = _decimal(asymmetric.group("nom"))
        plus = _decimal(asymmetric.group("plus"))
        minus = _decimal(asymmetric.group("minus").lstrip("-"))
        return {
            "nominal": _round(nominal),
            "upper": _round(nominal + plus),
            "lower": _round(nominal - minus),
            "unit": "mm",
            "symbol_type": symbol_type,
        }

    if lower_text.startswith("min"):
        nominal = _decimal(re.search(NUMBER_PATTERN, text).group(0))
        return {"nominal": _round(nominal), "upper": "", "lower": _round(nominal), "unit": "mm", "symbol_type": "Minimum"}

    if lower_text.startswith("max"):
        nominal = _decimal(re.search(NUMBER_PATTERN, text).group(0))
        return {"nominal": _round(nominal), "upper": _round(nominal), "lower": "", "unit": "mm", "symbol_type": "Maximum"}

    normalized = _strip_prefix_and_diameter(text)
    if "±" in normalized or "+/-" in normalized:
        parts = re.split(r"±|\+/-", normalized)
        nominal = _decimal(parts[0])
        tolerance = _decimal(parts[1])
        return {
            "nominal": _round(nominal),
            "upper": _round(nominal + tolerance),
            "lower": _round(nominal - tolerance),
            "unit": "mm",
            "symbol_type": symbol_type,
        }

    match = re.search(NUMBER_PATTERN, normalized)
    if not match:
        return {"nominal": "", "upper": "", "lower": "", "unit": "mm", "symbol_type": symbol_type}
    nominal = _decimal(match.group(0))
    upper = _round(nominal)
    return {"nominal": upper, "upper": upper, "lower": "", "unit": "mm", "symbol_type": symbol_type}


def extract_sample_qty(text: str) -> str:
    match = SAMPLE_QTY_PATTERN.search(str(text or ""))
    return re.sub(r"\s+", "", match.group("qty")) if match else ""


def source_sentence(text: str, start: int, end: int) -> str:
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    start = max(0, start - 80)
    end = min(len(normalized), end + 80)
    return normalized[start:end].strip()


def extract_pdf_text(pdf_path: str | Path) -> list[dict[str, object]]:
    import fitz

    path = Path(pdf_path)
    rows: list[dict[str, object]] = []
    with fitz.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            rows.append(
                {
                    "Source File": str(path),
                    "Page": page_number,
                    "Extracted Text": text,
                    "OCR Used": "N" if text else "Y 후보",
                    "Confidence": "1.0" if text else "",
                    "Confirmed": "N",
                    "Remark": "텍스트 추출 결과는 Draft이며 사람이 확인해야 합니다.",
                }
            )
    return rows


def build_inspection_row(no: int, drawing_no: str, spec_text: str, page: object, source_text: str, sample_qty: str = "") -> dict[str, object]:
    parsed = parse_dimension_spec(spec_text, no)
    method, tool = method_tool_for_no(no)
    return {
        "No.": no,
        "Drawing No.": drawing_no.replace(" ", ""),
        "Inspection Point": f"Dimension {no:02d}",
        "Item": "Dimension",
        "Symbol": f"DIM_{no:02d}",
        "View": "",
        "Datum": "",
        "Nominal": parsed["nominal"],
        "Upper": parsed["upper"],
        "Lower": parsed["lower"],
        "Unit": parsed["unit"],
        "Method": method,
        "Tool": tool,
        "Sample Qty": sample_qty,
        "Criticality": "Major",
        "Related Risk": "",
        "Source PDF Page": page,
        "Source Text": source_text,
        "Confirmed": "N",
        "Remark": AUTO_EXTRACT_REMARK,
    }


def parse_inspection_standard_dimension_rows(raw_ocr_df: pd.DataFrame) -> pd.DataFrame:
    rows_by_no: dict[int, dict[str, object]] = {}
    for _, raw in raw_ocr_df.iterrows():
        page = raw.get("Page", "")
        text = str(raw.get("Extracted Text", ""))
        sample_qty = extract_sample_qty(text)
        normalized_text = re.sub(r"\s+", " ", text)
        for match in DIMENSION_ROW_PATTERN.finditer(normalized_text):
            no = int(match.group("no"))
            if not 1 <= no <= 24 or no in rows_by_no:
                continue
            source_text = source_sentence(normalized_text, match.start(), match.end())
            rows_by_no[no] = build_inspection_row(
                no=no,
                drawing_no=match.group("drawing_no"),
                spec_text=match.group("spec"),
                page=page,
                source_text=source_text,
                sample_qty=sample_qty,
            )
    return pd.DataFrame([rows_by_no[no] for no in sorted(rows_by_no)], columns=TABLE_SCHEMAS["inspection_standard_db"])


def parse_dimension_candidates(raw_ocr_df: pd.DataFrame) -> pd.DataFrame:
    dimension_rows = parse_inspection_standard_dimension_rows(raw_ocr_df)
    if not dimension_rows.empty:
        return dimension_rows

    rows: list[dict[str, object]] = []
    for _, raw in raw_ocr_df.iterrows():
        page = raw.get("Page", "")
        text = str(raw.get("Extracted Text", ""))
        sample_qty = extract_sample_qty(text)
        for match in SPEC_TEXT_PATTERN.finditer(text):
            spec_text = match.group("spec")
            source_text = source_sentence(text, match.start(), match.end())
            no = len(rows) + 1
            rows.append(build_inspection_row(no, "", spec_text, page, source_text, sample_qty))
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["inspection_standard_db"])


def parse_inspection_pdf(pdf_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_df = pd.DataFrame(extract_pdf_text(pdf_path), columns=TABLE_SCHEMAS["raw_ocr_text"])
    draft_df = parse_dimension_candidates(raw_df)
    return raw_df, draft_df

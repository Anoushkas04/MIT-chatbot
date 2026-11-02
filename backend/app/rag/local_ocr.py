import hashlib
import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image


OCR_CACHE_VERSION = 1
OCR_LAYOUT_VERSION = 2
MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "sept": 9,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


@lru_cache
def get_ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise RuntimeError(
            "Local OCR is enabled but RapidOCR is not installed. "
            "Install the backend requirements first."
        ) from exc
    return RapidOCR()


def extract_page(
    image_path: Path,
    page: dict,
    cache_dir: Path,
    *,
    min_confidence: float = 0.45,
    max_image_edge: int = 2600,
    force: bool = False,
) -> dict:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{page['id']}.json"
    fingerprint = _fingerprint(image_path, min_confidence, max_image_edge)
    layout_fingerprint = _layout_fingerprint(page)
    cached = None
    if cache_path.is_file() and not force:
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if (
                cached.get("fingerprint") == fingerprint
                and cached.get("layout_fingerprint") == layout_fingerprint
            ):
                return cached
        except (OSError, json.JSONDecodeError):
            cached = None

    can_reprocess = (
        cached
        and cached.get("fingerprint") == fingerprint
        and isinstance(cached.get("lines"), list)
        and len(cached.get("image_size", [])) == 2
    )
    if can_reprocess:
        original_size = tuple(cached["image_size"])
        lines = cached["lines"]
        elapsed = cached.get("elapsed")
        engine = cached.get("engine", "rapidocr_onnxruntime")
    else:
        image = Image.open(image_path).convert("RGB")
        original_size = image.size
        image = _resize_image(image, max_image_edge)
        result, elapsed = get_ocr_engine()(np.asarray(image))
        scale_x = original_size[0] / image.size[0]
        scale_y = original_size[1] / image.size[1]
        lines = []
        for item in result or []:
            box, text, confidence = item
            clean = " ".join(str(text).split())
            score = float(confidence)
            if not clean or score < min_confidence:
                continue
            scaled_box = [
                [round(float(point[0]) * scale_x, 2), round(float(point[1]) * scale_y, 2)]
                for point in box
            ]
            lines.append({"box": scaled_box, "text": clean, "confidence": round(score, 4)})
        engine = "rapidocr_onnxruntime"

    source = str(page.get("source", ""))
    if "calendar" in source.lower():
        segments = _calendar_segments(lines, original_size, page)
        events = _calendar_events(segments, page)
    else:
        segments = [{
            "title": f"{source} page {page.get('page_number')}",
            "text": _layout_text(lines),
            "metadata": {},
        }]
        events = []
    text = "\n\n".join(segment["text"] for segment in segments if segment.get("text")).strip()
    payload = {
        "version": OCR_CACHE_VERSION,
        "layout_version": OCR_LAYOUT_VERSION,
        "fingerprint": fingerprint,
        "layout_fingerprint": layout_fingerprint,
        "page_id": page["id"],
        "document_id": page.get("document_id"),
        "source": source,
        "page_number": page.get("page_number"),
        "image_size": list(original_size),
        "engine": engine,
        "elapsed": elapsed,
        "line_count": len(lines),
        "average_confidence": round(
            sum(line["confidence"] for line in lines) / len(lines), 4
        ) if lines else 0.0,
        "lines": lines,
        "segments": segments,
        "calendar_events": events,
        "text": text,
    }
    temporary = cache_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(cache_path)
    return payload


def clear_ocr_engine_cache() -> None:
    get_ocr_engine.cache_clear()


def _resize_image(image: Image.Image, max_edge: int) -> Image.Image:
    if max_edge <= 0 or max(image.size) <= max_edge:
        return image
    scale = max_edge / max(image.size)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def _fingerprint(image_path: Path, min_confidence: float, max_edge: int) -> str:
    digest = hashlib.sha256()
    digest.update(f"rapidocr:{OCR_CACHE_VERSION}:{min_confidence}:{max_edge}".encode())
    with image_path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _layout_fingerprint(page: dict) -> str:
    values = {
        "version": OCR_LAYOUT_VERSION,
        "source": page.get("source"),
        "page_number": page.get("page_number"),
        "academic_year": page.get("academic_year"),
        "document_type": page.get("document_type"),
    }
    return hashlib.sha256(
        json.dumps(values, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _bounds(line: dict) -> tuple[float, float, float, float]:
    xs = [point[0] for point in line["box"]]
    ys = [point[1] for point in line["box"]]
    return min(xs), min(ys), max(xs), max(ys)


def _center(line: dict) -> tuple[float, float]:
    left, top, right, bottom = _bounds(line)
    return (left + right) / 2, (top + bottom) / 2


def _layout_text(lines: list[dict]) -> str:
    ordered = sorted(lines, key=lambda line: (_bounds(line)[1], _bounds(line)[0]))
    return "\n".join(line["text"] for line in ordered)


def _month_value(value: str) -> tuple[int, int] | None:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    match = re.fullmatch(
        r"(jan|feb|mar|apr|may|jun|jul|july|aug|sep|sept|oct|nov|dec)\s*(\d{2}|20\d{2})",
        normalized,
    )
    if not match:
        return None
    year = int(match.group(2))
    if year < 100:
        year += 2000
    return year, MONTHS[match.group(1)]


def _calendar_segments(lines: list[dict], image_size: tuple[int, int], page: dict) -> list[dict]:
    headers = []
    for line in lines:
        month = _month_value(line["text"])
        if month:
            x, _ = _center(line)
            headers.append({"line": line, "x": x, "year": month[0], "month": month[1]})
    headers.sort(key=lambda item: item["x"])
    if not headers:
        return [{
            "title": f"{page.get('source')} page {page.get('page_number')}",
            "text": _layout_text(lines),
            "metadata": {},
        }]

    segments = []
    footer_cutoff = image_size[1] * 0.965
    for index, header in enumerate(headers):
        left_boundary = (
            (headers[index - 1]["x"] + header["x"]) / 2
            if index > 0 else 0
        )
        right_boundary = (
            (header["x"] + headers[index + 1]["x"]) / 2
            if index < len(headers) - 1 else image_size[0]
        )
        header_bottom = _bounds(header["line"])[3]
        column_lines = []
        for line in lines:
            x, y = _center(line)
            if (
                left_boundary <= x < right_boundary
                and y > header_bottom + 2
                and y < footer_cutoff
                and line is not header["line"]
            ):
                column_lines.append(line)
        column_lines.sort(key=lambda line: (_bounds(line)[1], _bounds(line)[0]))
        month_name = datetime(header["year"], header["month"], 1).strftime("%B %Y")
        body = "\n".join(line["text"] for line in column_lines)
        segments.append({
            "title": month_name,
            "text": (
                f"Academic calendar {month_name}.\n"
                f"Source: {page.get('source')}, page {page.get('page_number')}.\n"
                f"{body}"
            ).strip(),
            "metadata": {
                "calendar_year": header["year"],
                "calendar_month": header["month"],
                "calendar_month_name": month_name,
            },
            "lines": column_lines,
        })
    return segments


def _calendar_events(segments: list[dict], page: dict) -> list[dict]:
    events = []
    date_pattern = re.compile(
        r"^\s*(\d{1,2})\s*(?:(?:M|T|W|TH|F|S|SUN|SUNDAY)\b)?\s*(.*)$",
        flags=re.IGNORECASE,
    )
    for segment in segments:
        metadata = segment.get("metadata", {})
        year = metadata.get("calendar_year")
        month = metadata.get("calendar_month")
        if not year or not month:
            continue
        current = None
        for line in segment.get("lines", []):
            text = line["text"].strip()
            match = date_pattern.match(text)
            if match:
                if current:
                    event = _finish_event(current, page)
                    if event:
                        events.append(event)
                day = int(match.group(1))
                if not 1 <= day <= 31:
                    current = None
                    continue
                current = {
                    "year": year,
                    "month": month,
                    "day": day,
                    "parts": [match.group(2).strip()] if match.group(2).strip() else [],
                    "confidence": [line["confidence"]],
                }
            elif current:
                current["parts"].append(text)
                current["confidence"].append(line["confidence"])
        if current:
            event = _finish_event(current, page)
            if event:
                events.append(event)
    unique = {}
    for event in events:
        key = (event["date"], event["title"].lower())
        unique[key] = event
    return list(unique.values())


def _finish_event(value: dict, page: dict) -> dict | None:
    title = " ".join(part for part in value["parts"] if part).strip(" -")
    title = re.sub(r"\s+", " ", title)
    if not title or title.upper() in {"SUNDAY", "HOLIDAY"}:
        return None
    try:
        date = datetime(value["year"], value["month"], value["day"])
    except ValueError:
        return None
    return {
        "date": date.date().isoformat(),
        "title": title,
        "category": _event_category(title),
        "academic_year": page.get("academic_year") or f"{value['year']}-{value['year'] + 1}",
        "semester": "Odd" if value["month"] >= 7 else "Even",
        "department": "all",
        "source": page.get("source"),
        "document_id": page.get("document_id"),
        "page_number": page.get("page_number"),
        "confidence": round(sum(value["confidence"]) / len(value["confidence"]), 4),
    }


def _event_category(title: str) -> str:
    lowered = title.lower()
    if "exam" in lowered or "re-test" in lowered or "answer script" in lowered:
        return "Exams"
    if "last date" in lowered or "register" in lowered or "submit" in lowered:
        return "Deadlines"
    if "holiday" in lowered or any(
        name in lowered
        for name in ("christmas", "republic day", "gandhi", "deepavali", "ramzan")
    ):
        return "Holidays"
    if "revels" in lowered or "tech tatva" in lowered or "techtatva" in lowered:
        return "Events"
    return "Academic"

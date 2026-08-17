from io import BytesIO

import pandas as pd

from config.defaults import FIELD_ALIASES
from utils.cleaning import normalized

HEADER_TERMS = {
    normalized(alias)
    for aliases in FIELD_ALIASES.values()
    for alias in aliases
} | {
    "organisation unit name", "program stage", "event date",
    "رقم تعريف المريض", "الاسم الثلاثي", "تاريخ الميلاد",
    "الجنس", "نوع الاقامة", "نوع الإقامة", "نوع الزيارة",
}


def header_score(values):
    cells = [normalized(value) for value in values if normalized(value)]
    score = 0
    for cell in cells:
        if cell in HEADER_TERMS:
            score += 4
        elif any(term in cell or cell in term for term in HEADER_TERMS if len(term) >= 5):
            score += 1
        if any(token in cell for token in ("تشاخيص", "diagnosis", "imci_", "ncd")):
            score += 1
    return score


def read_excel_with_detected_header(reader, *args, **kwargs):
    requested_header = kwargs.get("header", 0)
    frame = reader(*args, **kwargs)
    if requested_header not in (0, "infer"):
        return frame
    current_score = header_score(frame.columns)
    if current_score >= 8:
        return frame

    probe_kwargs = dict(kwargs)
    probe_kwargs["header"] = None
    probe_kwargs["nrows"] = 20
    probe = reader(*args, **probe_kwargs)
    if probe.empty:
        return frame
    scores = [header_score(row.tolist()) for _, row in probe.iterrows()]
    best_row = max(range(len(scores)), key=scores.__getitem__)
    if scores[best_row] < 8 or scores[best_row] <= current_score:
        return frame
    final_kwargs = dict(kwargs)
    final_kwargs["header"] = best_row
    final_kwargs.pop("nrows", None)
    return reader(*args, **final_kwargs)

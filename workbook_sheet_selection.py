from io import BytesIO

import pandas as pd

from excel_intake import header_score, read_excel_with_detected_header


def rank_sheet(frame):
    rows, columns = frame.shape
    recognised = header_score(frame.columns)
    # عدد الخلايا هو المؤشر الأقوى، ثم جودة أسماء الحقول وعدد الأعمدة.
    return (rows * columns, recognised, columns, rows)


def inspect_sheets(data, sheet_names, engine="openpyxl", reader=pd.read_excel):
    details = {}
    for sheet in sheet_names:
        try:
            frame = read_excel_with_detected_header(
                reader, BytesIO(data), sheet_name=sheet, dtype=object, engine=engine
            )
            details[sheet] = {
                "rows": int(len(frame)),
                "columns": int(len(frame.columns)),
                "score": rank_sheet(frame),
            }
        except Exception:
            details[sheet] = {"rows": 0, "columns": 0, "score": (0, 0, 0, 0)}
    return details


def best_sheet(details, fallback=None):
    if not details:
        return fallback
    return max(details, key=lambda name: details[name]["score"])

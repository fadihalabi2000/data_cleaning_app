from io import BytesIO

import pandas as pd

from excel_intake import read_excel_with_detected_header
from utils.columns import auto_mapping


def test_detects_excel_header_after_preamble_rows():
    raw = pd.DataFrame([
        ["تقرير عيادة الأطفال", None, None, None],
        ["تاريخ التصدير", "2026-08-01", None, None],
        ["Organisation unit name", "Program stage", "رقم تعريف المريض", "Event date"],
        ["مركز 1", "أطفال", "P-1", "2026-07-31"],
    ])
    data = BytesIO()
    raw.to_excel(data, index=False, header=False)
    data.seek(0)
    frame = read_excel_with_detected_header(pd.read_excel, data, dtype=object, engine="openpyxl")
    mapping = auto_mapping(frame.columns)
    assert mapping["org_unit"] == "Organisation unit name"
    assert mapping["program_stage"] == "Program stage"
    assert mapping["patient_id"] == "رقم تعريف المريض"
    assert mapping["event_date"] == "Event date"
    assert len(frame) == 1

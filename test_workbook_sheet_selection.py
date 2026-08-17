from io import BytesIO

import pandas as pd

from workbook_sheet_selection import best_sheet, inspect_sheets


def test_selects_largest_data_sheet():
    data = BytesIO()
    with pd.ExcelWriter(data, engine="openpyxl") as writer:
        pd.DataFrame({"مؤشر": range(20), "قيمة": range(20)}).to_excel(writer, sheet_name="ورقة2", index=False)
        pd.DataFrame({f"عمود{i}": range(120) for i in range(63)}).to_excel(writer, sheet_name="بيانات الأطفال", index=False)
    details = inspect_sheets(data.getvalue(), ["ورقة2", "بيانات الأطفال"])
    assert details["ورقة2"]["rows"] == 20
    assert details["بيانات الأطفال"]["columns"] == 63
    assert best_sheet(details) == "بيانات الأطفال"

"""مدخل الصيانة المستقر: تنظيف أغلفة rerun وفرض قراءة ورقة البيانات الفعلية."""

import runpy
from io import BytesIO

import pandas as pd
import streamlit as st

import engine_audit_v2
from workbook_sheet_selection import best_sheet, inspect_sheets


_NAMES = ("button", "selectbox", "markdown", "multiselect", "download_button", "file_uploader")
if not hasattr(st, "_quality19_native_elements"):
    st._quality19_native_elements = {name: getattr(st, name) for name in _NAMES}
    st._quality19_native_read_excel = pd.read_excel
else:
    for name, function in st._quality19_native_elements.items():
        setattr(st, name, function)
    pd.read_excel = st._quality19_native_read_excel

for attribute in ("_clinic_fix_originals", "_health_audit_originals", "_allclinic2_base_multiselect"):
    if hasattr(st, attribute):
        delattr(st, attribute)


_read_excel = st._quality19_native_read_excel


def reliable_read_excel(source, *args, **kwargs):
    """إذا اختيرت ورقة ملخص صغيرة بالخطأ، اقرأ ورقة البيانات الأكبر تلقائياً."""
    sheet = kwargs.get("sheet_name", args[0] if args else 0)
    data = st.session_state.get("workbook_bytes")
    filename = st.session_state.get("workbook_name", "")
    if data and isinstance(sheet, (str, int)):
        engine = kwargs.get("engine") or ("xlrd" if filename.lower().endswith(".xls") else "openpyxl")
        try:
            names = list(pd.ExcelFile(BytesIO(data), engine=engine).sheet_names)
            details = inspect_sheets(data, names, engine=engine, reader=_read_excel)
            preferred = best_sheet(details, names[0])
            selected_name = names[sheet] if isinstance(sheet, int) and 0 <= sheet < len(names) else sheet
            selected = details.get(selected_name, {}).get("score", (0,))[0]
            preferred_size = details.get(preferred, {}).get("score", (0,))[0]
            if selected_name in names and preferred != selected_name and preferred_size >= max(100, selected * 3):
                if args:
                    args = (preferred, *args[1:])
                else:
                    kwargs["sheet_name"] = preferred
                st.session_state["maintenance_actual_sheet"] = preferred
        except Exception:
            pass
    return _read_excel(source, *args, **kwargs)


pd.read_excel = reliable_read_excel


_extended_audit = engine_audit_v2.audit_dataframe


def resilient_audit(df, context):
    try:
        return _extended_audit(df, context)
    except Exception as exc:
        try:
            errors, skipped = engine_audit_v2.audit_existing(df, context)
        except Exception as baseline_exc:
            errors, skipped, exc = pd.DataFrame(), pd.DataFrame(), baseline_exc
        skipped = skipped if isinstance(skipped, pd.DataFrame) else pd.DataFrame(skipped or [])
        notice = pd.DataFrame([{
            "اسم الملف": context.get("filename", ""), "نوع العيادة": context.get("clinic", ""),
            "اسم قاعدة التدقيق": "فحص صيانة القواعد الموسعة",
            "سبب التجاوز": f"استمر التدقيق الأساسي وتم تجاوز الإضافة المتعثرة: {type(exc).__name__}",
        }])
        return errors, pd.concat([skipped, notice], ignore_index=True, sort=False)


engine_audit_v2.audit_dataframe = resilient_audit
runpy.run_path("app_quality14.py", run_name="__main__")

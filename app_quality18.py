"""نسخة الصيانة النهائية: إصلاح اختيار ورقة البيانات عند أدنى طبقة Streamlit."""

import runpy
from io import BytesIO

import pandas as pd
import streamlit as st

import engine_audit_v2
from workbook_sheet_selection import best_sheet, inspect_sheets


if not hasattr(st, "_quality18_native_selectbox"):
    st._quality18_native_selectbox = st.selectbox


def data_sheet_selectbox(label, options, *args, **kwargs):
    choices = list(options)
    data = st.session_state.get("workbook_bytes")
    name = st.session_state.get("workbook_name", "")
    if data and len(choices) > 1:
        engine = "xlrd" if name.lower().endswith(".xls") else "openpyxl"
        try:
            sheet_names = list(pd.ExcelFile(BytesIO(data), engine=engine).sheet_names)
            if choices == sheet_names:
                preferred = best_sheet(inspect_sheets(data, sheet_names, engine=engine), sheet_names[0])
                kwargs["index"] = choices.index(preferred)
                kwargs.pop("key", None)
        except Exception:
            # ملفات DHIS المعتادة تضع البيانات الخام في Sheet 1 والملخص في الورقة الأولى.
            if "Sheet 1" in choices:
                kwargs["index"] = choices.index("Sheet 1")
    return st._quality18_native_selectbox(label, choices, *args, **kwargs)


# نجعل كل طبقات الاستعادة القديمة تعود إلى المصحح، لا إلى غلاف سابق.
st.selectbox = data_sheet_selectbox
if hasattr(st, "_repair_native_elements"):
    st._repair_native_elements["selectbox"] = data_sheet_selectbox
for attribute in ("_clinic_fix_originals", "_health_audit_originals", "_allclinic2_base_multiselect"):
    if hasattr(st, attribute):
        delattr(st, attribute)


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

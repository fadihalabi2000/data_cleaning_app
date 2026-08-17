"""نسخة الصيانة: تثبيت قراءة ورقة البيانات ومنع توقف التدقيق بالكامل."""

import runpy
from io import BytesIO

import pandas as pd
import streamlit as st

import engine_audit_v2


@st.cache_data(max_entries=8, show_spinner=False)
def workbook_sheet_names(data, engine):
    return tuple(pd.ExcelFile(BytesIO(data), engine=engine).sheet_names)


@st.cache_data(max_entries=16, show_spinner=False)
def sheet_profile(data, sheet_names, engine):
    from workbook_sheet_selection import inspect_sheets
    return inspect_sheets(data, list(sheet_names), engine=engine)


_base_selectbox = st.selectbox


def reliable_sheet_selectbox(label, options, *args, **kwargs):
    """يتعرف إلى منتقي الورقة من خياراته، ولا يعتمد على نص الملصق أو ترتيب الطبقات."""
    choices = list(options)
    data = st.session_state.get("workbook_bytes")
    name = st.session_state.get("workbook_name", "")
    if data and len(choices) > 1:
        engine = "xlrd" if name.lower().endswith(".xls") else "openpyxl"
        actual_sheets = workbook_sheet_names(data, engine)
        if tuple(choices) == actual_sheets:
            from workbook_sheet_selection import best_sheet
            details = sheet_profile(data, actual_sheets, engine)
            preferred = best_sheet(details, actual_sheets[0])
            kwargs["index"] = choices.index(preferred)
            signature = st.session_state.get("workbook_signature", "current")
            kwargs["key"] = f"maintenance_sheet_{signature}"
    return _base_selectbox(label, choices, *args, **kwargs)


st.selectbox = reliable_sheet_selectbox


_extended_audit = engine_audit_v2.audit_dataframe


def resilient_audit(df, context):
    """أي عطل في إضافة حديثة لا يلغي التدقيق الأساسي ولا يوقف التطبيق."""
    try:
        return _extended_audit(df, context)
    except Exception as exc:
        try:
            errors, skipped = engine_audit_v2.audit_existing(df, context)
        except Exception as baseline_exc:
            errors = pd.DataFrame()
            skipped = pd.DataFrame()
            exc = baseline_exc
        skipped = skipped if isinstance(skipped, pd.DataFrame) else pd.DataFrame(skipped or [])
        notice = pd.DataFrame([{
            "اسم الملف": context.get("filename", ""),
            "نوع العيادة": context.get("clinic", ""),
            "اسم قاعدة التدقيق": "فحص صيانة القواعد الموسعة",
            "سبب التجاوز": f"تم الحفاظ على تشغيل التطبيق وتجاوز الإضافة التي تعذّر تنفيذها: {type(exc).__name__}",
        }])
        return errors, pd.concat([skipped, notice], ignore_index=True, sort=False)


engine_audit_v2.audit_dataframe = resilient_audit
runpy.run_path("app_quality14.py", run_name="__main__")

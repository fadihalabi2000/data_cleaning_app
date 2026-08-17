"""نقطة تشغيل الصيانة المستقرة بعد إزالة تعارض طبقات عناصر Streamlit."""

import runpy
from io import BytesIO

import pandas as pd
import streamlit as st

import engine_audit_v2


@st.cache_data(max_entries=8, show_spinner=False)
def _sheet_names(data, engine):
    return tuple(pd.ExcelFile(BytesIO(data), engine=engine).sheet_names)


@st.cache_data(max_entries=16, show_spinner=False)
def _sheet_details(data, names, engine):
    from workbook_sheet_selection import inspect_sheets
    return inspect_sheets(data, list(names), engine=engine)


_native_selectbox = st.selectbox


def stable_selectbox(label, options, *args, **kwargs):
    choices = list(options)
    data = st.session_state.get("workbook_bytes")
    filename = st.session_state.get("workbook_name", "")
    if data and len(choices) > 1:
        engine = "xlrd" if filename.lower().endswith(".xls") else "openpyxl"
        names = _sheet_names(data, engine)
        if tuple(choices) == names:
            from workbook_sheet_selection import best_sheet
            preferred = best_sheet(_sheet_details(data, names, engine), names[0])
            kwargs["index"] = choices.index(preferred)
            signature = st.session_state.get("workbook_signature", "current")
            kwargs["key"] = f"stable_sheet_{signature}"
    return _native_selectbox(label, choices, *args, **kwargs)


# طبقة قديمة تستعيد نسخة مخزنة من العناصر في كل rerun؛ نعطيها النسخة المصانة صراحةً.
st._clinic_fix_originals = {
    "button": st.button,
    "selectbox": stable_selectbox,
    "markdown": st.markdown,
    "multiselect": st.multiselect,
    "download_button": st.download_button,
}
st._health_audit_originals = {
    "button": st.button,
    "selectbox": stable_selectbox,
    "markdown": st.markdown,
}
st.selectbox = stable_selectbox


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
            "اسم الملف": context.get("filename", ""),
            "نوع العيادة": context.get("clinic", ""),
            "اسم قاعدة التدقيق": "فحص صيانة القواعد الموسعة",
            "سبب التجاوز": f"استمر التدقيق الأساسي وتم تجاوز الإضافة المتعثرة: {type(exc).__name__}",
        }])
        return errors, pd.concat([skipped, notice], ignore_index=True, sort=False)


engine_audit_v2.audit_dataframe = resilient_audit
runpy.run_path("app_quality14.py", run_name="__main__")

import hashlib
import runpy

import streamlit as st

from workbook_sheet_selection import best_sheet, inspect_sheets

base_uploader = st.file_uploader


def workbook_aware_uploader(*args, **kwargs):
    upload = base_uploader(*args, **kwargs)
    if upload is not None:
        data = upload.getvalue()
        signature = hashlib.sha1(data).hexdigest()
        if st.session_state.get("workbook_signature") != signature:
            st.session_state.workbook_signature = signature
            st.session_state.workbook_bytes = data
            st.session_state.workbook_name = upload.name
            st.session_state.pop("smart_sheet_selector", None)
            st.session_state.pop("workbook_sheet_details", None)
    return upload


base_selectbox = st.selectbox


def workbook_aware_selectbox(label, options, *args, **kwargs):
    if label != "ورقة البيانات":
        return base_selectbox(label, options, *args, **kwargs)
    options = list(options)
    data = st.session_state.get("workbook_bytes")
    name = st.session_state.get("workbook_name", "")
    if data and options:
        details = st.session_state.get("workbook_sheet_details")
        if details is None:
            engine = "xlrd" if name.lower().endswith(".xls") else "openpyxl"
            details = inspect_sheets(data, options, engine=engine)
            st.session_state.workbook_sheet_details = details
        preferred = best_sheet(details, options[0])
        kwargs["index"] = options.index(preferred)
        kwargs.setdefault("key", "smart_sheet_selector")
        kwargs.setdefault(
            "help",
            "يختار التطبيق تلقائياً الورقة الأكبر، ويمكنك تغييرها يدوياً.",
        )
    return base_selectbox(label, options, *args, **kwargs)


st.file_uploader = workbook_aware_uploader
st.selectbox = workbook_aware_selectbox
runpy.run_path("app_quality9.py", run_name="__main__")

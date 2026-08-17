import runpy

import streamlit as st
import utils.columns as column_utils

from clinic_detection import weighted_suggest_clinic

column_utils.suggest_clinic = weighted_suggest_clinic

base_radio = st.radio


def file_aware_clinic_radio(label, options, *args, **kwargs):
    if label == "العيادة":
        signature = st.session_state.get("workbook_signature", "current")
        kwargs.setdefault("key", f"smart_clinic_{signature}")
    return base_radio(label, options, *args, **kwargs)


st.radio = file_aware_clinic_radio

base_markdown = st.markdown


def right_aligned_markdown(body, *args, **kwargs):
    if isinstance(body, str):
        # طبقة RTL السابقة استخدمت flex-start الذي ظهر يساراً في إصدار Streamlit الحالي.
        body = body.replace("justify-content:flex-start!important", "justify-content:flex-end!important")
        body = body.replace("justify-content:flex-start !important", "justify-content:flex-end !important")
    return base_markdown(body, *args, **kwargs)


st.markdown = right_aligned_markdown
runpy.run_path("app_quality11.py", run_name="__main__")

import runpy

import streamlit as st
import engine_generalfix
from general_diag_filter import general_diagnosis_columns, is_general_diagnosis

engine_generalfix.is_general_diagnosis = is_general_diagnosis
engine_generalfix.general_diagnosis_columns = general_diagnosis_columns

# محاذاة بطاقات النص العربية مباشرة، من دون حقن CSS أثناء set_page_config.
# هذا يمنع تداخل وسوم style مع طبقة التصميم السابقة وظهورها كنص في الصفحة.
base_markdown = st.markdown


def aligned_markdown(body, *args, **kwargs):
    if isinstance(body, str):
        body = body.replace(
            '<div class="card">',
            '<div class="card" dir="rtl" style="direction:rtl;text-align:right">',
        )
        body = body.replace("<small>", '<small dir="rtl" style="display:block;text-align:right">')
    return base_markdown(body, *args, **kwargs)


st.markdown = aligned_markdown
runpy.run_path("app_quality5.py", run_name="__main__")

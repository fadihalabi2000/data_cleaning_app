import runpy

import pandas as pd
import streamlit as st

from excel_intake import read_excel_with_detected_header

base_read_excel = pd.read_excel


def smart_read_excel(*args, **kwargs):
    return read_excel_with_detected_header(base_read_excel, *args, **kwargs)


pd.read_excel = smart_read_excel

# إذا كان Streamlit يحتفظ بـ None بينما يوجد index مكتشف، نحذف القيمة القديمة
# قبل إنشاء الحقل لكي يظهر العمود المقترح فعلياً في واجهة الأطفال.
base_selectbox = st.selectbox


def mapping_aware_selectbox(label, options, *args, **kwargs):
    key = kwargs.get("key")
    index = kwargs.get("index")
    if index is None and args:
        index = args[0]
    if key and str(key).startswith("v3_") and index and st.session_state.get(key) is None:
        del st.session_state[key]
    return base_selectbox(label, options, *args, **kwargs)


st.selectbox = mapping_aware_selectbox
runpy.run_path("app_quality8.py", run_name="__main__")

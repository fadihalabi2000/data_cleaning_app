"""مدخل الإنتاج المصان: يمنع تراكم غلاف لوحة النتائج بين عمليات rerun."""

import runpy

import streamlit as st


if not hasattr(st, "_quality20_native_header"):
    st._quality20_native_header = st.header
else:
    st.header = st._quality20_native_header

runpy.run_path("app_quality19.py", run_name="__main__")

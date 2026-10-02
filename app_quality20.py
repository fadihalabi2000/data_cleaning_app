"""مدخل الإنتاج المصان مع قاعدة تكرار زيارة ANC في اليوم نفسه."""

import runpy

import streamlit as st

import engine_audit_v2
from validators.women_anc_duplicate import install_women_rule


if not hasattr(st, "_quality20_native_header"):
    st._quality20_native_header = st.header
else:
    st.header = st._quality20_native_header

install_women_rule(engine_audit_v2)
runpy.run_path("app_quality19.py", run_name="__main__")


import runpy
import pandas as pd
import streamlit as st
import config.defaults as defaults
import engine_pro
import engine_v5
import utils.columns as column_utils
from utils.cleaning import normalized

defaults.FIELD_ALIASES["consultation_type"] = [
    "نوع الاستشارة ( هاتفية / فيزيائية )", "نوع الاستشارة (هاتفية / فيزيائية)",
    "نوع الاستشارة", "Consultation type",
]
defaults.FIELD_ALIASES["imaging"] = ["تصوير", "التصوير", "الأشعة", "Imaging"]

original_auto_mapping = column_utils.auto_mapping
def robust_auto_mapping(columns):
    mapping = original_auto_mapping(columns)
    if not mapping.get("consultation_type"):
        mapping["consultation_type"] = next((c for c in columns if ("استشار" in normalized(c) and "نوع" in normalized(c)) or "consultation" in normalized(c)), None)
    if not mapping.get("imaging"):
        mapping["imaging"] = next((c for c in columns if "تصوير" in normalized(c) or "اشعة" in normalized(c) or "أشعة" in str(c)), None)
    return mapping
column_utils.auto_mapping = robust_auto_mapping

original_read_excel = pd.read_excel
def tracked_read_excel(*args, **kwargs):
    frame = original_read_excel(*args, **kwargs)
    st.session_state["latest_uploaded_dataframe"] = frame
    return frame
pd.read_excel = tracked_read_excel

original_selectbox = st.selectbox
def enhanced_selectbox(label, options, *args, **kwargs):
    selected = original_selectbox(label, options, *args, **kwargs)
    if label == "نوع الاستشارة" and selected is not None:
        frame = st.session_state.get("latest_uploaded_dataframe")
        if frame is not None and selected in frame.columns:
            available = sorted({str(v).strip() for v in frame[selected].dropna() if str(v).strip()})
            default = [v for v in available if "هاتف" in normalized(v)]
            chosen = st.multiselect("القيم التي تعني استشارة هاتفية", available, default=default or (["هاتفية"] if "هاتفية" in available else []), key="phone_consultation_values_ui")
            st.session_state.v3_settings["phone_consultation_values"] = chosen or ["هاتفية"]
            st.caption("القيم الأخرى مثل «فيزيائية» لا تُعامل كاستشارة هاتفية.")
    return selected
st.selectbox = enhanced_selectbox

engine_pro.audit_dataframe = engine_v5.audit_dataframe
runpy.run_path("app_v3.py", run_name="__main__")

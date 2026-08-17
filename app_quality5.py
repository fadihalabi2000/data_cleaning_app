import hashlib
import re
import runpy

import streamlit as st
import utils.columns as column_utils
from utils.cleaning import normalized
import engine_clinic_diagnosis
import engine_generalfix
from config.defaults import DEFAULT_SETTINGS


def clean_column_name(value):
    value = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]", "", str(value))
    return re.sub(r"\s+", " ", value).strip()


def robust_find_column(columns, aliases):
    norm = {column: normalized(clean_column_name(column)) for column in columns}
    for alias in aliases:
        target = normalized(clean_column_name(alias))
        match = next((column for column, value in norm.items() if value == target), None)
        if match is not None:
            return match
    for alias in aliases:
        target = normalized(clean_column_name(alias))
        match = next((column for column, value in norm.items() if target in value or value in target), None)
        if match is not None:
            return match
    return None


column_utils.find_column = robust_find_column
column_utils.auto_mapping = lambda columns: {
    key: robust_find_column(columns, aliases) for key, aliases in column_utils.FIELD_ALIASES.items()
}

base_uploader = st.file_uploader


def source_aware_uploader(*args, **kwargs):
    upload = base_uploader(*args, **kwargs)
    if upload is None:
        return upload
    signature = hashlib.sha1(upload.getvalue()).hexdigest()
    if st.session_state.get("audit_source_signature") != signature:
        for key in list(st.session_state):
            if key.startswith("v3g_") or (key.startswith("v3_") and key not in {"v3_settings", "v3_results"}):
                del st.session_state[key]
        st.session_state.audit_source_signature = signature
        st.session_state.v3_results = None
    return upload


st.file_uploader = source_aware_uploader
DEFAULT_SETTINGS["max_age"] = 100.0
engine_clinic_diagnosis.audit_dataframe = engine_generalfix.audit_dataframe
runpy.run_path("app_allclinics2.py", run_name="__main__")

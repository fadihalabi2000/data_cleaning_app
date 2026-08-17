import hashlib
import runpy
import re

import streamlit as st
import utils.columns as column_utils
from utils.cleaning import normalized


def clean_column_name(value):
    value = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]", "", str(value))
    return re.sub(r"\s+", " ", value).strip()


def robust_find_column(columns, aliases):
    norm = {column: normalized(clean_column_name(column)) for column in columns}
    for alias in aliases:
        target = normalized(clean_column_name(alias))
        exact = next((column for column, value in norm.items() if value == target), None)
        if exact is not None:
            return exact
    for alias in aliases:
        target = normalized(clean_column_name(alias))
        fuzzy = next((column for column, value in norm.items() if target in value or value in target), None)
        if fuzzy is not None:
            return fuzzy
    return None


column_utils.find_column = robust_find_column
column_utils.auto_mapping = lambda columns: {
    key: robust_find_column(columns, aliases)
    for key, aliases in column_utils.FIELD_ALIASES.items()
}

# Streamlit يحتفظ بقيمة selectbox القديمة بحسب المفتاح. عند تحميل ملف جديد نمسح
# مفاتيح ربط الأعمدة فقط، كي تظهر اقتراحات الملف الجديد تلقائياً.
base_uploader = st.file_uploader


def source_aware_uploader(*args, **kwargs):
    upload = base_uploader(*args, **kwargs)
    if upload is None:
        return upload
    data = upload.getvalue()
    signature = hashlib.sha1(data).hexdigest()
    if st.session_state.get("audit_source_signature") != signature:
        for key in list(st.session_state):
            if key.startswith("v3g_") or (
                key.startswith("v3_")
                and key not in {"v3_settings", "v3_results", "v3_source_signature"}
            ):
                del st.session_state[key]
        st.session_state.audit_source_signature = signature
        st.session_state.v3_results = None
    return upload


st.file_uploader = source_aware_uploader
runpy.run_path("app_quality3.py", run_name="__main__")

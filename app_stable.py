import runpy
import streamlit as st
from rule_store import PersistentRuleList, load_rules

# Streamlit يعيد تنفيذ الملف عند كل تفاعل. نحتفظ بالدوال الأصلية مرة واحدة
# ونستعيدها قبل تركيب إضافات الواجهة لمنع التغليف المتكرر والمفاتيح المكررة.
if not hasattr(st,"_health_audit_originals"):
    st._health_audit_originals={
        "button":st.button,
        "selectbox":st.selectbox,
        "markdown":st.markdown,
    }
else:
    st.button=st._health_audit_originals["button"]
    st.selectbox=st._health_audit_originals["selectbox"]
    st.markdown=st._health_audit_originals["markdown"]

if "custom_rules" not in st.session_state:
    st.session_state.custom_rules=PersistentRuleList(load_rules())
elif not isinstance(st.session_state.custom_rules,PersistentRuleList):
    st.session_state.custom_rules=PersistentRuleList(st.session_state.custom_rules)

runpy.run_path("app_rules.py",run_name="__main__")

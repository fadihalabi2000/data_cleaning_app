import runpy
import streamlit as st
import engine_rules
import engine_womenfix
from rule_store import PersistentRuleList,load_rules

# استعادة عناصر Streamlit الأصلية عند كل rerun لمنع تراكم الأغلفة.
if not hasattr(st,"_health_audit_originals"):
    st._health_audit_originals={"button":st.button,"selectbox":st.selectbox,"markdown":st.markdown}
else:
    st.button=st._health_audit_originals["button"]
    st.selectbox=st._health_audit_originals["selectbox"]
    st.markdown=st._health_audit_originals["markdown"]

if "custom_rules" not in st.session_state:
    st.session_state.custom_rules=PersistentRuleList(load_rules())
elif not isinstance(st.session_state.custom_rules,PersistentRuleList):
    st.session_state.custom_rules=PersistentRuleList(st.session_state.custom_rules)

# إصلاح اتجاه البنود المرقمة وبقية المكونات العربية.
base_markdown=st.markdown
RTL_FIX="""<style>
.step{direction:rtl!important;display:flex!important;flex-direction:row!important;justify-content:flex-start!important;align-items:center!important;text-align:right!important;width:100%!important}
.step .num,.step-num{direction:rtl!important;order:0!important;margin-left:10px!important;margin-right:0!important;flex:0 0 auto!important}
.step-title{direction:rtl!important;text-align:right!important;order:1!important}
.stMultiSelect [data-baseweb="tag"]{direction:rtl!important}
label,p,.stCaptionContainer{direction:rtl!important;text-align:right!important}
</style>"""
rtl_injected=False
def rtl_markdown(body,*args,**kwargs):
    global rtl_injected
    if not rtl_injected and isinstance(body,str) and "<style>" in body:
        body=body+RTL_FIX; rtl_injected=True
    return base_markdown(body,*args,**kwargs)
st.markdown=rtl_markdown

engine_rules.audit_dataframe=engine_womenfix.audit_dataframe
runpy.run_path("app_rules.py",run_name="__main__")

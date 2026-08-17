import runpy
import streamlit as st
import engine_rules
import engine_womenfix2
from rule_store import PersistentRuleList,load_rules

if not hasattr(st,"_health_audit_originals"):
    st._health_audit_originals={"button":st.button,"selectbox":st.selectbox,"markdown":st.markdown}
else:
    st.button=st._health_audit_originals["button"]; st.selectbox=st._health_audit_originals["selectbox"]; st.markdown=st._health_audit_originals["markdown"]
if "custom_rules" not in st.session_state: st.session_state.custom_rules=PersistentRuleList(load_rules())
elif not isinstance(st.session_state.custom_rules,PersistentRuleList): st.session_state.custom_rules=PersistentRuleList(st.session_state.custom_rules)

base_markdown=st.markdown; injected=False
RTL="""<style>.step{direction:rtl!important;display:flex!important;flex-direction:row!important;justify-content:flex-start!important;text-align:right!important;width:100%!important}.step .num,.step-num{order:0!important;margin-left:10px!important;margin-right:0!important}.step-title{order:1!important;text-align:right!important}label,p,.stCaptionContainer{direction:rtl!important;text-align:right!important}</style>"""
def rtl_markdown(body,*args,**kwargs):
    global injected
    if not injected and isinstance(body,str) and "<style>" in body: body+=RTL; injected=True
    return base_markdown(body,*args,**kwargs)
st.markdown=rtl_markdown
engine_rules.audit_dataframe=engine_womenfix2.audit_dataframe
runpy.run_path("app_rules.py",run_name="__main__")

import re
import runpy
import streamlit as st
import engine_rules
import engine_clinic_diagnosis
import utils.export_pro as export_pro
import utils.export_compat as export_compat
from rule_store import PersistentRuleList,load_rules
from utils.cleaning import normalized

# استعادة العناصر الأصلية عند كل rerun.
if not hasattr(st,"_clinic_fix_originals"):
    st._clinic_fix_originals={"button":st.button,"selectbox":st.selectbox,"markdown":st.markdown,"multiselect":st.multiselect,"download_button":st.download_button}
else:
    for name,func in st._clinic_fix_originals.items(): setattr(st,name,func)
if not hasattr(st,"_health_audit_originals"):
    st._health_audit_originals={k:st._clinic_fix_originals[k] for k in ["button","selectbox","markdown"]}
else:
    st._health_audit_originals={k:st._clinic_fix_originals[k] for k in ["button","selectbox","markdown"]}

if "custom_rules" not in st.session_state: st.session_state.custom_rules=PersistentRuleList(load_rules())
elif not isinstance(st.session_state.custom_rules,PersistentRuleList): st.session_state.custom_rules=PersistentRuleList(st.session_state.custom_rules)

# استبعاد أدوية الضماد من الاختيار الافتراضي فقط، مع بقاء القائمة قابلة للتعديل.
base_multi=st.multiselect
def clinic_multiselect(label,options,*args,**kwargs):
    if label=="أعمدة خدمات الضماد":
        default=kwargs.get("default",[])
        kwargs["default"]=[c for c in default if not ("ادوية" in normalized(c).replace("أ","ا") and "ضماد" in normalized(c))]
        label="أعمدة تشخيص وخدمات الضماد — دون أدوية الضماد"
        kwargs.setdefault("help","هذه المجموعة محفوظة لعيادة الضماد فقط ويمكن تعديلها.")
    return base_multi(label,options,*args,**kwargs)
st.multiselect=clinic_multiselect

# اتجاه عربي صحيح.
base_markdown=st.markdown; injected=False
RTL="""<style>.step{direction:rtl!important;display:flex!important;flex-direction:row!important;justify-content:flex-start!important;text-align:right!important;width:100%!important}.step .num,.step-num{order:0!important;margin-left:10px!important;margin-right:0!important}.step-title{order:1!important;text-align:right!important}label,p,.stCaptionContainer{direction:rtl!important;text-align:right!important}</style>"""
def rtl_markdown(body,*args,**kwargs):
    global injected
    if not injected and isinstance(body,str) and "<style>" in body: body+=RTL; injected=True
    return base_markdown(body,*args,**kwargs)
st.markdown=rtl_markdown

# تصدير Excel متوافق وأسماء ملفات سليمة.
export_pro.export_workbook=export_compat.export_workbook; export_pro.export_single_rule=export_compat.export_single_rule
base_download=st.download_button
def compatible_download(label,data,*args,**kwargs):
    if kwargs.get("file_name","").lower().endswith(".xlsx"):
        kwargs["file_name"]=re.sub(r'[\\/:*?"<>|]+','-',kwargs["file_name"])
        kwargs["mime"]="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return base_download(label,data,*args,**kwargs)
st.download_button=compatible_download

engine_rules.audit_dataframe=engine_clinic_diagnosis.audit_dataframe
runpy.run_path("app_rules.py",run_name="__main__")

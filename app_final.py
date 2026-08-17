import runpy
import streamlit as st

original_markdown=st.markdown
POLISH="""<style>
.block-container{padding-bottom:5rem!important}
[data-testid="stMetric"]{border-top:4px solid #0e7490!important;transition:transform .18s ease,box-shadow .18s ease}
[data-testid="stMetric"]:hover{transform:translateY(-2px);box-shadow:0 10px 24px #0f172a14!important}
[data-testid="stFileUploaderDropzone"]{min-height:150px;display:flex;align-items:center}
[data-testid="stRadio"] [role="radiogroup"]{gap:10px;background:#eaf2f6;padding:8px;border-radius:16px}
[data-testid="stRadio"] label{background:white;border:1px solid #dce7ed;border-radius:12px;padding:10px 15px;box-shadow:0 2px 8px #0f172a0a}
.stTabs [data-baseweb="tab-list"]{background:#eaf2f6;padding:6px;border-radius:14px;gap:6px}
.stTabs [data-baseweb="tab"]{border-radius:10px;padding:8px 18px}.stTabs [aria-selected="true"]{background:white;box-shadow:0 3px 9px #0f172a16}
[data-testid="stDataFrame"]{border:1px solid #dce7ed;border-radius:14px;overflow:hidden;box-shadow:0 5px 16px #0f172a08}
.stAlert{border-radius:14px}.stSelectbox,.stMultiSelect{margin-bottom:.35rem}
</style>"""
injected=False
def polished_markdown(body,*args,**kwargs):
    global injected
    if not injected and isinstance(body,str) and "<style>" in body:
        body=body+POLISH; injected=True
    return original_markdown(body,*args,**kwargs)
st.markdown=polished_markdown
runpy.run_path("app_v6.py",run_name="__main__")

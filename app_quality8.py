import base64
import runpy
from pathlib import Path

import streamlit as st
import engine_generalfix
from general_diag_filter import general_diagnosis_columns, is_general_diagnosis

engine_generalfix.is_general_diagnosis = is_general_diagnosis
engine_generalfix.general_diagnosis_columns = general_diagnosis_columns

logo_path = Path(__file__).resolve().parent / "assets" / "uossm-logo-alt.png"
logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
logo_uri = f"data:image/png;base64,{logo_data}"

base_markdown = st.markdown
brand_css = """
.uossm-brand{display:flex;align-items:center;justify-content:flex-start;margin-bottom:12px}
.uossm-logo{width:92px;height:92px;object-fit:contain;background:#fff;border-radius:50%;padding:7px;box-shadow:0 8px 24px #00000024}
.hero{position:relative;border-top:7px solid #F36F3A!important;background:linear-gradient(135deg,#000 0%,#202020 72%,#343434 100%)!important}
.hero:after{content:"";position:absolute;left:0;bottom:0;width:34%;height:6px;background:#F36F3A;border-radius:0 8px 0 18px}
.hero h1{color:#fff!important}.hero p{color:#f1f1f1!important}.badge{border-color:#F36F3A!important;color:#fff!important}
.step,.step-title,h1,h2,h3,h4{color:#111!important}.num{background:#F36F3A!important;color:#fff!important}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:#F36F3A!important;color:#fff!important}
.stButton>button[kind="primary"]:hover,.stDownloadButton>button[kind="primary"]:hover{background:#d95a28!important}
[data-testid="stMetric"]{border-top-color:#F36F3A!important}
[data-testid="stFileUploaderDropzone"]{border-color:#F36F3A!important;background:#fff!important}
.stTabs [aria-selected="true"]{color:#F36F3A!important;border-bottom-color:#F36F3A!important}
html,body,.stApp,[class*="css"]{font-family:"Helvetica Neue",Arial,sans-serif!important}
"""


def branded_markdown(body, *args, **kwargs):
    if isinstance(body, str):
        body = body.replace(
            '<div class="card">',
            '<div class="card" dir="rtl" style="direction:rtl;text-align:right">',
        ).replace("<small>", '<small dir="rtl" style="display:block;text-align:right">')
        if "<style>" in body and ".hero{" in body and ".uossm-brand" not in body:
            body = body.replace("</style>", brand_css + "</style>", 1)
        if '<div class="hero"><h1>' in body:
            logo = f'<div class="uossm-brand"><img class="uossm-logo" src="{logo_uri}" alt="شعار UOSSM"></div>'
            body = body.replace('<div class="hero"><h1>', f'<div class="hero">{logo}<h1>', 1)
    return base_markdown(body, *args, **kwargs)


st.markdown = branded_markdown
runpy.run_path("app_quality5.py", run_name="__main__")

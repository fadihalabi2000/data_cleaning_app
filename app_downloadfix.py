import re
import runpy
import streamlit as st
import utils.export_pro as export_pro
import utils.export_compat as export_compat

export_pro.export_workbook=export_compat.export_workbook
export_pro.export_single_rule=export_compat.export_single_rule

if not hasattr(st,"_health_download_original"):
    st._health_download_original=st.download_button
else:
    st.download_button=st._health_download_original
base_download=st.download_button
def compatible_download(label,data,*args,**kwargs):
    filename=kwargs.get("file_name")
    if filename and filename.lower().endswith(".xlsx"):
        kwargs["file_name"]=re.sub(r'[\\/:*?"<>|]+','-',filename)
        kwargs["mime"]="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return base_download(label,data,*args,**kwargs)
st.download_button=compatible_download
runpy.run_path("app_latest.py",run_name="__main__")

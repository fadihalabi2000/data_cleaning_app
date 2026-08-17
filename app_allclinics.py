import runpy
import streamlit as st
from clinic_diagnosis_defaults import contains_diagnoses

# تثبيت دالة أصلية واحدة حتى لا تتراكم الأغلفة عند rerun.
if not hasattr(st,"_allclinic_base_multiselect"):
    st._allclinic_base_multiselect=st.multiselect
else:
    st.multiselect=st._allclinic_base_multiselect
base_multi=st.multiselect

def diagnosis_multiselect(label,options,*args,**kwargs):
    if label in {"أعمدة تشخيص الأطفال","أعمدة تشخيص العيادة العامة"}:
        current=kwargs.get("default",[])
        kwargs["default"]=[column for column in current if contains_diagnoses(column)]
        clinic="الأطفال" if "الأطفال" in label else "العامة"
        kwargs.setdefault("help",f"تُكتشف تلقائياً كل الأعمدة التي تحتوي «تشاخيص» وتحفظ لعيادة {clinic} بشكل مستقل.")
        label=f"أعمدة تشاخيص العيادة {clinic}"
    return base_multi(label,options,*args,**kwargs)

st.multiselect=diagnosis_multiselect
# الطبقة التالية تستعيد هذه الدالة ثم تضيف استثناء أدوية الضماد فوقها.
if hasattr(st,"_clinic_fix_originals"):
    st._clinic_fix_originals["multiselect"]=diagnosis_multiselect

runpy.run_path("app_clinic_diagnosis.py",run_name="__main__")

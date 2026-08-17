import runpy

import streamlit as st

from clinic_diagnosis_defaults import contains_diagnoses
from engine_generalfix import general_diagnosis_columns

if not hasattr(st, "_allclinic2_base_multiselect"):
    st._allclinic2_base_multiselect = st.multiselect
else:
    st.multiselect = st._allclinic2_base_multiselect
base_multi = st.multiselect


def diagnosis_multiselect(label, options, *args, **kwargs):
    current = list(kwargs.get("default", []))
    if label == "أعمدة تشخيص الأطفال":
        kwargs["default"] = [column for column in current if contains_diagnoses(column)]
        label = "أعمدة تشاخيص عيادة الأطفال"
    elif label == "أعمدة تشخيص العيادة العامة":
        detected = general_diagnosis_columns(options)
        kwargs["default"] = detected or current
        kwargs.setdefault(
            "help",
            "تُجمع تلقائياً أعمدة NCD وNCD_Not_Applicable وعائلات IMCI بكل ترقيماتها.",
        )
        label = "أعمدة تشخيص العيادة العامة — NCD وIMCI"
    return base_multi(label, options, *args, **kwargs)


st.multiselect = diagnosis_multiselect
if hasattr(st, "_clinic_fix_originals"):
    st._clinic_fix_originals["multiselect"] = diagnosis_multiselect

runpy.run_path("app_clinic_diagnosis.py", run_name="__main__")

"""مدخل ثابت يعيد عناصر Streamlit الأصلية قبل تحميل طبقات التطبيق القديمة في كل rerun."""

import runpy

import streamlit as st


_ELEMENTS = ("button", "selectbox", "markdown", "multiselect", "download_button", "file_uploader")
if not hasattr(st, "_repair_native_elements"):
    st._repair_native_elements = {name: getattr(st, name) for name in _ELEMENTS}
else:
    for name, function in st._repair_native_elements.items():
        setattr(st, name, function)

# يمنع استعادة أغلفة من rerun سابق، وهي سبب تكرار المفاتيح وتوقف الصفحة.
for attribute in ("_clinic_fix_originals", "_health_audit_originals", "_allclinic2_base_multiselect"):
    if hasattr(st, attribute):
        delattr(st, attribute)

runpy.run_path("app_quality16.py", run_name="__main__")

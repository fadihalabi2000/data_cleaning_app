import runpy

import clinic_diagnosis_defaults
import engine_childfix
import engine_generalfix
from child_diag_filter import is_child_diagnosis

# app_allclinics2 يستعمل هذه الدالة لاختيار أعمدة الأطفال الافتراضية.
clinic_diagnosis_defaults.contains_diagnoses = is_child_diagnosis
# app_quality5 يقرأ دالة engine_generalfix لاحقاً؛ نضع أمامها طبقة الأطفال.
engine_generalfix.audit_dataframe = engine_childfix.audit_dataframe

runpy.run_path("app_quality10.py", run_name="__main__")

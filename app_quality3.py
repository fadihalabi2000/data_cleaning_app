import runpy

import engine_clinic_diagnosis
import engine_quality2
from config.defaults import DEFAULT_SETTINGS

DEFAULT_SETTINGS["max_age"] = 100.0
engine_clinic_diagnosis.audit_dataframe = engine_quality2.audit_dataframe
runpy.run_path("app_allclinics.py", run_name="__main__")

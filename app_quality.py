import runpy
import config.defaults as defaults
import engine_clinic_diagnosis
import engine_quality

defaults.DEFAULT_SETTINGS["max_age"]=100.0
engine_clinic_diagnosis.audit_dataframe=engine_quality.audit_dataframe
runpy.run_path("app_allclinics.py",run_name="__main__")

import runpy
import config.defaults as defaults
import engine_v5
import engine_v6

defaults.DEFAULT_SETTINGS["pediatric_max_age"]=14.0
defaults.DEFAULT_SETTINGS["hypertension_min_age"]=30.0
defaults.DEFAULT_SETTINGS["women_min_age"]=14.0
defaults.DEFAULT_SETTINGS["phone_consultation_values"]=["هاتفية"]
engine_v5.audit_dataframe=engine_v6.audit_dataframe
runpy.run_path("app_v5.py",run_name="__main__")

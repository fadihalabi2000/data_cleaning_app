import runpy
import engine_rules
import engine_womenfix

engine_rules.audit_dataframe=engine_womenfix.audit_dataframe
runpy.run_path("app_stable.py",run_name="__main__")

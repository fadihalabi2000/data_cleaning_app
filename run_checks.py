import tempfile
from pathlib import Path
import pandas as pd
from config.defaults import DEFAULT_SETTINGS
from engine import audit_dataframe
from utils.columns import detected_groups
from utils.export import export_workbook

def ctx(df,clinic,mapping): return {"filename":"check.xlsx","clinic":clinic,"mapping":mapping,"groups":detected_groups(df.columns),"settings":dict(DEFAULT_SETTINGS)}
def has(errors,rule): return not errors.empty and rule in set(errors["اسم قاعدة التدقيق"])
groups=detected_groups(["تشاخيص1","تشاخيص 2","تشاخيص.1","NCD1","NCD1.1","NCD_Not_Applicable1.1"])
assert (len(groups["diagnosis"]),len(groups["ncd"]),len(groups["ncd_na"]))==(3,2,1)
df=pd.DataFrame({"تشاخيص1":["ارتفاع ضغط الدم"],"العمر":[12]}); errors,_=audit_dataframe(df,ctx(df,"عامة",{"age":"العمر"})); assert has(errors,"ضغط بعمر صغير")
df=pd.DataFrame({"الضماد1":["خياطة جرح"],"نوع الإصابة":[""]}); errors,_=audit_dataframe(df,ctx(df,"ضماد",{"injury_type":"نوع الإصابة"})); assert has(errors,"خياطة دون نوع إصابة")
df=pd.DataFrame({"NCD1":["سكري"],"NCD_Not_Applicable1":["نعم"]}); errors,_=audit_dataframe(df,ctx(df,"داخلية / NCD",{})); assert has(errors,"تناقض تشخيص NCD")
df=pd.DataFrame({"الاسم الثلاثي":["سارة أحمد"]*2,"تاريخ الميلاد":["2000-01-01"]*2,"Event date":["2026-01-01","2026-02-01"],"رقم زيارة الحمل":["ANC1","ANC3"]})
mapping={"full_name":"الاسم الثلاثي","birth_date":"تاريخ الميلاد","event_date":"Event date","anc_visit":"رقم زيارة الحمل"}; errors,skipped=audit_dataframe(df,ctx(df,"نسائية",mapping)); assert len(errors[errors["اسم قاعدة التدقيق"]=="تسلسل زيارات الحمل"])==2
blob=export_workbook(errors,skipped,{"إجمالي السجلات":2,"إجمالي النتائج":len(errors)}); target=Path(tempfile.gettempdir())/"health-audit-check.xlsx"; target.write_bytes(blob); assert target.stat().st_size>5000
print(f"OK: checks passed; export={target}; bytes={target.stat().st_size}")

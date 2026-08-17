import pandas as pd
from config.defaults import DEFAULT_SETTINGS
from engine_v6 import audit_dataframe
from utils.columns import detected_groups

def ctx(df,clinic,mapping,settings=None):
    base=dict(DEFAULT_SETTINGS); base.update(settings or {})
    return {"filename":"test.xlsx","clinic":clinic,"mapping":mapping,"groups":detected_groups(df.columns),"settings":base}
def count(errors,rule): return 0 if errors.empty else int((errors["اسم قاعدة التدقيق"]==rule).sum())

# NCD: قيمة في Not Applicable المرقم تعني أنه ليس مفقوداً.
df=pd.DataFrame({"NCD1":["", "", "سكري"],"NCD_Not_Applicable1":["", "", ""],"NCD_Not_Applicable1.1":["نعم", "", ""]})
e,_=audit_dataframe(df,ctx(df,"داخلية / NCD",{}))
assert count(e,"تشخيص NCD مفقود")==1

# هاتفية + جديد خطأ، هاتفية + مراجعة سليمة.
df=pd.DataFrame({"نوع الاستشارة":["هاتفية","هاتفية"],"نوع الزيارة":["جديد","مراجعة"],"تشاخيص1":["التهاب","التهاب"]})
e,_=audit_dataframe(df,ctx(df,"عامة",{"consultation_type":"نوع الاستشارة","visit_type":"نوع الزيارة"},{"phone_consultation_values":["هاتفية"]}))
assert count(e,"استشارة هاتفية بنوع زيارة غير صحيح")==1

# الجنس.
df=pd.DataFrame({"الاسم الثلاثي":["محمد علي","فاطمة أحمد"],"الجنس":["أنثى","أنثى"],"تشاخيص1":["سليم","سليم"]})
e,_=audit_dataframe(df,ctx(df,"عامة",{"full_name":"الاسم الثلاثي","gender":"الجنس"}))
assert count(e,"اشتباه بتعارض الجنس")==1

# الأطفال والنسائية.
child=pd.DataFrame({"العمر":[13,14],"تشاخيص1":["التهاب","التهاب"]})
e,_=audit_dataframe(child,ctx(child,"أطفال",{"age":"العمر"})); assert count(e,"عمر غير مناسب لعيادة الأطفال")==1
women=pd.DataFrame({"العمر":[14,15],"تشاخيص1":["التهاب","التهاب"]})
e,_=audit_dataframe(women,ctx(women,"نسائية",{"age":"العمر"})); assert count(e,"عمر غير مناسب للعيادة النسائية")==1

# الضغط فوق 30 فقط.
pressure=pd.DataFrame({"العمر":[30,31],"تشاخيص1":["ارتفاع ضغط الدم","ارتفاع ضغط الدم"]})
e,_=audit_dataframe(pressure,ctx(pressure,"عامة",{"age":"العمر"})); assert count(e,"تشخيص ضغط بعمر 30 أو أقل")==1
ncdp=pd.DataFrame({"العمر":[29,40],"NCD1":["HTN","HTN"],"NCD_Not_Applicable1":["",""]})
e,_=audit_dataframe(ncdp,ctx(ncdp,"داخلية / NCD",{"age":"العمر"})); assert count(e,"تشخيص ضغط بعمر 30 أو أقل")==1

# تنظيم الأسرة/لولب مع ANC.
women=pd.DataFrame({"الأمراض التوليدية1":["تنظيم الأسرة","لولب","حمل"],"رقم زيارة الحمل":["ANC 1","","ANC 2"],"تشاخيص1":["أ","ب","ج"]})
e,_=audit_dataframe(women,ctx(women,"نسائية",{"anc_visit":"رقم زيارة الحمل"})); assert count(e,"تنظيم الأسرة مع زيارة حمل ANC")==1
print("OK v6: all requested rules passed")

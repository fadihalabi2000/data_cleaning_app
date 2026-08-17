import pandas as pd
from engine_v5 import audit_dataframe as audit_v5
from utils.cleaning import age_years, clean_text, normalized, parse_dates
from validators.base import result_rows

MALE_NAMES={"محمد","أحمد","احمد","محمود","علي","عمر","خالد","حسن","حسين","مصطفى","يوسف","إبراهيم","ابراهيم","عبدالله","عبد الرحمن","رامي","سامر","ياسر","زيد","آدم","ادم","حمزة"}
FEMALE_NAMES={"فاطمة","مريم","سارة","ساره","نور","هدى","رنا","لينا","زينب","آية","ايه","آلاء","اسماء","أسماء","خديجة","عائشة","ريم","لين","لجين","سندس"}

def age_series(df,mapping):
    if mapping.get("age"):
        return pd.to_numeric(df[mapping["age"]].map(clean_text),errors="coerce")
    if mapping.get("birth_date") and mapping.get("event_date"):
        return age_years(parse_dates(df[mapping["birth_date"]]),parse_dates(df[mapping["event_date"]]))
    return pd.Series(float("nan"),index=df.index)

def add(errors,frame):
    return pd.concat([errors,frame],ignore_index=True,sort=False) if not frame.empty else errors

def audit_dataframe(df,ctx):
    errors,skipped=audit_v5(df,ctx); clinic=ctx["clinic"]; m=ctx["mapping"]; groups=ctx["groups"]
    remove={"عمر مراجع عيادة الأطفال","ضغط بعمر صغير","تعذر التحقق من عمر مريض مشخص بالضغط"}
    if clinic=="داخلية / NCD": remove|={"غياب التشخيص","تشخيص NCD مفقود"}
    if not errors.empty: errors=errors[~errors["اسم قاعدة التدقيق"].isin(remove)].copy()
    ages=age_series(df,m)

    # NCD ناقص فقط عندما تكون مجموعتا التشخيص وغير المنطبق فارغتين معاً.
    if clinic=="داخلية / NCD":
        ncd,na=groups.get("ncd",[]),groups.get("ncd_na",[])
        if ncd and na:
            actual=df[ncd].apply(lambda s:s.map(clean_text).ne("")).any(axis=1)
            not_app=df[na].apply(lambda s:s.map(clean_text).ne("")).any(axis=1)
            errors=add(errors,result_rows(df,~actual & ~not_app,ctx,"تشخيص NCD مفقود","جميع أعمدة NCD وجميع أعمدة NCD_Not_Applicable فارغة",[*ncd,*na]))

    # الاستشارة الهاتفية يجب أن تكون زيارة مراجعة.
    consultation,visit=m.get("consultation_type"),m.get("visit_type")
    if consultation and visit:
        phones={normalized(x) for x in ctx["settings"].get("phone_consultation_values",["هاتفية"])}
        mask=df[consultation].map(normalized).isin(phones) & ~df[visit].map(normalized).eq(normalized("مراجعة"))
        errors=add(errors,result_rows(df,mask,ctx,"استشارة هاتفية بنوع زيارة غير صحيح","الاستشارة الهاتفية يجب أن يكون نوع الزيارة فيها «مراجعة» وليس «جديد» أو فارغاً",[consultation,visit]))

    # تعارض الجنس من الاسم، مع ثقة عالية للقوائم ووسط للأسماء المؤنثة شكلاً.
    name_col,gender_col=m.get("full_name"),m.get("gender")
    if name_col and gender_col:
        predicted=[]; confidence=[]
        for value in df[name_col]:
            first=clean_text(value).split(" ")[0] if clean_text(value) else ""
            if first in MALE_NAMES: predicted.append("ذكر"); confidence.append("عالي")
            elif first in FEMALE_NAMES: predicted.append("أنثى"); confidence.append("عالي")
            elif first.endswith(("ة","اء","ى")) and first not in MALE_NAMES: predicted.append("أنثى"); confidence.append("متوسط")
            else: predicted.append(""); confidence.append("")
        predicted=pd.Series(predicted,index=df.index); confidence=pd.Series(confidence,index=df.index)
        actual=df[gender_col].map(lambda v:"أنثى" if "أنث" in clean_text(v) else ("ذكر" if "ذكر" in clean_text(v) else ""))
        mismatch=predicted.ne("") & actual.ne("") & predicted.ne(actual)
        frame=result_rows(df,mismatch,ctx,"اشتباه بتعارض الجنس",lambda r,v:f"الجنس المتوقع من الاسم «{predicted.loc[r.name]}» بينما المسجل «{actual.loc[r.name]}»؛ مستوى الثقة: {confidence.loc[r.name]}",[name_col,gender_col],"اشتباه")
        if not frame.empty: frame["مستوى الثقة"]=frame["رقم الصف الأصلي"].map(lambda row:confidence.loc[int(row)-2])
        errors=add(errors,frame)

    # سياسات العمر حسب العيادة.
    age_cols=[x for x in [m.get("age"),m.get("birth_date"),m.get("event_date")] if x]
    if clinic=="أطفال": errors=add(errors,result_rows(df,ages.ge(14),ctx,"عمر غير مناسب لعيادة الأطفال","عمر المراجع 14 سنة أو أكثر؛ عيادة الأطفال مخصصة لمن هم دون 14",age_cols,"مراجعة"))
    if clinic=="نسائية": errors=add(errors,result_rows(df,ages.le(14),ctx,"عمر غير مناسب للعيادة النسائية","عمر المراجعة 14 سنة أو أقل؛ يلزم أن تكون فوق 14",age_cols,"مراجعة"))

    # الضغط في العامة والداخلية يجب أن يكون العمر فوق 30.
    if clinic in {"عامة","داخلية / NCD"}:
        diag=groups.get("diagnosis",[]) if clinic=="عامة" else groups.get("ncd",[])
        keys=[normalized(x) for x in ctx["settings"].get("hypertension_keywords",["ضغط","hypertension","htn"])]
        if diag:
            pressure=df[diag].apply(lambda s:s.map(lambda v:any(k in normalized(v) for k in keys))).any(axis=1)
            errors=add(errors,result_rows(df,pressure & ages.le(30),ctx,"تشخيص ضغط بعمر 30 أو أقل","تشخيص ارتفاع ضغط يتطلب مراجعة لأن العمر يجب أن يكون فوق 30 سنة",[*diag,*age_cols],"اشتباه"))
            errors=add(errors,result_rows(df,pressure & ages.isna(),ctx,"تعذر التحقق من عمر مريض الضغط","يوجد تشخيص ضغط لكن تعذر حساب العمر",[*diag,*age_cols],"مراجعة"))

    # تنظيم الأسرة أو اللولب يتعارض مع تسجيل زيارة حمل ANC.
    if clinic=="نسائية" and m.get("anc_visit"):
        obstetric=[c for c in groups.get("gyne_indicators",[]) if "التوليد" in normalized(c)] or groups.get("gyne_indicators",[])
        if obstetric:
            family=df[obstetric].apply(lambda s:s.map(lambda v:any(k in normalized(v) for k in ["تنظيم الاسرة","تنظيم الأسرة","لولب"]))).any(axis=1)
            anc=df[m["anc_visit"]].map(clean_text).ne("")
            errors=add(errors,result_rows(df,family & anc,ctx,"تنظيم الأسرة مع زيارة حمل ANC","تشخيص تنظيم الأسرة أو اللولب لا يحتاج رقم زيارة ANC؛ القيمتان متعارضتان",[*obstetric,m["anc_visit"]]))
    if not errors.empty: errors=errors.drop_duplicates(subset=["اسم الملف","رقم الصف الأصلي","اسم قاعدة التدقيق"])
    return errors,skipped

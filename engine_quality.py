import pandas as pd
from engine_clinic_diagnosis import audit_dataframe as audit_existing
from engine_v6 import MALE_NAMES,FEMALE_NAMES
from gender_learning import canonical_gender,first_name,learn_consistent_batch,load_knowledge,prediction
from utils.cleaning import age_years,clean_text,parse_dates
from validators.base import result_rows

GENDER_RULE="اشتباه بتعارض الجنس"

def fallback_prediction(name):
    first=first_name(name)
    if first in MALE_NAMES: return {"gender":"ذكر","confidence":"عالي","source":"قاعدة اسم"}
    if first in FEMALE_NAMES: return {"gender":"أنثى","confidence":"عالي","source":"قاعدة اسم"}
    if first.endswith(("ة","اء","ى")) and first not in MALE_NAMES: return {"gender":"أنثى","confidence":"متوسط","source":"قاعدة لغوية"}
    return None

def audit_dataframe(df,context):
    errors,skipped=audit_existing(df,context); mapping=context["mapping"]
    if not errors.empty: errors=errors[errors["اسم قاعدة التدقيق"]!=GENDER_RULE].copy()

    name_col,gender_col=mapping.get("full_name"),mapping.get("gender")
    knowledge=load_knowledge()
    if name_col and gender_col:
        predictions=[]
        for name in df[name_col]:
            learned=prediction(name,knowledge)
            if learned: learned["source"]="تعلم تاريخي"
            predictions.append(learned or fallback_prediction(name))
        predicted=pd.Series([p["gender"] if p else "" for p in predictions],index=df.index)
        actual=df[gender_col].map(canonical_gender)
        mismatch=predicted.ne("") & actual.ne("") & predicted.ne(actual)
        frame=result_rows(df,mismatch,context,GENDER_RULE,
            lambda row,values:f"الجنس المتوقع «{predicted.loc[row.name]}» والمسجل «{actual.loc[row.name]}»؛ المصدر: {predictions[row.name]['source']}؛ الثقة: {predictions[row.name]['confidence']}",
            [name_col,gender_col],"اشتباه")
        if not frame.empty:
            frame["مصدر استنتاج الجنس"]=frame["رقم الصف الأصلي"].map(lambda r:predictions[int(r)-2]["source"])
            frame["مستوى الثقة"]=frame["رقم الصف الأصلي"].map(lambda r:predictions[int(r)-2]["confidence"])
            errors=pd.concat([errors,frame],ignore_index=True,sort=False)
        # التعلم بعد التصنيف، ولا يؤثر في نتيجة الجولة الحالية.
        learn_consistent_batch(df[name_col],df[gender_col],knowledge)

    event_col,birth_col=mapping.get("event_date"),mapping.get("birth_date")
    if event_col:
        events=parse_dates(df[event_col]); today=pd.Timestamp.today().normalize()
        future=events.gt(today)
        frame=result_rows(df,future,context,"تاريخ زيارة في المستقبل",lambda row,values:f"تاريخ الزيارة {events.loc[row.name].date()} يأتي بعد تاريخ اليوم {today.date()}",[event_col])
        if not frame.empty: errors=pd.concat([errors,frame],ignore_index=True,sort=False)
    if birth_col and event_col:
        ages=age_years(parse_dates(df[birth_col]),parse_dates(df[event_col]))
        max_age=float(context["settings"].get("max_age",100))
        frame=result_rows(df,ages.gt(max_age),context,"عمر يتجاوز الحد المنطقي",lambda row,values:f"العمر المحسوب {ages.loc[row.name]:.1f} سنة ويتجاوز الحد {max_age:g}",[birth_col,event_col])
        if not frame.empty: errors=pd.concat([errors,frame],ignore_index=True,sort=False)
    if not errors.empty: errors=errors.drop_duplicates(subset=["اسم الملف","رقم الصف الأصلي","اسم قاعدة التدقيق"])
    return errors,skipped

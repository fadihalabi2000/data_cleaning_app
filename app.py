from copy import deepcopy
import pandas as pd
import streamlit as st

from config.defaults import CLINIC_TYPES, DEFAULT_SETTINGS, FIELD_ALIASES
from engine import audit_dataframe
from utils.cleaning import clean_text
from utils.columns import auto_mapping, detected_groups, suggest_clinic
from utils.export import export_single_rule, export_workbook

st.set_page_config(page_title="مدقّق بيانات المراكز الصحية", page_icon="🩺", layout="wide")
st.markdown("""<style>
html,body,[class*="css"]{direction:rtl;text-align:right} .stDataFrame{direction:rtl}
.hero{padding:1.4rem;border-radius:18px;background:linear-gradient(120deg,#0b4f6c,#1786a3);color:white;margin-bottom:1rem}
.hero h1{margin:0;font-size:2rem}.hero p{margin:.45rem 0 0;color:#e8f7fb}
[data-testid="stMetric"]{background:#f5fafb;border:1px solid #dbecef;padding:12px;border-radius:14px}
</style><div class="hero"><h1>مدقّق بيانات المراكز الصحية</h1><p>اكتشاف الأخطاء وتصديرها للمراجعة — دون تعديل ملفات المصدر.</p></div>""",unsafe_allow_html=True)

if "audit_results" not in st.session_state: st.session_state.audit_results=None
if "settings" not in st.session_state: st.session_state.settings=deepcopy(DEFAULT_SETTINGS)

with st.sidebar:
    st.header("إعدادات التدقيق")
    s=st.session_state.settings
    s["allowed_residency"]=st.text_input("قيم الإقامة المسموحة", "، ".join(s["allowed_residency"])).replace(",","،").split("،")
    s["max_age"]=st.number_input("الحد الأعلى للعمر",1.0,150.0,float(s["max_age"]))
    s["hypertension_min_age"]=st.number_input("الحد الأدنى لاشتباه الضغط",0.0,100.0,float(s["hypertension_min_age"]))
    s["pediatric_max_age"]=st.number_input("حد عمر الأطفال",0.0,30.0,float(s["pediatric_max_age"]))
    s["check_anc_gaps"]=st.toggle("اكتشاف فجوات ANC",s["check_anc_gaps"])
    s["check_empty_dressing"]=st.toggle("اشتراط بيانات الضماد",s["check_empty_dressing"])
    s["check_pediatric_age"]=st.toggle("مراجعة عمر الأطفال",s["check_pediatric_age"])
    with st.expander("الكلمات والقيم"):
        for key,label in [("hypertension_keywords","كلمات الضغط"),("suture_keywords","كلمات الخياطة"),("ncd_na_active_values","قيم تفعيل غير منطبق")]:
            s[key]=[x.strip() for x in st.text_area(label,"\n".join(s[key])).splitlines() if x.strip()]

tab_upload,tab_reference=st.tabs(["رفع بيانات DHIS2","ملف أخطاء مرجعي"])
with tab_reference:
    reference=st.file_uploader("اختياري: ارفع تقرير أخطاء سابقاً لفهم التوزيع",type=["xlsx","xls"],key="reference")
    if reference:
        ref=pd.read_excel(reference)
        st.info("يعرض هذا القسم التقرير السابق فقط، ولا يدخله ضمن عملية التدقيق.")
        if "الخطأ" in ref.columns: st.bar_chart(ref["الخطأ"].fillna("غير مصنف").value_counts())
        st.dataframe(ref.head(100),use_container_width=True,hide_index=True)

with tab_upload:
    files=st.file_uploader("ارفع ملفاً أو عدة ملفات خام",type=["xlsx","xls"],accept_multiple_files=True)
    if not files:
        st.info("ابدأ برفع ملف Excel خام. سيبقى الملف كما هو؛ التطبيق ينشئ تقارير أخطاء منفصلة فقط.")
        st.stop()

    jobs=[]
    for i,file in enumerate(files):
        try:
            excel=pd.ExcelFile(file); sheet=st.selectbox(f"ورقة العمل — {file.name}",excel.sheet_names,key=f"sheet_{i}")
            df=pd.read_excel(file,sheet_name=sheet,dtype=object)
        except Exception as exc:
            st.error(f"تعذرت قراءة {file.name}: {exc}"); continue
        mapping=auto_mapping(df.columns); groups=detected_groups(df.columns)
        program_values=df[mapping["program_stage"]].dropna().astype(str).head(20) if mapping.get("program_stage") else []
        proposed=suggest_clinic(file.name,df.columns,program_values)
        with st.expander(f"{file.name} — {len(df):,} صف",expanded=True):
            clinic=st.selectbox("نوع العيادة",CLINIC_TYPES,index=CLINIC_TYPES.index(proposed),key=f"clinic_{i}")
            st.caption("راجِع الربط التلقائي. اختيار «غير موجود» يؤدي إلى تجاوز القاعدة المرتبطة مع تسجيل السبب.")
            options=[None,*list(df.columns)]
            cols=st.columns(3)
            for pos,(key,aliases) in enumerate(FIELD_ALIASES.items()):
                default=options.index(mapping[key]) if mapping[key] in options else 0
                mapping[key]=cols[pos%3].selectbox(aliases[0],options,index=default,format_func=lambda x:"— غير موجود —" if x is None else str(x),key=f"map_{i}_{key}")
            st.markdown("**مجموعات الأعمدة المكتشفة والقابلة للتعديل**")
            for key,label in [("diagnosis","التشخيص"),("labs","المخبر"),("imaging","التصوير"),("dressing","الضماد"),("ncd","NCD"),("ncd_na","NCD غير منطبق"),("gyne_indicators","مؤشرات نسائية/توليدية")]:
                groups[key]=st.multiselect(label,list(df.columns),default=groups[key],key=f"grp_{i}_{key}")
            jobs.append({"df":df,"filename":file.name,"clinic":clinic,"mapping":mapping,"groups":groups,"settings":deepcopy(s)})

    if st.button("تشغيل التدقيق",type="primary",use_container_width=True):
        all_errors=[]; all_skipped=[]; total=0
        with st.spinner("يتم تطبيق قواعد التدقيق دون تغيير البيانات..."):
            for job in jobs:
                total+=len(job["df"]); errors,skipped=audit_dataframe(job["df"],job)
                if not errors.empty: all_errors.append(errors)
                if not skipped.empty: all_skipped.append(skipped)
        errors=pd.concat(all_errors,ignore_index=True,sort=False) if all_errors else pd.DataFrame()
        skipped=pd.concat(all_skipped,ignore_index=True) if all_skipped else pd.DataFrame()
        bad_records=errors[["اسم الملف","رقم الصف الأصلي"]].drop_duplicates().shape[0] if not errors.empty else 0
        summary={"عدد الملفات":len(jobs),"إجمالي السجلات":total,"السجلات التي تحمل ملاحظة":bad_records,"السجلات دون ملاحظات":max(0,total-bad_records),"إجمالي نتائج القواعد":len(errors),"القواعد المتجاوزة":len(skipped)}
        st.session_state.audit_results=(errors,skipped,summary)

if st.session_state.audit_results:
    errors,skipped,summary=st.session_state.audit_results
    st.divider(); st.subheader("ملخص النتائج")
    cols=st.columns(6)
    for col,(label,value) in zip(cols,summary.items()): col.metric(label,f"{value:,}")
    if errors.empty: st.success("لم تُكتشف أخطاء بالقواعد التي أمكن تنفيذها.")
    else:
        c1,c2=st.columns(2)
        with c1: st.bar_chart(errors["اسم قاعدة التدقيق"].value_counts())
        with c2: st.bar_chart(errors["نوع العيادة"].value_counts())
        st.subheader("تفاصيل الأخطاء")
        rules=["الكل",*errors["اسم قاعدة التدقيق"].dropna().unique().tolist()]
        selected=st.selectbox("تصفية حسب القاعدة",rules)
        view=errors if selected=="الكل" else errors[errors["اسم قاعدة التدقيق"]==selected]
        severity=st.multiselect("درجة الحالة",errors["درجة الحالة"].dropna().unique(),default=list(errors["درجة الحالة"].dropna().unique()))
        view=view[view["درجة الحالة"].isin(severity)]
        st.dataframe(view,use_container_width=True,hide_index=True,height=480)
        if selected!="الكل": st.download_button("تنزيل نتيجة هذه القاعدة",export_single_rule(view),file_name=f"errors-{selected}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if not skipped.empty:
        with st.expander(f"القواعد المتجاوزة ({len(skipped)})"): st.dataframe(skipped,use_container_width=True,hide_index=True)
    st.download_button("تنزيل التقرير الشامل",export_workbook(errors,skipped,summary),file_name="health-center-audit.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",type="primary",use_container_width=True)

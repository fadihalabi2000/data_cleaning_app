from copy import deepcopy
from io import BytesIO
import pandas as pd
import streamlit as st

from config.defaults import DEFAULT_SETTINGS, FIELD_ALIASES
from engine_pro import audit_dataframe
from utils.columns import auto_mapping, detected_groups, suggest_clinic
from utils.export_pro import export_single_rule, export_workbook

st.set_page_config(page_title="منصة تدقيق المراكز الصحية", page_icon="✚", layout="wide", initial_sidebar_state="collapsed")
CLINICS={
 "أطفال":("👶","التشخيص والعمر",[("diagnosis","أعمدة تشخيص الأطفال")]),
 "نسائية":("🌷","الحمل والتشخيص النسائي",[("diagnosis","أعمدة التشخيص المرجعية"),("gyne_indicators","أعمدة الأمراض النسائية والتوليدية")]),
 "ضماد":("🩹","الضماد والخياطة",[("dressing","أعمدة خدمات الضماد")]),
 "عامة":("🩺","التشخيص والضغط",[("diagnosis","أعمدة تشخيص العيادة العامة")]),
 "داخلية / NCD":("❤️","الأمراض المزمنة",[("ncd","أعمدة تشخيص NCD"),("ncd_na","أعمدة NCD غير المنطبق")])}
COMMON=["org_unit","program_stage","patient_id","full_name","birth_date","event_date","gender","residency","visit_type","consultation_type","imaging","age"]
EXTRA={"نسائية":["anc_visit"],"ضماد":["injury_type"],"أطفال":[],"عامة":[],"داخلية / NCD":[]}
st.markdown("""<style>html,body,[class*="css"],.stApp{direction:rtl;text-align:right}.stApp{background:#f5f8fb}.block-container{max-width:1380px;padding-top:1.3rem}.hero{background:linear-gradient(135deg,#083344,#075985,#0e7490);color:#fff;padding:28px 34px;border-radius:24px;box-shadow:0 15px 38px #07598525}.hero h1{margin:0}.hero p{color:#d9f1f7}.badge{padding:7px 12px;border:1px solid #ffffff38;background:#ffffff14;border-radius:30px}.step{font-size:1.25rem;font-weight:800;color:#17324d;margin:24px 0 10px}.num{display:inline-grid;place-items:center;width:32px;height:32px;background:#0e7490;color:white;border-radius:10px;margin-left:8px}.card{background:white;border:1px solid #e2e8f0;padding:17px;border-radius:16px;box-shadow:0 5px 18px #17324d0b}[data-testid="stMetric"]{background:white;border:1px solid #e2e8f0;padding:14px;border-radius:15px}[data-testid="stFileUploaderDropzone"]{background:white;border:2px dashed #7dd3fc;border-radius:16px}.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:linear-gradient(90deg,#0369a1,#0e7490);border:0;border-radius:12px;min-height:46px;font-weight:800}[data-testid="stDataFrame"]{direction:rtl}</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>منصة تدقيق بيانات المراكز الصحية</h1><p>اكتشاف الأخطاء وإنتاج تقارير قابلة للتصحيح دون المساس بملف المصدر.</p><span class="badge">🔒 قراءة وتدقيق فقط</span></div>',unsafe_allow_html=True)
if "v3_results" not in st.session_state: st.session_state.v3_results=None
if "v3_settings" not in st.session_state: st.session_state.v3_settings=deepcopy(DEFAULT_SETTINGS)
def step(n,t): st.markdown(f'<div class="step"><span class="num">{n}</span>{t}</div>',unsafe_allow_html=True)
def values_of(df,col): return sorted({str(v).strip() for v in df[col].dropna() if str(v).strip()}) if col else []

step(1,"رفع ملف البيانات")
upload=st.file_uploader("ملف Excel الخام",type=["xlsx","xls"])
if not upload:
 st.info("ارفع ملف البيانات فقط؛ ملف الأخطاء السابق مرجع للتطوير ولا يلزم رفعه."); st.stop()
try:
 data=upload.getvalue(); engine="xlrd" if upload.name.lower().endswith(".xls") else "openpyxl"; book=pd.ExcelFile(BytesIO(data),engine=engine)
except Exception as e: st.error(f"تعذرت قراءة الملف: {e}"); st.stop()
a,b,c=st.columns([2,1,1]); sheet=a.selectbox("ورقة البيانات",book.sheet_names)
df=pd.read_excel(BytesIO(data),sheet_name=sheet,dtype=object,engine=engine); b.metric("السجلات",f"{len(df):,}"); c.metric("الأعمدة",len(df.columns))

mapping=auto_mapping(df.columns); groups=detected_groups(df.columns)
pv=df[mapping["program_stage"]].dropna().astype(str).head(30) if mapping.get("program_stage") else []
suggest=suggest_clinic(upload.name,df.columns,pv)
step(2,"اختيار العيادة")
names=list(CLINICS); clinic=st.radio("العيادة",names,index=names.index(suggest),horizontal=True,captions=[CLINICS[x][1] for x in names],label_visibility="collapsed")
icon,desc,clinic_groups=CLINICS[clinic]; st.markdown(f'<div class="card"><b>{icon} عيادة {clinic}</b><br><small>{desc} — القواعد المشتركة تطبق تلقائياً.</small></div>',unsafe_allow_html=True)

step(3,"ربط الأعمدة")
t1,t2,t3=st.tabs(["الأعمدة الأساسية",f"إعدادات {clinic}","الحدود والكلمات"]); opts=[None,*list(df.columns)]
with t1:
 st.info("تظهر هنا الحقول اللازمة لكل العيادات فقط. الحقول الخاصة تظهر داخل تبويب العيادة.")
 cols=st.columns(3)
 for i,key in enumerate(COMMON):
  aliases=FIELD_ALIASES[key]; idx=opts.index(mapping[key]) if mapping.get(key) in opts else 0
  mapping[key]=cols[i%3].selectbox(aliases[0],opts,idx,format_func=lambda x:"— غير موجود —" if x is None else str(x),key=f"v3_{clinic}_{key}")
 for key in set(FIELD_ALIASES)-set(COMMON)-set(EXTRA[clinic]): mapping[key]=None
with t2:
 st.markdown("#### أعمدة التشخيص")
 st.caption("يُكتشف غياب التشخيص عندما تكون جميع الأعمدة المحددة فارغة في السجل.")
 for key,label in clinic_groups: groups[key]=st.multiselect(label,list(df.columns),default=groups.get(key,[]),key=f"v3g_{clinic}_{key}")
 if clinic=="نسائية":
  key="anc_visit"; idx=opts.index(mapping[key]) if mapping.get(key) in opts else 0
  mapping[key]=st.selectbox("عمود زيارات الحمل ANC",opts,idx,format_func=lambda x:"— غير موجود —" if x is None else str(x))
  guess=next((x for x in df.columns if "postnatal" in str(x).lower() or "بعد الحمل" in str(x)),None)
  mapping["postnatal"]=st.selectbox("عمود زيارات ما بعد الحمل Postnatal",opts,opts.index(guess) if guess in opts else 0,format_func=lambda x:"— غير موجود —" if x is None else str(x))
  anc_vals=values_of(df,mapping.get("anc_visit")); post_vals=values_of(df,mapping.get("postnatal"))
  st.markdown("**قيم ANC المقروءة تلقائياً من الملف:**"); st.code("  •  ".join(anc_vals[:40]) if anc_vals else "لا توجد قيم/لم يُحدد العمود",language=None)
  if mapping.get("postnatal"): st.markdown("**قيم Postnatal المقروءة تلقائياً:**"); st.code("  •  ".join(post_vals[:40]) if post_vals else "لا توجد قيم",language=None)
 if clinic=="ضماد":
  key="injury_type"; idx=opts.index(mapping[key]) if mapping.get(key) in opts else 0; mapping[key]=st.selectbox("عمود نوع الإصابة",opts,idx,format_func=lambda x:"— غير موجود —" if x is None else str(x))
with t3:
 s=st.session_state.v3_settings; x,y,z=st.columns(3)
 s["allowed_residency"]=[q.strip() for q in x.text_input("قيم الإقامة السليمة","، ".join(s["allowed_residency"])).replace(",","،").split("،") if q.strip()]
 s["max_age"]=y.number_input("أقصى عمر منطقي",1.,150.,float(s["max_age"]))
 if clinic=="أطفال": s["pediatric_max_age"]=z.number_input("حد عمر الأطفال",0.,30.,float(s["pediatric_max_age"]))
 if clinic=="عامة": s["hypertension_min_age"]=z.number_input("أدنى عمر للضغط",0.,100.,float(s["hypertension_min_age"]))
 if clinic=="نسائية": s["check_anc_gaps"]=z.toggle("اكتشاف فجوات ANC",s["check_anc_gaps"])

step(4,"تشغيل التدقيق")
if st.button("بدء التدقيق وإنشاء التقارير",type="primary",use_container_width=True):
 ctx={"filename":upload.name,"clinic":clinic,"mapping":mapping,"groups":groups,"settings":deepcopy(st.session_state.v3_settings)}
 with st.spinner("يتم تدقيق السجلات..."): errors,skipped=audit_dataframe(df,ctx)
 bad=errors[["اسم الملف","رقم الصف الأصلي"]].drop_duplicates().shape[0] if not errors.empty else 0
 summary={"نوع العيادة":clinic,"إجمالي السجلات":len(df),"السجلات المتأثرة":bad,"السجلات السليمة":len(df)-bad,"إجمالي الأخطاء والملاحظات":len(errors),"القواعد المتجاوزة":len(skipped),"نسبة السجلات المتأثرة":round(bad/len(df)*100,1) if len(df) else 0}
 st.session_state.v3_results=errors,skipped,summary
if st.session_state.v3_results:
 errors,skipped,summary=st.session_state.v3_results; st.divider(); st.header("لوحة نتائج التدقيق")
 keys=["إجمالي السجلات","السجلات المتأثرة","السجلات السليمة","إجمالي الأخطاء والملاحظات","القواعد المتجاوزة","نسبة السجلات المتأثرة"]
 for col,key in zip(st.columns(6),keys): col.metric(key,f"{summary[key]}%" if key.startswith("نسبة") else summary[key])
 if errors.empty: st.success("لم تُكتشف أخطاء ضمن القواعد القابلة للتنفيذ.")
 else:
  l,r=st.columns(2)
  with l: st.subheader("حسب القاعدة"); st.bar_chart(errors["اسم قاعدة التدقيق"].value_counts(),horizontal=True)
  with r: st.subheader("حسب المركز"); st.bar_chart(errors["Organisation unit name"].replace("","غير محدد").value_counts().head(12))
  rule=st.selectbox("عرض قاعدة",["الكل",*errors["اسم قاعدة التدقيق"].unique()]); view=errors if rule=="الكل" else errors[errors["اسم قاعدة التدقيق"]==rule]
  show=[x for x in ["رقم الصف الأصلي","Organisation unit name","رقم تعريف المريض","اسم قاعدة التدقيق","درجة الحالة","سبب الخطأ","الأعمدة المرتبطة بالخطأ","القيم المرتبطة بالخطأ"] if x in view]
  st.dataframe(view[show],use_container_width=True,hide_index=True,height=450)
  if rule!="الكل": st.download_button("تنزيل هذه القاعدة",export_single_rule(view),file_name=f"{rule}.xlsx")
 if not skipped.empty:
  with st.expander(f"القواعد المتجاوزة ({len(skipped)})"): st.dataframe(skipped,use_container_width=True,hide_index=True)
 st.download_button("تنزيل تقرير Excel الشامل",export_workbook(errors,skipped,summary),file_name=f"تقرير-{clinic}.xlsx",type="primary",use_container_width=True)

from copy import deepcopy
from io import BytesIO
import pandas as pd
import streamlit as st

from config.defaults import DEFAULT_SETTINGS, FIELD_ALIASES
from engine_pro import audit_dataframe
from utils.columns import auto_mapping, detected_groups, suggest_clinic
from utils.export_pro import export_single_rule, export_workbook

st.set_page_config(page_title="منصة تدقيق المراكز الصحية", page_icon="✚", layout="wide", initial_sidebar_state="collapsed")

CLINICS = {
    "أطفال": {"icon":"👶", "color":"#7C3AED", "desc":"التشخيص والعمر", "groups":[("diagnosis","أعمدة تشخيص الأطفال")]},
    "نسائية": {"icon":"🌷", "color":"#DB2777", "desc":"ANC والتشخيص النسائي", "groups":[("diagnosis","أعمدة التشخيص المرجعية"),("gyne_indicators","مؤشرات الأمراض النسائية والتوليدية")]},
    "ضماد": {"icon":"🩹", "color":"#EA580C", "desc":"الضماد والخياطة", "groups":[("dressing","أعمدة خدمات الضماد")]},
    "عامة": {"icon":"🩺", "color":"#0284C7", "desc":"التشخيص والضغط", "groups":[("diagnosis","أعمدة تشخيص العيادة العامة")]},
    "داخلية / NCD": {"icon":"❤️", "color":"#DC2626", "desc":"الأمراض المزمنة", "groups":[("ncd","أعمدة تشخيص NCD"),("ncd_na","أعمدة NCD غير المنطبق")]},
}

st.markdown("""<style>
html,body,[class*="css"],.stApp{direction:rtl;text-align:right}.stApp{background:#F6F8FB}.block-container{max-width:1380px;padding-top:1.4rem;padding-bottom:4rem}
.hero{background:linear-gradient(135deg,#083344,#075985 56%,#0E7490);border-radius:24px;padding:28px 34px;color:white;box-shadow:0 16px 40px #07598525;margin-bottom:20px;position:relative;overflow:hidden}.hero:after{content:'✚';position:absolute;left:38px;top:-30px;font-size:140px;color:#ffffff12}.hero h1{margin:0;font-size:2.1rem}.hero p{margin:8px 0 0;color:#DDF4FA;font-size:1.04rem}.privacy{display:inline-block;margin-top:14px;padding:7px 12px;background:#ffffff16;border:1px solid #ffffff30;border-radius:999px;font-size:.86rem}
.step{display:flex;align-items:center;gap:10px;margin:24px 0 12px}.step-num{width:32px;height:32px;border-radius:10px;background:#0E7490;color:white;display:grid;place-items:center;font-weight:800}.step-title{font-size:1.23rem;font-weight:800;color:#17324D}.card{background:white;border:1px solid #E3EAF2;border-radius:18px;padding:18px 20px;box-shadow:0 6px 22px #17324D0B;margin-bottom:12px}.soft{background:#F0F9FF;border-color:#BAE6FD}.clinic-title{font-size:1.22rem;font-weight:800}.muted{color:#64748B;font-size:.92rem}
[data-testid="stMetric"]{background:white;border:1px solid #E3EAF2;padding:16px;border-radius:16px;box-shadow:0 4px 16px #17324D0A}[data-testid="stFileUploaderDropzone"]{background:white;border:2px dashed #7DD3FC;border-radius:18px;padding:18px}.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:linear-gradient(90deg,#0369A1,#0E7490);border:0;border-radius:12px;font-weight:800;min-height:46px}.stTabs [data-baseweb="tab-list"]{gap:8px;background:#EAF0F6;border-radius:14px;padding:5px}.stTabs [data-baseweb="tab"]{border-radius:10px;padding:8px 20px}.stTabs [aria-selected="true"]{background:white;box-shadow:0 2px 8px #17324D18}[data-testid="stDataFrame"]{direction:rtl;border:1px solid #E3EAF2;border-radius:14px;overflow:hidden}
</style>""", unsafe_allow_html=True)
st.markdown("""<div class="hero"><h1>منصة تدقيق بيانات المراكز الصحية</h1><p>ارفع ملف البيانات، اختر العيادة، ثم استخرج الأخطاء والتقارير الإحصائية خلال لحظات.</p><span class="privacy">🔒 لا يتم تعديل ملف المصدر أو تصحيح أي قيمة تلقائياً</span></div>""", unsafe_allow_html=True)

if "pro_results" not in st.session_state: st.session_state.pro_results = None
if "pro_settings" not in st.session_state: st.session_state.pro_settings = deepcopy(DEFAULT_SETTINGS)

def heading(number, title): st.markdown(f'<div class="step"><span class="step-num">{number}</span><span class="step-title">{title}</span></div>', unsafe_allow_html=True)

def open_book(upload):
    data = upload.getvalue(); is_xls = upload.name.lower().endswith(".xls")
    return data, pd.ExcelFile(BytesIO(data), engine="xlrd" if is_xls else "openpyxl"), "xlrd" if is_xls else "openpyxl"

heading(1, "رفع ملف البيانات")
uploaded = st.file_uploader("ملف البيانات الخام من DHIS2", type=["xlsx","xls"], help="يدعم XLSX وXLS")
if not uploaded:
    st.markdown('<div class="card soft"><b>جاهز للبدء</b><div class="muted">ارفع ملف البيانات الخام فقط. ملف الأخطاء السابق كان مرجعاً للتطوير ولا يظهر ضمن خطوات التطبيق.</div></div>', unsafe_allow_html=True); st.stop()
try: payload, book, reader_engine = open_book(uploaded)
except ImportError:
    st.error("هذا ملف XLS قديم. مكتبة xlrd غير مثبتة بعد؛ شغّل: pip install -r requirements-pro.txt"); st.stop()
except Exception as exc:
    st.error(f"تعذرت قراءة الملف. تأكد أنه Excel سليم وغير محمي. التفاصيل: {exc}"); st.stop()

c1,c2,c3 = st.columns([2,1,1])
sheet_name = c1.selectbox("ورقة البيانات", book.sheet_names)
try: df = pd.read_excel(BytesIO(payload), sheet_name=sheet_name, dtype=object, engine=reader_engine)
except Exception as exc: st.error(f"تعذرت قراءة الورقة: {exc}"); st.stop()
c2.metric("عدد السجلات", f"{len(df):,}"); c3.metric("عدد الأعمدة", f"{len(df.columns):,}")
st.caption(f"{uploaded.name}  •  {sheet_name}  •  الملف الأصلي محفوظ دون تغيير")

mapping, groups = auto_mapping(df.columns), detected_groups(df.columns)
program_values = df[mapping["program_stage"]].dropna().astype(str).head(30) if mapping.get("program_stage") else []
suggested = suggest_clinic(uploaded.name, df.columns, program_values)

heading(2, "اختيار واجهة العيادة")
clinic_names = list(CLINICS)
clinic = st.radio("نوع العيادة", clinic_names, index=clinic_names.index(suggested), horizontal=True, captions=[CLINICS[x]["desc"] for x in clinic_names], label_visibility="collapsed")
meta = CLINICS[clinic]
st.markdown(f'<div class="card"><div class="clinic-title" style="color:{meta["color"]}">{meta["icon"]} إعدادات عيادة {clinic}</div><div class="muted">القواعد المشتركة تُطبق أولاً، ثم قواعد {clinic} فقط.</div></div>', unsafe_allow_html=True)

heading(3, "تأكيد الأعمدة والقواعد")
basic_tab, clinic_tab, rules_tab = st.tabs(["الأعمدة الأساسية", f"إعدادات {clinic}", "الكلمات والحدود"])
options = [None, *list(df.columns)]
with basic_tab:
    st.info("راجع الربط التلقائي وعدّل الحقول غير الصحيحة فقط. العمود غير الموجود يؤدي إلى تجاوز القاعدة المرتبطة دون إيقاف التدقيق.")
    selectors = st.columns(3)
    for pos,(key,aliases) in enumerate(FIELD_ALIASES.items()):
        idx = options.index(mapping[key]) if mapping.get(key) in options else 0
        mapping[key] = selectors[pos%3].selectbox(aliases[0], options, idx, format_func=lambda x:"— غير موجود —" if x is None else str(x), key=f"pro_{clinic}_{key}")
with clinic_tab:
    st.markdown("#### أعمدة التشخيص الخاصة بالعيادة")
    st.caption("لا يوجد تشخيص عندما تكون جميع الأعمدة المحددة فارغة في السجل نفسه.")
    for key,label in meta["groups"]:
        groups[key] = st.multiselect(label, list(df.columns), default=groups.get(key,[]), key=f"pro_group_{clinic}_{key}")
    notes = {
        "أطفال":"غياب التشخيص، ومراجعة العمر خارج سياسة عيادة الأطفال.",
        "نسائية":"تسلسل ANC والتكرار والانعكاس والفجوات، ومؤشر نسائي دون تشخيص.",
        "ضماد":"غياب خدمة الضماد، ووجود خياطة دون نوع إصابة.",
        "عامة":"غياب التشخيص، وتشخيص ضغط تحت الحد العمري.",
        "داخلية / NCD":"غياب تشخيص NCD، والتناقض بين التشخيص و«غير منطبق».",
    }
    st.success("القواعد الخاصة: " + notes[clinic])
with rules_tab:
    s = st.session_state.pro_settings; a,b,c = st.columns(3)
    s["allowed_residency"] = [x.strip() for x in a.text_input("الإقامة المسموحة", "، ".join(s["allowed_residency"])).replace(",","،").split("،") if x.strip()]
    s["max_age"] = b.number_input("أقصى عمر منطقي", 1.0,150.0,float(s["max_age"]))
    if clinic=="عامة":
        s["hypertension_min_age"] = c.number_input("أدنى عمر لتشخيص الضغط",0.0,100.0,float(s["hypertension_min_age"]))
        s["hypertension_keywords"] = [x.strip() for x in st.text_area("كلمات الضغط", "\n".join(s["hypertension_keywords"])).splitlines() if x.strip()]
    elif clinic=="أطفال": s["pediatric_max_age"] = c.number_input("الحد الأعلى لعمر الأطفال",0.0,30.0,float(s["pediatric_max_age"]))
    elif clinic=="نسائية": s["check_anc_gaps"] = c.toggle("اكتشاف فجوات ANC",s["check_anc_gaps"])
    elif clinic=="ضماد":
        s["check_empty_dressing"] = c.toggle("اعتبار الضماد الفارغ خطأ",s["check_empty_dressing"])
        s["suture_keywords"] = [x.strip() for x in st.text_area("كلمات الخياطة", "\n".join(s["suture_keywords"])).splitlines() if x.strip()]
    else: s["ncd_na_active_values"] = [x.strip() for x in st.text_area("قيم تفعيل غير منطبق", "\n".join(s["ncd_na_active_values"])).splitlines() if x.strip()]

with st.expander("جاهزية التدقيق"):
    st.write(f"تم ربط **{sum(bool(v) for v in mapping.values())}** من **{len(mapping)}** حقلاً أساسياً.")
    for key,label in meta["groups"]: st.write(f"- {label}: **{len(groups.get(key,[]))}** عمود")

heading(4, "التدقيق وإنتاج التقارير")
if st.button("بدء التدقيق وإنشاء التقارير", type="primary", use_container_width=True):
    context = {"filename":uploaded.name,"clinic":clinic,"mapping":mapping,"groups":groups,"settings":deepcopy(st.session_state.pro_settings)}
    with st.spinner("جاري فحص السجلات دون تعديلها..."): errors, skipped = audit_dataframe(df,context)
    bad = errors[["اسم الملف","رقم الصف الأصلي"]].drop_duplicates().shape[0] if not errors.empty else 0
    summary = {"نوع العيادة":clinic,"إجمالي السجلات":len(df),"السجلات المتأثرة":bad,"السجلات السليمة":max(0,len(df)-bad),"إجمالي الأخطاء والملاحظات":len(errors),"القواعد المتجاوزة":len(skipped),"نسبة السجلات المتأثرة":round(bad/len(df)*100,1) if len(df) else 0}
    st.session_state.pro_results = errors,skipped,summary,clinic,uploaded.name

if st.session_state.pro_results:
    errors,skipped,summary,result_clinic,result_file = st.session_state.pro_results
    st.divider(); st.markdown("## لوحة نتائج التدقيق"); st.caption(f"{result_file} • عيادة {result_clinic}")
    keys=["إجمالي السجلات","السجلات المتأثرة","السجلات السليمة","إجمالي الأخطاء والملاحظات","القواعد المتجاوزة","نسبة السجلات المتأثرة"]
    for col,key in zip(st.columns(6),keys): col.metric(key, f"{summary[key]}%" if key.startswith("نسبة") else f"{summary[key]:,}")
    if errors.empty: st.success("لم تُكتشف أخطاء ضمن القواعد التي أمكن تنفيذها.")
    else:
        left,right=st.columns([1.15,1])
        with left: st.markdown("#### الأخطاء حسب القاعدة"); st.bar_chart(errors["اسم قاعدة التدقيق"].value_counts(),horizontal=True,color="#0E7490")
        with right: st.markdown("#### الأخطاء حسب المركز"); st.bar_chart(errors["Organisation unit name"].replace("","غير محدد").value_counts().head(12),color="#F59E0B")
        details,stats=st.tabs(["سجلات الأخطاء","التقارير الإحصائية"])
        with details:
            x,y=st.columns(2); rule=x.selectbox("قاعدة التدقيق",["الكل",*errors["اسم قاعدة التدقيق"].dropna().unique()]); severity_list=errors["درجة الحالة"].dropna().unique().tolist(); severity=y.multiselect("درجة الحالة",severity_list,default=severity_list)
            view=errors[errors["درجة الحالة"].isin(severity)]; view=view if rule=="الكل" else view[view["اسم قاعدة التدقيق"]==rule]
            preferred=["رقم الصف الأصلي","Organisation unit name","رقم تعريف المريض","اسم قاعدة التدقيق","درجة الحالة","سبب الخطأ","الأعمدة المرتبطة بالخطأ","القيم المرتبطة بالخطأ"]
            st.dataframe(view[[c for c in preferred if c in view]],use_container_width=True,hide_index=True,height=470)
            if rule!="الكل": st.download_button("تنزيل أخطاء القاعدة",export_single_rule(view),file_name=f"{rule}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with stats:
            by_rule=errors.groupby(["اسم قاعدة التدقيق","درجة الحالة"]).size().reset_index(name="العدد").sort_values("العدد",ascending=False); by_center=errors.groupby("Organisation unit name").size().reset_index(name="العدد").sort_values("العدد",ascending=False)
            x,y=st.columns(2); x.dataframe(by_rule,use_container_width=True,hide_index=True); y.dataframe(by_center,use_container_width=True,hide_index=True)
    if not skipped.empty:
        with st.expander(f"قواعد متجاوزة بسبب أعمدة مفقودة ({len(skipped)})"): st.dataframe(skipped,use_container_width=True,hide_index=True)
    st.download_button("تنزيل تقرير التدقيق الشامل Excel",export_workbook(errors,skipped,summary),file_name=f"تقرير-تدقيق-{result_clinic}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",type="primary",use_container_width=True)

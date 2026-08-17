import runpy
import pandas as pd
import streamlit as st
import engine_v6
import engine_rules

engine_v6.audit_dataframe = engine_rules.audit_dataframe
original_button = st.button

OPERATORS = {
    "يساوي إحدى القيم": "equals_any", "لا يساوي أياً من القيم": "not_equals_any",
    "يحتوي على مقطع": "contains_any", "لا يحتوي على مقطع": "not_contains_any",
    "فارغ": "is_blank", "غير فارغ": "not_blank",
    "أكبر من": "greater", "أكبر أو يساوي": "greater_equal",
    "أصغر من": "less", "أصغر أو يساوي": "less_equal", "بين رقمين": "between",
}

def rule_builder():
    frame = st.session_state.get("latest_uploaded_dataframe")
    if frame is None: return
    if "custom_rules" not in st.session_state: st.session_state.custom_rules=[]
    st.markdown("### مختبر القواعد المخصصة")
    st.caption("أنشئ قواعد إضافية من بيانات الملف نفسه. القواعد تُطبّق دون تعديل الملف الأصلي.")
    saved_tab, create_tab = st.tabs([f"القواعد المحفوظة ({len(st.session_state.custom_rules)})", "إضافة قاعدة جديدة"])
    with saved_tab:
        if not st.session_state.custom_rules: st.info("لم تُضف قواعد مخصصة بعد.")
        else:
            overview=[]
            for i,rule in enumerate(st.session_state.custom_rules,1):
                overview.append({"#":i,"اسم القاعدة":rule["name"],"درجة الحالة":rule["severity"],"منطق الربط":"كل الشروط" if rule["logic"]=="all" else "أي شرط","عدد الشروط":len(rule["conditions"])})
            st.dataframe(pd.DataFrame(overview),use_container_width=True,hide_index=True)
            remove=st.selectbox("قاعدة للحذف",[None,*range(len(st.session_state.custom_rules))],format_func=lambda x:"— اختر —" if x is None else st.session_state.custom_rules[x]["name"],key="remove_custom_rule")
            if original_button("حذف القاعدة المحددة",disabled=remove is None,key="delete_custom_rule"):
                st.session_state.custom_rules.pop(remove); st.rerun()
    with create_tab:
        name=st.text_input("اسم قاعدة التدقيق",placeholder="مثال: خدمة مخبرية مع نوع زيارة غير مناسب",key="custom_rule_name")
        a,b,c=st.columns(3)
        severity=a.selectbox("درجة الحالة",["خطأ","اشتباه","مراجعة"],key="custom_severity")
        logic_label=b.selectbox("طريقة ربط الشروط",["يجب تحقق كل الشروط","يكفي تحقق أي شرط"],key="custom_logic")
        count=c.number_input("عدد الشروط",1,6,1,1,key="custom_condition_count")
        conditions=[]
        for i in range(int(count)):
            st.markdown(f"**الشرط {i+1}**")
            x,y=st.columns([1,1])
            column=x.selectbox("العمود",list(frame.columns),key=f"custom_col_{i}")
            operator_label=y.selectbox("عامل الفلترة",list(OPERATORS),key=f"custom_op_{i}")
            operator=OPERATORS[operator_label]; condition={"column":column,"operator":operator}
            available=sorted({str(v).strip() for v in frame[column].dropna() if str(v).strip()})
            if operator in {"equals_any","not_equals_any"}:
                condition["values"]=st.multiselect("القيم المطلوبة — مقروءة من الملف",available,key=f"custom_vals_{i}")
            elif operator in {"contains_any","not_contains_any"}:
                tokens=st.text_input("المقاطع النصية مفصولة بفاصلة",key=f"custom_tokens_{i}")
                condition["values"]=[v.strip() for v in tokens.replace("،",",").split(",") if v.strip()]
                if available: st.caption("نماذج من قيم العمود: "+" • ".join(available[:12]))
            elif operator=="between":
                n1,n2=st.columns(2); condition["minimum"]=n1.number_input("من",key=f"custom_min_{i}"); condition["maximum"]=n2.number_input("إلى",key=f"custom_max_{i}")
            elif operator in {"greater","greater_equal","less","less_equal"}:
                condition["number"]=st.number_input("القيمة الرقمية",key=f"custom_num_{i}")
            conditions.append(condition)
        message=st.text_input("رسالة سبب الخطأ",placeholder="اشرح لماذا يُعد السجل مخالفاً",key="custom_message")
        if original_button("حفظ القاعدة المخصصة",type="primary",key="save_custom_rule"):
            invalid=not name.strip() or any(c["operator"] in {"equals_any","not_equals_any","contains_any","not_contains_any"} and not c.get("values") for c in conditions)
            if invalid: st.error("أدخل اسم القاعدة والقيم المطلوبة لكل شرط.")
            else:
                st.session_state.custom_rules.append({"name":name.strip(),"severity":severity,"logic":"all" if logic_label.startswith("يجب") else "any","conditions":conditions,"message":message.strip()})
                st.success("تم حفظ القاعدة وستُطبق عند بدء التدقيق."); st.rerun()
    st.session_state.v3_settings["custom_rules"]=st.session_state.custom_rules

def enhanced_button(label,*args,**kwargs):
    if label == "بدء التدقيق وإنشاء التقارير": rule_builder()
    return original_button(label,*args,**kwargs)
st.button=enhanced_button
runpy.run_path("app_final.py",run_name="__main__")

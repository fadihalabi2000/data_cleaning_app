"""نقطة التشغيل الاحترافية: القواعد الموسعة + إعداداتها + لوحة النتائج المتقدمة."""

import runpy

import pandas as pd
import streamlit as st

import engine_audit_v2
import engine_childfix
import utils.columns as column_utils


# تلتقط طبقات التطبيق اللاحقة هذه الدالة، وبذلك تبقى كل الإصلاحات القديمة فعالة.
engine_childfix.audit_dataframe = engine_audit_v2.audit_dataframe

_base_detected_groups = column_utils.detected_groups


def detected_groups_without_drugs(columns):
    groups = _base_detected_groups(columns)
    for key in ("ncd", "ncd_na", "diagnosis"):
        if key in groups:
            groups[key] = [column for column in groups[key] if "drug" not in str(column).casefold()]
    return groups


column_utils.detected_groups = detected_groups_without_drugs


def _current_clinic():
    for key, value in st.session_state.items():
        if str(key).startswith("smart_clinic_") and value:
            return value
    return ""


def _guess_column(columns, fragments):
    return next(
        (column for column in columns if any(fragment in str(column).casefold() for fragment in fragments)),
        None,
    )


def advanced_rule_settings():
    frame = st.session_state.get("latest_uploaded_dataframe")
    settings = st.session_state.setdefault("v3_settings", {})
    with st.expander("إعدادات القواعد المتقدمة", expanded=False):
        st.caption("القيم الافتراضية مناسبة للاستخدام المباشر، ويمكن تعديلها لكل عملية تدقيق.")
        left, right = st.columns(2)
        settings["duplicate_birthdate_max_days"] = left.number_input(
            "أقصى فرق لتاريخ الميلاد عند كشف التكرار (يوم)",
            min_value=0, max_value=3650,
            value=int(settings.get("duplicate_birthdate_max_days", 365)),
            key="advanced_duplicate_birth_days",
        )
        settings["duplicate_min_score"] = right.slider(
            "الحد الأدنى لدرجة الاشتباه بالتكرار",
            min_value=0, max_value=100,
            value=int(settings.get("duplicate_min_score", 70)),
            key="advanced_duplicate_min_score",
        )
        if _current_clinic() == "نسائية" and isinstance(frame, pd.DataFrame):
            columns = list(frame.columns)
            options = [None, *columns]
            current = settings.get("pregnancy_type_column")
            if current not in columns:
                current = _guess_column(columns, ["نوع الحمل", "pregnancy type", "pregnancy_type"])
            settings["pregnancy_type_column"] = st.selectbox(
                "عمود نوع الحمل",
                options,
                index=options.index(current) if current in options else 0,
                format_func=lambda value: "— غير موجود —" if value is None else str(value),
                key="advanced_pregnancy_type_column",
                help="تستخدمه قاعدة ثبات نوع الحمل بين زيارات المستفيدة.",
            )


_base_button = st.button


def enhanced_button(label, *args, **kwargs):
    if label == "بدء التدقيق وإنشاء التقارير":
        advanced_rule_settings()
    return _base_button(label, *args, **kwargs)


st.button = enhanced_button


def _filter_values(frame, column, label, key):
    if column not in frame:
        return frame
    values = sorted(str(value) for value in frame[column].dropna().unique() if str(value).strip())
    chosen = st.multiselect(label, values, key=key)
    return frame[frame[column].astype(str).isin(chosen)] if chosen else frame


_base_header = st.header


def enhanced_header(body, *args, **kwargs):
    result = _base_header(body, *args, **kwargs)
    if body != "لوحة نتائج التدقيق":
        return result
    state = st.session_state.get("v3_results")
    if not state:
        return result
    errors = state[0]
    if errors is None or errors.empty:
        return result
    st.markdown("### لوحة التحليل المتقدم")
    high = int(errors.get("درجة الأهمية", pd.Series(dtype=str)).eq("High").sum())
    review = int(errors.get("تصنيف الملاحظة", pd.Series(dtype=str)).eq("بحاجة للمراجعة").sum())
    suspects = int(errors.get("تصنيف الملاحظة", pd.Series(dtype=str)).eq("اشتباه").sum())
    for column, label, value in zip(st.columns(4), ["إجمالي النتائج", "عالية الأهمية", "بحاجة للمراجعة", "حالات الاشتباه"], [len(errors), high, review, suspects]):
        column.metric(label, value)
    with st.expander("تصفية النتائج المتقدمة", expanded=True):
        view = errors
        filters = [
            ("نوع العيادة", "العيادة"), ("اسم قاعدة التدقيق", "قاعدة التدقيق"),
            ("درجة الأهمية", "درجة الأهمية"), ("تصنيف الملاحظة", "تصنيف الملاحظة"),
            ("Organisation unit name", "المركز"), ("Program stage", "مرحلة البرنامج"),
        ]
        columns = st.columns(3)
        for index, (field, label) in enumerate(filters):
            with columns[index % 3]:
                view = _filter_values(view, field, label, f"advanced_filter_{index}")
        st.caption(f"النتائج المطابقة: {len(view):,} من أصل {len(errors):,}")
        display = [column for column in [
            "رقم الصف الأصلي", "Organisation unit name", "Program stage", "رقم تعريف المريض",
            "اسم قاعدة التدقيق", "تصنيف الملاحظة", "درجة الأهمية", "سبب الخطأ",
            "درجة التشابه الإجمالية", "مستوى الثقة",
        ] if column in view]
        st.dataframe(view[display], hide_index=True, height=360)
    return result


st.header = enhanced_header
runpy.run_path("app_quality13.py", run_name="__main__")

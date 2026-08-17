import pandas as pd

from gender_learning import learn_consistent_batch, load_knowledge, prediction
from validators.base import result_rows
from validators.identity_utils import canonical_gender, normalized_first_name

KNOWN_MALE_NAMES = {
    "محمد", "احمد", "محمود", "خالد", "عمر", "علي", "حسن", "حسين", "يوسف",
    "ابراهيم", "عبدالله", "مصطفي", "سامر", "ماهر", "رامي", "فادي", "حمزة", "زيد",
}
KNOWN_FEMALE_NAMES = {
    "فاطمة", "مريم", "اية", "سارة", "نور", "هدي", "رنا", "ريم", "زينب",
    "خديجة", "عائشة", "اسماء", "دعاء", "رباب", "حنان", "لينا", "لجين", "سندس",
}


def predict_gender(name, knowledge=None):
    first = normalized_first_name(name)
    if not first:
        return {"gender": "", "confidence": "غير مؤكد", "source": "لا يوجد اسم أول"}
    learned = prediction(name, knowledge or {})
    if learned:
        return {"gender": learned["gender"], "confidence": learned["confidence"], "source": "تعلم تاريخي"}
    if first in KNOWN_MALE_NAMES:
        return {"gender": "ذكر", "confidence": "عالي", "source": "قاموس الأسماء"}
    if first in KNOWN_FEMALE_NAMES:
        return {"gender": "أنثى", "confidence": "عالي", "source": "قاموس الأسماء"}
    if first.endswith(("ة", "اء", "ي")):
        return {"gender": "أنثى", "confidence": "متوسط", "source": "مؤشر لغوي"}
    return {"gender": "", "confidence": "غير مؤكد", "source": "لا توجد قرائن كافية"}


def validate_gender_consistency(df, ctx):
    mapping = ctx["mapping"]
    name_col, gender_col = mapping.get("full_name"), mapping.get("gender")
    if not name_col or not gender_col:
        missing = [label for value, label in [(name_col, "الاسم الثلاثي"), (gender_col, "الجنس")] if not value]
        return pd.DataFrame(), [{"اسم الملف": ctx["filename"], "نوع العيادة": ctx["clinic"], "اسم قاعدة التدقيق": "عدم تطابق الجنس", "سبب التجاوز": "تعذر التشغيل لعدم تحديد: " + "، ".join(missing)}]
    knowledge = load_knowledge()
    predictions = pd.Series([predict_gender(value, knowledge) for value in df[name_col]], index=df.index)
    predicted = predictions.map(lambda item: item["gender"])
    actual = df[gender_col].map(canonical_gender)
    confidence = predictions.map(lambda item: item["confidence"])
    mismatch = predicted.ne("") & actual.ne("") & predicted.ne(actual) & confidence.isin(["عالي", "متوسط"])
    frame = result_rows(
        df, mismatch, ctx, "عدم تطابق الجنس",
        lambda row, values: (
            f"الجنس المسجل «{actual.loc[row.name]}»، بينما الاسم الأول «{normalized_first_name(row[name_col])}» "
            f"مصنف كـ«{predicted.loc[row.name]}» بدرجة ثقة {confidence.loc[row.name]}."
        ),
        [name_col, gender_col], "اشتباه",
    )
    if not frame.empty:
        by_row = {position + 2: item for position, item in enumerate(predictions)}
        frame["مستوى الثقة"] = frame["رقم الصف الأصلي"].map(lambda row: by_row[row]["confidence"])
        frame["مصدر استنتاج الجنس"] = frame["رقم الصف الأصلي"].map(lambda row: by_row[row]["source"])
        frame["تصنيف الملاحظة"] = frame["مستوى الثقة"].map(lambda value: "خطأ" if value == "عالي" else "بحاجة للمراجعة")
        frame["درجة الأهمية"] = "Medium"
    learn_consistent_batch(df[name_col], df[gender_col], knowledge)
    return frame, []

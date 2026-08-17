from utils.cleaning import clean_text, normalized
from validators.base import require, result_rows

def validate(df, ctx):
    if not require(ctx, "بيانات الضماد", groups=["dressing"]): return []
    cols=ctx["groups"]["dressing"]; out=[]; s=ctx["settings"]
    if s["check_empty_dressing"]:
        empty=~df[cols].apply(lambda x:x.map(lambda v:bool(clean_text(v)))).any(axis=1)
        out.append(result_rows(df, empty, ctx, "بيانات الضماد مفقودة", "جميع أعمدة الضماد فارغة", cols))
    if require(ctx, "خياطة دون نوع إصابة", keys=["injury_type"]):
        injury=ctx["mapping"]["injury_type"]; keys=[normalized(x) for x in s["suture_keywords"]]
        sut=df[cols].apply(lambda x:x.map(lambda v:any(k in normalized(v) for k in keys))).any(axis=1)
        out.append(result_rows(df, sut & df[injury].map(clean_text).eq(""), ctx, "خياطة دون نوع إصابة", "وُجدت خياطة بينما نوع الإصابة فارغ", [*cols,injury]))
    return [x for x in out if not x.empty]

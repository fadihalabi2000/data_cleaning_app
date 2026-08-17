from utils.cleaning import clean_text, normalized
from validators.base import require, result_rows

def validate(df, ctx):
    if not require(ctx, "تشخيص NCD", groups=["ncd","ncd_na"]): return []
    ncd,na=ctx["groups"]["ncd"],ctx["groups"]["ncd_na"]
    actual=df[ncd].apply(lambda x:x.map(lambda v:bool(clean_text(v)))).any(axis=1)
    active_values={normalized(x) for x in ctx["settings"]["ncd_na_active_values"]}
    not_app=df[na].apply(lambda x:x.map(normalized).isin(active_values)).any(axis=1)
    return [x for x in [
        result_rows(df, ~actual & ~not_app, ctx, "تشخيص NCD مفقود", "لا يوجد تشخيص NCD ولا اختيار غير منطبق", [*ncd,*na]),
        result_rows(df, actual & not_app, ctx, "تناقض تشخيص NCD", "يوجد تشخيص NCD بالتزامن مع اختيار غير منطبق", [*ncd,*na]),
    ] if not x.empty]

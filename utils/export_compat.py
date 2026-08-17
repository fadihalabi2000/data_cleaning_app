from io import BytesIO
import pandas as pd
from utils.export_pro import safe_sheet_name,style_table

def export_workbook(errors,skipped,summary):
    """Excel-compatible report without optional drawing/chart parts."""
    output=BytesIO(); used=set()
    by_rule=errors.groupby(["اسم قاعدة التدقيق","درجة الحالة"]).size().reset_index(name="العدد") if not errors.empty else pd.DataFrame(columns=["اسم قاعدة التدقيق","درجة الحالة","العدد"])
    by_center=errors.groupby("Organisation unit name").size().reset_index(name="العدد").sort_values("العدد",ascending=False) if not errors.empty else pd.DataFrame(columns=["Organisation unit name","العدد"])
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        pd.DataFrame(summary.items(),columns=["المؤشر","القيمة"]).to_excel(writer,sheet_name="الملخص",index=False); used.add("الملخص")
        by_rule.to_excel(writer,sheet_name="إحصاء حسب القاعدة",index=False); used.add("إحصاء حسب القاعدة")
        by_center.to_excel(writer,sheet_name="إحصاء حسب المركز",index=False); used.add("إحصاء حسب المركز")
        (errors if not errors.empty else pd.DataFrame(columns=["لا توجد أخطاء"])).to_excel(writer,sheet_name="جميع الأخطاء",index=False); used.add("جميع الأخطاء")
        (skipped if not skipped.empty else pd.DataFrame(columns=["لا توجد قواعد متجاوزة"])).to_excel(writer,sheet_name="القواعد المتجاوزة",index=False); used.add("القواعد المتجاوزة")
        if not errors.empty:
            for rule,part in errors.groupby("اسم قاعدة التدقيق",sort=False):
                part.to_excel(writer,sheet_name=safe_sheet_name(rule,used),index=False)
        for ws in writer.book.worksheets: style_table(ws)
        writer.book["الملخص"].column_dimensions["A"].width=40
        writer.book["الملخص"].column_dimensions["B"].width=22
        writer.book.calculation.fullCalcOnLoad=True
        writer.book.calculation.forceFullCalc=True
    output.seek(0); return output.getvalue()

def export_single_rule(df):
    output=BytesIO()
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        df.to_excel(writer,sheet_name="الأخطاء",index=False); style_table(writer.book["الأخطاء"])
    output.seek(0); return output.getvalue()

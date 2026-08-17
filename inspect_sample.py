from pathlib import Path
import json
import pandas as pd

path = Path(r"E:\تدقيق PHC\‏‏2026-7\تدقيق\تدقيق\تدقيق حتى -23-7 اوسم كندا.xlsx")
book = pd.ExcelFile(path)
result = {"path": str(path), "sheets": []}
for name in book.sheet_names:
    df = pd.read_excel(path, sheet_name=name, dtype=object)
    result["sheets"].append({
        "name": name,
        "rows": len(df),
        "columns": [str(c) for c in df.columns],
        "samples": {
            str(c): [str(v) for v in df[c].dropna().astype(str).head(5).tolist()]
            for c in df.columns
        },
    })
print(json.dumps(result, ensure_ascii=False, indent=2))

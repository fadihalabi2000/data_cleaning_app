import json
from pathlib import Path

STORE_PATH = Path(__file__).resolve().parent / "config" / "custom_rules.json"

def load_rules():
    try:
        if STORE_PATH.exists():
            data=json.loads(STORE_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data,list) else []
    except (OSError,json.JSONDecodeError):
        return []
    return []

def save_rules(rules):
    STORE_PATH.parent.mkdir(parents=True,exist_ok=True)
    temporary=STORE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(list(rules),ensure_ascii=False,indent=2),encoding="utf-8")
    temporary.replace(STORE_PATH)

class PersistentRuleList(list):
    def append(self,item):
        super().append(item); save_rules(self)
    def pop(self,index=-1):
        item=super().pop(index); save_rules(self); return item
    def clear(self):
        super().clear(); save_rules(self)
    def remove(self,item):
        super().remove(item); save_rules(self)

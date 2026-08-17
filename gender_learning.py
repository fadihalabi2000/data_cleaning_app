import json
from pathlib import Path
from utils.cleaning import clean_text

STORE=Path(__file__).resolve().parent/"config"/"gender_knowledge.json"

def first_name(value):
    text=clean_text(value)
    return text.split()[0] if text else ""

def canonical_gender(value):
    text=clean_text(value)
    if "أنث" in text or "انث" in text: return "أنثى"
    if "ذكر" in text: return "ذكر"
    return ""

def load_knowledge():
    try:
        data=json.loads(STORE.read_text(encoding="utf-8")) if STORE.exists() else {}
        return data if isinstance(data,dict) else {}
    except (OSError,json.JSONDecodeError): return {}

def save_knowledge(data):
    STORE.parent.mkdir(parents=True,exist_ok=True)
    temp=STORE.with_suffix(".tmp")
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    temp.replace(STORE)

def prediction(name,knowledge,min_examples=2,min_ratio=.90):
    stats=knowledge.get(first_name(name),{})
    male=int(stats.get("ذكر",0)); female=int(stats.get("أنثى",0)); total=male+female
    if total<min_examples: return None
    best_gender,best=max((("ذكر",male),("أنثى",female)),key=lambda item:item[1])
    ratio=best/total if total else 0
    if ratio<min_ratio: return None
    return {"gender":best_gender,"confidence":"عالي" if ratio>=.98 and total>=3 else "متوسط","ratio":ratio,"examples":total}

def learn_consistent_batch(names,genders,knowledge=None,min_batch=2):
    knowledge=knowledge or load_knowledge(); batch={}
    for name,gender in zip(names,genders):
        first=first_name(name); actual=canonical_gender(gender)
        if first and actual:
            batch.setdefault(first,{"ذكر":0,"أنثى":0})[actual]+=1
    changed=False
    for first,counts in batch.items():
        total=counts["ذكر"]+counts["أنثى"]
        # لا نتعلم من ظهور مفرد أو من اسم متناقض داخل الملف نفسه.
        if total>=min_batch and (counts["ذكر"]==0 or counts["أنثى"]==0):
            current=knowledge.setdefault(first,{"ذكر":0,"أنثى":0})
            current["ذكر"]=int(current.get("ذكر",0))+counts["ذكر"]
            current["أنثى"]=int(current.get("أنثى",0))+counts["أنثى"]
            changed=True
    if changed: save_knowledge(knowledge)
    return knowledge

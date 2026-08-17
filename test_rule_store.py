from rule_store import PersistentRuleList

def test_persistent_rule_list_mutations(tmp_path,monkeypatch):
    saved=[]
    monkeypatch.setattr("rule_store.save_rules",lambda rules:saved.append(list(rules)))
    rules=PersistentRuleList()
    rules.append({"name":"قاعدة"})
    assert saved[-1]==[{"name":"قاعدة"}]
    rules.pop()
    assert saved[-1]==[]

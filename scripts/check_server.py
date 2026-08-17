import collections
import json
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=15) as r:
        return r.status, r.read()


st, body = get("/api/parties")
assert st == 200
parties = json.loads(body.decode("utf-8"))
print("parties:", [p["party"] for p in parties])
assert len(parties) == 6
exp = {"Единая Россия": 390, "КПРФ": 332, "Яблоко": 263, "ЛДПР": 10, "Справедливая Россия": 4, "Новые люди": 3}
cnt = {p["party"]: p["count"] for p in parties}
assert cnt == exp, cnt

st, body = get("/api/deputies?limit=2000")
assert st == 200
data = json.loads(body.decode("utf-8"))
print("total:", data["total"], "returned:", data["count"])
assert data["total"] == 1002
assert data["count"] == 1002

names = [x["name"] for x in data["items"]]
assert "Зюганов Геннадий Андреевич" in names
assert "Слуцкий Леонид Эдуардович" in names
assert "Миронов Сергей Михайлович" in names
assert "Нечаев Алексей Геннадиевич" in names
assert "Щербаков Ярослав Евгеньевич" in names
assert all(x["party"] for x in data["items"])
assert all(x["color"] for x in data["items"])
assert all(x["photo"] == "" or x["photo"].startswith("/static/images/photos/") for x in data["items"])
assert all(x["region"] for x in data["items"])
assert all(isinstance(x["list_complete"], bool) for x in data["items"])

with_photo = sum(1 for x in data["items"] if x["photo"])
print("with photo:", with_photo)

c = collections.Counter(x["party"] for x in data["items"])
print("by party:", dict(c))

st, body = get("/")
assert st == 200 and "ГосДума".encode("utf-8") in body
print("index ok")

st, body = get("/api/deputies?party=" + urllib.parse.quote("Яблоко") + "&limit=2000")
ya = json.loads(body.decode("utf-8"))
print("Яблоко count:", ya["count"])
assert all(x["party"] == "Яблоко" for x in ya["items"])

st, body = get("/api/deputies/kprf-0001")
d = json.loads(body.decode("utf-8"))
print("detail:", d["name"], "|", d["party"], "|", d["region"], "|", d["photo"])

print("ALL CHECKS PASSED")

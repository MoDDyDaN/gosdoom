import json
import re
import os

TMP = r"C:\Users\Den\AppData\Local\Temp\opencode"
ROOT = r"C:\gosdoom"

with open(os.path.join(TMP, "duma.html"), encoding="utf-8-sig") as f:
    duma_html = f.read()
with open(os.path.join(TMP, "data.json"), encoding="utf-8-sig") as f:
    data = json.load(f)

# ---------- parse main deputies page ----------
blocks = re.findall(r'<li class="list-persons__item">(.*?)</li>', duma_html, re.S)
print("person blocks:", len(blocks))

person_photo = {}
person_info = {}
for html in blocks:
    m = re.search(r'href="/duma/persons/(\d+)/"', html)
    if not m:
        continue
    pid = m.group(1)
    img = re.search(r'src="(/media/persons/[^"]+?/[^"]+\.(?:jpg|jpeg|png|webp|jfif))"', html, re.I)
    if img:
        person_photo[pid] = "https://duma.gov.ru" + img.group(1)
    fam = re.search(r"<strong>(.*?)</strong>", html, re.S)
    sec = re.search(r'class="second-name">(.*?)</span>', html, re.S)
    post = re.search(r'person__post">(.*?)</div>', html, re.S)
    person_info[pid] = {
        "family": re.sub(r"<[^>]+>", "", fam.group(1)).strip() if fam else "",
        "given": sec.group(1).strip() if sec else "",
        "post": post.group(1).strip() if post else "",
        "html": html,
    }
print("photos:", len(person_photo), "named:", len(person_info))

# inspect missing photos
missing = [pid for pid in person_info if pid not in person_photo]
print("missing photos:", len(missing))
for pid in missing[:3]:
    h = person_info[pid]["html"]
    imgs = re.findall(r"<img[^>]*>", h)
    print("PID", pid, imgs[:2])

# ---------- faction/party maps ----------
faction_short = {
    "72100024": "ЕДИНАЯ РОССИЯ",
    "72100004": "КПРФ",
    "72100005": "ЛДПР",
    "72100035": "НОВЫЕ ЛЮДИ",
    "72100027": "СПРАВЕДЛИВАЯ РОССИЯ",
}
faction_name = {
    "72100024": "Единая Россия",
    "72100004": "Коммунистическая партия Российской Федерации",
    "72100005": "Либерально-демократическая партия России",
    "72100035": "Новые люди",
    "72100027": "Справедливая Россия — За правду",
}
party_color = {
    "72100024": "#0091D3",
    "72100004": "#D40000",
    "72100005": "#004A99",
    "72100035": "#00A9A3",
    "72100027": "#F36A21",
    "72100011": "#6E7781",
}

person_map = {str(p["id"]): p for p in data["persons"]}

deputies = []
for pid, info in person_info.items():
    p = person_map.get(pid)
    party = "ВНЕ ФРАКЦИЙ"
    faction = "Не входит во фракции"
    color = "#9AA0A6"
    region = ""
    committee = ""
    position = ""
    lead = ""
    if p:
        cur = None
        for fp in p.get("fraction_positions", []):
            if fp.get("actual") is True:
                cur = fp
                break
        if cur is None:
            for fp in p.get("fraction_positions", []):
                if fp.get("convocation") == 8:
                    cur = fp
                    break
        if cur:
            org = str(cur.get("org", ""))
            if org in faction_short:
                party = faction_short[org]
                faction = faction_name[org]
                color = party_color[org]
            elif org == "72100011":
                party = "ВНЕ ФРАКЦИЙ"
                faction = "Не входит во фракции"
            else:
                faction = cur.get("org_title") or ""
            region = cur.get("regions_title") or ""
            if not region:
                region = "Федеральный список"
        if p.get("commission_positions"):
            c = p["commission_positions"][0]
            committee = c.get("org_title", "")
            position = c.get("position_text", "")
        lead = p.get("lead", "")

    deputies.append(
        {
            "id": pid,
            "name": (info["family"] + " " + info["given"]).strip(),
            "family": info["family"],
            "given": info["given"],
            "party": party,
            "faction": faction,
            "color": color,
            "region": region,
            "committee": committee,
            "position": position,
            "lead": lead,
            "photo": person_photo.get(pid, ""),
        }
    )

print("deputies total:", len(deputies))
from collections import Counter

for k, v in Counter(d["party"] for d in deputies).items():
    print(f"{k}: {v}")

with open(os.path.join(ROOT, "data", "deputies.json"), "w", encoding="utf-8") as f:
    json.dump(deputies, f, ensure_ascii=False, indent=1)
print("saved data/deputies.json")

"""Build data/candidates.json from parsed federal lists (IX convocation, elections 18-20 Sep 2026).

Sources:
  - Единая Россия: er_list.pdf  -> er_parsed.json (full list, 390)
  - КПРФ:            kprf.html   -> kprf_parsed.json  (full list, 332)
  - Яблоко:          yabloko.html -> yabloko_parsed.json (full list, 263)
  - ЛДПР / Справедливая Россия / Новые люди: only общефедеральная часть published
    (full lists exist only at cikrf.ru, unreachable from this network).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = Path(r"C:\Users\Den\AppData\Local\Temp\opencode")
OUT = ROOT / "data" / "candidates.json"

PARTIES = {
    "Единая Россия":          {"color": "#0091D3", "prefix": "er"},
    "КПРФ":                   {"color": "#D40000", "prefix": "kprf"},
    "ЛДПР":                   {"color": "#004A99", "prefix": "ldpr"},
    "Справедливая Россия":    {"color": "#F36A21", "prefix": "sr"},
    "Новые люди":             {"color": "#00A9A3", "prefix": "nl"},
    "Яблоко":                 {"color": "#2E7D32", "prefix": "yabl"},
}

STATUS = "Кандидат в депутаты Госдумы IX созыва"
LEAD = "Выборы депутатов Государственной Думы IX созыва · 18–20 сентября 2026"


def title_ru(name):
    parts = []
    for w in name.strip().split():
        sub = []
        for part in w.split("-"):
            if not part:
                continue
            sub.append(part[0].upper() + part[1:].lower())
        parts.append("-".join(sub))
    return " ".join(parts)


def norm(name):
    return re.sub(r"\s+", "", name.lower().replace("ё", "е"))


def clean_region(s):
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    return s


def load_photo_map():
    src = ROOT / "data" / "deputies.json"
    if not src.exists():
        return {}
    m = {}
    for d in json.loads(src.read_text(encoding="utf-8")):
        m[norm(d.get("name", ""))] = d.get("photo", "")
    return m


def make_candidate(prefix, name, party, region, group, num, list_complete, photo_map, is_federal):
    name = title_ru(name)
    parts = name.split()
    family = parts[0] if parts else ""
    given = " ".join(parts[1:]) if len(parts) > 1 else ""
    return {
        "id": f"{prefix}-{num:04d}",
        "name": name,
        "family": family,
        "given": given,
        "party": party,
        "faction": party,
        "color": PARTIES[party]["color"],
        "region": region,
        "group": group,
        "list_number": num,
        "committee": STATUS,
        "position": ("Общефедеральная часть" if is_federal else f"Региональная группа · № {num} в списке партии"),
        "lead": LEAD,
        "list_complete": list_complete,
        "photo": photo_map.get(norm(name), ""),
    }


def build():
    photo_map = load_photo_map()
    out = []

    # 1) ЕДИНАЯ РОССИЯ (full)
    er = json.loads((TMP / "er_parsed.json").read_text(encoding="utf-8"))
    pref = PARTIES["Единая Россия"]["prefix"]
    n = 0
    for c in er["federal"]:
        n += 1
        out.append(make_candidate(pref, c["fio"], "Единая Россия",
                                  "Общефедеральная часть", "Общефедеральная часть",
                                  n, True, photo_map, True))
    for c in er["regional"]:
        n += 1
        grp = c["group"]
        region = er["group_region"].get(grp, grp)
        out.append(make_candidate(pref, c["fio"], "Единая Россия",
                                  clean_region(region), grp, n, True, photo_map, False))

    # 2) КПРФ (full)
    kprf = json.loads((TMP / "kprf_parsed.json").read_text(encoding="utf-8"))
    pref = PARTIES["КПРФ"]["prefix"]
    n = 0
    for name in kprf["federal"]:
        n += 1
        out.append(make_candidate(pref, name, "КПРФ",
                                  "Общефедеральная часть", "Общефедеральная часть",
                                  n, True, photo_map, True))
    for g in kprf["groups"]:
        grp = f"Региональная группа № {g['num']}"
        for i, name in enumerate(g["names"], 1):
            n += 1
            out.append(make_candidate(pref, name, "КПРФ",
                                      g["region"], grp, n, True, photo_map, False))

    # 3) ЯБЛОКО (full)
    yab = json.loads((TMP / "yabloko_parsed.json").read_text(encoding="utf-8"))
    pref = PARTIES["Яблоко"]["prefix"]
    n = 0
    for name in yab["federal"]:
        n += 1
        out.append(make_candidate(pref, name, "Яблоко",
                                  "Общефедеральная часть", "Общефедеральная часть",
                                  n, True, photo_map, True))
    for g in yab["groups"]:
        grp = f"Региональная группа № {g['num']}"
        for i, name in enumerate(g["names"], 1):
            n += 1
            out.append(make_candidate(pref, name, "Яблоко",
                                      clean_region(g["region"]), grp, n, True, photo_map, False))

    # 4) ЛДПР (federal part only)
    ldpr = ["Слуцкий Леонид Эдуардович", "Верещагин Алексей", "Воропаева Мария",
            "Луговой Андрей Константинович", "Бут Виктор Анатольевич", "Курдюмов Александр",
            "Жирков Дмитрий", "Свищев Дмитрий Александрович", "Козлов Сергей",
            "Чернышов Борис Александрович"]
    pref = PARTIES["ЛДПР"]["prefix"]
    for i, name in enumerate(ldpr, 1):
        out.append(make_candidate(pref, name, "ЛДПР",
                                  "Общефедеральная часть", "Общефедеральная часть",
                                  i, False, photo_map, True))

    # 5) СПРАВЕДЛИВАЯ РОССИЯ (federal part only)
    sr = ["Миронов Сергей Михайлович", "Бабаков Александр Михайлович",
          "Ким Марина Александровна", "Чернышев Олег"]
    pref = PARTIES["Справедливая Россия"]["prefix"]
    for i, name in enumerate(sr, 1):
        out.append(make_candidate(pref, name, "Справедливая Россия",
                                  "Общефедеральная часть", "Общефедеральная часть",
                                  i, False, photo_map, True))

    # 6) НОВЫЕ ЛЮДИ (federal part only)
    nl = ["Нечаев Алексей Геннадиевич", "Даванков Владислав Андреевич",
          "Авксентьева Сардана Владимировна"]
    pref = PARTIES["Новые люди"]["prefix"]
    for i, name in enumerate(nl, 1):
        out.append(make_candidate(pref, name, "Новые люди",
                                  "Общефедеральная часть", "Общефедеральная часть",
                                  i, False, photo_map, True))

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    from collections import Counter
    cnt = Counter(c["party"] for c in out)
    withphoto = sum(1 for c in out if c["photo"])
    print("total:", len(out), "with photo:", withphoto)
    for k, v in cnt.items():
        print(f"  {k}: {v}")
    print("sample:", out[0]["name"], "|", out[0]["photo"])


if __name__ == "__main__":
    build()

"""Сбор данных о доходах/имуществе кандидатов с Декларатора (декларатор.org / rosdek.org).

Источник: rosdek.org/people/<fio_url> — зеркало Декларатора с данными,
собранными из официальных деклараций (ЦИК, Госдума). Декларатор подтверждает
источники официальными ссылками. С 2023 г. персональные декларации депутатов
официально не публикуются, поэтому берём предвыборные декларации 2025
(кандидаты в ГД 2026) или последние антикоррупционные декларации Госдумы.
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "candidates.json"

SITE = "https://rosdek.org"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

TRANS = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "'", "э": "e", "ю": "iu", "я": "ia",
}


def translit(s: str) -> str:
    return "".join(TRANS.get(c, c) for c in s.lower())


def fio_url(family: str, given: str, patronymic: str = "") -> str:
    parts = [translit(family)] + [translit(w) for w in given.split()]
    if patronymic:
        parts.append(translit(patronymic))
    return "_".join(parts)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower().replace("ё", "е"))


def fetch_page(url: str):
    try:
        r = requests.get(url, timeout=30, headers=HEADERS)
        return r.text if r.status_code == 200 else ""
    except Exception:
        return ""


def parse_declarations(html: str):
    """Парсим блоки деклараций rosdek: тип, должность, орган, доход, площадь, транспорт."""
    blobs = re.findall(r'<div class="Data-content-v-dup".*?(?=<div class="Data-content-v-dup"|</div>\s*</div>\s*</div>\s*</main>)', html, re.S)
    if not blobs:
        blobs = re.findall(r'<div class="Data-content-v-dup".*?</div></div></div></div> <!----> <!----> <!----> <!----></div>', html, re.S)
    decls = []
    for b in blobs:
        def _cap(cls):
            m = re.search(rf'{cls}[^>]*>([^<]*)<', b)
            return m.group(1).strip() if m else ""
        typ = _cap("DecDocumentType-header-")
        pos = _cap("DecDocumentType-position-")
        dep = _cap("DecDocumentType-department-")
        incomes = re.findall(r'DecProgress-caption-[^>]*>([^<]*)<', b)
        veh = re.findall(r'DecVehicleList-count-[^>]*>\s*([\d\s]+)\s*шт\.', b)
        if not typ:
            continue
        d = {
            "type": typ,
            "role": pos,
            "office": dep,
            "income": "",
            "realestate": "",
            "vehicles": "",
            "url": "",
        }
        for inc in incomes:
            inc = inc.replace("\xa0", "")
            if "₽" in inc and not d["income"]:
                m = re.match(r"([\d\s,\.]+)", inc)
                if m:
                    d["income"] = m.group(1).replace(" ", "").replace(",", ".")
            elif "м" in inc:
                m = re.match(r"([\d\s,\.]+)", inc)
                if m:
                    raw = m.group(1).replace(" ", "").replace(",", ".")
                    v = float(raw)
                    if v > (float(d["realestate"]) if d["realestate"] else 0):
                        d["realestate"] = raw
        if veh:
            d["vehicles"] = veh[0].replace(" ", "")
        m = re.search(r'href="(/section/\d+/)"', b)
        if m:
            d["url"] = "https://declarator.org" + m.group(1)
        decls.append(d)
    return decls


def pick_best(decls):
    """Предпочитаем предвыборную декларацию 2025 (кандидат в ГД), иначе последнюю декларацию Госдумы."""
    target = [d for d in decls if "2025" in d["type"] and "кандидат" in d["role"].lower() and "гд" in (d["office"] + d["role"]).lower()]
    if target:
        return target[0]
    for d in decls:
        if "депутат государственной думы" in d["role"].lower() or "государственная дума" in d["office"].lower():
            return d
    return decls[0] if decls else None


def fmt_rub(v: str) -> str:
    if not v:
        return ""
    try:
        n = float(v)
    except ValueError:
        return v
    whole = int(n)
    frac = round((n - whole) * 100)
    s = f"{whole:,}".replace(",", " ")
    if frac:
        s += f",{frac:02d}"
    return s + " ₽"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with OUT.open(encoding="utf-8") as f:
        candidates = json.load(f)

    only = sys.argv[1] if len(sys.argv) > 1 else None
    found = no_decl = 0
    t0 = time.time()
    for i, c in enumerate(candidates):
        if only and c["id"] != only:
            continue
        if c.get("assets"):
            continue
        url = f"{SITE}/people/{fio_url(c['family'], c['given'])}"
        html = fetch_page(url)
        time.sleep(0.1)
        if not html:
            no_decl += 1
            continue
        m = re.search(r"<title>(.*?)</title>", html, re.S)
        if m:
            title = norm(m.group(1))
            want = norm(f"{c['family']} {c['given']}")
            if not title.startswith(want.split()[0]) or want.split()[0] not in title:
                no_decl += 1
                continue
        best = pick_best(parse_declarations(html))
        if not best:
            no_decl += 1
            continue
        assets = []
        if best["income"]:
            assets.append({"type": f"Доход ({best['type']}, {best['role']})", "value": fmt_rub(best["income"])})
        if best["realestate"]:
            assets.append({"type": "Недвижимость (общая площадь)", "value": best["realestate"] + " м²"})
        if best["vehicles"]:
            assets.append({"type": "Транспортные средства", "value": best["vehicles"] + " шт."})
        if not assets:
            no_decl += 1
            continue
        c["assets"] = assets
        c["source"] = {"url": best["url"] or url, "label": "Декларатор (официальные декларации ЦИК/Госдумы)"}
        found += 1
        print(f"{c['id']} {c['name']}: {assets[0]['value'] if assets else '-'}")
        if found % 25 == 0:
            print(f"... прогресс: найдено {found}, обработано {i+1}/{len(candidates)}, {time.time()-t0:.0f}с")
            with OUT.open("w", encoding="utf-8") as f:
                json.dump(candidates, f, ensure_ascii=False, indent=1)

    with OUT.open("w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=1)
    print(f"\nИтого: найдено {found}, без деклараций {no_decl}")


if __name__ == "__main__":
    main()
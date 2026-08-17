import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

ROOT = r"C:\gosdoom"
PHOTO_DIR = os.path.join(ROOT, "static", "images", "photos")

with open(os.path.join(ROOT, "data", "deputies.json"), encoding="utf-8") as f:
    deputies = json.load(f)

os.makedirs(PHOTO_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch(url):
    for scheme in ("http", "https"):
        try:
            r = requests.get(scheme + url[4:] if url.startswith("http:") else url.replace("https://", f"{scheme}://"), timeout=25, headers=HEADERS)
            if r.status_code == 200 and len(r.content) > 100:
                return url, r.content
        except Exception:
            continue
    return url, None


def main():
    existing = {os.path.splitext(f)[0]: f for f in os.listdir(PHOTO_DIR)}
    ok = fail = skip = 0
    tasks = []
    for d in deputies:
        url = d["photo"]
        if url.startswith("/static/"):
            skip += 1
            continue
        if d["id"] in existing:
            d["photo"] = "/static/images/photos/" + existing[d["id"]]
            ok += 1
            skip += 1
            continue
        tasks.append((d["id"], url))

    print("skipped:", skip, "to fetch:", len(tasks))
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(fetch, url): (pid, url) for pid, url in tasks}
        for fut in as_completed(futs):
            pid, url = futs[fut]
            try:
                _, content = fut.result()
            except Exception:
                content = None
            if content:
                ext = os.path.splitext(url)[1] or ".jpg"
                fname = f"{pid}{ext}"
                with open(os.path.join(PHOTO_DIR, fname), "wb") as f:
                    f.write(content)
                for d in deputies:
                    if d["id"] == pid:
                        d["photo"] = "/static/images/photos/" + fname
                        break
                ok += 1
            else:
                for d in deputies:
                    if d["id"] == pid:
                        d["photo"] = ""
                        break
                fail += 1

    with open(os.path.join(ROOT, "data", "deputies.json"), "w", encoding="utf-8") as f:
        json.dump(deputies, f, ensure_ascii=False, indent=1)
    print("ok:", ok, "fail:", fail)


if __name__ == "__main__":
    main()

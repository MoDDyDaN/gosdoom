import json
import os
from pathlib import Path

import subprocess

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "candidates.json"
PARTIES_INFO_FILE = ROOT / "data" / "parties_info.json"

PREV_DEPUTIES_FILE = ROOT / "data" / "deputies.json"

with open(DATA_FILE, encoding="utf-8") as f:
    DEPUTIES = json.load(f)

with open(PARTIES_INFO_FILE, encoding="utf-8") as f:
    PARTIES_INFO = json.load(f)

# Депутаты Госдумы VIII созыва (2021–2026): по ним есть реальные данные о голосованиях.
_prev_names = set()
if PREV_DEPUTIES_FILE.is_file():
    with open(PREV_DEPUTIES_FILE, encoding="utf-8") as f:
        for _pd in json.load(f):
            _prev_names.add(_pd.get("name", "").strip())

for d in DEPUTIES:
    d.setdefault("was_duty", d.get("name", "").strip() in _prev_names)

PARTIES = {}
for d in DEPUTIES:
    key = d["party"]
    if key not in PARTIES:
        PARTIES[key] = {"party": key, "color": d["color"], "count": 0}
    PARTIES[key]["count"] += 1
PARTIES = sorted(PARTIES.values(), key=lambda p: -p["count"])

app = FastAPI(title="Госдума Маркет", version="1.0.0")


@app.get("/api/deputies")
def get_deputies(
    q: str = Query("", description="Поиск по имени/фамилии"),
    party: str = Query("", description="Фракция"),
    region: str = Query("", description="Регион"),
    limit: int = Query(500, ge=1, le=2000),
):
    q = q.strip().lower()
    results = []
    for d in DEPUTIES:
        if q and q not in d["name"].lower():
            continue
        if party and d["party"] != party:
            continue
        if region and region.lower() not in d["region"].lower():
            continue
        results.append(d)
        if len(results) >= limit:
            break
    return {"total": len(DEPUTIES), "count": len(results), "items": results}


@app.get("/api/parties")
def get_parties():
    return PARTIES


@app.get("/api/parties/info")
def get_parties_info():
    return PARTIES_INFO


@app.get("/api/deputies/{deputy_id}")
def get_deputy(deputy_id: str):
    for d in DEPUTIES:
        if d["id"] == deputy_id:
            return d
    return {"error": "not found"}


@app.get("/")
def index():
    return FileResponse(ROOT / "templates" / "index.html")


@app.get("/parties")
def parties_page():
    return FileResponse(ROOT / "templates" / "parties.html")


@app.get("/parliament")
def parliament_page():
    return FileResponse(ROOT / "templates" / "parliament.html")


@app.get("/process")
def process_page():
    return FileResponse(ROOT / "templates" / "process.html")


@app.get("/video")
def video_page():
    return FileResponse(ROOT / "templates" / "video.html")


@app.get("/duels")
def duels_page():
    return FileResponse(ROOT / "templates" / "duels.html")

DUELS_FILE = ROOT / "data" / "duels.json"


@app.get("/api/duels")
def get_duels(region: str = Query("", description="Регион (субъект РФ)")):
    if not DUELS_FILE.is_file():
        return {"regions": [], "duels": []}
    with open(DUELS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    regions = sorted({d["region"] for d in data.get("duels", [])})
    duels = [d for d in data.get("duels", []) if (not region or d["region"] == region)]
    return {"regions": regions, "region": region, "count": len(duels), "duels": duels}


VIDEO_EXTS = {".mp4", ".webm", ".ogv", ".ogg", ".mov", ".m4v", ".mkv"}

VIDEO_TITLES = {
    "gosduma-golosovanie": "За что голосовала Госдума",
    "newpeople-starye-lica": "«Новые люди» — старые лица. Красивый проект Единой России",
}


def _video_duration(path: Path) -> int:
    if imageio_ffmpeg is None:
        return 0
    try:
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        out = subprocess.run(
            [exe, "-i", str(path)],
            capture_output=True,
            text=True,
            errors="ignore",
            timeout=30,
        ).stderr
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Duration:"):
                d = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = d.split(":")
                return int(h) * 3600 + int(m) * 60 + int(float(s))
    except Exception:
        pass
    return 0


@app.get("/api/videos")
def get_videos():
    videos_dir = ROOT / "static" / "videos"
    thumbs_dir = ROOT / "static" / "images" / "thumbs"
    items = []
    if videos_dir.is_dir():
        for path in sorted(videos_dir.iterdir(), key=lambda p: p.name.lower()):
            if path.is_file() and path.suffix.lower() in VIDEO_EXTS and path.stem[0] != ".":
                poster = thumbs_dir / f"{path.stem}.jpg"
                items.append(
                    {
                        "name": path.stem,
                        "title": VIDEO_TITLES.get(path.stem, path.stem),
                        "file": path.name,
                        "url": f"/static/videos/{path.name}",
                        "poster": (
                            f"/static/images/thumbs/{path.stem}.jpg"
                            if poster.is_file()
                            else ""
                        ),
                        "duration": _video_duration(path),
                        "size": path.stat().st_size,
                    }
                )
    return {"count": len(items), "items": items}


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)

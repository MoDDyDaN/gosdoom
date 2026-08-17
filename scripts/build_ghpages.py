"""Сборка статической версии сайта для GitHub Pages в папку docs/.

Запуск: python scripts/build_ghpages.py
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"

PAGE_RENAMES = {
    "/": "index.html",
    "/parties": "parties.html",
    "/parliament": "parliament.html",
    "/process": "process.html",
    "/video": "video.html",
    "/duels": "duels.html",
}

PAGES = ["index", "parties", "parliament", "process", "video", "duels"]


def clean(out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)


def copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst)


def rewrite_abs_paths(text: str) -> str:
    text = text.replace('"/static/', '"static/').replace("'/static/", "'static/")
    for route, page in PAGE_RENAMES.items():
        if route == "/":
            continue
        text = text.replace(f'href="{route}"', f'href="{page}"')
    text = text.replace('href="/"', 'href="index.html"')
    return text


def build_html() -> None:
    for name in PAGES:
        src = ROOT / "templates" / f"{name}.html"
        text = src.read_text(encoding="utf-8")
        text = rewrite_abs_paths(text)
        (OUT / f"{name}.html").write_text(text, encoding="utf-8")


def build_static() -> None:
    for sub in ("css", "js", "images"):
        copy_tree(ROOT / "static" / sub, OUT / "static" / sub)
    for js in OUT.glob("static/js/*.js"):
        text = js.read_text(encoding="utf-8")
        text = text.replace('"/static/', '"static/').replace("'/static/", "'static/")
        text = text.replace("`/static/", "`static/")
        js.write_text(text, encoding="utf-8")


def rewrite_api_js() -> None:
    """Переписываем fetch к /api/* на статические JSON в app.js, duels.js, party-info.js."""
    app = OUT / "static" / "js" / "app.js"
    text = app.read_text(encoding="utf-8")
    text = text.replace(
        'fetch("/api/deputies?limit=2000").then((r) => r.json()),',
        'fetch("data/candidates.json").then((r) => r.json()),',
    )
    text = text.replace(
        'fetch("/api/parties").then((r) => r.json()),',
        'fetch("data/parties.json").then((r) => r.json()),',
    )
    text = text.replace(
        """      const [deputies, parties] = await Promise.all([
        fetch("data/candidates.json").then((r) => r.json()),
        fetch("data/parties.json").then((r) => r.json()),
      ]);
      state.deputies = deputies.items;
      state.parties = parties;
      totalStat.textContent = `${deputies.total} кандидатов`;""",
        """      const [candidates, parties] = await Promise.all([
        fetch("data/candidates.json").then((r) => r.json()),
        fetch("data/parties.json").then((r) => r.json()),
      ]);
      state.deputies = candidates;
      state.parties = parties;
      totalStat.textContent = `${candidates.length} кандидатов`;""",
    )
    text = text.replace(
        'fetch("/api/parties/info").then((r) => r.json());',
        'fetch("data/parties_info.json").then((r) => r.json());',
    )
    app.write_text(text, encoding="utf-8")

    info = OUT / "static" / "js" / "party-info.js"
    text = info.read_text(encoding="utf-8")
    text = text.replace(
        'fetch("/api/parties/info").then((r) => r.json());',
        'fetch("data/parties_info.json").then((r) => r.json());',
    )
    info.write_text(text, encoding="utf-8")

    duels = OUT / "static" / "js" / "duels.js"
    text = duels.read_text(encoding="utf-8")
    text = text.replace(
        'fetch("/api/duels").then((r) => r.json()),',
        'fetch("data/duels.json").then((r) => r.json()),',
    )
    text = text.replace(
        'fetch("/api/deputies?limit=2000").then((r) => r.json()),',
        'fetch("data/candidates.json").then((r) => r.json()),',
    )
    text = text.replace(
        """      const [duels, deputies] = await Promise.all([
        fetch("data/duels.json").then((r) => r.json()),
        fetch("data/candidates.json").then((r) => r.json()),
      ]);
      const byId = new Map(deputies.items.map((x) => [x.id, x]));
      state.duels = duels.duels.map((d) => ({
        ...d,
        a: { ...(byId.get(d.a.id) || d.a), ...d.a },
        b: { ...(byId.get(d.b.id) || d.b), ...d.b },
      }));
      state.deputies = deputies.items;
      state.regions = duels.regions;""",
        """      const [duelsData, candidates] = await Promise.all([
        fetch("data/duels.json").then((r) => r.json()),
        fetch("data/candidates.json").then((r) => r.json()),
      ]);
      const byId = new Map(candidates.map((x) => [x.id, x]));
      state.duels = duelsData.duels.map((d) => ({
        ...d,
        a: { ...(byId.get(d.a.id) || d.a), ...d.a },
        b: { ...(byId.get(d.b.id) || d.b), ...d.b },
      }));
      state.deputies = candidates;
      state.regions = [...new Set(duelsData.duels.map((d) => d.region))].sort();""",
    )
    text = text.replace(
        'fetch("/api/parties/info").then((r) => r.json());',
        'fetch("data/parties_info.json").then((r) => r.json());',
    )
    duels.write_text(text, encoding="utf-8")


def build_data() -> None:
    (OUT / "data").mkdir(parents=True)

    candidates_raw = (ROOT / "data" / "candidates.json").read_text(encoding="utf-8")
    candidates = json.loads(candidates_raw)
    parties = {}
    for d in candidates:
        key = d["party"]
        if key not in parties:
            parties[key] = {"party": key, "color": d["color"], "count": 0}
        parties[key]["count"] += 1
    parties = sorted(parties.values(), key=lambda p: -p["count"])
    (OUT / "data" / "parties.json").write_text(
        json.dumps(parties, ensure_ascii=False), encoding="utf-8"
    )

    for name in ("candidates.json", "parties_info.json", "duels.json"):
        text = (ROOT / "data" / name).read_text(encoding="utf-8")
        text = text.replace('"/static/', '"static/')
        (OUT / "data" / name).write_text(text, encoding="utf-8")


def build_video_js() -> None:
    """На GitHub Pages видео не хостится — показываем пустое состояние."""
    js = OUT / "static" / "js" / "video.js"
    text = js.read_text(encoding="utf-8")
    text = re.sub(
        r"fetch\(\"/api/videos\"\).*?\.catch\(function \(\) \{\s*showEmpty\(\);\s*\}\);",
        "showEmpty();",
        text,
        flags=re.S,
    )
    js.write_text(text, encoding="utf-8")


def main() -> None:
    clean(OUT)
    build_html()
    build_static()
    build_data()
    rewrite_api_js()
    build_video_js()
    print(f"Готово: {OUT}")


if __name__ == "__main__":
    main()
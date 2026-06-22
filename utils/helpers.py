from __future__ import annotations

import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterator, Tuple


# ─── Slug ────────────────────────────────────────────────────────────────────

def safe_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"


# ─── File helpers ────────────────────────────────────────────────────────────

def bundle_zip(md_text: str, md_filename: str, images_dir: Path) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(md_filename, md_text.encode("utf-8"))
        if images_dir.exists() and images_dir.is_dir():
            for p in images_dir.rglob("*"):
                if p.is_file():
                    z.write(p, arcname=str(p))
    return buf.getvalue()


def list_past_blogs() -> List[Path]:
    cwd = Path(".")
    files = [p for p in cwd.glob("*.md") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def read_md_file(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def extract_title_from_md(md: str, fallback: str = "Untitled") -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            t = line[2:].strip()
            return t or fallback
    return fallback


# ─── Streaming helper ────────────────────────────────────────────────────────

def try_stream(graph_app, inputs: Dict[str, Any], config: Dict) -> Iterator[Tuple[str, Any]]:
    try:
        for step in graph_app.stream(inputs, config=config, stream_mode="updates"):
            yield ("updates", step)
        out = graph_app.invoke(inputs, config=config)
        yield ("final", out)
        return
    except Exception:
        pass

    out = graph_app.invoke(inputs, config=config)
    yield ("final", out)


def extract_latest_state(current: Dict, payload: Any) -> Dict:
    if isinstance(payload, dict):
        if len(payload) == 1 and isinstance(next(iter(payload.values())), dict):
            current.update(next(iter(payload.values())))
        else:
            current.update(payload)
    return current

import asyncio
import hashlib
import io
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image

CACHE = Path.home() / ".cache" / "baldwin"


def _fetch(url: str) -> bytes | None:
    try:
        if url.startswith("file://"):
            return Path(unquote(urlparse(url).path)).read_bytes()
        if url.startswith(("http://", "https://")):
            CACHE.mkdir(parents=True, exist_ok=True)
            f = CACHE / hashlib.sha1(url.encode()).hexdigest()
            if not f.exists():
                with urllib.request.urlopen(url, timeout=5) as r:
                    f.write_bytes(r.read())
            return f.read_bytes()
    except Exception:
        pass
    return None


async def load(url: str) -> Image.Image | None:
    if not url:
        return None
    data = await asyncio.to_thread(_fetch, url)
    if not data:
        return None
    try:
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        return None


def placeholder() -> Image.Image:
    return Image.new("RGB", (64, 64), (40, 40, 48))


def accents(img: Image.Image, n: int = 3) -> list[str]:
    """Dominant, reasonably saturated/bright colors as hex strings."""
    small = img.resize((64, 64)).quantize(colors=8)
    pal = small.getpalette()[: 8 * 3]
    counts = sorted(small.getcolors(), reverse=True)
    out = []
    for _, idx in counts:
        r, g, b = pal[idx * 3: idx * 3 + 3]
        if max(r, g, b) < 70 or max(r, g, b) - min(r, g, b) < 25:
            continue
        out.append(f"#{r:02x}{g:02x}{b:02x}")
    defaults = ["#7aa2f7", "#bb9af7", "#7dcfff"]
    return (out + defaults)[:n]

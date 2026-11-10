"""Accent colors for baldwin, in priority order:

1. user override   ($BALDWIN_ACCENT or ~/.config/baldwin/config.toml)
2. the live terminal palette, asked via OSC 4 (kitty, Alacritty, WezTerm, foot, Ghostty,
   iTerm2, GNOME Terminal/VTE, Konsole, xterm, ...)
3. terminal config files (kitty incl. `include`, Alacritty toml + imports, foot, Ghostty,
   .Xresources)
4. a default red

The accent is a 3-step ramp built from one ANSI hue (red by default): the normal color,
the bright color, and a lightened bright color.
"""
import functools
import glob
import os
import re
import select
import time
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python 3.10
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

NAMES = {"red": 1, "green": 2, "yellow": 3, "blue": 4, "magenta": 5, "cyan": 6}
FALLBACK = {1: ("#d7263d", "#ff4d5e"), 2: ("#2ea043", "#56d364"), 3: ("#d29922", "#e3b341"),
            4: ("#388bfd", "#79c0ff"), 5: ("#a371f7", "#d2a8ff"), 6: ("#1b7c83", "#56d4dd")}
SLOTS = [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14]
HEX = re.compile(r"#?([0-9a-fA-F]{6})")


def _hex(v) -> str | None:
    if not isinstance(v, str):
        return None
    v = v.strip().strip("\"'")
    if v.lower().startswith("0x"):
        v = v[2:]
    m = HEX.fullmatch(v)
    return "#" + m[1].lower() if m else None


def mix(a: str, b: str, t: float) -> str:
    """Blend hex color a toward b by t (0..1)."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(ca, cb))


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


# ---- terminal config files -> {ansi index: "#rrggbb"} ---------------------------------

def _kitty(path: Path, depth=0) -> dict:
    pal: dict = {}
    if depth > 5:
        return pal
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return pal
    for line in lines:
        parts = line.split(None, 1)
        if len(parts) != 2 or parts[0].startswith("#"):
            continue
        key, val = parts[0], parts[1].split()[0]
        if key in ("include", "globinclude"):
            pattern = os.path.expanduser(parts[1].strip())
            if not os.path.isabs(pattern):
                pattern = str(path.parent / pattern)
            for f in sorted(glob.glob(pattern)):
                pal.update(_kitty(Path(f), depth + 1))
        elif (m := re.fullmatch(r"color(\d+)", key)) and _hex(val):
            pal[int(m[1])] = _hex(val)
    return pal


def read_kitty() -> dict:
    dirs = [os.environ.get("KITTY_CONFIG_DIRECTORY"), config_home() / "kitty",
            Path.home() / ".config" / "kitty"]
    for d in filter(None, dirs):
        pal = _kitty(Path(d) / "kitty.conf")
        if pal:
            return pal
    return {}


def _alacritty(path: Path, depth=0) -> dict:
    if tomllib is None or depth > 5:
        return {}
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    pal: dict = {}
    imports = list(data.get("general", {}).get("import", [])) + list(data.get("import", []))
    for imp in imports:
        p = Path(os.path.expanduser(str(imp)))
        pal.update(_alacritty(p if p.is_absolute() else path.parent / p, depth + 1))
    colors = data.get("colors", {})
    for group, off in (("normal", 0), ("bright", 8)):
        g = colors.get(group, {})
        for name, i in NAMES.items():
            if isinstance(g, dict) and _hex(g.get(name)):
                pal[i + off] = _hex(g[name])
    return pal


def read_alacritty() -> dict:
    return _alacritty(config_home() / "alacritty" / "alacritty.toml")


def read_foot() -> dict:
    pal: dict = {}
    try:
        lines = (config_home() / "foot" / "foot.ini").read_text().splitlines()
    except OSError:
        return pal
    section = ""
    for line in lines:
        line = line.strip()
        if line.startswith("["):
            section = line.strip("[]")
        elif section.startswith("colors") and (m := re.match(r"(regular|bright)(\d)\s*=\s*(\S+)", line)):
            if _hex(m[3]):
                pal[int(m[2]) + (8 if m[1] == "bright" else 0)] = _hex(m[3])
    return pal


def _ghostty_file(path: Path) -> dict:
    pal: dict = {}
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return pal
    theme = None
    for line in lines:
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key == "theme":
            theme = val.strip("\"'")
        elif key == "palette" and (m := re.match(r"(\d+)\s*=\s*(\S+)", val)) and _hex(m[2]):
            pal[int(m[1])] = _hex(m[2])
    if theme:  # user theme files; explicit palette lines in the config win
        pal = {**_ghostty_file(path.parent / "themes" / theme), **pal}
    return pal


def read_ghostty() -> dict:
    for name in ("config", "config.ghostty"):
        pal = _ghostty_file(config_home() / "ghostty" / name)
        if pal:
            return pal
    return {}


def read_xresources() -> dict:
    pal: dict = {}
    for name in (".Xresources", ".Xdefaults"):
        try:
            text = (Path.home() / name).read_text()
        except OSError:
            continue
        for m in re.finditer(r"color(\d+)\s*:\s*(#[0-9a-fA-F]{6})", text):
            pal[int(m[1])] = _hex(m[2])
    return pal


def _file_readers():
    """Readers ordered so the terminal we appear to be running in is tried first."""
    env = os.environ
    term = (env.get("TERM", "") + " " + env.get("TERM_PROGRAM", "")).lower()
    order = [("kitty", read_kitty), ("alacritty", read_alacritty), ("foot", read_foot),
             ("ghostty", read_ghostty)]
    here = [r for n, r in order if n in term or (n == "kitty" and env.get("KITTY_WINDOW_ID"))
            or (n == "ghostty" and env.get("GHOSTTY_RESOURCES_DIR"))
            or (n == "alacritty" and env.get("ALACRITTY_SOCKET"))]
    rest = [r for _, r in order if r not in here]
    return here + rest + [read_xresources]


# ---- live palette via OSC 4 -----------------------------------------------------------

def parse_osc(buf: bytes) -> dict:
    pal = {}
    pat = rb"\x1b\]4;(\d+);rgb:([0-9a-fA-F]{1,4})/([0-9a-fA-F]{1,4})/([0-9a-fA-F]{1,4})"
    for m in re.finditer(pat, buf):
        comps = [int(m[k], 16) / (16 ** len(m[k]) - 1) for k in (2, 3, 4)]
        pal[int(m[1])] = "#%02x%02x%02x" % tuple(round(c * 255) for c in comps)
    return pal


def query_terminal(fd: int | None = None, timeout: float = 0.4) -> dict:
    """Ask the terminal for its palette. A trailing DA1 query marks the end of the replies,
    so terminals without OSC 4 support don't make us wait the full timeout."""
    try:
        import termios
        import tty
    except ImportError:  # not a POSIX system
        return {}
    own = fd is None
    if own:
        try:
            fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
        except OSError:
            return {}
    try:
        old = termios.tcgetattr(fd)
    except termios.error:
        if own:
            os.close(fd)
        return {}
    buf = b""
    try:
        tty.setcbreak(fd)
        os.write(fd, b"".join(b"\x1b]4;%d;?\x1b\\" % i for i in SLOTS) + b"\x1b[c")
        end = time.monotonic() + timeout
        while (left := end - time.monotonic()) > 0:
            if not select.select([fd], [], [], left)[0]:
                break
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            buf += chunk
            if re.search(rb"\x1b\[\?[\d;]*c", buf):
                break
    except OSError:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        if own:
            os.close(fd)
    return parse_osc(buf)


def detect_palette() -> dict:
    pal = query_terminal()
    if pal:
        return pal
    for reader in _file_readers():
        pal = reader()
        if pal:
            return pal
    return {}


# ---- user override + final ramp -------------------------------------------------------

def _override() -> list[str] | None:
    v = os.environ.get("BALDWIN_ACCENT")
    if not v and tomllib is not None:
        try:
            v = tomllib.loads((config_home() / "baldwin" / "config.toml").read_text()).get("accent")
        except (OSError, ValueError):
            v = None
    if isinstance(v, str):
        v = v.split(",")
    if isinstance(v, list):
        v = [str(x).strip() for x in v if str(x).strip()]
    return v or None


def ramp(low: str | None, high: str | None) -> list[str]:
    if low and high:
        return [low, high, mix(high, "#ffffff", 0.35)]
    base = low or high
    return [mix(base, "#000000", 0.2), base, mix(base, "#ffffff", 0.35)]


@functools.lru_cache(maxsize=1)
def load() -> list[str]:
    """Three accent colors, darkest to lightest."""
    ov = _override()
    slot = 1
    if ov:
        hexes = [_hex(x) for x in ov]
        if all(hexes):
            return ramp(hexes[0], hexes[1]) if len(hexes) < 3 else hexes[:3]
        slot = NAMES.get(ov[0].lower(), 1)
    pal = detect_palette()
    low, high = pal.get(slot), pal.get(slot + 8)
    if not (low or high):
        low, high = FALLBACK[slot]
    return ramp(low, high)

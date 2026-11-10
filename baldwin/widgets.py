import time

import numpy as np
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from . import audio
from .mpris import Track

BLOCKS = " ▁▂▃▄▅▆▇█"


def _rgb(h: str):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def gradient(colors: list[str], n: int) -> list[str]:
    stops = [_rgb(c) for c in colors]
    out = []
    for i in range(n):
        t = i / max(n - 1, 1) * (len(stops) - 1)
        a = min(int(t), len(stops) - 2)
        f = t - a
        c = [round(stops[a][k] + (stops[a + 1][k] - stops[a][k]) * f) for k in range(3)]
        out.append("#%02x%02x%02x" % tuple(c))
    return out


def fmt_time(s: float) -> str:
    s = int(max(s, 0))
    return f"{s // 60:02d}:{s % 60:02d}"


class Banner(Widget):
    """Top rule: `-=[ baldwin ]=-----...` filled to the full width with dashes."""
    DEFAULT_CSS = "Banner { height: 1; margin-bottom: 1; }"
    accent = reactive("#ff4d5e")

    def render(self) -> Text:
        w = self.size.width
        head = "-=[ "
        t = Text(head, style="dim")
        t.append("baldwin", style=f"bold {self.accent}")
        t.append(" ]=", style="dim")
        t.append("-" * max(w - len(t.plain), 0), style="dim")
        return t


class InfoPanel(Static):
    """fastfetch-style key/value block."""

    DEFAULT_CSS = "InfoPanel { height: auto; border: ascii; padding: 0 2; }"

    def show(self, t: Track, accents: list[str]):
        a, b = accents[0], accents[1]
        self.styles.border = ("ascii", b)
        self.border_title = f"[ {t.artist or 'unknown'} @ {t.player or 'player'} ]"
        self.border_subtitle = f"[ {t.status.lower()} ]"
        out = Text()
        rows = [("Title", t.title), ("Artist", t.artist), ("Album", t.album),
                ("Player", t.player), ("Status", t.status),
                ("Volume", f"{round(t.volume * 100)}%"),
                ("Shuffle", "on" if t.shuffle else "off"), ("Loop", t.loop)]
        for k, v in rows:
            out.append(f"{k:<8}", style=f"bold {a}")
            out.append((v or "-") + "\n")
        for c in accents:
            out.append("   ", style=f"on {c}")
        self.update(out)


class ArtFooter(Widget):
    """Decorative ASCII strip under the info panel, fading through the accent colors."""
    DEFAULT_CSS = "ArtFooter { height: 2; margin-top: 1; }"
    colors = reactive(["#d7263d", "#ff4d5e", "#ff8fa3"])
    ROWS = (".-'-._", "'  '  '")

    def render(self) -> Text:
        w = self.size.width
        cols = gradient(self.colors, max(w, 2))
        out = Text()
        for r, pat in enumerate(self.ROWS):
            for i in range(w):
                out.append(pat[i % len(pat)], style=cols[i])
            if r < len(self.ROWS) - 1:
                out.append("\n")
        return out


class Visualizer(Widget):
    DEFAULT_CSS = "Visualizer { height: 1fr; min-height: 3; }"
    colors = reactive(["#d7263d", "#ff4d5e", "#ff8fa3"])
    playing = reactive(False)

    # Smoothing ported from cava's cavacore with its defaults (noise_reduction 0.77, 60 fps):
    # instant attack, quadratic gravity fall, leaky integral, slow autosens.
    NR = 0.77
    FPS = 60
    GRAVITY = (60 / FPS) ** 2.5 * 1.54 / NR

    def on_mount(self):
        self.cap = audio.Capture()
        self.sens = 0.1
        self.acc = 0.0
        self.last = time.monotonic()
        self._reset(1)
        self.set_interval(1 / self.FPS, self.refresh)

    def on_unmount(self):
        self.cap.close()

    def _reset(self, n: int):
        self.peak = np.zeros(n)
        self.fall = np.zeros(n)
        self.mem = np.zeros(n)
        self.prev = np.zeros(n)
        self.levels = np.zeros(n)

    def _step(self, raw: np.ndarray, silent: bool):
        out = raw * self.sens
        falling = out < self.prev
        fell = np.clip(self.peak * (1 - self.fall ** 2 * self.GRAVITY), 0, None)
        out = np.where(falling, fell, out)
        self.fall = np.where(falling, self.fall + 0.028, 0.0)
        self.peak = np.where(falling, self.peak, out)
        self.prev = out
        out = self.mem * self.NR + out
        self.mem = out
        if out.max() > 1.0:  # autosens
            self.sens *= 0.98
        elif not silent:
            self.sens *= 1.001
        self.levels = np.clip(out, 0, 1)

    def _update_levels(self, n: int):
        now = time.monotonic()
        self.acc += min(now - self.last, 0.1) * self.FPS
        self.last = now
        if len(self.levels) != n:
            self._reset(n)
        playing = self.cap.ok and self.playing
        if playing:
            raw = np.log1p(audio.bands(self.cap.snapshot(), n) * 200)
            raw *= np.linspace(0.8, 1.4, n)  # tilt: highs carry less energy
        else:
            raw = np.zeros(n)
        while self.acc >= 1:  # fixed 60 Hz steps like cava
            self.acc -= 1
            self._step(raw, silent=not playing)

    def render(self) -> Text:
        w, h = self.size
        if w < 2 or h < 1:
            return Text("")
        n = max(w // 3, 1)  # cava default: bar width 2 + spacing 1
        self._update_levels(n)
        cols = gradient(self.colors, n)
        eighths = (self.levels * h * 8).astype(int)
        out = Text()
        for row in range(h):  # row 0 = top
            base = (h - 1 - row) * 8
            for i in range(n):
                v = min(max(eighths[i] - base, 0), 8)
                out.append(BLOCKS[v] * 2 + " ", style=cols[i])
            if row < h - 1:
                out.append("\n")
        return out


class TimeBar(Widget):
    DEFAULT_CSS = "TimeBar { height: 1; }"
    position = reactive(0.0)
    length = reactive(0.0)
    accent = reactive("#ff4d5e")

    class Seek(Message):
        def __init__(self, seconds: float):
            super().__init__()
            self.seconds = seconds

    def _bar_span(self):
        left = len(fmt_time(self.position)) + 1
        right = len(fmt_time(self.length)) + 1
        return left, max(self.size.width - left - right, 1)

    def render(self) -> Text:
        left, width = self._bar_span()
        frac = self.position / self.length if self.length else 0
        filled = min(int(frac * width), width - 1)
        t = Text(fmt_time(self.position) + " ")
        t.append("━" * filled, style=self.accent)
        t.append("●", style=f"bold {self.accent}")
        t.append("─" * (width - filled - 1), style="dim")
        t.append(" " + fmt_time(self.length))
        return t

    def on_click(self, e):
        if not self.length:
            return
        left, width = self._bar_span()
        frac = min(max((e.x - left) / width, 0), 1)
        self.post_message(self.Seek(frac * self.length))


class ControlButton(Widget):
    """Small boxed ASCII button; `lit` highlights it (e.g. shuffle on)."""
    DEFAULT_CSS = "ControlButton { width: 12; height: 3; margin: 0 1; }"
    glyph = reactive("")
    lit = reactive(False)
    accent = reactive("#ff4d5e")

    class Pressed(Message):
        def __init__(self, button: "ControlButton"):
            super().__init__()
            self.button = button

    def __init__(self, glyph: str, id: str, big: bool = False):
        super().__init__(id=id)
        self.glyph = glyph
        self.big = big

    def render(self) -> Text:
        w = self.size.width
        hot = self.lit or self.big or self.is_mouse_over
        style = f"bold {self.accent}" if hot else "dim"
        if self.is_mouse_over:
            style += " reverse"
        tl, tr, bl, br, h = ("╔", "╗", "╚", "╝", "═") if self.big else ("╭", "╮", "╰", "╯", "─")
        v = "║" if self.big else "│"
        return Text(f"{tl}{h * (w - 2)}{tr}\n{v}{self.glyph.center(w - 2)}{v}\n{bl}{h * (w - 2)}{br}",
                    style=style)

    def on_click(self):
        self.post_message(self.Pressed(self))

    def watch_mouse_over(self, _):
        self.refresh()


class Controls(Horizontal):
    DEFAULT_CSS = "Controls { height: 3; align: center middle; }"

    def compose(self) -> ComposeResult:
        yield ControlButton("><", "shuffle")
        yield ControlButton("|<<", "prev")
        yield ControlButton("> PLAY", "play", big=True)
        yield ControlButton(">>|", "next")
        yield ControlButton("(@)", "loop")

    def sync(self, t: Track, accent: str):
        for b in self.query(ControlButton):
            b.accent = accent
        self.query_one("#play", ControlButton).glyph = "|| PAUSE" if t.status == "Playing" else "> PLAY"
        self.query_one("#shuffle", ControlButton).lit = t.shuffle
        loop = self.query_one("#loop", ControlButton)
        loop.lit = t.loop != "None"
        loop.glyph = "(1)" if t.loop == "Track" else "(@)"

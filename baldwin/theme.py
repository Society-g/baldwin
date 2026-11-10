"""Accent colors read from the kitty config so baldwin follows the terminal theme."""
import re
from pathlib import Path

FALLBACK = {"color1": "#d7263d", "color9": "#ff4d5e", "color10": "#ff8fa3",
            "color11": "#ffb07a"}


def load() -> list[str]:
    colors = dict(FALLBACK)
    try:
        for line in (Path.home() / ".config/kitty/kitty.conf").read_text().splitlines():
            m = re.match(r"\s*(color\d+)\s+(#[0-9a-fA-F]{6})\s*$", line)
            if m:
                colors[m[1]] = m[2]
    except OSError:
        pass
    return [colors["color1"], colors["color9"], colors["color10"]]

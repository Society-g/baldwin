import os
import pty
import threading

import pytest

from baldwin import theme


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
    for v in ("KITTY_CONFIG_DIRECTORY", "BALDWIN_ACCENT"):
        monkeypatch.delenv(v, raising=False)
    theme.load.cache_clear()
    monkeypatch.setattr(theme, "query_terminal", lambda *a, **k: {})
    yield tmp_path
    theme.load.cache_clear()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_default_red(isolated):
    assert theme.load() == theme.ramp("#d7263d", "#ff4d5e")


def test_kitty_follows_include(isolated):
    write(isolated / ".config/kitty/kitty.conf", "include current-theme.conf\n")
    write(isolated / ".config/kitty/current-theme.conf", "color1 #112233\ncolor9 #445566\n")
    assert theme.load()[:2] == ["#112233", "#445566"]


def test_kitty_config_dir_env(isolated, monkeypatch):
    write(isolated / "elsewhere/kitty.conf", "color1 #010203\ncolor9 #040506\n")
    monkeypatch.setenv("KITTY_CONFIG_DIRECTORY", str(isolated / "elsewhere"))
    assert theme.load()[:2] == ["#010203", "#040506"]


def test_alacritty_import(isolated):
    write(isolated / ".config/alacritty/theme.toml",
          '[colors.normal]\nred = "#aa0000"\n[colors.bright]\nred = "0xff5555"\n')
    write(isolated / ".config/alacritty/alacritty.toml", 'general.import = ["theme.toml"]\n')
    assert theme.load()[:2] == ["#aa0000", "#ff5555"]


def test_foot(isolated):
    write(isolated / ".config/foot/foot.ini", "[colors]\nregular1=cc0000\nbright1=ff3333\n")
    assert theme.load()[:2] == ["#cc0000", "#ff3333"]


def test_ghostty_palette_and_theme(isolated):
    write(isolated / ".config/ghostty/themes/mine", "palette = 1=#123456\npalette = 9=#abcdef\n")
    write(isolated / ".config/ghostty/config", "theme = mine\npalette = 9=#fedcba\n")
    assert theme.load()[:2] == ["#123456", "#fedcba"]


def test_xresources(isolated):
    write(isolated / ".Xresources", "*.color1: #bb0000\n*.color9: #ff0000\n")
    assert theme.load()[:2] == ["#bb0000", "#ff0000"]


def test_override_name_and_hex(isolated, monkeypatch):
    write(isolated / ".config/foot/foot.ini", "[colors]\nregular4=0000aa\nbright4=5555ff\n")
    monkeypatch.setenv("BALDWIN_ACCENT", "blue")
    assert theme.load()[:2] == ["#0000aa", "#5555ff"]
    theme.load.cache_clear()
    monkeypatch.setenv("BALDWIN_ACCENT", "#111111,#222222,#333333")
    assert theme.load() == ["#111111", "#222222", "#333333"]


def test_override_config_file(isolated):
    write(isolated / ".config/baldwin/config.toml", 'accent = ["#101010", "#202020"]\n')
    assert theme.load()[:2] == ["#101010", "#202020"]


def test_osc_beats_files(isolated, monkeypatch):
    write(isolated / ".config/foot/foot.ini", "[colors]\nregular1=cc0000\nbright1=ff3333\n")
    monkeypatch.setattr(theme, "query_terminal", lambda *a, **k: {1: "#0a0a0a", 9: "#0b0b0b"})
    assert theme.load()[:2] == ["#0a0a0a", "#0b0b0b"]


def test_parse_osc_widths():
    buf = (b"\x1b]4;1;rgb:ffff/0000/8080\x1b\\\x1b]4;9;rgb:f/0/8\x07\x1b[?62;c")
    assert theme.parse_osc(buf) == {1: "#ff0080", 9: "#ff0088"}


def test_query_terminal_over_pty(monkeypatch):
    monkeypatch.undo()  # use the real query_terminal for this test
    master, slave = pty.openpty()

    def fake_terminal():
        os.read(master, 4096)  # the queries
        os.write(master, b"\x1b]4;1;rgb:d7d7/2626/3d3d\x1b\\\x1b]4;9;rgb:ffff/4d4d/5e5e\x1b\\\x1b[?62;4c")

    t = threading.Thread(target=fake_terminal)
    t.start()
    pal = theme.query_terminal(fd=slave, timeout=2)
    t.join()
    assert pal[1] == "#d7263d"
    assert pal[9] == "#ff4d5e"

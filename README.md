# baldwin

A terminal now-playing visualizer for Linux.

```
┌────────┐  artist @ spotify
│ cover  │  ─────────────────
│  art   │  Title   For Kicks
│        │  Artist  Metric
└────────┘  Album   Pagans in Vegas
▁▃▅▇█▇▅▃▁▂▄▆█▆▄▂▁   (spectrum visualizer)
01:23 ━━━━━━●──────────── 04:56
 ╭────╮ ╭────╮ ╔══════╗ ╭────╮ ╭────╮
 │ >< │ │ |<<│ ║> PLAY║ │>>| │ │(@) │
 ╰────╯ ╰────╯ ╚══════╝ ╰────╯ ╰────╯
```

- Cover art and fastfetch-style track info
- Audio-reactive spectrum bars (captures whatever your system is playing)
- Clickable time bar and stylized ASCII media buttons
- Works with any MPRIS player: Spotify, mpv, Firefox, VLC, ...
- Follows your terminal theme: accent colors are read from your kitty config, and the
  background is transparent so your terminal opacity shows through

## Requirements

- Linux with a PipeWire audio server (uses `pw-cat` to capture the visualizer audio)
- [`playerctl`](https://github.com/altdesktop/playerctl) for track info and controls
- Python 3.10+
- A terminal with the kitty graphics protocol (kitty, WezTerm, ...) for true cover art.
  Other terminals fall back to a lower-resolution cover.

Install the system packages with your package manager, e.g.

```sh
# Arch
sudo pacman -S playerctl pipewire
# Debian/Ubuntu
sudo apt install playerctl pipewire-bin
# Fedora
sudo dnf install playerctl pipewire-utils
```

## Install

Clone the repo and run the script for your distro. It installs the system packages and baldwin itself:

```sh
git clone https://github.com/Society-g/baldwin
cd baldwin
./install/install-ubuntu.sh   # Ubuntu / Debian / Mint
./install/install-fedora.sh   # Fedora
./install/install-arch.sh     # Arch / Manjaro
./install/install-nix.sh      # Nix / NixOS
```

Then open a new terminal and run `baldwin`.

### Manual install

With [pipx](https://pipx.pypa.io) (recommended):

```sh
pipx install git+https://github.com/Society-g/baldwin
baldwin
```

Or from a clone:

```sh
git clone https://github.com/Society-g/baldwin
cd baldwin
pipx install .
```

### NixOS / Nix

```sh
git clone https://github.com/Society-g/baldwin
cd baldwin
nix-shell --run 'python -m baldwin'
```

## Controls

| Key | Action |
| --- | --- |
| `space` | play / pause |
| `n` / `p` | next / previous |
| `←` / `→` | seek -5s / +5s |
| `↑` / `↓` | volume up / down |
| `s` | toggle shuffle |
| `l` | cycle loop (none / playlist / track) |
| `q` | quit |

The time bar and the buttons are clickable too.

## Theming

Colors come from `color1`, `color9` and `color10` in `~/.config/kitty/kitty.conf`
(the visualizer gradient and accents). If that file is missing it uses a red default.
For a see-through window, set `background_opacity` in kitty.

## Troubleshooting

- **Bars don't move:** check `pw-cat` is installed and a player is actually playing.
- **"Nothing playing":** `playerctl status` must report a player.
- **No cover art:** not every player publishes `mpris:artUrl`.

## Development

```sh
nix-shell          # or: pip install -e . pytest
python -m pytest
```

## License

MIT

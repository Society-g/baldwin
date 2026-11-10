import asyncio
from dataclasses import dataclass

FIELDS = ["status", "position", "length", "title", "artist", "album",
          "art", "player", "volume", "shuffle", "loop"]
FORMAT = "\t".join("{{%s}}" % f for f in (
    "status", "position", "mpris:length", "title", "artist", "album",
    "mpris:artUrl", "playerName", "volume", "shuffle", "loop"))


@dataclass
class Track:
    status: str = "Stopped"
    position: float = 0.0  # seconds
    length: float = 0.0  # seconds
    title: str = ""
    artist: str = ""
    album: str = ""
    art: str = ""
    player: str = ""
    volume: float = 0.0
    shuffle: bool = False
    loop: str = "None"

    @property
    def key(self):
        return (self.title, self.artist, self.album, self.art)


def _num(s, scale=1.0):
    try:
        return float(s) / scale
    except ValueError:
        return 0.0


def parse(line: str) -> Track:
    parts = line.rstrip("\n").split("\t")
    parts += [""] * (len(FIELDS) - len(parts))
    d = dict(zip(FIELDS, parts))
    return Track(
        status=d["status"] or "Stopped",
        position=_num(d["position"], 1e6),
        length=_num(d["length"], 1e6),
        title=d["title"], artist=d["artist"], album=d["album"],
        art=d["art"], player=d["player"],
        volume=_num(d["volume"]),
        shuffle=d["shuffle"].lower() == "true",
        loop=d["loop"] or "None",
    )


async def _run(*args) -> str:
    proc = await asyncio.create_subprocess_exec(
        "playerctl", *args,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    out, _ = await proc.communicate()
    return out.decode(errors="replace")


async def poll() -> Track | None:
    out = await _run("metadata", "--format", FORMAT)
    return parse(out) if out.strip() else None


async def play_pause(): await _run("play-pause")
async def next_track(): await _run("next")
async def previous(): await _run("previous")
async def seek(seconds: float): await _run("position", f"{max(seconds, 0):.2f}")
async def set_volume(v: float): await _run("volume", f"{min(max(v, 0), 1):.2f}")


async def toggle_shuffle():
    await _run("shuffle", "Toggle")


async def cycle_loop():
    cur = (await _run("loop")).strip()
    nxt = {"None": "Playlist", "Playlist": "Track", "Track": "None"}.get(cur, "None")
    await _run("loop", nxt)

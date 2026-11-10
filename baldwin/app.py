from PIL import Image
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual_image.widget import Image as ImageWidget

from . import cover, mpris, theme
from .widgets import ArtFooter, Banner, ControlButton, Controls, InfoPanel, TimeBar, Visualizer


class Baldwin(App):
    ansi_color = True  # let kitty's transparent background show through
    CSS = """
    Screen { padding: 1 2; background: ansi_default; }
    * { background: transparent; }
    #header { height: 16; }
    #cover { width: 26; height: 14; border: ascii; margin-right: 3; }
    #side { width: 1fr; height: 16; }
    """
    BINDINGS = [
        ("space", "play_pause", "Play/Pause"),
        ("n", "next", "Next"), ("p", "prev", "Prev"),
        ("left", "seek(-5)", "-5s"), ("right", "seek(5)", "+5s"),
        ("up", "vol(0.05)", "Vol+"), ("down", "vol(-0.05)", "Vol-"),
        ("s", "shuffle", "Shuffle"), ("l", "loop", "Loop"),
        ("q", "quit", "Quit"),
    ]

    TITLE = "baldwin"
    track = None
    accents = theme.load()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Banner()
            with Horizontal(id="header"):
                yield ImageWidget(cover.placeholder(), id="cover")
                with Vertical(id="side"):
                    yield InfoPanel(id="info")
                    yield ArtFooter()
            yield Visualizer()
            yield TimeBar()
            yield Controls()

    def on_mount(self):
        self.set_interval(0.25, self.refresh_track)

    async def refresh_track(self):
        t = await mpris.poll()
        if t is None:
            t = mpris.Track(title="Nothing playing")
        changed = self.track is None or t.key != self.track.key
        self.track = t
        if changed:
            img = await cover.load(t.art) or cover.placeholder()
            self.query_one("#cover", ImageWidget).image = img
            self.query_one(Visualizer).colors = self.accents
            self.query_one(TimeBar).accent = self.accents[1]
            self.query_one(Banner).accent = self.accents[1]
            self.query_one("#cover").styles.border = ("ascii", self.accents[1])
            self.query_one(ArtFooter).colors = self.accents
        self.query_one(InfoPanel).show(t, self.accents)
        self.query_one(Controls).sync(t, self.accents[1])
        self.query_one(Visualizer).playing = t.status == "Playing"
        bar = self.query_one(TimeBar)
        bar.length, bar.position = t.length, t.position

    def on_time_bar_seek(self, m: TimeBar.Seek):
        self.run_worker(mpris.seek(m.seconds))

    def on_control_button_pressed(self, e):
        fn = {"play": mpris.play_pause, "next": mpris.next_track,
              "prev": mpris.previous, "shuffle": mpris.toggle_shuffle,
              "loop": mpris.cycle_loop}[e.button.id]
        self.run_worker(fn())

    def action_play_pause(self): self.run_worker(mpris.play_pause())
    def action_next(self): self.run_worker(mpris.next_track())
    def action_prev(self): self.run_worker(mpris.previous())
    def action_shuffle(self): self.run_worker(mpris.toggle_shuffle())
    def action_loop(self): self.run_worker(mpris.cycle_loop())

    def action_seek(self, d: float):
        if self.track:
            self.run_worker(mpris.seek(self.track.position + d))

    def action_vol(self, d: float):
        if self.track:
            self.run_worker(mpris.set_volume(self.track.volume + d))


def main():
    Baldwin().run()

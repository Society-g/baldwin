import numpy as np

from baldwin import audio, mpris


def test_parse():
    t = mpris.parse("Playing\t83000000\t225000000\tSong\tArt\tAlb\tfile:///x.png\tmpv\t0.5\ttrue\tTrack\n")
    assert t.status == "Playing" and t.position == 83 and t.length == 225
    assert t.shuffle and t.loop == "Track" and t.volume == 0.5


def test_parse_short():
    assert mpris.parse("Paused\t0").title == ""


def test_bands_peak_in_right_band():
    n = 16
    f = 1000.0
    x = np.sin(2 * np.pi * f * np.arange(audio.N) / audio.RATE).astype(np.float32)
    b = audio.bands(x, n)
    edges = audio.band_edges(n)
    expected = np.searchsorted(edges, f) - 1
    assert int(b.argmax()) == expected

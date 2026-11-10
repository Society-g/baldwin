import subprocess
import threading

import numpy as np

RATE = 44100
N = 4096  # longer window = finer bass resolution
_WINDOW = np.hanning(N).astype(np.float32)


def band_edges(n_bands: int, lo=50.0, hi=10000.0):
    return np.geomspace(lo, hi, n_bands + 1)


def bands(samples: np.ndarray, n_bands: int) -> np.ndarray:
    """Magnitude per log-spaced band for a mono window of N samples."""
    spec = np.abs(np.fft.rfft(samples * _WINDOW)) / N
    freqs = np.fft.rfftfreq(N, 1 / RATE)
    edges = band_edges(n_bands)
    out = np.zeros(n_bands, dtype=np.float32)
    for i in range(n_bands):
        mask = (freqs >= edges[i]) & (freqs < edges[i + 1])
        if mask.sum() >= 2:
            out[i] = spec[mask].max()
        else:  # band spans <2 bins: interpolate to avoid stepping/flicker
            out[i] = np.interp((edges[i] + edges[i + 1]) / 2, freqs, spec)
    return out


class Capture:
    """Records the default sink's monitor via pw-cat into a ring buffer."""

    def __init__(self):
        self.buf = np.zeros(N, dtype=np.float32)
        self.ok = False
        self._proc = None
        self._stop = False
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            self._proc = subprocess.Popen(
                ["pw-cat", "--record", "--rate", str(RATE), "--channels", "2",
                 "--format", "f32", "-P", "{ stream.capture.sink=true }", "-"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError:
            return
        chunk = 1024 * 2 * 4
        while not self._stop:
            data = self._proc.stdout.read(chunk)
            if not data:
                break
            self.ok = True
            s = np.frombuffer(data[: len(data) // 8 * 8], dtype=np.float32)
            mono = s.reshape(-1, 2).mean(axis=1)
            self.buf = np.concatenate([self.buf, mono])[-N:]
        self.ok = False

    def snapshot(self) -> np.ndarray:
        return self.buf.copy()

    def close(self):
        self._stop = True
        if self._proc:
            self._proc.terminate()

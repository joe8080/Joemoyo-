"""Give the single piano note (audio/piano_note.mp3, first 2.6s) a long ballroom ring.

Convolves it with a 5s exponentially decaying, darkened noise tail so the note
blooms and fades slowly under Shot 1. Writes audio/piano_note_ring.wav.
"""
import subprocess

import numpy as np

SR = 48000

raw = subprocess.run(["ffmpeg", "-v", "error", "-t", "2.6", "-i", "audio/piano_note.mp3", "-ac", "1",
                      "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
dry = np.frombuffer(raw, np.float32).astype(np.float64)
dry *= np.clip(np.linspace(1.6, 0, len(dry)) ** 0.5, 0, 1)        # end the take before its stray knock

n = int(5.0 * SR)
t = np.arange(n) / SR
rng = np.random.default_rng(3)
ir = rng.standard_normal(n) * np.exp(-t / 1.1)                      # ~5s decay to silence
X = np.fft.rfft(ir)
f = np.fft.rfftfreq(n, 1 / SR)
X *= 1 / (1 + (f / 2500) ** 2)                                      # darker, warmer room
ir = np.fft.irfft(X, n)
ir /= np.abs(ir).max()

L = len(dry) + n
wet = np.fft.irfft(np.fft.rfft(dry, L) * np.fft.rfft(ir, L), L)
wet *= np.abs(dry).max() / (np.abs(wet).max() + 1e-12)
y = np.zeros(L)
y[:len(dry)] += dry
y += 0.8 * wet
y *= 0.7 / np.abs(y).max()
y *= np.minimum(1, np.linspace(L / SR, 0, L) / 1.0)                # soft final second
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-",
                "audio/piano_note_ring.wav"], input=y.astype(np.float64).tobytes(), check=True)
print("audio/piano_note_ring.wav", f"{L / SR:.2f}s")

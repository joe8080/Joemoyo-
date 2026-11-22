"""Your own plugins live in this folder. Every .py file here is loaded automatically.

Copy this file, rename it, and change the maths. Then:

    python -m studio plugins                  # your plugin appears in the list
    python -m studio plug warmth song.wav     # run it
    python -m studio plug joe-gig clip.mp4    # run your own chain

An audio plugin receives stereo audio as a NumPy array (samples x 2, values -1..1) and the
sample rate, and returns the processed audio plus a short note for the report.
"""
import numpy as np

from studio.plugins import chain, plugin, stft_apply


@plugin("warmth", "audio", "Example: a gentle tilt that adds low-mid body and softens the very top.",
        amount=(2.0, "tilt in dB (try 1 to 4)"))
def warmth(x, sr, amount=2.0):
    amount = float(amount)

    def gain_fn(power, freqs):
        # +amount dB around 200 Hz, sliding to -amount dB by 10 kHz.
        octaves_from_1k = np.log2(np.maximum(freqs, 20.0) / 1000.0)
        db = np.clip(-amount * octaves_from_1k / 2.3, -amount, amount)
        return np.broadcast_to(10 ** (db / 20), power.shape)

    return stft_apply(x, gain_fn), {"note": f"added {amount:.1f} dB of warmth"}


# Your own one-word chain: built-in plugins and your own, in the order you want them.
chain("joe-gig", "Joe's gig sound: tone match, tame harshness, a touch of warmth, level.",
      ["matchtone", "deharsh", ("warmth", {"amount": 1.0}), ("level", {"lufs": -14.0})])

"""Synthesised sound design for Film 2 (all original, no samples).
Stems: bed.wav (ambient pad that follows the colour script) and sfx.wav (UI sounds keyed to the visuals).
Event times come from anchors.json, the same file the visuals use."""
import json, numpy as np
from scipy.signal import butter, sosfilt, lfilter

SR = 48000
A = json.load(open('/tmp/film2r/audio/anchors.json'))
DUR = A['end'] + 1.5
N = int(DUR * SR)
rng = np.random.default_rng(7)

def env_exp(n, tau):  # fast attack, exponential decay
    t = np.arange(n) / SR
    return np.exp(-t / tau) * np.minimum(1, t / 0.002)

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x)

def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x)

def add(buf, t, sig, gain=1.0):
    i = int(t * SR)
    if i >= len(buf) or i < 0:
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain

def tick(f=2200, dur=0.09, tau=0.022):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) * env_exp(n, tau)
    s += 0.35 * np.sin(2 * np.pi * f * 2.01 * t) * env_exp(n, tau * 0.5)
    click = rng.standard_normal(n) * env_exp(n, 0.002) * 0.3
    return s * 0.7 + hp(click, 3000)

def thump(f0=95, f1=38, dur=0.55, tau=0.17):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.07)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * env_exp(n, tau)
    click = lp(rng.standard_normal(n), 900) * env_exp(n, 0.012) * 0.35
    return s + click

def chime(freqs=(880, 1108.7), dur=1.1, tau=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) * env_exp(n, tau) * (0.7 if i else 1.0) for i, f in enumerate(freqs))
    s += 0.2 * np.sin(2 * np.pi * freqs[0] * 3.01 * t) * env_exp(n, tau * 0.35)
    return s * 0.45

def whoosh(dur=0.55, lo=250, hi=5200, peak=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n); y = 0.0
    fc = lo * (hi / lo) ** np.clip(t / (dur * peak * 1.4), 0, 1)
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    for i in range(n):
        y += a[i] * (noise[i] - y); out[i] = y
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return hp(out, 150) * env * 2.2

def sweep_up(dur=1.2, lo=300, hi=7000, peak=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    fc = lo * (hi / lo) ** (t / dur)
    out = np.zeros(n); y = 0.0
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    for i in range(n):
        y += a[i] * (noise[i] - y); out[i] = y
    env = (t / dur) ** 1.6 * np.minimum(1, (dur - t) / 0.05)
    return hp(out, 200) * env * 2.0 * peak

def bell(f=1318.5, dur=1.6, tau=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.2) + 0.3 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.08)
    return s * env_exp(n, tau) * 0.4

def warn_pair():
    out = np.zeros(int(0.5 * SR))
    add(out, 0, tick(660, tau=0.03), 0.9); add(out, 0.13, tick(660, tau=0.03), 0.9)
    return out

def alert_hit():
    out = np.zeros(int(0.9 * SR))
    add(out, 0, thump(120, 42, 0.8, 0.28), 1.0)
    add(out, 0.02, tick(310, 0.25, 0.09), 0.5); add(out, 0.3, tick(310, 0.25, 0.09), 0.4)
    return out

# ------------------------------ SFX stem ------------------------------
sfx = np.zeros(N)
S = lambda k: A[k]
def card(t, level=1.0, low=False):
    add(sfx, t - 0.02, whoosh(0.42, 300, 4200), 0.16 * level)
    add(sfx, t + 0.18, tick(1900 + rng.integers(0, 300)), 0.22 * level)
    if low: add(sfx, t + 0.12, thump(80, 45, 0.4, 0.12), 0.25 * level)
def status(t, kind):
    if kind == 'ok': add(sfx, t, chime(), 0.55); add(sfx, t, thump(70, 45, 0.3, 0.1), 0.2)
    if kind == 'warn': add(sfx, t, warn_pair(), 0.5); add(sfx, t, thump(70, 45, 0.3, 0.1), 0.18)
    if kind == 'alert': add(sfx, t, alert_hit(), 0.55)
def section(t):
    add(sfx, t - 0.15, whoosh(0.8, 120, 2600, 0.7), 0.2)
    add(sfx, t + 0.25, thump(70, 36, 0.7, 0.22), 0.34)

# cold open
add(sfx, 0.0, whoosh(1.6, 200, 3200, 0.8), 0.14)
for k in range(1, 36):
    p = 1 - (1 - k / 35) ** (1 / 3)
    add(sfx, 0.15 + 2.4 * p, tick(1500 + k * 26, 0.05, 0.012), 0.10)
add(sfx, 2.7, thump(95, 40, 0.8, 0.3), 0.4)
for k in ('amazon', 'alphabet', 'microsoft', 'meta'): card(S(k), 0.9)
add(sfx, S('eighty1'), chime((988, 1244.5), 0.9, 0.3), 0.4)
add(sfx, S('fiveq'), thump(90, 38, 0.9, 0.3), 0.5); add(sfx, S('fiveq') - 0.1, whoosh(0.9, 150, 3500, 0.7), 0.22)
for i, f in enumerate([880, 988, 1108.7, 1318.5, 1480]): add(sfx, S('fiveq') + 0.7 + i * 0.3 + 0.05, tick(f, 0.12, 0.03), 0.3)
# Q1
section(S('q1'))
for t in (S('q1') + 3.0, S('q1') + 4.6, S('q1_right') - 1.6): card(t, 0.7)
add(sfx, S('q1_right'), chime((784, 987.8), 0.8, 0.25), 0.35)
for i, t in enumerate((S('q1_chip'), S('q1_chip') + 0.5, S('q1_chip') + 1.0, S('q1_capex'))): add(sfx, t, tick(1500 + i * 180, 0.1, 0.03), 0.3); add(sfx, t, whoosh(0.5, 200, 1800), 0.1)
add(sfx, S('q1_capex') + 0.3, sweep_up(0.5, 400, 3000), 0.12)
status(S('q1_pace'), 'ok')
# Q2
section(S('q2'))
card(S('q2_mem'), 1.0, True); card(S('q2_pack'), 1.0, True); card(S('q2_short'), 0.6)
status(S('q2_yes'), 'warn')
for i in range(5): add(sfx, S('q2_but') + 1.1 * (i + 1), tick(1200 + i * 60, 0.07, 0.02), 0.2)
card(S('q2_but'), 0.6)
# Q3
section(S('q3'))
add(sfx, S('q3_track'), sweep_up(1.4, 200, 2400), 0.14); card(S('q3_track'), 0.8)
add(sfx, S('q3_plan'), sweep_up(1.6, 300, 6000), 0.2)
add(sfx, S('q3_op'), sweep_up(0.8, 800, 5000), 0.12); add(sfx, S('q3_op') + 0.6, tick(2400), 0.25)
status(S('q3_30'), 'alert'); add(sfx, S('q3_30'), sweep_up(1.2, 200, 2000), 0.12)
add(sfx, S('q3_partial'), tick(1700, 0.1, 0.03), 0.3)
for k in ('q3_slip', 'q3_seven', 'q3_uk'): card(S(k), 0.9, True)
add(sfx, S('q3_bldg'), thump(60, 33, 1.0, 0.4), 0.5); card(S('q3_bldg'), 0.8)
card(S('q3_iea'), 0.9); add(sfx, S('q3_iea') + 0.3, tick(1500), 0.25); add(sfx, S('q3_iea') + 1.2, tick(1900), 0.25)
add(sfx, S('q3_fifth'), alert_hit(), 0.3)
# Q4
section(S('q4'))
for i in range(4): add(sfx, S('q4') + 1.2 + i * 0.3, tick(1100 + i * 140, 0.08, 0.02), 0.22)
add(sfx, S('q4_12'), sweep_up(0.9, 300, 3500), 0.14); add(sfx, S('q4_12') + 0.5, tick(2000), 0.25)
add(sfx, S('q4_lead'), sweep_up(1.6, 200, 3000), 0.13)
status(S('q4_ahead'), 'ok')
add(sfx, S('q4_watch'), warn_pair(), 0.4)
# Q5
section(S('q5'))
card(S('q5') + 1.2, 0.9); card(S('q5') + 2.6, 0.9); add(sfx, S('q5') + 2.3, tick(700, 0.12, 0.05), 0.25)
status(S('q5_notyet'), 'warn')
for i, k in enumerate((S('q5_40'), S('q5_40') + 0.5, S('q5_google'))): add(sfx, k, tick(1400 + i * 200, 0.1, 0.03), 0.28)
add(sfx, S('q5_capex'), whoosh(0.7, 200, 3000), 0.18); card(S('q5_capex') + 0.5, 0.8, True)
card(S('q5_backlog'), 0.9); card(S('q5_backlog') + 0.5, 0.9)
add(sfx, S('q5_promise') - 0.1, thump(130, 50, 0.7, 0.2), 0.6); add(sfx, S('q5_promise') - 0.1, tick(520, 0.4, 0.15), 0.4)
for k in ('q5_bonds', 'q5_meta', 'q5_jv', 'q5_circ'): card(S(k), 0.8)
# Map
section(S('map'))
for i, k in enumerate(('l_chips', 'l_net', 'l_fab', 'l_pow', 'l_build', 'l_gen', 'l_spend')):
    add(sfx, S(k), thump(110 + i * 14, 55, 0.35, 0.09), 0.34); add(sfx, S(k) + 0.05, tick(1000 + i * 170, 0.1, 0.03), 0.22)
add(sfx, S('l_wait'), chime((784, 987.8, 1175), 1.2, 0.4), 0.45)
# So what
section(S('sowhat'))
for k in ('sw1', 'sw2', 'sw3'): card(S(k), 0.9, True)
add(sfx, S('sw3') + 0.3, sweep_up(1.0, 400, 3500), 0.1)
add(sfx, S('sw_isa'), tick(1600), 0.28); add(sfx, S('sw_isa') + 0.4, tick(1900), 0.28)
# Close
for i in range(5): add(sfx, S('close') + i * 0.25 + 0.05, tick(1000 + i * 150, 0.1, 0.03), 0.28)
add(sfx, S('close') - 0.1, whoosh(0.8, 150, 3000, 0.7), 0.18)
card(S('disc'), 0.7)
add(sfx, S('sub') - 0.95, sweep_up(1.0, 300, 7500), 0.28); add(sfx, S('sub') + 0.05, bell(), 0.5)

# ------------------------------ BED stem ------------------------------
def note_hz(n):  # midi
    return 440.0 * 2 ** ((n - 69) / 12)
CHORDS = {  # midi notes
    'Am9': [45, 52, 57, 60, 64, 71], 'Fmaj7': [41, 48, 53, 57, 60, 64], 'Dm_b6': [38, 45, 50, 53, 57, 63],
    'Cmaj9': [36, 43, 48, 52, 55, 62], 'Dm': [38, 45, 50, 53, 57, 60], 'Fmaj9': [41, 48, 53, 57, 60, 67], 'Cmaj7': [36, 43, 48, 52, 55, 59],
}
PLAN = [(0, 'Am9'), (S('q1'), 'Am9'), (S('q2'), 'Fmaj7'), (S('q3'), 'Dm_b6'), (S('q4'), 'Cmaj9'), (S('q5'), 'Dm'), (S('map'), 'Fmaj9'), (S('sowhat'), 'Cmaj7'), (S('close'), 'Cmaj9')]
def pad(freq, n, t0):
    t = np.arange(n) / SR + t0
    s = np.zeros(n)
    for det in (-7, 0, 6):
        f = freq * 2 ** (det / 1200)
        # band-limited-ish saw from few harmonics
        for h in range(1, 7):
            s += np.sin(2 * np.pi * f * h * t + h) / h * (0.8 ** (h - 1))
    return s / 3
bed = np.zeros(N)
xf = 2.5
for idx, (t0, name) in enumerate(PLAN):
    t1 = PLAN[idx + 1][0] if idx + 1 < len(PLAN) else DUR
    i0 = int(max(0, t0 - xf) * SR); i1 = min(N, int((t1 + xf) * SR))
    n = i1 - i0
    seg = np.zeros(n)
    for m in CHORDS[name]:
        seg += pad(note_hz(m), n, i0 / SR) * (1.0 if m < 50 else 0.7)
    seg = lp(seg, 900)
    tt = np.arange(n) / SR + i0 / SR
    g = np.clip((tt - (t0 - xf)) / (2 * xf), 0, 1) * np.clip((t1 + xf - tt) / (2 * xf), 0, 1)
    g = np.minimum(1, g * 2)
    seg *= g * (0.8 + 0.2 * np.sin(2 * np.pi * tt / 11.0))
    bed[i0:i1] += seg
bed *= 1 / (np.max(np.abs(bed)) + 1e-9)
air = hp(lp(rng.standard_normal(N), 6000), 1500) * 0.012
bed = bed * 0.5 + air
# fade ends
fi = int(2.0 * SR); bed[:fi] *= np.linspace(0, 1, fi); fo = int(3.0 * SR); bed[-fo:] *= np.linspace(1, 0, fo)

def save(name, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], 1)
    import wave
    with wave.open(name, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype('<i2').tobytes())

sfx = sfx / max(1.0, np.max(np.abs(sfx)) / 0.9)
save('/tmp/film2r/audio/bed.wav', bed)
save('/tmp/film2r/audio/sfx.wav', sfx)
print('bed peak', round(float(np.max(np.abs(bed))), 3), 'sfx peak', round(float(np.max(np.abs(sfx))), 3), 'dur', round(DUR, 1))

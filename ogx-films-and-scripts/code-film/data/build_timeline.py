"""Build remotion/src/episodes/<ep>/timeline.json from the episode script.

Two modes:
  1. Real audio: data/<ep>/words.json exists (made by data/words.py from the narration track).
     Every script word is aligned to the spoken words, so scenes, cues and captions follow the voice.
  2. Estimate (no audio yet): durations from word counts, scaled to TARGET seconds if given.

Cues in the script are phrases, not seconds: a cue lands on the first word of its phrase.
Usage: python3 data/build_timeline.py dahomey [target_seconds]
"""
import difflib, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FPS = 30
ep = sys.argv[1]; target = float(sys.argv[2]) if len(sys.argv) > 2 else None
script = json.load(open(os.path.join(HERE, ep, 'script.json')))
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower().replace("é", "e").replace("à", "a").replace("ç", "c"))
LEAD, PRE, END, GAP, SEC_GAP, WPS = 0.3, 1.2, 6.0, 0.55, 1.5, 2.9

toks = []                                   # (line index, word index, display word)
for i, s in enumerate(script):
    for j, w in enumerate(s['text'].split()):
        toks.append((i, j, w))
wpath = os.path.join(HERE, ep, 'words.json')
times = [None] * len(toks)
real = os.path.exists(wpath)
if real:
    spoken = json.load(open(wpath))         # [[word, start, end], ...]
    a = [norm(t[2]) for t in toks]; b = [norm(w[0]) for w in spoken]
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = spoken[blk.b + k][1]
    known = [k for k, t in enumerate(times) if t is not None]
    print(f'aligned {len(known)}/{len(toks)} words to the voice')
    for k in range(len(times)):             # fill unmatched words between their neighbours
        if times[k] is None:
            lo = max([x for x in known if x < k], default=None); hi = min([x for x in known if x > k], default=None)
            if lo is None: times[k] = max(0.0, times[hi] - 0.3 * (hi - k))
            elif hi is None: times[k] = times[lo] + 0.3 * (k - lo)
            else: times[k] = times[lo] + (times[hi] - times[lo]) * (k - lo) / (hi - lo)
    last_end = spoken[-1][2]
else:
    cur = PRE
    for i, s in enumerate(script):
        n = len(s['text'].split())
        if i: cur += SEC_GAP if s['sec'] != script[i - 1]['sec'] else GAP
        for j in range(n): times[sum(len(x['text'].split()) for x in script[:i]) + j] = cur + j / WPS
        cur += n / WPS
    last_end = cur
    if target:
        k = (target - END) / last_end
        times = [t * k for t in times]; last_end *= k

scenes, base = [], 0
for i, s in enumerate(script):
    ws = s['text'].split(); n = len(ws); t = times[base:base + n]
    start = 0.0 if i == 0 else max(0.0, t[0] - LEAD)
    cues = []
    for ph in s.get('cues', []):
        p = [norm(x) for x in ph.split()]; nw = [norm(x) for x in ws]
        hit = next((j for j in range(n - len(p) + 1) if nw[j:j + len(p)] == p), None)
        if hit is None: raise SystemExit(f"{s['id']}: cue phrase not in line: {ph}")
        cues.append(t[hit])
    scenes.append(dict(id=s['id'], sec=s['sec'], start=start, narr=t[0], cues=cues, words=[[w, x] for w, x in zip(ws, t)]))
    base += n
total = last_end + END
out = []
for i, s in enumerate(scenes):
    end = scenes[i + 1]['start'] if i + 1 < len(scenes) else total
    fr = lambda x: round((x - s['start']) * FPS)
    out.append(dict(id=s['id'], sec=s['sec'], start=round(s['start'] * FPS), end=round(end * FPS), cues=[fr(c) for c in s['cues']], words=[[w, fr(x)] for w, x in s['words']]))
dst = os.path.join(HERE, '..', 'remotion', 'src', 'episodes', ep, 'timeline.json')
json.dump(dict(fps=FPS, total_frames=round(total * FPS), real_audio=real, scenes=out), open(dst, 'w'))
print(f"{'REAL AUDIO' if real else 'ESTIMATE'}: {len(out)} scenes, total {int(total // 60)}:{total % 60:04.1f}")

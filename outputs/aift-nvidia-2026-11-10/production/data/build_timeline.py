"""Build remotion/src/timeline.json, deliverables/subtitles.srt and chapters from data/script.json.
Narration timing per line comes from, in order of preference:
  1. data/words.json  (word-level alignment of the real voice track: {id: [[word, start_s], ...]})
  2. audio/proc/<id>.wav duration, with marks placed proportionally by character offset
  3. no audio: estimated pace (WPS words per second), marks proportional by character offset
Each line has `marks`: phrases whose spoken start time becomes cue k for the scene."""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FPS = 30
script = json.load(open(os.path.join(HERE, 'script.json')))
PRE, SEC_GAP, GAP, END, WPS = 0.5, 3.4, 1.3, 1.0, 2.4
words_p = os.path.join(HERE, 'words.json'); WORDS = json.load(open(words_p)) if os.path.exists(words_p) else {}
def wav_dur(sid):
    p = os.path.join(HERE, '..', 'audio', 'proc', sid + '.wav')
    if os.path.exists(p):
        return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))
    return None
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
_P = {}
def pauses(sid):
    if sid not in _P:
        p = os.path.join(HERE, '..', 'audio', 'proc', sid + '.wav')
        r = subprocess.run(['ffmpeg', '-i', p, '-af', 'silencedetect=n=-36dB:d=0.16', '-f', 'null', '-'], capture_output=True, text=True).stderr if os.path.exists(p) else ''
        _P[sid] = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)]
    return _P[sid]
def time_at(line, char_off, dur):
    t = time_at0(line, char_off, dur)
    if char_off == 0: return 0.0
    prev = line['text'][:char_off].rstrip()
    ps = pauses(line['id'])
    if ps and prev and prev[-1] in '.?!:;,\u201d':          # phrase follows a punctuation pause: snap to the real pause end
        win = 1.6 if prev[-1] in '.?!\u201d' else 1.0
        c = min(ps, key=lambda x: abs(x - t))
        if abs(c - t) <= win: return max(0.0, c - 0.05)
    return t
def time_at0(line, char_off, dur):
    """seconds after line start at which the character offset is spoken"""
    sid, text = line['id'], line['text']
    if sid in WORDS and WORDS[sid]:
        k = len([w for w in text[:char_off].split() if norm(w)])          # index of the word starting at char_off
        ws = WORDS[sid]; k = min(k, len(ws) - 1)
        return max(0.0, ws[k][1] - 0.06)
    # proportional: weight punctuation pauses a little
    w = lambda t: len(t) + 7 * len(re.findall(r'[.?!:;]', t)) + 3 * t.count(',')
    return dur * w(text[:char_off]) / max(1, w(text))
def sentences(text):
    out, pos = [], 0
    for m in re.finditer(r'[^.?!]+[.?!]+[”"]?\s*', text):
        out.append((m.start(), m.group().strip()))
    return out
cur, scenes, subs = 0.0, [], []
audio = True
for i, s in enumerate(script):
    new = i == 0 or s['section'] != script[i - 1]['section']
    g = PRE if i == 0 else (SEC_GAP if new else GAP)
    d = wav_dur(s['id'])
    if d is None:
        audio = False; d = len(s['text'].split()) / WPS
    vis = cur + (0 if i == 0 else 0.3); ns = cur + g; ne = ns + d
    offs = [s['text'].find(m) for m in s['marks']]
    cues = [ns + time_at(s, o, d) for o in offs]
    scenes.append(dict(id=s['id'], section=s['section'], new_section=new, vis_start=round(vis * FPS), narr_start=round(ns * FPS), narr_end=round(ne * FPS),
                       cues=[round(c * FPS) for c in cues], impact=s.get('impact', []), riser=s.get('riser', False)))
    sen = sentences(s['text'])
    for k, (o, t) in enumerate(sen):
        a = ns + time_at(s, o, d); b = ns + (time_at(s, sen[k + 1][0], d) if k + 1 < len(sen) else d)
        subs.append((a, b, t))
    cur = ne + s.get('post', 0)
total = cur + END
for i, s in enumerate(scenes):
    s['vis_end'] = scenes[i + 1]['vis_start'] if i + 1 < len(scenes) else round(total * FPS)
json.dump(dict(fps=FPS, total_frames=round(total * FPS), audio=audio, scenes=scenes), open(os.path.join(HERE, '..', 'remotion', 'src', 'timeline.json'), 'w'), indent=1)
# ---- SRT: split long sentences into chunks of <= 84 chars (2 lines of 42)
def chunks(t, n=84):
    if len(t) <= n: return [t]
    parts = re.split(r'(?<=[,;:])\s+|\s+(?=and |or |but |because |with |while |rather |whether )', t)
    out, cur_ = [], ''
    for p in parts:
        for piece in ([p] if len(p) <= n else re.findall(r'.{1,%d}(?:\s+|$)' % n, p)):
            piece = piece.strip()
            if cur_ and len(cur_) + 1 + len(piece) > n: out.append(cur_); cur_ = piece
            else: cur_ = (cur_ + ' ' + piece).strip()
    if cur_: out.append(cur_)
    return out
def two(t):
    if len(t) <= 42: return t
    m = len(t) // 2; sp = [i for i, c in enumerate(t) if c == ' ']; i = min(sp, key=lambda x: abs(x - m)); return t[:i] + '\n' + t[i + 1:]
ts = lambda x: '%02d:%02d:%02d,%03d' % (x // 3600, x % 3600 // 60, x % 60, round(x % 1 * 1000) % 1000)
os.makedirs(os.path.join(HERE, '..', 'deliverables'), exist_ok=True)
n, lines = 0, []
for a, b, t in subs:
    cs = chunks(t); tot = sum(len(c) for c in cs); acc = 0
    for c in cs:
        x = a + (b - a) * acc / tot; acc += len(c); y = a + (b - a) * acc / tot
        n += 1; lines.append('%d\n%s --> %s\n%s\n' % (n, ts(x), ts(max(x + 0.4, y - 0.04)), two(c)))
open(os.path.join(HERE, '..', 'deliverables', 'subtitles.srt'), 'w').write('\n'.join(lines))
TITLES = {'00': 'Why Nvidia fell: two dates to watch', '01': 'What actually happened', '02': 'Why investors care', '03': 'What the price move tells us', '04': 'Check the business', '05': 'Two dates, different questions', '06': 'Three scenarios', '07': 'Investor checklist and sources'}
ch = ['0:00 ' + TITLES['00']] + ['%d:%02d %s' % (s['vis_start'] / FPS // 60, s['vis_start'] / FPS % 60, TITLES[s['section']]) for s in scenes if s['new_section'] and s['section'] != '00']
open(os.path.join(HERE, '..', 'deliverables', 'chapters.txt'), 'w').write('\n'.join(ch) + '\n')
print('\n'.join(ch)); print(f'total {int(total // 60)}:{total % 60:04.1f}  audio={audio}  subs={n}')

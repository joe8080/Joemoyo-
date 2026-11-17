// Turns an episode script (plain data) into a timed timeline + audio cue list.
// Everything downstream (drawing, sound) is a pure function of this timeline.
//
// `voices` (optional) maps "<speaker>-<nn>" -> { dur, env } for recorded lines. When a line has a
// voice clip its length drives the beat, the captions and the lip-sync; otherwise the line falls
// back to timed captions with synthesised speech blips.

const WORD_STEP = 0.2; // seconds between caption words when there is no voice clip
const LINE_GAP = 0.26; // breath between voiced lines

export function tokens(text) {
  // "*word*" or "*several words*" => highlighted
  let hl = false;
  return text.split(/\s+/).filter(Boolean).map((raw) => {
    if (raw.startsWith('*')) hl = true;
    const word = { t: raw.replace(/\*/g, ''), hl };
    if (raw.length > 1 && raw.replace(/[.,!?…—:;’')]+$/, '').endsWith('*')) hl = false;
    return word;
  });
}

export function compile(ep, voices = {}) {
  const cast = ep.cast || {};
  const shots = [];
  const cues = [];
  const music = [{ t: 0, mood: ep.mood || 'tense' }];
  const lineNo = {};
  let voiced = false;
  let t = 0;

  ep.shots.forEach((src, index) => {
    const shot = structuredClone(src);
    shot.index = index;
    shot.start = t;
    if (index > 0) cues.push({ t, kind: 'whoosh' });
    if (shot.music) music.push({ t, mood: shot.music });

    let cur = t;
    shot.beats = (shot.beats || []).map((b) => {
      const beat = { ...b, start: cur };
      if (b.say) {
        const think = b.who === 'think';
        const speaker = think ? 'you' : b.who;
        lineNo[speaker] = (lineNo[speaker] || 0) + 1;
        const key = `${speaker}-${String(lineNo[speaker]).padStart(2, '0')}`;
        const clip = voices[key];
        const actor = cast[b.who];
        beat.words = tokens(b.say);
        beat.tag = actor ? actor.name : think ? 'YOU · THINKING' : 'YOU';
        beat.col = actor ? actor.accent : think ? '#38bdf8' : '#22c55e';
        beat.vt = cur + (b.pre || 0); // moment the line starts being spoken

        if (clip) {
          voiced = true;
          // spread the words across the clip in proportion to their length
          const total = beat.words.reduce((s, w) => s + w.t.length + 1.5, 0);
          let acc = 0;
          beat.wt = beat.words.map((w) => { const at = beat.vt + 0.03 + (acc / total) * Math.max(0.2, clip.dur - 0.25); acc += w.t.length + 1.5; return at; });
          if (clip.words && clip.words.length === beat.words.length) { beat.wt = clip.words.map((x) => beat.vt + x); beat.exact = true; }
          beat.talkDur = clip.dur;
          beat.env = clip.env;
          cues.push({ t: beat.vt, kind: 'voice', key, think });
          beat.end = beat.vt + clip.dur + (b.gap ?? LINE_GAP);
        } else {
          const step = think ? WORD_STEP * 0.85 : WORD_STEP;
          let wt = beat.vt + 0.06;
          beat.wt = beat.words.map((w) => { const at = wt; wt += step + (/[.,!?…—]$/.test(w.t) ? 0.13 : 0); return at; });
          beat.talkDur = wt - beat.vt + 0.1;
          const voice = actor ? actor.voice || 220 : think ? 330 : 440;
          beat.wt.forEach((at, i) => cues.push({ t: at, kind: 'blip', voice, soft: think, n: i }));
          beat.end = beat.vt + (b.dur ?? Math.max(1.4, beat.talkDur + 0.85));
        }
      } else {
        beat.end = cur + (b.wait ?? b.dur ?? 1);
      }
      const fxAt = beat.vt ?? cur;
      beat.fxAt = fxAt;
      if (b.fx === 'boom') cues.push({ t: fxAt, kind: 'boom' });
      if (b.fx === 'heart') cues.push({ t: cur, kind: 'heart', dur: beat.end - cur });
      if (b.sfx) cues.push({ t: cur + (b.sfxAt || 0), kind: b.sfx, dur: beat.end - cur });
      if (b.music) music.push({ t: cur, mood: b.music });
      cur = beat.end;
      return beat;
    });

    let end = Math.max(cur, t + (shot.dur || 0));

    if (shot.type === 'card') {
      cues.push({ t, kind: 'thud' });
      shot.words = tokens(shot.text);
      end = t + (shot.dur || 1.6);
    }
    if (shot.type === 'end') {
      cues.push({ t: t + 0.05, kind: 'ding' });
      shot.words = tokens(shot.lesson);
      shot.wt = shot.words.map((_, i) => 0.5 + i * 0.17);
      shot.wt.forEach((at, i) => cues.push({ t: t + at, kind: 'blip', voice: 520, soft: true, n: i }));
      shot.ctaAt = 0.5 + shot.words.length * 0.17 + 0.5;
      cues.push({ t: t + shot.ctaAt, kind: 'cash' });
      end = t + shot.ctaAt + 2.8;
    }
    if (shot.type === 'phone') {
      const d = shot.data || {};
      if (shot.heart) cues.push({ t, kind: 'heart', dur: end - t });
      if (shot.app === 'chat') {
        for (const m of d.messages || []) cues.push({ t: t + m.at, kind: m.from === 'me' ? 'sent' : 'pop' });
        for (const ty of d.typing || []) end = Math.max(end, t + ty.at + ty.dur);
      }
      if (shot.app === 'lock') for (const n of d.notifs || []) cues.push({ t: t + n.at, kind: 'ding' });
      if ((shot.app === 'bank' || shot.app === 'portfolio') && d.dur) {
        for (let k = 0; k < d.dur; k += 0.07) cues.push({ t: t + d.at + k, kind: 'tick' });
        if (shot.app === 'bank') cues.push({ t: t + d.at + d.dur, kind: 'thud' });
      }
      if (d.sell) cues.push({ t: t + d.sell.at, kind: 'riser', dur: d.sell.dur });
    }
    if (shot.type === 'scene') {
      const names = Object.keys(shot.actors || {});
      names.forEach((n, i) => {
        const base = names.length === 1 ? { x: 0.5 } : { x: 0.3 + 0.4 * i, h: 840 };
        shot.actors[n] = { ...cast[n], ...base, ...shot.actors[n], seed: i + 1 };
      });
    }

    shot.end = end + (shot.hold ?? 0.12);
    t = shot.end;
    shots.push(shot);
  });

  // "follow" sticker held over the final shot so the video ends on the punchline, not a slide
  let outro = null;
  if (ep.outro && shots.length) {
    const last = shots.at(-1);
    outro = { text: ep.outro, footer: ep.footer || '', start: last.end - 0.1, dur: 1.9 };
    last.end += outro.dur;
    t = last.end;
    cues.push({ t: outro.start, kind: 'pop' });
  }

  const segs = music
    .sort((a, b) => a.t - b.t)
    .map((m, i, arr) => ({ mood: m.mood, t0: m.t, t1: i + 1 < arr.length ? arr[i + 1].t : t }))
    .filter((s) => s.t1 - s.t0 > 0.05);

  return {
    meta: {
      id: ep.id,
      cast,
      voiced,
      outro,
      pov: tokens(ep.pov),
      disclaimer: ep.disclaimer || 'A made-up story for entertainment & education.',
    },
    shots,
    cues: cues.sort((a, b) => a.t - b.t),
    music: segs,
    duration: t,
  };
}

# Stick-Man POV Drama Engine

Viral-style stick-man POV drama shorts, made **100% from code** — no stock footage, no AI video, no samples.
Drawing is HTML canvas, sound is synthesised maths, output is a vertical 1080×1920 MP4 ready for Shorts / TikTok / Reels.

## Render

1. `cd stickman_drama`
2. `node render.mjs all` — renders every script in `episodes/` to `out/<id>.mp4` (+ a poster `.jpg`)
3. One episode only: `node render.mjs episodes/ep1-the-loan.mjs`
4. Quick look without rendering video: `node render.mjs episodes/ep1-the-loan.mjs --stills 1,5,9`

Needs Node 20+, `playwright` (with Chromium) and `ffmpeg` on the PATH.

## Episodes included

| File | POV hook | Length |
|---|---|---|
| `ep1-the-loan.mjs` | your best mate asks to borrow £2,000 | 46s |
| `ep2-the-crash.mjs` | you open your portfolio during a market crash | 43s |
| `ep3-no-budget.mjs` | your boss says there's no budget for a raise | 34s |

## Write a new episode

Copy an episode file and edit the text. An episode is a list of **shots**; a shot holds **beats** (one line of dialogue each).
Timing, captions, lip-flap, camera and sound are all worked out automatically.

```js
export default {
  id: 'ep4-my-story',
  pov: 'POV: your landlord *raises the rent* again',   // *stars* = yellow highlight
  mood: 'tense',                                        // tense | sad | win | none
  cast: { dave: { name: 'DAVE', look: 'cap', accent: '#e11d48', voice: 200 } },
  shots: [
    { type: 'scene', bg: 'room', hands: 'idle', actors: { dave: {} }, beats: [
      { who: 'dave',  say: 'Rent is going up *again*.', emo: 'smug', pose: 'crossed', fx: 'boom' },
      { who: 'think', say: 'Not this time.' },
      { who: 'you',   say: 'Read clause *seven*.', hands: 'paper', react: { dave: { emo: 'shock', pose: 'handsUp' } } },
    ], paper: { title: 'TENANCY', lines: ['Clause 7: fixed rent'], sign: 'Dave' } },
    { type: 'card', text: 'ONE WEEK LATER' },
    { type: 'end', lesson: 'Always *read the contract*.', cta: 'Follow for Part 2' },
  ],
};
```

| Option | Values |
|---|---|
| Shot `type` | `scene`, `phone`, `card`, `end` |
| Scene `bg` | `pub`, `office`, `room`, `street` |
| POV `hands` | `idle`, `fists`, `phone`, `paper`, `none` |
| Beat `who` | a cast name, `you` (spoken), `think` (inner voice) |
| `emo` | `neutral happy laugh smug angry sad cry shock nervous awkward` |
| `pose` | `idle shrug handsUp crossed beg facepalm wave hips think pointUp open cheer` |
| `look` | `cap`, `tie`, `glasses`, `shades`, `hair` |
| Beat `fx` | `boom` (impact + zoom), `zoom` (slow push-in), `shake`, `heart` (heartbeat) |
| Beat `sfx` / `music` | `cash`, `ding`, `riser` / change mood mid-scene |
| Phone `app` | `bank`, `chat`, `feed`, `portfolio`, `lock` (see the three episodes for the `data` each takes) |
| Silent pause | `{ wait: 1.5 }` as a beat |

## Files

- `compile.mjs` — script → timed timeline + sound cues
- `engine.js` — draws every frame (figures, POV hands, phone screens, captions)
- `audio.mjs` — synthesises music + sound effects to WAV
- `render.mjs` — headless Chromium frames → ffmpeg → MP4

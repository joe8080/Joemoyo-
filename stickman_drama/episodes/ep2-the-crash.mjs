// Episode 2 — The Crash (comedy sketch, voiced)
export default {
  id: 'ep2-the-crash',
  pov: 'POV: your coworker becomes a *stock market expert*',
  mood: 'comedy',
  outro: 'Follow for more',
  footer: 'Comedy sketch. Not financial advice.',
  cast: { gary: { name: 'GARY', look: 'glasses', accent: '#2563eb' } },
  shots: [
    {
      type: 'phone', app: 'portfolio', heart: true,
      data: { base: 20800, from: 20800, to: 15988, at: 0.2, dur: 1.8, trend: 'crash' },
      beats: [{ who: 'gary', say: 'Oof. Is that your *portfolio*? That is a *lot* of red.', pre: 0.5 }],
    },
    {
      type: 'scene', bg: 'office', hands: 'phone', actors: { gary: { emo: 'smug', pose: 'crossed' } },
      beats: [
        { who: 'you', say: 'It’s a *long-term* investment, Gary.' },
        { who: 'gary', say: 'Sell *everything*. I sold yesterday. I’m basically a *genius*.', emo: 'smug', pose: 'pointUp' },
        { who: 'you', say: 'Didn’t you buy at the *top* last month?', react: { gary: { emo: 'awkward', pose: 'idle' } } },
        { who: 'gary', say: 'I bought at *a* top. Not *the* top.', emo: 'angry', pose: 'crossed', pre: 0.4 },
        { who: 'you', say: 'So where’s your money *now*?' },
        { who: 'gary', say: 'Somewhere *safe*. My brother-in-law has a *coin*. It’s got a *dog* on it.', emo: 'happy', pose: 'open', fx: 'zoom' },
        { who: 'think', say: 'He’s put his pension in a *dog*.', react: { gary: { emo: 'smug', pose: 'hips' } } },
        { who: 'gary', say: 'You’ll see. Two years from now, I’ll be on a *yacht*.', emo: 'laugh', pose: 'cheer' },
      ],
    },
    { type: 'card', text: '2 YEARS LATER', dur: 1.3 },
    {
      type: 'phone', app: 'portfolio',
      data: { base: 20800, from: 15988, to: 31460, at: 0.2, dur: 1.8, trend: 'moon', time: '08:30' },
      beats: [{ who: 'think', say: 'I did absolutely *nothing*. For two years.', pre: 0.9, sfx: 'cash', sfxAt: 0.3 }],
    },
    {
      type: 'scene', bg: 'office', hands: 'phone', actors: { gary: { emo: 'nervous', pose: 'think' } },
      beats: [
        { who: 'gary', say: 'So, hypothetically. Is it too late to get back *in*?', emo: 'nervous', pose: 'think' },
        { who: 'you', say: 'How’s the *dog coin*?', react: { gary: { emo: 'awkward', pose: 'idle' } } },
        { who: 'gary', say: '…The dog *ran away*.', emo: 'sad', pose: 'idle', pre: 0.5 },
        { who: 'you', say: 'And the *yacht*?' },
        { who: 'gary', say: '…It’s more of a *bus pass*.', emo: 'cry', pose: 'facepalm', pre: 0.6, fx: 'boom' },
      ],
    },
  ],
};

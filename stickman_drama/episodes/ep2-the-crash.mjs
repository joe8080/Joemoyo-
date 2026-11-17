// Episode 2 — The Crash
export default {
  id: 'ep2-the-crash',
  pov: 'POV: you open your portfolio during a *market crash*',
  mood: 'tense',
  disclaimer: 'A made-up story for entertainment & education. Not financial advice. Capital at risk.',
  cast: { gary: { name: 'GARY', look: 'glasses', accent: '#2563eb', voice: 165 } },
  shots: [
    {
      type: 'phone', app: 'portfolio', heart: true,
      data: { base: 20800, from: 20800, to: 15988, at: 0.3, dur: 2.0, trend: 'crash' },
      beats: [{ wait: 1.2 }, { who: 'think', say: 'Down *£4,812*. In *one* week.', fx: 'boom' }],
    },
    {
      type: 'scene', bg: 'office', hands: 'phone', actors: { gary: { emo: 'smug', pose: 'crossed' } },
      beats: [
        { who: 'gary', say: 'Told you. I sold *everything* yesterday.', emo: 'smug', pose: 'crossed' },
        { who: 'gary', say: 'It’s going to *zero*. Get out while you still can!', emo: 'laugh', pose: 'pointUp', fx: 'zoom' },
        { who: 'think', say: 'Maybe he’s right… maybe I should *sell*.', react: { gary: { emo: 'smug', pose: 'hips' } } },
      ],
    },
    {
      type: 'phone', app: 'portfolio', heart: true,
      data: { base: 20800, from: 15988, to: 15988, trend: 'crash', sell: { at: 0.5, dur: 3.6 } },
      beats: [
        { wait: 0.6 },
        { who: 'think', say: 'One tap. And the pain *stops*.', fx: 'shake' },
        { who: 'think', say: '…but so does the *plan*.' },
      ],
    },
    { type: 'card', text: 'THE PLAN', sub: 'Invest every month. 10+ years. Don’t panic.', dur: 2.6, music: 'none' },
    {
      type: 'scene', bg: 'office', hands: 'idle', actors: { gary: { emo: 'smug', pose: 'hips' } }, music: 'tense',
      beats: [
        { who: 'you', say: 'I’m not selling. I’m sticking to the *plan*.', react: { gary: { emo: 'neutral', pose: 'idle' } } },
        { who: 'gary', say: 'You’re *insane*.', emo: 'shock', pose: 'handsUp', fx: 'boom' },
      ],
    },
    { type: 'card', text: '2 YEARS LATER', dur: 1.5, music: 'win' },
    {
      type: 'phone', app: 'portfolio',
      data: { base: 20800, from: 15988, to: 31460, at: 0.3, dur: 2.2, trend: 'moon', time: '08:30' },
      beats: [{ wait: 1.6 }, { who: 'think', say: 'Same funds. Same plan. *Up 51%*.', sfx: 'cash' }],
    },
    {
      type: 'scene', bg: 'office', hands: 'phone', actors: { gary: { emo: 'nervous', pose: 'think' } },
      beats: [
        { who: 'gary', say: 'So… is it *safe* to get back in now?', emo: 'nervous', pose: 'think' },
        { who: 'you', say: 'You’ve been in *cash* this whole time?!', react: { gary: { emo: 'awkward', pose: 'idle' } } },
        { who: 'gary', say: '…I was waiting for the *dip*.', emo: 'cry', pose: 'facepalm', fx: 'boom' },
      ],
    },
    { type: 'end', lesson: 'Time *in* the market beats *timing* the market.', cta: 'Follow for more' },
  ],
};

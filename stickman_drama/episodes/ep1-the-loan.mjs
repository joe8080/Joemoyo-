// Episode 1 — The Loan
export default {
  id: 'ep1-the-loan',
  pov: 'POV: your best mate asks to borrow *£2,000*',
  mood: 'tense',
  cast: { kyle: { name: 'KYLE', look: 'cap', accent: '#e11d48', voice: 215 } },
  shots: [
    {
      type: 'scene', bg: 'pub', hands: 'idle', actors: { kyle: { emo: 'nervous' } },
      beats: [
        { who: 'kyle', say: 'Bro… I need a *massive* favour.', emo: 'nervous', pose: 'beg', fx: 'boom' },
        { who: 'kyle', say: 'Just *£2,000*. Back in your account by *Friday*.', emo: 'happy', pose: 'open' },
        { who: 'think', say: 'Friday… *which* Friday?', react: { kyle: { emo: 'awkward', pose: 'idle' } } },
        { who: 'kyle', say: 'Ten years we’ve been mates. You *trust* me, right?', emo: 'sad', pose: 'beg', fx: 'zoom' },
      ],
    },
    {
      type: 'phone', app: 'bank', heart: true, data: { from: 2340, to: 340, at: 0.9, dur: 1.3, payee: 'KYLE' },
      beats: [{ wait: 1.6 }, { who: 'think', say: 'That’s basically *everything* I’ve got…' }],
    },
    { type: 'card', text: '3 MONTHS LATER', dur: 1.5, music: 'none' },
    {
      type: 'phone', app: 'chat',
      data: {
        name: 'Kyle', status: 'online',
        messages: [
          { from: 'me', text: 'Hey mate, any news on the £2k?', at: 0.3 },
          { from: 'me', text: 'Rent is due Monday…', at: 1.4, seenAt: 2.3 },
        ],
        typing: [{ at: 3.1, dur: 1.7 }],
      },
      beats: [{ wait: 3.1 }, { who: 'think', say: 'He’s typing…', dur: 1.7 }, { who: 'think', say: '…and he *stopped*.', fx: 'boom' }],
    },
    {
      type: 'phone', app: 'feed', music: 'tense',
      data: { user: 'kyle.lives', place: 'Ibiza, Spain', caption: 'Work hard, play harder #blessed', likes: 1284 },
      beats: [{ wait: 0.9 }, { who: 'think', say: 'Hang on. Is that… *IBIZA?!*', fx: 'boom' }],
    },
    {
      type: 'scene', bg: 'street', hands: 'fists', actors: { kyle: { emo: 'happy' } },
      paper: { title: 'LOAN AGREEMENT', lines: ['£2,000 — repay by Friday'], sign: 'Kyle' },
      beats: [
        { who: 'you', say: 'Kyle. Where’s my *two grand*?', react: { kyle: { emo: 'awkward' } } },
        { who: 'kyle', say: 'Wow. You’re *really* making this about *money*?', emo: 'smug', pose: 'crossed' },
        { who: 'kyle', say: 'I thought we were *friends*.', emo: 'sad', pose: 'open', fx: 'zoom' },
        { who: 'think', say: 'Good thing I kept *this*.', hands: 'paper', react: { kyle: { emo: 'neutral', pose: 'idle' } } },
        { who: 'you', say: 'Signed. Dated. *Your* handwriting.', fx: 'boom', sfx: 'cash', music: 'win', react: { kyle: { emo: 'shock', pose: 'handsUp' } } },
        { who: 'kyle', say: '…I can do *fifty quid* a month?', emo: 'nervous', pose: 'beg' },
      ],
    },
    { type: 'end', lesson: 'Only lend what you can afford to *never see again* — and get it *in writing*.', cta: 'Follow for Part 2' },
  ],
};

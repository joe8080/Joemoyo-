// Episode 1 — The Loan (comedy sketch, voiced)
export default {
  id: 'ep1-the-loan',
  pov: 'POV: your mate asks to borrow *£2,000*',
  mood: 'comedy',
  outro: 'Follow for Part 2',
  cast: { kyle: { name: 'KYLE', look: 'cap', accent: '#e11d48' } },
  shots: [
    {
      type: 'scene', bg: 'pub', hands: 'idle', actors: { kyle: { emo: 'happy' } },
      paper: { title: 'LOAN AGREEMENT', lines: ['£2,000 — repay by Friday', '(an actual Friday)'], sign: 'Kyle' },
      beats: [
        { who: 'kyle', say: 'Mate. Quick question. How much do you *love* me?', emo: 'happy', pose: 'beg', fx: 'boom' },
        { who: 'you', say: 'How much is this going to *cost* me?', react: { kyle: { emo: 'awkward', pose: 'idle' } } },
        { who: 'kyle', say: '*Two grand*. But I’ll pay you back *Friday*.', emo: 'happy', pose: 'open' },
        { who: 'you', say: '*Which* Friday?' },
        { who: 'kyle', say: '…*A* Friday.', emo: 'awkward', pose: 'idle', pre: 0.5 },
        { who: 'you', say: 'Kyle. You still owe me *twenty quid* from *2019*.', react: { kyle: { emo: 'nervous' } } },
        { who: 'kyle', say: 'That wasn’t a loan! That was an *investment*. In our *friendship*.', emo: 'happy', pose: 'pointUp' },
        { who: 'you', say: 'What’s it even *for*?' },
        { who: 'kyle', say: 'A *business opportunity*! My cousin’s mate sells a course on how to *get rich*.', emo: 'laugh', pose: 'cheer', fx: 'zoom' },
        { who: 'you', say: 'So *he* gets rich by selling *you* the course.', react: { kyle: { emo: 'neutral', pose: 'idle' } } },
        { who: 'kyle', say: '…Say that again, but *slower*.', emo: 'awkward', pose: 'think', pre: 0.6 },
        { who: 'you', say: 'Fine. I’ll lend it to you. If you sign *this*.', hands: 'paper', react: { kyle: { emo: 'neutral', pose: 'idle' } } },
        { who: 'kyle', say: 'A *contract*?! I thought we were *friends*!', emo: 'shock', pose: 'handsUp', fx: 'boom' },
        { who: 'you', say: 'We are. That’s why there’s *no interest*.', react: { kyle: { emo: 'sad', pose: 'idle' } } },
        { who: 'kyle', say: '…Can I borrow a *pen*?', emo: 'nervous', pose: 'beg', pre: 0.5 },
        { who: 'think', say: 'I *never* saw that pen again.', fx: 'boom', pre: 0.3, react: { kyle: { emo: 'happy', pose: 'wave' } } },
      ],
    },
  ],
};

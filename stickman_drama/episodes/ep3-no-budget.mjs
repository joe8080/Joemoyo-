// Episode 3 — No Budget
export default {
  id: 'ep3-no-budget',
  pov: 'POV: your boss says there’s *no budget* for a raise',
  mood: 'tense',
  cast: { boss: { name: 'BOSS', look: 'tie', accent: '#7c3aed', voice: 135 } },
  shots: [
    {
      type: 'scene', bg: 'office', hands: 'idle', actors: { boss: { emo: 'happy', pose: 'open' } },
      beats: [
        { who: 'boss', say: 'You’ve been *incredible* this year. Truly.', emo: 'happy', pose: 'open', fx: 'boom' },
        { who: 'think', say: 'Here it comes… the *raise*.' },
        { who: 'boss', say: 'But there’s just *no budget* for raises.', emo: 'sad', pose: 'shrug', fx: 'boom' },
        { who: 'boss', say: 'We’re a *family* here. Family isn’t about *money*.', emo: 'happy', pose: 'open', fx: 'zoom' },
        { who: 'think', say: 'My landlord isn’t *family*.', react: { boss: { emo: 'happy', pose: 'hips' } } },
      ],
    },
    {
      type: 'phone', app: 'lock', music: 'none',
      data: { time: '12:04', notifs: [{ at: 0.5, app: 'Mail', from: 'Rival Corp · Talent Team', body: 'We’d love to offer you the role. Salary: 30% above your current pay.' }] },
      beats: [{ wait: 2.0 }, { who: 'think', say: '*Thirty percent* more?!', fx: 'boom' }],
    },
    { type: 'card', text: 'NEXT MORNING', dur: 1.5 },
    {
      type: 'scene', bg: 'office', hands: 'idle', actors: { boss: { emo: 'happy', pose: 'hips' } }, music: 'tense',
      paper: { title: 'RESIGNATION', lines: ['Two weeks’ notice.', 'Thanks for the “family”.'], sign: 'Me' },
      beats: [
        { who: 'you', say: 'I’m handing in my *notice*.', hands: 'paper', react: { boss: { emo: 'neutral', pose: 'idle' } } },
        { who: 'boss', say: 'WAIT— we can *match* it!', emo: 'shock', pose: 'handsUp', fx: 'boom' },
        { who: 'boss', say: 'Plus *ten percent* on top. Starting today!', emo: 'nervous', pose: 'beg' },
        { who: 'you', say: 'So the budget *did* exist.', sfx: 'cash', music: 'win', react: { boss: { emo: 'awkward', pose: 'idle' } } },
        { who: 'boss', say: '…it’s a *family* budget.', emo: 'cry', pose: 'facepalm', fx: 'boom' },
      ],
    },
    { type: 'end', lesson: 'Loyalty is great. *Knowing your market value* pays better.', cta: 'Follow for more' },
  ],
};

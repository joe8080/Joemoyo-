// Episode 3 — No Budget (comedy sketch, voiced)
export default {
  id: 'ep3-no-budget',
  pov: 'POV: your boss says there’s *no budget* for a raise',
  mood: 'comedy',
  outro: 'Follow for more',
  cast: { boss: { name: 'BOSS', look: 'tie', accent: '#7c3aed' } },
  shots: [
    {
      type: 'scene', bg: 'office', hands: 'idle', actors: { boss: { emo: 'happy', pose: 'open' } },
      beats: [
        { who: 'boss', say: 'Come in, sit down. You’ve had an *incredible* year. Best on the team.', emo: 'happy', pose: 'open', fx: 'boom' },
        { who: 'think', say: 'Here it comes. The *raise*.' },
        { who: 'boss', say: 'So we got you… a *pizza party*!', emo: 'laugh', pose: 'cheer', fx: 'boom' },
        { who: 'you', say: '…A pizza party.', pre: 0.5, react: { boss: { emo: 'happy', pose: 'open' } } },
        { who: 'boss', say: '*One slice* each. We’re a *family* here.', emo: 'happy', pose: 'pointUp' },
        { who: 'you', say: 'I was hoping for a *raise*.' },
        { who: 'boss', say: 'There’s just *no budget*. Times are tough for *everyone*.', emo: 'sad', pose: 'shrug' },
        { who: 'you', say: 'Is that your new *sports car* outside?', react: { boss: { emo: 'awkward', pose: 'idle' } } },
        { who: 'boss', say: 'That is a *company morale vehicle*.', emo: 'nervous', pose: 'hips', pre: 0.4 },
      ],
    },
    {
      type: 'phone', app: 'lock',
      data: { time: '12:04', notifs: [{ at: 0.3, app: 'Mail', from: 'Rival Corp · Talent Team', body: 'We’d love to offer you the role. Salary: 30% above your current pay.' }] },
      beats: [{ who: 'think', say: '*Thirty percent* more. And *no pizza*.', pre: 1.5 }],
    },
    {
      type: 'scene', bg: 'office', hands: 'idle', actors: { boss: { emo: 'happy', pose: 'hips' } },
      paper: { title: 'RESIGNATION', lines: ['Two weeks’ notice.', 'Keep the pizza.'], sign: 'Me' },
      beats: [
        { who: 'you', say: 'I *quit*.', hands: 'paper', pre: 0.3, react: { boss: { emo: 'neutral', pose: 'idle' } } },
        { who: 'boss', say: 'WAIT! We can *match* it! Plus *ten percent*!', emo: 'shock', pose: 'handsUp', fx: 'boom' },
        { who: 'you', say: 'So there *was* a budget.', react: { boss: { emo: 'awkward', pose: 'idle' } } },
        { who: 'boss', say: '…It’s a *family* budget.', emo: 'nervous', pose: 'beg', pre: 0.5 },
        { who: 'you', say: 'Then I’m *moving out*.', fx: 'boom', react: { boss: { emo: 'cry', pose: 'facepalm' } } },
      ],
    },
  ],
};

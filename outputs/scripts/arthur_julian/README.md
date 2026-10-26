# The Founder's Test — Arthur & Julian (vertical micro-drama)

Format: 9:16 vertical, 50–60s per episode, 3 episodes per day (12:00 / 16:00 / 20:00 UK).

| Day | Episodes | File |
|-----|----------|------|
| 1 | Ep 1–3 (Setup, Escalation, The Drop) | `episodes_01-03.md` |
| 2 | Ep 4–6 (The Fall, The Night Shift, The Fall Guy) | `episodes_04-06.md` |

## Character lock (paste before every image/video prompt)

> Style: Cinematic vertical 9:16 mobile drama, hyper-realistic, dramatic moody lighting.

- **Arthur (The Founder):** 68, weathered face, silver hair. Ep 1: faded blue warehouse janitor jumpsuit. Ep 2 onward: tweed jacket or custom Savile Row suit.
- **Julian (The Arrogant Heir, Arthur's grandson):** 28, slicked-back dark hair, bespoke charcoal slim-fit suit, arrogant smirk. Ep 5 onward: the same faded blue jumpsuit, hair falling loose.
- **Marcus (The Loyal Worker):** early 40s, Black British, short beard, broad build. Hi-vis vest over a grey work shirt (Ep 2–3); navy suit with an "Operations Director" lanyard (Ep 4 onward).
- **Victor Hale (The CFO, the real villain):** late 50s, thin, clean-shaven, silver-rimmed glasses, camel overcoat over a black suit, cold smile.

## Environments
- Warehouse: high-tech corporate logistics warehouse at night, towering steel racks, blue overhead industrial lighting.
- Boardroom: 9th floor, glass walls, massive conference table, city skyline behind.
- Shredder room: small grey back office off the warehouse floor, one flickering fluorescent tube, paper strips everywhere.

## Story so far (canon)
1. Julian fires the "old janitor" (Arthur, undercover) on the warehouse floor.
2. Julian deactivates Marcus's badge and shreds both men's complaint files.
3. Arthur walks into the boardroom as the founder and fires Julian.
4. Julian is demoted to the night shift under Marcus. An anonymous text points him to the shredder room.
5. The shredded files show 300 pallets going missing every month. Victor catches Julian reading them.
6. Victor has forged Julian's signature on every theft. Marcus records Victor's confession. Victor hints that someone in the family wants Arthur gone.

## Production log

### Ep 1, The Setup (finished: `ep1/Ep1_The_Setup_9x16.mp4`, 29s, 720×1280)
- **Voices (ElevenLabs, eleven_v4):** Julian = "Posh Josh". Arthur = "Alistair – Cultured and Articulate". Reuse these for every episode.
- **Character lock:** `assets/character_ref_arthur_julian.png`. Wire it into every scene clip as the reference image.
- **Video:** Seedance 2.5, 9:16, 720p. Each clip gets the reference image plus its voice line as reference audio, so the lips sync.
- **Fix:** scene 1 came back with improvised dialogue. It was re-synced with Sync 3 lip-sync (silence mode). Always check each clip's audio against its line.
- **Music:** ElevenLabs Music v2.5, 32s instrumental tension bed, ducked under dialogue.
- **Edit:** `python3 assemble.py ep1`. This burns bold yellow captions, adds the "PART 1" tag, ducks the music and normalises to -14 LUFS.
- **Cost:** about £15 (images £2.70, voices £0.70, 4 clips £10.80, lip-sync fix £0.65, music £0.50).

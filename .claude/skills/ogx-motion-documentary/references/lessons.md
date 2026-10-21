# Joe's corrections on Adwa, by round. Apply all of these from the start on the next film.

- **v1 → v1.1 (voice and maps)**
  - Narration rewritten to Joe's own voice bible: conversational, "have a look at this", less lecture.
  - Maps must be **real** relief and satellite data with zooms, not hand-drawn diagrams.
  - Fact fix: "single morning" became "single day". Check time words against the claim ledger.
- **v1.1 → v1.2 (pictures and music)**
  - "More images, fewer cards." Cards went from 27 to 3; facts stay as on-screen captions over pictures.
  - Long lines get a second picture partway through.
  - Music was mixed by scene: one cue per act with varied moods, not one long bed.
  - "OrigineX" must be said OR-ih-jin-EX (respelled "Origin-ex" in the voice prompt).
- **v1.2 → v1.3 (motion)**
  - "Turn the images into motion clips… people standing, walking, running… make it captivating." Every AI still is now animated.
  - Use Higgsfield ("we have other tools, come on"). Don't stall on asking which tool, and don't switch to other models (e.g. LTX) unprompted.
  - Joe works away from the desk: "get everything done by the time I come back". Run long jobs to completion autonomously, keep them resumable, then send the result.
- **v1.3 → v1.4 (picture sync and CTA)**
  - **Picture must match who the line names, in order.** At 10:01 the line said "an emperor… and an empress" but only Taytu showed. Fix: open on Menelik (A02), then dissolve to Taytu (A04) just before "and an empress". Whenever a line names two people or places, give each its own picture, timed to the words.
  - **Don't promise unconfirmed future content.** The end card's "Next time, the Valley Tonga" was removed from both the voice and the card ("not sure what we're doing yet").
  - **Subscribe badge** at about 2:00 and on the end card. Spec is in house-style.md.
  - Use "–", not "→", in Cinzel. The arrow showed as an empty box in v1.2 and v1.3.
  - Save the whole process as this skill. Joe will refine it after more films, so update this file with each new round of notes.

## Joe's review pattern
He watches the 720p copy on his phone and replies with timestamps plus a plain description. Answer with:

1. a short numbered list of what changed;
2. the new review link/file;
3. anything that needs his decision.

He likes it cohesive and captivating, and he notices picture–voice mismatches.

- **v1.4 → v1.5 (MJ fact-check brief, applied at Joe's instruction)**
  - **Every claim's precision must match its source.** MJ's brief corrected:
    - "the artist was never there" (too broad) → "a later artistic reconstruction";
    - Kaffa listed among pre-Adwa conquests (it was 1897);
    - "the first big clash" → "a major Ethiopian victory";
    - "by early afternoon it was over" (fighting continued);
    - the holiday date (2 March, not 1 March; keep the 1896 battle date separate);
    - an over-specific supply source (France and Russia);
    - exact clock times and evening dates where accounts differ;
    - a sweeping "nobody counted the dead";
    - an ambiguous "within a year" → "in 1897";
    - an **unnamed historian**: cut it rather than replace it with new unsourced detail.
  - **Default wording habits from now on:**
    - "around dawn" / "late February" where accounts disagree;
    - "by one estimate" plus "the Italian-led army" (it included Eritrean soldiers);
    - name the year instead of a relative span;
    - attribute legends to "some accounts";
    - label paraphrased documents PARAPHRASE on screen.
  - **Archive provenance:**
    - Date the artwork, not the event: the Adwa painting is c. 1940.
    - Credit photo licences exactly (CC BY-SA ≠ public domain).
    - Drop images whose provenance runs to Quora or other secondary sites.
    - Don't caption a composite's panel as a specific event unless the original issue is identified. Swap it for a real map or a labelled AI reconstruction.
  - **Maps on a phone:**
    - darker base, type ≥ 40 pt on dark plates;
    - one movement at a time, with earlier moves dimmed;
    - persistent unit names and a legend;
    - ~1 s extra hold per battle map.
  - **Patch method that worked:**
    1. Put all corrected lines in **one** new take of the same voice (4 variations).
    2. Pick the one closest in pace.
    3. Scribe it, split at the quietest point (`scripts/split_patch.py`), and apply one uniform gain matched to the original clips.
    4. Patch timeline.json by shot number, keeping each shot's lead and gap, adding map holds, and renumbering (`scripts/patch_timeline.py`).
    5. Rebuild the mix and SRT, then do a full render.
  - **Deliver with a fact-check pass:** a change log (old wording / new wording / final timecode / source), the final script, the SRT, updated claim and asset ledgers, and an honest list of what's still unresolved.

---
name: studio
description: >
  Joe's personal video studio. Turns a script into a finished MP4 by sending each job
  (voiceover, pictures, animated shots, music) to the best of his connected generation
  tools (Higgsfield, ElevenLabs, OpenArt, Artlist) behind a hard budget guard, then
  assembling the video locally. Use when Joe says "make / produce / render the video",
  "run the studio", "make a short about X", "finish the <title> video", "how much would
  this video cost", or wants a script or build sheet turned into an actual video file.
  Not for research, script writing or thumbnails: hand those to the ogx-* skills,
  originex-content-engine or youtube-content-pipeline, then come back here with the script.
---

# Studio

The engine in `studio/` plans the video, picks a tool for every job, enforces the
spending cap, remembers every result in `outputs/studio/<slug>/project.json`, and builds
the MP4 with ffmpeg. It never generates media. You do that with the connectors, and you
write the picture prompts. The split matters: the engine holds the money rules so they
do not depend on anyone's memory.

Run commands from the repo root as `python -m studio <command>`. Every command prints
JSON, and every status result has a `next_step` line: follow it. If the `studio`
connector is loaded, its `studio_*` tools do the same things.

Setup, once per fresh machine: `pip install -r studio/requirements.txt` (ffmpeg must be
installed).

## Money rules

These hold whatever else is going on.

1. Run a paid generation only for a job that `start` returned under `started`. If
   `start` refuses, do not run it and do not look for another way to run it.
2. A quote is the live price from the tool's own estimate call, never a guess or a
   remembered price. Each ready job's `quote_how` says which call to make.
3. Joe approves the spend once per video, after seeing the totals. Caps are set to
   what he approved. Only Joe raises a cap.
4. Never call a generator a second time to retry. Mark the job failed, then retry it
   through `start` (which charges the cap again) or `reroute` it.
5. Credits are separate per tool: 100 OpenArt credits and 100 ElevenLabs credits are
   different money. Report them per tool, never as one sum.

## The flow

1. **Script.** Get the narration. If Joe gives a topic, the script comes from the
   script skills or `python main.py history --topic "..."` first. Save it to a file.
2. **Plan.** `python -m studio new --title "..." --preset history --script file.md`
   (`python -m studio presets` lists the styles). This spends nothing. Tell Joe the
   planned length, the number of pictures, and that nothing has been spent.
3. **Prompts.** `python -m studio next <slug>` lists shots under `needs_prompt` with
   the narration each one sits under and any brief from the script. Write one prompt
   per shot and send them all at once:
   `python -m studio prompts <slug> prompts.json` with `{"s01-1": "...", ...}`.
4. **Quotes.** For each kind of job, get the live price as `quote_how` describes, then
   record it: `python -m studio quote <slug> <credits per job> --kind image`, or name
   job ids when prices differ (voiceover price depends on each scene's length).
5. **Approval.** `python -m studio status <slug>` shows `to_come` per tool. Check each
   tool's balance, then tell Joe in a few lines what the video will cost per tool and
   what he will have left. Ask once. After he says yes:
   `python -m studio budget <slug> openart=<n> elevenlabs=<n>`.
6. **Generate.** `python -m studio start <slug> <job ids>`, run the jobs it lists under
   `started`, then record results: `python -m studio done <slug> job=link job=link`.
   Use each tool's batch call for pictures and start those job ids together.
   If a job fails: `python -m studio fail <slug> <job> "why"` (add `--refunded` when the
   tool returned the credits), then retry or `reroute`. A rerouted job needs a new
   quote, and may need a cap on a different tool: go back to Joe for that.
7. **Assemble.** `python -m studio assemble <slug>` builds `<slug>.mp4` and `<slug>.srt`
   in the project folder. It is free. Send Joe the MP4.

## Writing picture prompts

- Describe the subject and the moment only. The preset's house style is added to every
  prompt automatically, which is what keeps the video looking like one piece.
- Make each picture show what the narration under it is saying. The `brief` is the
  script writer's suggestion for that scene; the `narration` is what is being said.
- Name recurring people, places and objects the same way every time.
- No text in pictures. For the history channel, check any factual visual detail the
  same way the OGX skills check claims.

## Running the tools

Every ready job carries `connector`, `tool`, `do` (exactly what to send) and `notes`
(that tool's quirks). Read `notes` before the first call to a tool. `python -m studio
routes` shows the full list and the fallback order.

- Record the direct file link the tool returns. Links can expire, so assemble in the
  same session when possible.
- Music comes from the Artlist catalog first, which uses no generation credits. Search
  with the preset's mood, tell Joe the pick, and download once.
- Animated shots only exist when the preset has `hero_every` above 0. Each one waits
  for its picture, then uses it as the first frame. If an animation is skipped, the
  still is used instead, so they are optional.
- If a download is blocked by this session's network, the error names the host. Tell
  Joe which host to allow in the environment settings, or save the file locally and
  record its path instead.

## Picking up later

`python -m studio list` shows every project and its next step. The project file is the
whole memory: jobs, links, quotes and what was spent. Media files are not kept in git.
Before a session ends with work in progress, offer once to save the project file to
the repo so the video can be resumed.

## Talking to Joe

Short numbered steps, plain words, decision first. Say what was spent and what is left
after each paid stage. Do not read out job ids, tool names or JSON.

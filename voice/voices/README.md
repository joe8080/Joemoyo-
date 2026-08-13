# Voice samples

Drop your cloning samples here as `.wav` files. The naming convention mirrors
VibeVoice's own presets:

```
en-Joe_man.wav
en-Maya_woman.wav
```

`generate.py` resolves them by any of `en-Joe_man`, `en-Joe`, or just `Joe`, so
you can write `--voices Joe Maya`.

## Making a good sample

Use `prepare_voice.py` rather than exporting by hand — it handles the format
conversion and the loudness levelling:

```bash
python voice/prepare_voice.py --input recording.mp4 --name Joe --gender man --start 30 --duration 20
```

What actually makes a clone sound right:

- **15-25 seconds** of continuous speech. Longer is not better; the model only
  needs enough to fix the timbre.
- **One speaker, no music, no room echo.** A backing track or a second voice in
  the sample bleeds into every line the model generates.
- **Your normal delivery.** The sample sets the register — if you read it in a
  flat voice, the whole episode comes out flat. Read it the way you narrate.
- **No long silences.** Trim to a clean run of speech with `--start`.

Samples are gitignored by default, since they are voice biometrics. Keep them
out of the repo unless you have a specific reason to commit them.

## Consent

Only clone a voice you own or have explicit permission to use. If you are adding
a second host, get that in writing before you generate anything you publish —
Microsoft withdrew the original release precisely because people were not doing
this.

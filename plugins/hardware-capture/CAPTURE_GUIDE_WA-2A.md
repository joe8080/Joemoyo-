# Capturing the WA-2A

Goal: record the test file through your WA-2A six times, at six knob settings. About 30 minutes including warm-up. Nothing here needs speed, so stop between passes whenever you like.

Test file: `MOYO_capture_test_48k.wav` (2 min 56 s, 48 kHz, 24-bit, mono). It contains sweeps and loud tones, so keep your monitors turned down.

## One-time setup

1. **Plug the Focusrite's USB cable into the PC.** No audio cables need to move.
2. **Check the WA-2A loop.** It needs both of these:
   - a Focusrite **line output** → WA-2A **input**
   - WA-2A **output** → a Focusrite **line input**

   If only the output side is wired, add one cable from any spare Focusrite line output to the WA-2A input.
3. **Switch the WA-2A on and leave it 15 minutes.** The valves and the optical cell change as they warm up.
4. **In FL Studio:** Options > Audio settings > Device > pick the **Focusrite USB ASIO** driver. Set the sample rate to **48000**.
   FL Studio can only use one interface at a time, so the 16Rig goes quiet while you do this. Switch back afterwards.
5. **Drag the test file into the Playlist.** Send it to mixer **Insert 1**.
6. **Insert 1:** set its output (bottom of the mixer strip) to the Focusrite output that feeds the WA-2A. Turn off its send to Master so the sweeps stay out of your speakers.
7. **Insert 2:** set its input (top of the mixer strip) to the Focusrite input that the WA-2A returns on. Choose the **mono** input, not the stereo pair. This arms it for recording.
8. **No plugins on either insert.** No EQ, no limiter, nothing on the Master either.

## Set the level once

1. On the WA-2A: switch to **COMPRESS**, turn **PEAK REDUCTION fully down to 0**.
2. Play the first 10 seconds of the test file. The steady tone goes out at **-18 dB**.
3. Turn the WA-2A **GAIN** knob until Insert 2 also reads about **-18 dB**.
4. **Write down the GAIN number and do not touch it again.** Do not touch the Focusrite input gain or any fader either. Every pass must use the same levels.

## The six passes

For each pass: set the knobs, press record, play the whole file to the end, stop.

| Pass | Switch | PEAK REDUCTION |
|---|---|---|
| 1 | COMPRESS | 0 |
| 2 | COMPRESS | 30 |
| 3 | COMPRESS | 45 |
| 4 | COMPRESS | 60 |
| 5 | COMPRESS | 75 |
| 6 | LIMIT | 60 |

Record them **in this order**. You do not need to rename anything: I identify each pass by its recording time and check it against how much compression I measure.

## Send them to me

1. The six recordings are in FL Studio's **Recorded** folder (in the Browser on the left).
2. Upload them to a Google Drive folder called **MOYO captures**.
3. Tell me the **GAIN number** you used, and that they're uploaded.

## If something looks wrong

- **Nothing comes back on Insert 2:** the loop is not complete. Check step 2 of the setup.
- **Insert 2 clips (goes red):** turn the Focusrite input gain for that channel all the way down, then redo "Set the level once" and start again from pass 1.
- **You touched a level mid-way:** tell me which pass. I only need the passes after that point redone.

## Optional seventh pass (improves accuracy)

Bypass the WA-2A with one cable: Focusrite output straight into the Focusrite input. Record the file once more. This measures the Focusrite's own sound so I can subtract it. Skip it if re-patching is a hassle.

## What I do with the recordings

The start and end of the file carry sync markers, so I can line each recording up to the sample and detect any speed or stretch error. From each pass I measure:

- frequency response and harmonics at four drive levels
- the compression curve (threshold and ratio at each knob setting)
- attack time, and release time after short and long loud passages
- whether bass and treble trigger the compression as much as mids
- noise floor

Then I build the model, run the same test file through it, and compare it against your recordings, including the 30 seconds of vocal-like material at the end.

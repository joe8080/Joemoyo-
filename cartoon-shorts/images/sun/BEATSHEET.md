# "Why is it so hard to fly to the Sun?" - beat sheet

Voice: ElevenLabs "Tim Riley - Natural. Conversational" (1gZSmkYVRMS8w1i4plmP), eleven_v4, one take, placed at 0.1 s.
Word times: ElevenLabs Scribe (images/sun/words.json), cross-checked with a loudness pause scan.
Comp: 1080x1920, 60 fps, 21.0 s (1260 frames). Delivered 2160x3840.

## Final lines
1. So, flying a rocket to the Sun takes fifty-five times more energy than going to Mars.
2. Basically, Earth is zooming sideways around the Sun.
3. Your rocket starts with that speed, so it keeps missing.
4. To fall in, you have to cancel most of it.
5. So NASA's Parker probe used Venus as a brake.

## Beats (times include the 0.1 s voice offset)

| time | words | on screen | pictures | sound |
|---|---|---|---|---|
| 0.00 | (frame 0) | Guy on a tiny sleeping Earth holding a rocket, sleeping Sun above | hero, earth, sun | - |
| 1.86 | "Sun" | Sun's eyes pop open, looks down at him | sun + code face | pop |
| 2.72 | "fifty-five" | squash-swap to worried, sweat drop slides; Sun goes smug (half lids) | worried | - |
| 5.62 | "Mars" | Mars pops in from the left, smug, winks | mars + code face | pop |
| 6.6-8.45 | "Basically, Earth" | camera pulls way back: Earth, guy and Sun in one wide; Earth opens its eyes on "Earth" | - | whoosh |
| 7.85-10.1 | "zooming sideways" | squash-swap to brace; Earth races sideways round its dashed orbit, grinning, wind lines | brace | wind bed |
| 10.18 / 10.50 | "Your rocket" | camera pushes in; turn into mirrored wind-up, release on "rocket" -> rocket flies with real gravity physics | windup, follow, rocket | launch |
| 12.95 | "keeps missing" | rocket whips past the Sun (closest approach) and swings back out; Sun goes "o" | - | whoosh |
| 13.02-13.85 | (pause) | cut: waist-up facepalm close-up | facepalm | pop (slap) |
| 15.46 | "cancel" | rocket flips round, retro flame, eye squeezed; sputters out in grey smoke, sweats | rocket + code | thruster |
| 18.55-19.15 | "Parker probe ... Venus" | Venus pops in beside the path, watches the rocket | venus + code face | pop |
| 19.1-19.6 | "as a brake" | Venus scowls and "inhales", rocket squashes and slows (brake puffs) | - | screech |
| 20.20 | (pause after the last word) | rocket falls into the Sun: splash, flash ring, steam; Sun squeezes "> <" and sweats; shake | - | boom + sizzle |
| 20.28-21.0 | - | swap to cheer; camera rushes back to the opening framing (loops to frame 0) | cheer | whoosh |

## Orbit physics (src/sun/timeline.ts)
2D gravity, RK4 (GM = 1, Earth orbit = 1). Launch from the hand with Earth's sideways velocity + a throw
-> first closest approach 0.48 (just outside the rays) = the miss. Retro burn at the far point cancels ~10 %
of the speed (closest approach drops to 0.30, still a miss). A braking pass by Venus then drops it in.
A monotone "sim clock" maps real time to orbit time so each event lands on its word.

## Facts (checked)
- NASA: reaching the Sun takes 55x more energy than reaching Mars.
- Earth (and every rocket launched from it) moves sideways around the Sun at ~30 km/s; you must shed most
  of that sideways speed to get close.
- Parker Solar Probe used seven Venus flybys to reduce its orbital speed and get closer to the Sun.

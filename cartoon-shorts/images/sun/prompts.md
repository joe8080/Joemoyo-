# Sun Short - picture prompts (Higgsfield gpt_image_2_5, 4k, high, transparent)

STYLE_CHAR = Flat 2D cartoon in exactly the same drawing style as the reference images: the same simple white character with a big round head, a small soft body, noodle arms with simple four-finger hands and short legs with rounded feet, thick smooth black outlines of even weight, flat white fill with a very soft pale-grey shade on one side, small solid black oval eyes, simple curved black eyebrows, no nose, no hair, no clothes, a pink tongue only when the mouth is open. Clean vector-like linework, flat colours, no texture, no text, no border. Isolated on a fully transparent background: no sky, no ground, no floor shadow.

STYLE_OBJ = Flat 2D cartoon in exactly the same drawing style as the reference images: thick smooth black outlines of even weight, flat colours with one simple soft shade, clean vector-like linework, no texture, no text, no border, no characters. Isolated on a fully transparent background: no sky, no ground, no floor shadow.

hero (2:3, no ref): see first generation job 16cf84e5-5566-4822-a2b3-1782d57706dc

All pictures: model gpt_image_2_5, resolution 4k, quality high, background transparent, reference = hero job 16cf84e5-5566-4822-a2b3-1782d57706dc.
Each prompt = the line below + STYLE_CHAR (poses) or STYLE_OBJ (objects).

| file | aspect | job id | what is different in this picture |
|---|---|---|---|
| hero | 2:3 | 16cf84e5-5566-4822-a2b3-1782d57706dc | Full body, three-quarter view facing right, curious happy (brows raised, small smile); hand on the RIGHT side of the image holds a small red-and-white toy rocket upright (rounded nose, two fins, one porthole), rocket about head height |
| worried | 2:3 | c7b042d7-b9a8-4ea7-8a05-8b0bee93608a | EDIT of hero: same pose/position/rocket, only the face: worried, looking up, brows tilted up in the middle, small wavy open mouth |
| brace | 2:3 | 9cd53575-e4e2-4775-be41-59743c4b6311 | Full body facing viewer, bracing against wind from the right side of the image, knees bent, leaning right, both arms hugging the rocket to the chest, scared "whoa" |
| windup | 2:3 | 52be0355-a2f6-405d-b17c-4edbeaff58d9 | Three-quarter view facing right, wind-up: arm on the RIGHT side raised high behind the head holding the rocket, other arm forward, determined |
| follow | 2:3 | 7c0ac0d8-0004-4930-9314-fc48c3329c5e | Three-quarter view facing right, follow-through: arm on the RIGHT side up and forward with an EMPTY open hand pointing at the sky, hopeful |
| facepalm | 4:5 | e07b1c46-6f7d-47b6-8983-2605fd2a8f64 | Waist-up close-up facing viewer: hand on the LEFT side pressed on forehead, eyes squeezed as flat lines, wavy flat mouth, slumped |
| cheer | 2:3 | d7d4fae1-490d-44ed-9248-8db97543aa40 | Full body facing viewer, both arms straight up, empty hands, little jump, happy curved eyes, big open smile |
| rocket | 1:1 | 336a7ce3-5ea0-41fc-af67-988777dc532b | Only the rocket from the reference, upright, side view, no flame, no hand |
| earth | 1:1 | 4d3f5e78-cf25-4602-87d5-dde638cb17f8 | Small cartoon Earth, flat blue ocean, rounded green continents, two small clouds, NO face |
| sun | 1:1 | 85f96140-b744-4daf-af57-028e8d4a98fc | Big cartoon Sun: yellow disc (#FFD23F), 12 short rounded orange (#FF9F1C) triangular rays with a gap, blank face area |
| mars | 1:1 | 705b3433-b385-4d1c-86c7-3219e558f57c | Small rusty red Mars, three darker craters near the edges, NO face |
| venus | 1:1 | e48ab35e-2092-463f-85bf-acae9dcb5406 | Small pale creamy Venus, two soft tan wavy bands, NO face |

Sound effects (seed_audio, wav 48 kHz, "Sound effect only, no music, no voice: ..."): whoosh, launch, pop, sizzle, thruster, wind, screech, boom -> images/sun/sfx_raw, peak-normalised to -1 dBFS in public/sun/sfx.

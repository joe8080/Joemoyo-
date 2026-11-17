"""Word timings from a narration track (voice, or voice + music). Writes data/<ep>/words.json.
Usage: python3 data/words.py dahomey audio/dahomey/narration.wav   (needs: pip install faster-whisper)"""
import json, subprocess, sys, numpy as np
from faster_whisper import WhisperModel
ep, src = sys.argv[1], sys.argv[2]
pcm = np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', src, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-']), np.float32)
m = WhisperModel('small.en', device='cpu', compute_type='int8')
segs, _ = m.transcribe(pcm, word_timestamps=True, language='en', beam_size=5, vad_filter=False)
out = [[w.word.strip(), round(w.start, 3), round(w.end, 3)] for s in segs for w in s.words]
json.dump(out, open(f'data/{ep}/words.json', 'w'))
print(len(out), 'words; last ends at', out[-1][2])

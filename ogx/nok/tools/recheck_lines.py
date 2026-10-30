"""Re-decode whole script lines (cut_in..cut_out from line_timing.csv) with Whisper medium.en."""
import csv, sys, wave, pathlib, numpy as np, sherpa_onnx
ROOT = pathlib.Path(__file__).resolve().parents[1]; M = pathlib.Path(sys.argv[1]); want = sys.argv[2].split(",")
w = wave.open(str(ROOT / "audio/vo/VO_16k.wav")); sr = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=str(M / "medium.en-encoder.onnx"), decoder=str(M / "medium.en-decoder.onnx"),
    tokens=str(M / "medium.en-tokens.txt"), language="en", task="transcribe", num_threads=4)
for r in csv.DictReader(open(ROOT / "audio/vo/line_timing.csv")):
    if r["line"] in want:
        st = rec.create_stream(); st.accept_waveform(sr, a[int(float(r["cut_in"]) * sr):int(float(r["cut_out"]) * sr)])
        rec.decode_stream(st); print(r["line"], "|", st.result.text.strip())

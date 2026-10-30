"""Cut build/shots.json into slice timing files (build/slices/slice_NN.json). Each slice holds only its own
shots plus the dissolve neighbours, and a frame range. Render slices with these files, never with the
full-film timing (Lessons 29 Oct: full timing.csv in a slice made one shot 300 s)."""
import json, math, pathlib, os
ROOT = pathlib.Path(__file__).resolve().parents[1]
VER = os.environ.get("OGX_VER")          # v1.1+: OGX_VER=v1.1 reads/writes build/v1.1/ (v1.0 paths untouched)
B = ROOT / "build" / VER if VER else ROOT / "build"
film = json.load(open(B / "shots.json")); fps = film["fps"]; shots = film["shots"]
N_PER = 8
total_f = int(math.ceil(film["total"] * fps))
cuts = [0] + [int(round(shots[i]["t0"] * fps)) for i in range(N_PER, len(shots), N_PER)] + [total_f]
(B / "slices").mkdir(parents=True, exist_ok=True)
for k in range(len(cuts) - 1):
    f0, f1 = cuts[k], cuts[k + 1]
    t0, t1 = f0 / fps, f1 / fps
    keep = [s for s in shots if s["t1"] + film["xfade"] >= t0 and s["t0"] - film["xfade"] <= t1]
    sl = {"slice": k, "f0": f0, "f1": f1, "shots": keep,
          "out": str(B / f"parts/slice_{k:02d}.mp4"), "out_qa": str(B / f"parts_qa/slice_{k:02d}.mp4")}
    json.dump(sl, open(B / f"slices/slice_{k:02d}.json", "w"), indent=1, ensure_ascii=False)
    assert all(s["t1"] - s["t0"] < 15 for s in keep), "a shot longer than 15 s: wrong timing file?"
print(f"{len(cuts) - 1} slices, {total_f} frames")

# Split a downloaded motion pack back into per-still clips (frame-exact, one decode pass).
import json, subprocess, sys
i = int(sys.argv[1])
groups = json.load(open("chunks.json")); fc = json.load(open("framecounts.json"))
keys = groups[i - 1]
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"chunks/chunk{i}.mp4", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
                       stdout=subprocess.PIPE)
fs = 1920 * 1080 * 3 // 2
for k in keys:
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", "1920x1080", "-r", "24",
                            "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "15", "-g", "24", "-pix_fmt", "yuv420p",
                            f"clips/{k}.mp4"], stdin=subprocess.PIPE)
    for _ in range(fc[k]):
        buf = dec.stdout.read(fs)
        assert len(buf) == fs, (k, "short")
        enc.stdin.write(buf)
    enc.stdin.close(); enc.wait()
    print(k, fc[k], flush=True)
rest = dec.stdout.read()
print("leftover bytes", len(rest)); dec.wait()

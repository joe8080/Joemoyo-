# Download bridged composition outputs (content.mp4) by session id from the session transcript; args: idx:session ...
import re, subprocess, sys
t = open('/root/.claude/projects/-home-user/c8a2a160-21fc-57ae-b255-e46475a247d7.jsonl').read()
for a in sys.argv[1:]:
    i, s = a.split(':')
    us = re.findall(r'https://storage\.googleapis\.com/xi-backend/[^"\\\s]*?/' + s + r'/[A-Za-z0-9]+/content\.mp4\?[^"\\\s]+', t)
    r = subprocess.run(["curl", "-sS", "-f", "-o", f"chunks/chunk{i}.mp4", us[-1]], capture_output=True, text=True)
    n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries", "stream=nb_read_frames",
                        "-of", "csv=p=0", f"chunks/chunk{i}.mp4"], capture_output=True, text=True).stdout.strip()
    print(i, r.returncode, n)

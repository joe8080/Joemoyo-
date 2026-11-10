"""Print each processed line's duration and its pauses; set script.json cues to pause END times."""
import glob, os, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
for p in sorted(glob.glob(os.path.join(HERE, 'proc', '*.wav'))):
    d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))
    r = subprocess.run(['ffmpeg', '-i', p, '-af', 'silencedetect=n=-38dB:d=0.22', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ends = [round(float(x), 2) for x in re.findall(r'silence_end: ([\d.]+)', r)]
    print(os.path.basename(p)[:-4], f'{d:.2f}s', 'pause ends:', ends)

# Hardware capture

Tools for measuring Joe's outboard gear so the MOYO plugins can be matched to it.

- `make_test_signal.py` builds the test file (`python3 make_test_signal.py OUT_DIR`). The WAV is 25 MB, so it is generated rather than committed. `--selftest` runs it through a simulated compressor and checks the analysis recovers the delay, ratio and release.
- `MOYO_capture_test_manifest.json` lists where each section of the test file starts, in samples.
- `CAPTURE_GUIDE_WA-2A.md` is the step-by-step for the first unit, the Warm Audio WA-2A.

Recordings go in a Google Drive folder called "MOYO captures".

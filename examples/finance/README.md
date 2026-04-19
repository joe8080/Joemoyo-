# AI-Finance channel examples

Two variants share the same images and narration but produce different
outputs:

## Long-form (1920x1080)

```bash
python -m video_agent \
    --channel finance.long \
    --images ./examples/finance/img \
    --audio  ./examples/finance/narration.mp3 \
    --music  ./examples/finance/bed.mp3 \
    --captions ./examples/finance/script.srt \
    --out ./out/finance-long.mp4
```

## Shorts (1080x1920 @ 60fps)

```bash
python -m video_agent \
    --channel finance.short \
    --images ./examples/finance/img \
    --audio  ./examples/finance/narration.mp3 \
    --manifest ./examples/finance/manifest.short.json \
    --out ./out/finance-short.mp4
```

Best practices for finance visuals:

- Export chart images at **2x** the target resolution so the Ken Burns
  upscale stays sharp.
- Keep the narration tight — finance.short uses 3s per image by default.
- Use `--seed` for deterministic pan choices when re-rendering an episode.

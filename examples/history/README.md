# History channel example

Drop a set of images (jpg/png/webp, ideally 3840x2160 or larger so the
Ken Burns upscale stays crisp) into `./img/`, record or generate the
narration as `narration.mp3`, then:

```bash
python -m video_agent \
    --channel history \
    --images ./examples/history/img \
    --audio  ./examples/history/narration.mp3 \
    --manifest ./examples/history/manifest.json \
    --out ./out/history-ep01.mp4
```

The manifest (`manifest.json`) in this folder is optional — delete it and
the agent will auto-distribute image durations across the narration
length.

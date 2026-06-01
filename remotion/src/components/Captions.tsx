import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

interface Cue {
  start: number;
  end: number;
  text: string;
}

const ts = (s: string): number => {
  // 00:00:12,000 -> seconds
  const m = s.trim().match(/(\d+):(\d+):(\d+)[,.](\d+)/);
  if (!m) return 0;
  return +m[1] * 3600 + +m[2] * 60 + +m[3] + +m[4] / 1000;
};

export const parseSrt = (srt: string): Cue[] => {
  if (!srt) return [];
  return srt
    .split(/\n\s*\n/)
    .map((block) => {
      const lines = block.trim().split("\n");
      const timeLine = lines.find((l) => l.includes("-->"));
      if (!timeLine) return null;
      const [a, b] = timeLine.split("-->");
      const text = lines.slice(lines.indexOf(timeLine) + 1).join(" ").trim();
      return { start: ts(a), end: ts(b), text };
    })
    .filter((c): c is Cue => !!c && !!c.text);
};

/** Renders burnt-in captions. Local frame 0 = first clip (place after intro). */
export const Captions: React.FC<{ srt: string }> = ({ srt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cues = React.useMemo(() => parseSrt(srt), [srt]);
  const active = cues.find((c) => t >= c.start && t <= c.end);
  if (!active) return null;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 70 }}>
      <div
        style={{
          fontFamily: "Inter, system-ui, sans-serif",
          fontSize: 44,
          color: "#fff",
          background: "rgba(0,0,0,0.5)",
          padding: "10px 26px",
          borderRadius: 8,
          textShadow: "0 2px 6px rgba(0,0,0,0.9)",
          maxWidth: "80%",
          textAlign: "center",
        }}
      >
        {active.text}
      </div>
    </AbsoluteFill>
  );
};

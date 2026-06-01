import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame } from "remotion";
import { Pan } from "../types";

/** A still image with a slow Ken Burns zoom/pan over `durationInFrames`. */
export const KenBurnsStill: React.FC<{
  src: string;
  pan: Pan;
  durationInFrames: number;
}> = ({ src, pan, durationInFrames }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateRight: "clamp",
  });

  const zoomFrom = 1.05;
  const zoomTo = 1.18;
  let scale = zoomFrom + (zoomTo - zoomFrom) * p;
  let x = 0;
  let y = 0;
  const travel = 6; // percent of frame to pan across

  switch (pan) {
    case "zoom-in":
      scale = 1.05 + 0.18 * p;
      break;
    case "zoom-out":
      scale = 1.23 - 0.18 * p;
      break;
    case "left-to-right":
      x = interpolate(p, [0, 1], [travel, -travel]);
      break;
    case "right-to-left":
      x = interpolate(p, [0, 1], [-travel, travel]);
      break;
    case "top-to-bottom":
      y = interpolate(p, [0, 1], [travel, -travel]);
      break;
    case "bottom-to-top":
      y = interpolate(p, [0, 1], [-travel, travel]);
      break;
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden" }}>
      {src ? (
        <Img
          src={src}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${scale}) translate(${x}%, ${y}%)`,
          }}
        />
      ) : (
        <AbsoluteFill
          style={{
            background: "linear-gradient(135deg,#2b2118,#0c0a08)",
            transform: `scale(${scale}) translate(${x}%, ${y}%)`,
          }}
        />
      )}
    </AbsoluteFill>
  );
};

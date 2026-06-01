import React from "react";
import { Composition } from "remotion";
import { Episode } from "./Episode";
import { DEFAULT_PROPS, EpisodeProps } from "./types";

/**
 * Total composition length = intro + sum(clip durations) + outro, in frames.
 * Cards/captions are overlaid on this timeline by absolute time.
 */
const durationInFrames = (props: EpisodeProps): number => {
  const fps = props.fps || 30;
  const intro = props.intro?.duration ?? 0;
  const outro = props.outro?.duration ?? 0;
  const clips = (props.clips || []).reduce((s, c) => s + (c.duration || 0), 0);
  return Math.max(1, Math.round((intro + clips + outro) * fps));
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Episode"
      component={Episode}
      defaultProps={DEFAULT_PROPS}
      fps={DEFAULT_PROPS.fps}
      width={DEFAULT_PROPS.width}
      height={DEFAULT_PROPS.height}
      durationInFrames={durationInFrames(DEFAULT_PROPS)}
      calculateMetadata={({ props }) => ({
        durationInFrames: durationInFrames(props as EpisodeProps),
        fps: (props as EpisodeProps).fps || 30,
        width: (props as EpisodeProps).width || 1920,
        height: (props as EpisodeProps).height || 1080,
      })}
    />
  );
};

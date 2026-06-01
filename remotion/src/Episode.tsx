import React from "react";
import { AbsoluteFill, Audio, Sequence, Series, interpolate, useCurrentFrame } from "remotion";
import { KenBurnsStill } from "./components/KenBurnsStill";
import { Captions } from "./components/Captions";
import {
  LowerThirdView,
  OutroView,
  QuoteCardView,
  StatCardView,
  TitleCardView,
} from "./components/Cards";
import { EpisodeProps } from "./types";

const FadeIn: React.FC<{ children: React.ReactNode; frames?: number }> = ({
  children,
  frames = 12,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, frames], [0, 1], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

export const Episode: React.FC<EpisodeProps> = (props) => {
  const fps = props.fps || 30;
  const sec = (s: number) => Math.max(1, Math.round(s * fps));

  const introFrames = props.intro ? sec(props.intro.duration) : 0;
  const clips = props.clips || [];

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Narration starts when the visuals start (after the intro card). */}
      {props.narrationUrl ? (
        <Sequence from={introFrames}>
          <Audio src={props.narrationUrl} />
        </Sequence>
      ) : null}

      {/* Intro card -> Ken Burns clips -> outro card, laid sequentially. */}
      <Series>
        {props.intro ? (
          <Series.Sequence durationInFrames={introFrames}>
            <FadeIn>
              <TitleCardView intro={props.intro} />
            </FadeIn>
          </Series.Sequence>
        ) : null}

        {clips.map((clip, i) => (
          <Series.Sequence key={i} durationInFrames={sec(clip.duration)}>
            <FadeIn>
              <KenBurnsStill src={clip.src} pan={clip.pan} durationInFrames={sec(clip.duration)} />
            </FadeIn>
          </Series.Sequence>
        ))}

        {props.outro ? (
          <Series.Sequence durationInFrames={sec(props.outro.duration)}>
            <FadeIn>
              <OutroView outro={props.outro} />
            </FadeIn>
          </Series.Sequence>
        ) : null}
      </Series>

      {/* Captions + dynamic cards are timed relative to narration start. */}
      <Sequence from={introFrames}>
        {props.srt ? <Captions srt={props.srt} /> : null}

        {(props.lowerThirds || []).map((d, i) => (
          <Sequence key={`lt${i}`} from={sec(d.at)} durationInFrames={sec(d.duration)}>
            <LowerThirdView data={d} />
          </Sequence>
        ))}
        {(props.statCards || []).map((d, i) => (
          <Sequence key={`st${i}`} from={sec(d.at)} durationInFrames={sec(d.duration)}>
            <StatCardView data={d} />
          </Sequence>
        ))}
        {(props.quoteCards || []).map((d, i) => (
          <Sequence key={`q${i}`} from={sec(d.at)} durationInFrames={sec(d.duration)}>
            <QuoteCardView data={d} />
          </Sequence>
        ))}
      </Sequence>
    </AbsoluteFill>
  );
};

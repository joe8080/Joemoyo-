import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Intro, LowerThird, Outro, QuoteCard, StatCard } from "../types";

const FONT = "Georgia, 'Times New Roman', serif";
const SANS = "Inter, system-ui, sans-serif";
const GOLD = "#d8b46a";

const useEnter = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame, fps, config: { damping: 200 } });
};

export const TitleCardView: React.FC<{ intro: Intro }> = ({ intro }) => {
  const e = useEnter();
  const y = interpolate(e, [0, 1], [40, 0]);
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        background: "radial-gradient(circle at center,#1a140d,#000)",
      }}
    >
      <div style={{ textAlign: "center", opacity: e, transform: `translateY(${y}px)` }}>
        <div style={{ fontFamily: FONT, color: "#fff", fontSize: 96, fontWeight: 700 }}>
          {intro.title}
        </div>
        {intro.subtitle ? (
          <div style={{ fontFamily: SANS, color: GOLD, fontSize: 38, marginTop: 20, letterSpacing: 2 }}>
            {intro.subtitle}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

export const LowerThirdView: React.FC<{ data: LowerThird }> = ({ data }) => {
  const e = useEnter();
  const x = interpolate(e, [0, 1], [-60, 0]);
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", paddingBottom: 140, paddingLeft: 100 }}>
      <div style={{ opacity: e, transform: `translateX(${x}px)` }}>
        <div
          style={{
            display: "inline-block",
            background: "rgba(0,0,0,0.65)",
            borderLeft: `6px solid ${GOLD}`,
            padding: "18px 30px",
          }}
        >
          <div style={{ fontFamily: FONT, color: "#fff", fontSize: 46, fontWeight: 700 }}>
            {data.name}
          </div>
          {data.detail ? (
            <div style={{ fontFamily: SANS, color: "#cfcfcf", fontSize: 28, marginTop: 6 }}>
              {data.detail}
            </div>
          ) : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const StatCardView: React.FC<{ data: StatCard }> = ({ data }) => {
  const e = useEnter();
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ textAlign: "center", opacity: e, transform: `scale(${0.9 + 0.1 * e})` }}>
        <div style={{ fontFamily: FONT, color: GOLD, fontSize: 150, fontWeight: 800 }}>
          {data.value}
        </div>
        <div style={{ fontFamily: SANS, color: "#fff", fontSize: 40, letterSpacing: 1 }}>
          {data.label}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const QuoteCardView: React.FC<{ data: QuoteCard }> = ({ data }) => {
  const e = useEnter();
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        background: "rgba(0,0,0,0.55)",
        padding: "0 220px",
      }}
    >
      <div style={{ textAlign: "center", opacity: e }}>
        <div style={{ fontFamily: FONT, color: "#fff", fontSize: 60, fontStyle: "italic", lineHeight: 1.3 }}>
          “{data.quote}”
        </div>
        {data.attribution ? (
          <div style={{ fontFamily: SANS, color: GOLD, fontSize: 34, marginTop: 30 }}>
            — {data.attribution}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

export const OutroView: React.FC<{ outro: Outro }> = ({ outro }) => {
  const e = useEnter();
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        background: "radial-gradient(circle at center,#1a140d,#000)",
      }}
    >
      <div style={{ textAlign: "center", opacity: e }}>
        <div style={{ fontFamily: FONT, color: "#fff", fontSize: 80, fontWeight: 700 }}>
          {outro.title}
        </div>
        {outro.cta ? (
          <div style={{ fontFamily: SANS, color: GOLD, fontSize: 40, marginTop: 24 }}>
            {outro.cta}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

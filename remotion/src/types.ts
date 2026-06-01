export type Pan =
  | "zoom-in"
  | "zoom-out"
  | "left-to-right"
  | "right-to-left"
  | "top-to-bottom"
  | "bottom-to-top";

export interface Clip {
  src: string; // image URL or staticFile() path
  duration: number; // seconds on screen
  pan: Pan;
  caption?: string;
}

export interface Intro {
  title: string;
  subtitle?: string;
  duration: number;
}

export interface LowerThird {
  at: number;
  name: string;
  detail?: string;
  duration: number;
}

export interface StatCard {
  at: number;
  value: string;
  label: string;
  duration: number;
}

export interface QuoteCard {
  at: number;
  quote: string;
  attribution?: string;
  duration: number;
}

export interface Outro {
  title: string;
  cta?: string;
  duration: number;
}

export interface EpisodeProps {
  fps: number;
  width: number;
  height: number;
  narrationUrl?: string | null;
  srt?: string;
  clips: Clip[];
  intro?: Intro | null;
  lowerThirds?: LowerThird[];
  statCards?: StatCard[];
  quoteCards?: QuoteCard[];
  outro?: Outro | null;
}

export const DEFAULT_PROPS: EpisodeProps = {
  fps: 30,
  width: 1920,
  height: 1080,
  narrationUrl: null,
  srt: "",
  clips: [
    { src: "", duration: 6, pan: "zoom-in", caption: "Great Zimbabwe" },
    { src: "", duration: 6, pan: "left-to-right", caption: "The Great Enclosure" },
  ],
  intro: { title: "Great Zimbabwe", subtitle: "The Stone City of a Lost Kingdom", duration: 4 },
  lowerThirds: [],
  statCards: [],
  quoteCards: [],
  outro: { title: "Chronicles of Time", cta: "Like and subscribe", duration: 5 },
};

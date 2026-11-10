import React from 'react';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame} from 'remotion';
import TL from './timeline.json';
import {Background, SectionCard} from './theme';
import * as S1 from './nv1';
import * as S2 from './nv2';
const S: any = {...S1, ...S2};
const SECTIONS: Record<string, [string, string]> = {
  '01': ['01', 'What actually happened'], '02': ['02', 'Why investors care'], '03': ['03', 'The price move'], '04': ['04', 'Check the business'],
  '05': ['05', 'Two dates, different questions'], '06': ['06', 'Three scenarios'], '07': ['07', 'Investor checklist'],
};
const XF = 10;
const Fade: React.FC<{len: number; first: boolean; children: React.ReactNode}> = ({len, first, children}) => {
  const f = useCurrentFrame();
  const a = first ? 1 : interpolate(f, [0, XF], [0, 1], {extrapolateRight: 'clamp'});
  const b = interpolate(f, [len - XF, len], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{opacity: Math.min(a, b)}}>{children}</AbsoluteFill>;
};
export const Video: React.FC = () => (
  <AbsoluteFill style={{background: '#070706'}}>
    <Background />
    {TL.scenes.map((s: any, i: number) => {
      const Comp = S[s.id];
      const isLast = i === TL.scenes.length - 1;
      const sectional = s.new_section && i > 0 && SECTIONS[s.section];
      const start = sectional ? s.narr_start - 14 : s.vis_start;
      const end = isLast ? s.vis_end : s.vis_end + XF;
      const len = end - start;
      const cues = s.cues.map((c: number) => c - start);
      return (
        <React.Fragment key={s.id}>
          {sectional ? (
            <Sequence from={s.vis_start} durationInFrames={s.narr_start - 8 - s.vis_start}>
              <SectionCard num={SECTIONS[s.section][0]} title={SECTIONS[s.section][1]} len={s.narr_start - 8 - s.vis_start} />
            </Sequence>
          ) : null}
          <Sequence from={start} durationInFrames={len}>
            <Fade len={len} first={i === 0}><Comp len={len} cues={cues} /></Fade>
          </Sequence>
        </React.Fragment>
      );
    })}
  </AbsoluteFill>
);

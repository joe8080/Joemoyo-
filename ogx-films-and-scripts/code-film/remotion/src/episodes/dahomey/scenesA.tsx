// Dahomey / Cotonou 1890, part A: cold open, who they were, the battle (S01-S26). Everything is drawn in code.
import React from 'react';
import {AbsoluteFill, interpolate, random, useCurrentFrame} from 'remotion';
import {C, DISPLAY, SERIF, MONO, Fade, Pop, Count, Typed, Draw, Stamp, H, Body, Label, Center, Rule, GeoMap, Pin, PT, Figure, Rain, Palisade, ease, lin, cu, clamp, shake} from '../../kit';

export type P = {cues: number[]; len: number};
const night = 'linear-gradient(180deg, #060A10 0%, #0B1016 55%, #0A0806 100%)';
const Chip: React.FC<{children: React.ReactNode; color?: string; style?: React.CSSProperties}> = ({children, color = C.gold, style}) => (
  <span style={{fontFamily: MONO, fontWeight: 600, fontSize: 26, letterSpacing: 2.5, color, border: `2px solid ${color}`, borderRadius: 8, padding: '8px 18px', background: 'rgba(11,9,7,0.7)', display: 'inline-block', whiteSpace: 'nowrap', ...style}}>{children}</span>);

// S01: where and when. Push in from West Africa to the coast.
export const S01: React.FC<P> = ({len}) => {
  const f = useCurrentFrame(); const z = ease(f, 4, len - 30);
  const k = interpolate(z, [0, 1], [2.1, 0.26]);
  return (<AbsoluteFill>
    <GeoMap cx={interpolate(z, [0, 1], [2000, PT.cotonou[0] + 120 * k])} cy={interpolate(z, [0, 1], [1300, PT.cotonou[1] - 110 * k])} k={k}>
      <text x={2325} y={1548} fontFamily="Cinzel, serif" fontWeight={700} fontSize={34 * k} fill={C.gold} opacity={ease(f, len * 0.45, 20) * 0.9} letterSpacing={6 * k} textAnchor="middle">KINGDOM OF DAHOMEY</text>
      <text x={PT.cotonou[0] + 60 * k} y={PT.cotonou[1] + 150 * k} fontFamily="Source Serif, serif" fontStyle="italic" fontSize={30 * k} fill="#6E8C99" opacity={ease(f, len * 0.5, 20)}>Gulf of Guinea</text>
      <Pin p={PT.abomey} k={k} text="ABOMEY" sub="royal capital" at={len * 0.55} color={C.text2} size={26} />
      <Pin p={PT.cotonou} k={k} text="COTONOU" sub="present-day Benin" at={18} color={C.gold} size={38} pulse />
    </GeoMap>
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 60% 45%, transparent 30%, rgba(4,6,10,0.78) 100%)'}} />
    <div style={{position: 'absolute', left: 90, bottom: 190}}>
      <Fade at={8}><Label size={30}>The night of</Label></Fade>
      <Fade at={14}><H size={104} style={{marginTop: 6}}>3 MARCH 1890</H></Fade>
    </div>
  </AbsoluteFill>);
};

// S02: the storm, and the garrison waiting behind the stockade
export const S02: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0);
  const flash = Math.max(lin(f, 40, 43, 0.5, 0) * (f >= 40 ? 1 : 0), lin(f, c0 - 6, c0 + 6, 0.7, 0) * (f >= c0 - 6 ? 1 : 0));
  return (<AbsoluteFill style={{background: night}}>
    <AbsoluteFill style={{background: '#C9D8E6', opacity: flash}} />
    <Rain n={130} opacity={0.55} />
    <Palisade y={1090} h={300} />
    <div style={{position: 'absolute', left: 120, top: 170}}>
      <Fade at={6}><Chip color={C.blue}>STORM ON THE COAST · FROM 7:00 PM</Chip></Fade>
    </div>
    <div style={{position: 'absolute', left: 120, top: 330, opacity: ease(f, c0, 10)}}>
      <Count to={359} at={c0} dur={40} style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 300, color: C.gold, lineHeight: 1}} />
      <H size={62} style={{marginTop: 4}}>DEFENDERS, WAITING IN THE DARK</H>
    </div>
  </AbsoluteFill>);
};

// S03: who the 359 were
export const S03: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2);
  const COLS = 40;
  return (<AbsoluteFill style={{padding: '120px 120px'}}>
    <Fade at={4}><Label>The garrison of 359</Label></Fade>
    <svg width={1680} height={390} style={{marginTop: 20}}>{Array.from({length: 359}).map((_, i) => {
      const x = (i % COLS) * 42 + 20, y = Math.floor(i / COLS) * 42 + 20; const african = i < 299;
      const p = african ? ease(f, c0 + i * 0.12, 8) : ease(f, c2 + (i - 299) * 0.4, 8);
      return <circle key={i} cx={x} cy={y} r={12} fill={p > 0.5 ? (african ? C.red : C.blue) : '#4A4030'} opacity={0.55 + 0.45 * p} />; })}</svg>
    <div style={{display: 'flex', gap: 60, marginTop: 6, alignItems: 'flex-start'}}>
      <Fade at={c0 + 10} style={{flex: 1.6}}>
        <H size={56} color={C.red} style={{whiteSpace: 'nowrap'}}>299 AFRICAN TIRAILLEURS</H>
        <Body size={36}>Senegalese, in red chéchias, and Gabonese</Body>
        <Fade at={c1} style={{marginTop: 12}}><Chip color={C.text2} style={{fontSize: 22}}>LANDED FROM THE CRUISER SANÉ · TWO WEEKS BEFORE</Chip></Fade>
      </Fade>
      <Fade at={c2} style={{flex: 1}}>
        <H size={56} color={C.blue}>THE REST</H>
        <Body size={36}>European marine officers and artillerymen</Body>
      </Fade>
    </div>
  </AbsoluteFill>);
};

// S04: the night watch in thirds
export const S04: React.FC<P> = ({cues, len}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0); const X0 = 210, WD = 1500;
  const run = lin(f, c0, len - 20);
  return (<AbsoluteFill style={{background: night}}>
    <Rain n={60} opacity={0.3} />
    <div style={{position: 'absolute', left: 210, top: 200}}>
      <Fade at={4}><Chip color={C.amber}>WARNED BY SPIES: AN ATTACK IS COMING</Chip></Fade>
      <Fade at={c0 - 6}><H size={84} style={{marginTop: 30}}>THEY WATCHED IN THIRDS</H></Fade>
    </div>
    <svg width={1920} height={1080} style={{position: 'absolute'}}>
      {[0, 1, 2].map((i) => { const on = lin(run, i / 3, i / 3 + 0.08); const active = run >= i / 3 && run < (i + 1) / 3 + 0.02;
        return <rect key={i} x={X0 + i * (WD / 3) + 6} y={600} width={WD / 3 - 12} height={70} rx={10} fill={active ? C.gold : C.goldDim} opacity={0.25 + 0.75 * on} />; })}
      {['7 PM', '10 PM', '1 AM', '4 AM'].map((t, i) => <text key={t} x={X0 + i * (WD / 3)} y={740} textAnchor="middle" fontFamily="Plex, monospace" fontWeight={600} fontSize={34} fill={C.text2}>{t}</text>)}
      <circle cx={X0 + run * WD} cy={545} r={22} fill={C.cream} opacity={0.9} />
      <circle cx={X0 + run * WD + 9} cy={539} r={19} fill="#0A0E14" />
    </svg>
    <Fade at={c0 + 14} style={{position: 'absolute', left: 210, top: 790}}><Body size={40}>One third of the garrison awake at a time, through the night.</Body></Fade>
  </AbsoluteFill>);
};

// S05: the north bastion, just before five
export const S05: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2);
  return (<AbsoluteFill style={{background: night}}>
    <svg width={1920} height={1080} style={{position: 'absolute'}}>
      {Array.from({length: 150}).map((_, i) => <circle key={i} cx={100 + random('bx' + i) * 1720} cy={130 + random('by' + i) * 300} r={10 + random('br' + i) * 14} fill="#16201A" opacity={0.9} />)}
      <Draw d="M 150 760 L 760 760 L 760 640 L 960 520 L 1160 640 L 1160 760 L 1770 760" at={6} dur={40} color={C.blue} w={8} />
      {f > c1 && [0, 1, 2].map((i) => { const t = ((f - c1) + i * 14) % 42; return <circle key={i} cx={1010} cy={330} r={20 + t * 4.2} fill="none" stroke={C.amber} strokeWidth={4} opacity={(1 - t / 42) * 0.9} />; })}
      <g opacity={ease(f, c0, 12)}><circle cx={960} cy={640} r={16} fill={C.blue} /><circle cx={960} cy={640} r={30} fill="none" stroke={C.blue} strokeWidth={3} /></g>
      {f > c2 && [-3, -2, -1, 1, 2, 3].map((i) => <circle key={i} cx={960 + i * 130} cy={800 - Math.abs(i) * 6} r={9} fill={C.blue} opacity={lin(f, c2 + Math.abs(i) * 5, c2 + Math.abs(i) * 5 + 8)} />)}
    </svg>
    <div style={{position: 'absolute', left: 120, top: 130}}><Fade at={4}><Chip>JUST BEFORE 5:00 AM</Chip></Fade></div>
    <Fade at={c0} style={{position: 'absolute', left: 800, top: 668}}><H size={40} color={C.blue}>LT COMPÉRAT</H><Label size={24} color={C.text2}>north bastion</Label></Fade>
    <Fade at={c1 + 4} style={{position: 'absolute', left: 1130, top: 290}}><Label size={30} color={C.amber}>Movement in the brush</Label></Fade>
    <Fade at={c2} style={{position: 'absolute', left: 150, top: 850}}><Body size={42} style={{fontStyle: 'italic', fontWeight: 400}}>He warned his men in a whisper.</Body></Fade>
  </AbsoluteFill>);
};

// S06: bells, then an army rises ten paces from the stakes
export const S06: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1); const rise = ease(f, c1, 16);
  return (<AbsoluteFill style={{background: night, transform: shake(f, c1, 1.8)}}>
    <svg width={1920} height={1080} style={{position: 'absolute'}}>
      <defs><clipPath id="gr"><rect x={0} y={0} width={1920} height={760} /></clipPath></defs>
      {[0, 1, 2, 3].map((i) => { const t = (f + i * 11) % 44; return <circle key={i} cx={330} cy={300} r={50 + t * 6} fill="none" stroke={C.gold} strokeWidth={5} opacity={(1 - t / 44) * lin(f, 2, 10)} />; })}
      <g transform={`rotate(${Math.sin(f / 2.2) * 16} 330 250)`}><path d="M 285 330 Q 285 240 330 235 Q 375 240 375 330 L 395 345 L 265 345 Z" fill={C.gold} /><circle cx={330} cy={356} r={11} fill={C.gold} /></g>
      {[0, 1, 2, 3, 4].map((i) => <path key={i} d={`M ${120 + i * 34} 760 L ${120 + i * 34} 520 L ${135 + i * 34} 498 L ${150 + i * 34} 520 L ${150 + i * 34} 760 Z`} fill="#211910" stroke={C.blue} strokeWidth={2} />)}
      <line x1={0} y1={760} x2={1920} y2={760} stroke="#3A3024" strokeWidth={4} />
      <g opacity={ease(f, c0, 12)}><path d="M 300 800 L 300 830 L 720 830 L 720 800" fill="none" stroke={C.cream} strokeWidth={4} />
        <text x={510} y={880} textAnchor="middle" fontFamily="Cinzel, serif" fontWeight={700} fontSize={44} fill={C.cream} letterSpacing={4}>TEN PACES</text></g>
      <g clipPath="url(#gr)">{Array.from({length: 16}).map((_, i) => <Figure key={i} x={760 + i * 70 + random('fx' + i) * 20} y={760 + (1 - rise) * (190 + random('fy' + i) * 60)} h={150 + random('fh' + i) * 30} color={i < 6 ? C.gold : '#8C6A3A'} />)}</g>
      {Array.from({length: 26}).map((_, i) => <ellipse key={i} cx={740 + i * 46} cy={760} rx={40} ry={16 + random('g' + i) * 14} fill="#101810" />)}
    </svg>
    <Fade at={3} style={{position: 'absolute', left: 470, top: 250}}><H size={70}>THEN BELLS SOUNDED</H></Fade>
  </AbsoluteFill>);
};

// S07: the claim, attributed, then the question the film asks
export const S07: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1); const q = ease(f, c1, 14);
  return (<AbsoluteFill>
    <AbsoluteFill style={{opacity: 1 - q * 0.86}}>
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        {[0, 1, 2].map((r) => Array.from({length: 13}).map((_, i) => <Figure key={r + '-' + i} x={((i * 150 + r * 50 + f * 1.6) % 2100) - 90} y={560 + r * 150} h={150} color={r === 0 ? C.gold : '#6B5330'} opacity={r === 0 ? 1 : 0.7} />))}
      </svg>
      <div style={{position: 'absolute', left: 120, top: 150}}>
        <Fade at={c0 - 4}><H size={70} color={C.gold}>AT ITS HEAD: THE WOMEN SOLDIERS</H></Fade>
        <Fade at={c0 + 8} style={{marginTop: 18}}><Chip color={C.amber}>ACCORDING TO GOVERNOR BAYOL</Chip></Fade>
      </div>
    </AbsoluteFill>
    <Center style={{opacity: q}}>
      <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 118, color: C.cream, textAlign: 'center', lineHeight: 1.12}}>What can we<br />actually <span style={{color: C.gold}}>prove</span>?</div>
      <svg width={560} height={30} style={{marginTop: 8}}><Draw d="M 6 16 Q 180 2 300 14 T 554 10" at={c1 + 12} dur={16} w={8} /></svg>
    </Center>
  </AbsoluteFill>);
};

// S08: title
export const S08: React.FC<P> = () => (<Center>
  <Fade at={4}><Label size={30}>OrigineX Human Archives</Label></Fade>
  <Fade at={10}><H size={150} style={{textAlign: 'center', marginTop: 22, fontWeight: 900, letterSpacing: 8}}>THE GHOST ARMY</H></Fade>
  <Fade at={18}><H size={96} color={C.gold} style={{letterSpacing: 16}}>OF DAHOMEY</H></Fade>
  <Rule at={26} w={620} />
  <Fade at={32}><Body size={46} style={{fontStyle: 'italic', fontWeight: 400}}>The women who fought France · 1890</Body></Fade>
</Center>);

// S09: the name, and when the corps began
export const S09: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2);
  return (<AbsoluteFill style={{padding: '170px 140px'}}>
    <Fade at={4}><Label>Their name meant, roughly</Label></Fade>
    <div style={{fontFamily: SERIF, fontStyle: 'italic', fontWeight: 400, fontSize: 104, color: C.cream, lineHeight: 1.15, marginTop: 26, minHeight: 250}}><Typed text={'“Make way for me, or I fall on you.”'} at={c0} cps={26} /></div>
    <Fade at={c1} style={{marginTop: 40}}><H size={64} color={C.gold}>A STANDING CORPS</H></Fade>
    <svg width={1640} height={150} style={{marginTop: 26}}>
      <Draw d="M 10 60 L 1630 60" at={c2 - 6} dur={30} color={C.goldDim} w={4} />
      <g opacity={ease(f, c2, 12)}><circle cx={140} cy={60} r={16} fill={C.gold} /><text x={140} y={120} textAnchor="middle" fontFamily="Cinzel, serif" fontWeight={700} fontSize={40} fill={C.gold}>1720s</text>
        <text x={190} y={36} fontFamily="Plex, monospace" fontWeight={600} fontSize={28} fill={C.text2} letterSpacing={2}>PROBABLY FORMED AS A PALACE GUARD</text></g>
      <g opacity={ease(f, c2 + 14, 12)}><circle cx={1500} cy={60} r={12} fill={C.cream} /><text x={1500} y={120} textAnchor="middle" fontFamily="Cinzel, serif" fontWeight={700} fontSize={40} fill={C.cream}>1890</text></g>
    </svg>
  </AbsoluteFill>);
};

// S10: about 1,500 by the late 1870s
export const S10: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0);
  return (<AbsoluteFill>
    <svg width={1920} height={1080} style={{position: 'absolute'}}>{Array.from({length: 1500}).map((_, i) => <circle key={i} cx={900 + (i % 50) * 19} cy={230 + Math.floor(i / 50) * 20} r={6} fill={C.gold} opacity={lin(f, c0 + (i / 1500) * 34, c0 + (i / 1500) * 34 + 4) * 0.9} />)}</svg>
    <div style={{position: 'absolute', left: 120, top: 300}}>
      <Label>By the late 1870s</Label>
      <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 190, color: C.gold, lineHeight: 1.05}}><span style={{fontSize: 90, color: C.text2}}>c. </span><Count to={1500} at={c0} dur={34} /></div>
      <H size={58}>WOMEN SOLDIERS</H>
    </div>
  </AbsoluteFill>);
};

// training tiles, shared by S11 and S35
const Tile: React.FC<{at: number; title: string; sub: string; children: React.ReactNode}> = ({at, title, sub, children}) => (
  <Pop at={at} from={0.85} style={{width: 500, background: 'rgba(25,19,12,0.9)', border: `2px solid ${C.line}`, borderRadius: 20, padding: '34px 30px 30px', textAlign: 'center'}}>
    <svg width={400} height={220} viewBox="0 0 400 220">{children}</svg>
    <H size={46} style={{marginTop: 14}}>{title}</H><Body size={32}>{sub}</Body>
  </Pop>);
export const Training: React.FC<{cues: number[]; days?: string}> = ({cues, days = 'lasting days'}) => (
  <div style={{display: 'flex', gap: 50, justifyContent: 'center'}}>
    <Tile at={cu(cues, 0)} title="THORN HEDGES" sub="climbed in drill">
      {Array.from({length: 9}).map((_, i) => <path key={i} d={`M ${30 + i * 40} 200 L ${50 + i * 40} ${60 + (i % 3) * 22} L ${70 + i * 40} 200 M ${38 + i * 40} 140 L ${22 + i * 40} 118 M ${62 + i * 40} 120 L ${80 + i * 40} 98`} stroke={C.teal} strokeWidth={6} fill="none" strokeLinecap="round" />)}
    </Tile>
    <Tile at={cu(cues, 1)} title="WRESTLING" sub="hand to hand">
      <Figure x={160} y={205} h={170} color={C.gold} gun={false} lean={16} /><Figure x={240} y={205} h={170} color={C.amber} gun={false} lean={-16} />
    </Tile>
    <Tile at={cu(cues, 2)} title="SURVIVAL" sub={`exercises ${days}`}>
      <path d="M 40 190 Q 200 -40 360 190" stroke={C.goldDim} strokeWidth={5} fill="none" strokeDasharray="4 14" strokeLinecap="round" />
      <circle cx={200} cy={76} r={34} fill={C.gold} /><line x1={20} y1={196} x2={380} y2={196} stroke={C.text2} strokeWidth={5} />
    </Tile>
  </div>);
export const S11: React.FC<P> = ({cues}) => (<Center>
  <Fade at={2} style={{marginBottom: 44}}><H size={72}>THEIR TRAINING WAS BRUTAL</H></Fade>
  <Training cues={cues} />
</Center>);

// S12: what they carried
export const S12: React.FC<P> = ({cues}) => {
  const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2);
  const Item: React.FC<{at: number; t: string; children: React.ReactNode}> = ({at, t, children}) => (<Fade at={at} style={{textAlign: 'center', width: 400}}><svg width={360} height={200} viewBox="0 0 360 200">{children}</svg><H size={50}>{t}</H></Fade>);
  return (<Center>
    <div style={{display: 'flex', gap: 60}}>
      <Item at={4} t="MUSKETS"><path d="M 20 150 L 70 120 L 330 60 L 334 72 L 90 138 L 60 176 Z" fill={C.gold} /></Item>
      <Item at={c0} t="BLADES"><path d="M 40 170 Q 180 150 300 30 Q 250 150 70 190 Z" fill={C.cream} /><rect x={22} y={166} width={52} height={18} rx={6} fill={C.goldDim} transform="rotate(-8 48 175)" /></Item>
      <Item at={c1} t="AMULETS"><path d="M 110 30 Q 180 150 250 30" fill="none" stroke={C.text2} strokeWidth={5} /><rect x={150} y={112} width={60} height={70} rx={12} fill={C.amber} /><line x1={150} y1={134} x2={210} y2={134} stroke={C.ink} strokeWidth={4} /></Item>
    </div>
    <Fade at={c1 + 14} style={{marginTop: 34}}><Chip color={C.muted}>NO WEAPON MODEL VERIFIED FOR 1890</Chip></Fade>
    <Fade at={c2} style={{marginTop: 46, display: 'flex', alignItems: 'center', gap: 30}}>
      <svg width={150} height={90}><path d="M 70 84 Q 10 70 14 8 Q 34 54 70 60 Z" fill="#D9DEE2" /><path d="M 80 84 Q 140 70 136 8 Q 116 54 80 60 Z" fill="#D9DEE2" /></svg>
      <Body size={46} color={C.cream}>Their colonel wore <span style={{color: '#D9DEE2'}}>silver horns</span> in her hair.</Body>
    </Fade>
  </Center>);
};

// S13: the order of march, as Bayol described it
export const S13: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame();
  const blocks: [string, string, number][] = [["THE WOMEN'S REGIMENT", C.gold, cu(cues, 0)], ['PRIESTS', C.teal, cu(cues, 1)], ['ROYAL GUARDS', C.amber, cu(cues, 2)], ['REGULAR TROOPS', '#9C7B4A', cu(cues, 3)]];
  return (<AbsoluteFill>
    <div style={{position: 'absolute', left: 120, top: 150}}><Fade at={4}><H size={66}>THE ORDER OF MARCH</H></Fade></div>
    <svg width={1920} height={1080} style={{position: 'absolute'}}>
      <line x1={60} y1={700} x2={1860} y2={700} stroke={C.line} strokeWidth={5} />
      <g opacity={ease(f, 10, 14)}><path d="M 1650 800 L 1800 800 M 1770 778 L 1800 800 L 1770 822" stroke={C.muted} strokeWidth={5} fill="none" strokeLinecap="round" /><text x={1630} y={812} textAnchor="end" fontFamily="Plex, monospace" fontSize={26} fill={C.muted} letterSpacing={3}>DIRECTION OF MARCH</text></g>
      {blocks.map(([name, col, at], b) => { const p = ease(f, at, 18); const x0 = 1460 - b * 430 - (1 - p) * 200 + Math.sin(f / 9 + b) * 3;
        return (<g key={name} opacity={p}>
          {Array.from({length: 8}).map((_, i) => <Figure key={i} x={x0 + (i % 4) * 78} y={690 - Math.floor(i / 4) * 34} h={b === 0 ? 150 : 130} color={col} opacity={i < 4 ? 0.6 : 1} />)}
          <text x={x0 + 118} y={470} textAnchor="middle" fontFamily="Cinzel, serif" fontWeight={700} fontSize={b === 0 ? 34 : 30} fill={col} letterSpacing={2}>{name}</text>
          <text x={x0 + 118} y={420} textAnchor="middle" fontFamily="Plex, monospace" fontWeight={600} fontSize={26} fill={C.muted}>{['1st', '2nd', '3rd', '4th'][b]}</text>
        </g>); })}
    </svg>
  </AbsoluteFill>);
};

// ---------- the battle map (schematic) ----------
const FORT: [number, number] = [1478, 500], GORE: [number, number] = [1255, 372], CENTRE: [number, number] = [940, 410], TELE: [number, number] = [430, 600];
const Post: React.FC<{p: [number, number]; name: string; sub?: string; dx?: number; dy?: number; anchor?: 'start' | 'end' | 'middle'}> = ({p, name, sub, dx = 26, dy = 10, anchor = 'start'}) => (<g>
  <rect x={p[0] - 13} y={p[1] - 13} width={26} height={26} fill={C.blue} stroke={C.bg} strokeWidth={3} />
  <text x={p[0] + dx} y={p[1] + dy} textAnchor={anchor} fontFamily="Cinzel, serif" fontWeight={700} fontSize={28} fill={C.blue} stroke={C.bg} strokeWidth={6} paintOrder="stroke" letterSpacing={1.5}>{name}</text>
  {sub && <text x={p[0] + dx} y={p[1] + dy + 28} textAnchor={anchor} fontFamily="Plex, monospace" fontWeight={500} fontSize={21} fill={C.text2} stroke={C.bg} strokeWidth={5} paintOrder="stroke">{sub}</text>}
</g>);
export const BattleMap: React.FC<{children?: React.ReactNode; dawn?: number; dim?: number}> = ({children, dawn = 0, dim = 0}) => {
  const f = useCurrentFrame();
  return (<AbsoluteFill style={{background: '#0E0C09'}}>
    <svg width={1920} height={1080} style={{position: 'absolute'}}>
      <defs>
        <marker id="ag" viewBox="0 0 10 10" refX={7} refY={5} markerWidth={5} markerHeight={5} orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill={C.gold} /></marker>
        <marker id="ar" viewBox="0 0 10 10" refX={7} refY={5} markerWidth={5} markerHeight={5} orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#B98A45" /></marker>
        <marker id="ab" viewBox="0 0 10 10" refX={7} refY={5} markerWidth={5} markerHeight={5} orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill={C.blue} /></marker>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill="#15120C" />
      <path d="M 0 790 Q 240 776 480 790 T 960 790 T 1440 790 L 1560 790 L 1560 0 L 1770 0 L 1770 790 L 1920 790 L 1920 1080 L 0 1080 Z" fill="#0B1920" />
      {[0, 1, 2].map((i) => <path key={i} d={`M ${-60 + ((f * 0.5 + i * 90) % 120)} ${850 + i * 62} ${Array.from({length: 18}).map((_, j) => `q 30 -9 60 0 t 60 0`).join(' ')}`} fill="none" stroke="#1C3540" strokeWidth={3} />)}
      {Array.from({length: 190}).map((_, i) => { const top = i < 130; const x = top ? 70 + random('wx' + i) * 1440 : 70 + random('wx' + i) * 250; const y = top ? 110 + random('wy' + i) * 200 : 330 + random('wy' + i) * 420;
        return <circle key={i} cx={x} cy={y} r={11 + random('wr' + i) * 12} fill="#1A2418" />; })}
      <text x={520} y={250} fontFamily="Plex, monospace" fontWeight={600} fontSize={26} fill="#5E7758" letterSpacing={10}>WOODS</text>
      <text x={150} y={470} fontFamily="Plex, monospace" fontWeight={600} fontSize={24} fill="#5E7758" letterSpacing={6}>WOODS</text>
      <text x={1665} y={330} fontFamily="Plex, monospace" fontWeight={600} fontSize={24} fill="#4B7384" letterSpacing={6} transform="rotate(90 1665 330)">LAGOON CHANNEL</text>
      <text x={110} y={900} fontFamily="Plex, monospace" fontWeight={600} fontSize={24} fill="#4B7384" letterSpacing={8}>ATLANTIC OCEAN</text>
      <path d="M 430 772 L 430 500 Q 430 410 560 410 L 1380 410 Q 1470 410 1480 520 L 1490 772" fill="rgba(134,174,224,0.06)" stroke={C.blue} strokeWidth={6} strokeDasharray="2 12" strokeLinecap="round" />
      {[[850, 640], [930, 660]].map(([x, y], i) => <rect key={i} x={x} y={y} width={56} height={36} fill="#3A3024" stroke={C.text2} strokeWidth={2} />)}
      <text x={1000} y={672} fontFamily="Plex, monospace" fontWeight={500} fontSize={21} fill={C.text2}>the factories (Régis, Fabre)</text>
      <Post p={TELE} name="TELEGRAPH" dx={28} />
      <Post p={CENTRE} name="CENTRE" sub="Oudard's section" dx={-10} dy={52} anchor="middle" />
      <Post p={GORE} name="LA GORE" sub="‘the Agor’" dx={-26} dy={-24} anchor="end" />
      <Post p={FORT} name="FORTIN COMPÉRAT" sub="half-built, on the lagoon" dx={-30} dy={56} anchor="end" />
      <g transform="translate(1000 880)"><path d="M -90 0 L 90 0 L 66 26 L -66 26 Z" fill={C.blue} /><rect x={-10} y={-34} width={20} height={34} fill={C.blue} /><line x1={-50} y1={-12} x2={50} y2={-12} stroke={C.blue} strokeWidth={5} />
        <text x={110} y={22} fontFamily="Cinzel, serif" fontWeight={700} fontSize={26} fill={C.blue} letterSpacing={2}>CRUISER SANÉ</text></g>
      <g transform="translate(1846 960)"><path d="M 0 -44 L 13 0 L 0 -10 L -13 0 Z" fill={C.text2} /><text x={0} y={30} textAnchor="middle" fontFamily="Cinzel, serif" fontWeight={700} fontSize={24} fill={C.text2}>N</text></g>
      <rect x={0} y={0} width={1920} height={1080} fill="#F3B56A" opacity={dawn * 0.055} />
      {children}
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} opacity={dim} />
    </svg>
  </AbsoluteFill>);
};
const LEFT_COL = 'M 1330 120 Q 1300 300 1452 478', RIGHT_COL = 'M 240 170 Q 250 380 400 560';
const ColLabel: React.FC<{x: number; y: number; t: string; s?: string; color?: string; at: number}> = ({x, y, t, s, color = C.gold, at}) => { const f = useCurrentFrame(); return (<g opacity={ease(f, at, 12)}>
  <text x={x} y={y} fontFamily="Cinzel, serif" fontWeight={900} fontSize={32} fill={color} stroke={C.bg} strokeWidth={7} paintOrder="stroke" letterSpacing={2}>{t}</text>
  {s && <text x={x} y={y + 30} fontFamily="Plex, monospace" fontWeight={600} fontSize={22} fill={C.cream} stroke={C.bg} strokeWidth={6} paintOrder="stroke">{s}</text>}</g>); };
const Ring: React.FC<{p: [number, number]; at: number; color?: string}> = ({p, at, color = C.red}) => { const f = useCurrentFrame(); if (f < at) return null; const t = (f - at) % 30;
  return <circle cx={p[0]} cy={p[1]} r={22 + t * 2.4} fill="none" stroke={color} strokeWidth={6} opacity={1 - t / 30} />; };

export const S14: React.FC<P> = ({cues}) => { const c0 = cu(cues, 0); return (<BattleMap>
  <Draw d={LEFT_COL} at={c0} dur={40} w={12} marker="url(#ag)" /><Draw d={RIGHT_COL} at={c0 + 6} dur={40} w={12} color="#B98A45" marker="url(#ar)" />
  <ColLabel x={1020} y={150} t="LEFT COLUMN" at={c0 + 10} /><ColLabel x={290} y={150} t="RIGHT COLUMN" color="#C9A064" at={c0 + 16} />
</BattleMap>); };
export const S15: React.FC<P> = ({cues}) => { const c0 = cu(cues, 0); return (<BattleMap>
  <Draw d={RIGHT_COL} at={-50} w={12} color="#B98A45" opacity={0.35} />
  <Draw d={LEFT_COL} at={-50} w={14} marker="url(#ag)" /><Ring p={FORT} at={c0} />
  <ColLabel x={900} y={150} t="LEFT COLUMN" s="the women's regiment + perhaps 1,000 men" at={2} />
</BattleMap>); };
export const S16: React.FC<P> = ({cues}) => { const f = useCurrentFrame(); const c0 = cu(cues, 0); return (<BattleMap>
  <Draw d={LEFT_COL} at={-50} w={12} marker="url(#ag)" opacity={0.5} />
  <Draw d={RIGHT_COL} at={2} w={12} color="#C9A064" dash="18 20" />
  <ColLabel x={290} y={150} t="RIGHT COLUMN" s="delayed in the telegraph woods" color="#C9A064" at={6} />
  <g opacity={ease(f, c0, 12)}><rect x={640} y={300} width={600} height={74} rx={10} fill="rgba(11,9,7,0.85)" stroke={C.cream} strokeWidth={2} />
    <text x={940} y={350} textAnchor="middle" fontFamily="Cinzel, serif" fontWeight={700} fontSize={32} fill={C.cream} letterSpacing={2}>NOTHING CAME AT THE CENTRE</text></g>
</BattleMap>); };
export const S17: React.FC<P> = ({cues}) => { const c0 = cu(cues, 0); return (<AbsoluteFill>
  <BattleMap dim={0.82}><Draw d={LEFT_COL} at={-50} w={12} marker="url(#ag)" /><Draw d={RIGHT_COL} at={-50} w={12} color="#C9A064" dash="18 20" /></BattleMap>
  <Center><Fade at={4}><H size={104} style={{textAlign: 'center'}}>SEVERAL THOUSAND<br />ATTACKERS?</H></Fade>
    <div style={{marginTop: 40}}><Stamp at={c0} text="No reliable count exists" size={58} /></div></Center>
</AbsoluteFill>); };

// S18: the eyewitness who disagrees
export const S18: React.FC<P> = ({cues}) => {
  const lines = ['The corps of women soldiers was not engaged that day.', 'A few took part of their own accord.', 'The rest watched from a short distance.'];
  return (<AbsoluteFill style={{padding: '150px 140px'}}>
    <Fade at={3}><Stamp at={3} text="One eyewitness disagrees" color={C.amber} size={44} rot={-2} /></Fade>
    <Fade at={cu(cues, 0)} style={{marginTop: 44, display: 'flex', alignItems: 'baseline', gap: 28}}><H size={96} color={C.gold}>FOÀ</H><Body size={44}>a trader who was there</Body></Fade>
    <div style={{marginTop: 36, borderLeft: `6px solid ${C.gold}`, paddingLeft: 40}}>
      {lines.map((l, i) => <Fade key={i} at={cu(cues, i + 1)} dx={-30} dy={0} style={{fontFamily: SERIF, fontWeight: 600, fontSize: 60, color: C.cream, lineHeight: 1.25, marginBottom: 26}}>{l}</Fade>)}
    </div>
  </AbsoluteFill>);
};

// S19: two accounts against one. No verdict by headcount.
export const S19: React.FC<P> = ({cues, len}) => {
  const c0 = cu(cues, 0);
  const Card: React.FC<{at: number; who: string; role: string}> = ({at, who, role}) => (<Pop at={at} from={0.8} style={{background: 'rgba(25,19,12,0.95)', border: `2px solid ${C.goldDim}`, borderRadius: 16, padding: '22px 34px', textAlign: 'center', minWidth: 300}}><H size={48} color={C.gold}>{who}</H><Label size={22} color={C.text2}>{role}</Label></Pop>);
  return (<AbsoluteFill style={{padding: '150px 110px'}}>
    <div style={{display: 'flex', gap: 60}}>
      <div style={{flex: 1.25}}>
        <div style={{display: 'flex', gap: 26}}><Card at={4} who="BAYOL" role="governor" /><Card at={10} who="NICOLAS" role="French account" /></div>
        <Fade at={16} style={{marginTop: 30}}><Body size={52} color={C.cream}>The women were at the <span style={{color: C.gold}}>head of the column</span>.</Body></Fade>
      </div>
      <div style={{width: 3, background: C.line}} />
      <div style={{flex: 1}}>
        <div style={{display: 'flex'}}><Card at={c0} who="FOÀ" role="trader · present" /></div>
        <Fade at={c0 + 8} style={{marginTop: 30}}><Body size={52} color={C.cream}>Most of them <span style={{color: C.amber}}>watched</span>.</Body></Fade>
      </div>
    </div>
    <Fade at={Math.min(c0 + 40, len - 70)} style={{marginTop: 70, textAlign: 'center'}}>
      <H size={64}>THE ACCOUNTS DISAGREE</H>
      <Body size={42} style={{marginTop: 10}}>Women were among the dead. Their exact role that morning is disputed.</Body>
    </Fade>
  </AbsoluteFill>);
};

// S20: the stockade
export const S20: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1); const gaps = [9, 10, 22, 23, 35, 36];
  return (<AbsoluteFill style={{background: night}}>
    <Rain n={50} opacity={0.25} />
    {f > c0 && gaps.filter((_, i) => i % 2 === 0).map((g, i) => random(`mz${i}-${Math.floor(f / 3)}`) > 0.55 ? <div key={i} style={{position: 'absolute', left: g * 40 - 10, top: 560 + random('mzy' + i + Math.floor(f / 3)) * 160, width: 90, height: 90, borderRadius: 90, background: 'radial-gradient(circle, #FFE9B0 0%, rgba(231,154,60,0.7) 35%, transparent 70%)'}} /> : null)}
    <Palisade y={1090} h={640} gaps={gaps} gapP={ease(f, 10, 50)} color="#15100A" />
    <div style={{position: 'absolute', left: 120, top: 150}}>
      <Fade at={4}><H size={64}>THE STAKES PULLED APART</H></Fade>
      <Fade at={c0}><Body size={44} style={{marginTop: 8}}>They fired through the gaps.</Body></Fade>
    </div>
    <Fade at={c1 + 30} style={{position: 'absolute', left: 120, top: 330}}><Chip color={C.cream} style={{fontSize: 34, padding: '14px 26px'}}>SOME GOT THROUGH THE STOCKADE. THE LINE HELD.</Chip></Fade>
  </AbsoluteFill>);
};

// S21: Compérat
export const S21: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2), c3 = cu(cues, 3);
  return (<AbsoluteFill style={{padding: '150px 130px'}}>
    <div style={{display: 'flex', alignItems: 'center', gap: 50}}>
      <svg width={300} height={300}><circle cx={150} cy={150} r={120} fill="none" stroke={C.blue} strokeWidth={5} /><Figure x={150} y={250} h={190} color={C.blue} gun={false} />
        {[[105, 120, 4], [190, 170, 14], [130, 200, c0]].map(([x, y, at], i) => <g key={i} opacity={lin(f, at, at + 4)}><circle cx={x} cy={y} r={15} fill={C.red} /><circle cx={x} cy={y} r={15 + Math.max(0, f - at) * 1.2} fill="none" stroke={C.red} strokeWidth={3} opacity={Math.max(0, 1 - (f - at) / 20)} /></g>)}</svg>
      <div><Fade at={3}><H size={84} color={C.blue}>LT COMPÉRAT</H></Fade><Fade at={8}><H size={58}>HIT THREE TIMES</H></Fade>
        <Fade at={c0}><Body size={40} style={{marginTop: 8}}>One bullet broke his shoulder blade.</Body></Fade>
        <Fade at={c1}><Body size={40} color={C.cream}>He stayed in command.</Body></Fade></div>
    </div>
    <div style={{marginTop: 50, borderLeft: `6px solid ${C.gold}`, paddingLeft: 40, fontFamily: SERIF, fontStyle: 'italic', fontWeight: 400, fontSize: 76, color: C.cream, lineHeight: 1.2, minHeight: 200}}>
      <Typed text={'“Stay at your post.'} at={c2} cps={22} /><br /><Typed text={'I am wounded too, and I am not complaining.”'} at={c3} cps={24} />
    </div>
  </AbsoluteFill>);
};

// S22: the Agor post and the counter-charge
export const S22: React.FC<P> = ({cues}) => { const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1); return (<BattleMap>
  <Draw d={LEFT_COL} at={-50} w={12} marker="url(#ag)" opacity={0.6} />
  <Ring p={GORE} at={4} color={C.amber} />
  <g opacity={lin(f, 8, 20)}><rect x={1290} y={300} width={250} height={48} rx={8} fill="rgba(11,9,7,0.85)" stroke={C.amber} strokeWidth={2} /><text x={1415} y={333} textAnchor="middle" fontFamily="Plex, monospace" fontWeight={600} fontSize={22} fill={C.amber}>BRIEFLY ABANDONED</text></g>
  <Draw d="M 1060 640 Q 1130 520 1210 420" at={c0} dur={26} w={12} color={C.blue} marker="url(#ab)" />
  <ColLabel x={700} y={560} t="2ND COMPANY" s="fired at ten paces" color={C.blue} at={c0 + 6} />
  <Draw d="M 1225 400 L 1290 250" at={c1} dur={12} w={12} color={C.blue} marker="url(#ab)" />
  <ColLabel x={1000} y={250} t="BAYONET CHARGE" color={C.blue} at={c1 + 4} />
</BattleMap>); };

// S23: the men who lay flat (side-view diagram)
export const S23: React.FC<P> = ({cues, len}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1); const adv = lin(f, 0, c0 + 10) * 760; const up = ease(f, c0, 14); const turn = ease(f, c1, 14);
  return (<AbsoluteFill style={{background: night}}>
    <svg width={1920} height={1080} style={{position: 'absolute'}}>
      <line x1={0} y1={720} x2={1920} y2={720} stroke={C.line} strokeWidth={5} />
      {Array.from({length: 6}).map((_, i) => <g key={i} opacity={1 - turn * 0.8}><Figure x={700 + i * 80} y={720} h={150} color={C.gold} lean={-88 * (1 - up)} gun={up > 0.6} />
        {up > 0.9 && turn < 0.3 && random(`lf${i}-${Math.floor(f / 4)}`) > 0.6 && <circle cx={760 + i * 80} cy={560} r={20} fill="#FFE9B0" />}</g>)}
      {Array.from({length: 9}).map((_, i) => { const rear = i < 3; const x = 300 + i * 85 + adv - (rear ? turn * 330 : 0);
        return <g key={i} transform={rear && turn > 0.5 ? `translate(${2 * x} 0) scale(-1 1)` : undefined}><Figure x={x} y={720} h={160} color={C.blue} /></g>; })}
    </svg>
    <div style={{position: 'absolute', left: 120, top: 160}}>
      <Fade at={4}><H size={60}>SOME LAY FLAT AND LET THE CHARGE PASS</H></Fade>
      <Fade at={c0}><Body size={46} color={C.gold} style={{marginTop: 10}}>Then they rose, and fired into the tirailleurs' backs.</Body></Fade>
      <Fade at={c1}><Body size={46} color={C.blue} style={{marginTop: 6}}>One section turned about.</Body></Fade>
    </div>
  </AbsoluteFill>);
};

// S24: naval gunfire
const Shell: React.FC<{to: [number, number]; at: number}> = ({to, at}) => { const f = useCurrentFrame(); const d = `M 1000 850 Q ${(1000 + to[0]) / 2} ${to[1] - 260} ${to[0]} ${to[1]}`;
  return (<g><Draw d={d} at={at} dur={16} w={5} color={C.cream} opacity={lin(f, at + 30, at + 50, 1, 0.25)} />{f > at + 15 && <circle cx={to[0]} cy={to[1]} r={10 + (f - at - 15) * 3} fill="none" stroke={C.amber} strokeWidth={7} opacity={Math.max(0, 1 - (f - at - 15) / 26)} />}</g>); };
export const S24: React.FC<P> = ({cues}) => { const c0 = cu(cues, 0); return (<BattleMap>
  <Draw d={LEFT_COL} at={-50} w={12} marker="url(#ag)" opacity={0.5} />
  <Shell to={[1130, 200]} at={c0} /><Shell to={[760, 240]} at={c0 + 12} /><Shell to={[230, 420]} at={c0 + 24} /><Shell to={[1390, 180]} at={c0 + 36} />
  <ColLabel x={1110} y={846} t="SHELLING THE WOODS" color={C.cream} at={c0} />
</BattleMap>); };

// S25: first light
export const S25: React.FC<P> = ({cues}) => { const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2); return (<BattleMap dawn={lin(f, 0, c1 + 60)}>
  <Draw d={LEFT_COL} at={-50} w={12} marker="url(#ag)" opacity={0.6} />
  <Draw d="M 1130 720 Q 1400 720 1466 566" at={c0 - 24} dur={24} w={12} color={C.blue} marker="url(#ab)" />
  <ColLabel x={640} y={736} t="4TH COMPANY SECTION" s="bayonets fixed: hand to hand at the fort" color={C.blue} at={c0 - 10} /><Ring p={FORT} at={c0} />
  {[0, 1, 2, 3, 4].map((i) => <Draw key={i} d={`M 960 396 L ${1180 + i * 50} ${250 - i * 12}`} at={c1 + i * 3} dur={8} w={4} color={C.cream} dash="10 12" />)}
  <ColLabel x={560} y={330} t="OBLIQUE FIRE FROM THE CENTRE" color={C.cream} at={c1 + 6} />
  <Draw d="M 560 560 Q 440 480 330 380" at={c2 - 20} dur={22} w={12} color={C.blue} marker="url(#ab)" />
  <ColLabel x={110} y={360} t="ROUT ON THE RIGHT" color={C.blue} at={c2 - 8} />
  <text x={1840} y={150} textAnchor="end" fontFamily="Plex, monospace" fontWeight={600} fontSize={28} fill={C.gold} letterSpacing={3} opacity={ease(f, 6, 14)}>FIRST LIGHT</text>
</BattleMap>); };

// S26: the clock of the battle
export const S26: React.FC<P> = ({cues, len}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2), c3 = cu(cues, 3);
  const X = (h: number) => 210 + ((h - 5) / 4.5) * 1500; const Y = 560;
  const prog = interpolate(f, [0, c0, c1, c2, c2 + 30], [5, 6.25, 7, 9, 9.5], clamp);
  const Tick: React.FC<{h: number; t: string; a: string; b?: string; at: number; up?: boolean}> = ({h, t, a, b, at, up}) => (<g opacity={ease(f, at, 12)}>
    <line x1={X(h)} y1={Y - 26} x2={X(h)} y2={Y + 26} stroke={C.cream} strokeWidth={5} />
    <text x={X(h)} y={up ? Y - 150 : Y + 90} textAnchor="middle" fontFamily="Cinzel, serif" fontWeight={900} fontSize={48} fill={C.gold}>{t}</text>
    <text x={X(h)} y={up ? Y - 104 : Y + 134} textAnchor="middle" fontFamily="Plex, monospace" fontWeight={600} fontSize={24} fill={C.cream} letterSpacing={1}>{a}</text>
    {b && <text x={X(h)} y={up ? Y - 72 : Y + 166} textAnchor="middle" fontFamily="Plex, monospace" fontWeight={500} fontSize={22} fill={C.text2}>{b}</text>}</g>);
  return (<AbsoluteFill>
    <div style={{position: 'absolute', left: 120, top: 140}}><Fade at={3}><H size={62}>THE MORNING OF 4 MARCH</H></Fade></div>
    <svg width={1920} height={1080} style={{position: 'absolute'}}>
      <line x1={X(5)} y1={Y} x2={X(9.5)} y2={Y} stroke={C.line} strokeWidth={14} strokeLinecap="round" />
      <line x1={X(5)} y1={Y} x2={X(prog)} y2={Y} stroke={C.gold} strokeWidth={14} strokeLinecap="round" />
      {f > c1 && Array.from({length: 9}).map((_, i) => { const hx = 6.4 + i * 0.3; return hx < prog ? <circle key={i} cx={X(hx)} cy={Y - 44 - (i % 2) * 20} r={8 + ((f + i * 7) % 20) * 0.5} fill="none" stroke={C.amber} strokeWidth={4} opacity={0.8 - ((f + i * 7) % 20) / 30} /> : null; })}
      <Tick h={5} t="c. 5:00" a="FIRST ASSAULT" at={4} />
      <Tick h={6.25} t="6:15" a="SECOND ATTACK" b="stopped at 200 m" at={c0 - 10} up />
      <Tick h={7.4} t="AGAIN AND AGAIN" a="THEY RE-FORMED" b="the Sané + a three-gun battery" at={c1} />
      <Tick h={9.15} t="c. 9:00" a="LAST ATTACKERS LEAVE" at={c2} up />
      <g opacity={ease(f, c3, 14)}><path d={`M ${X(5)} ${Y + 230} L ${X(5)} ${Y + 256} L ${X(9.5)} ${Y + 256} L ${X(9.5)} ${Y + 230}`} fill="none" stroke={C.cream} strokeWidth={4} />
        <text x={960} y={Y + 326} textAnchor="middle" fontFamily="Cinzel, serif" fontWeight={900} fontSize={66} fill={C.cream} letterSpacing={3}>ABOUT 4½ HOURS</text></g>
    </svg>
  </AbsoluteFill>);
};

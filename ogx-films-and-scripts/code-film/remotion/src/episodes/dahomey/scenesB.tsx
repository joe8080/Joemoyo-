// Dahomey / Cotonou 1890, part B: the cost, the evidence, the aftermath (S27-S50).
import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {C, DISPLAY, SERIF, MONO, Fade, Pop, Count, Typed, Draw, Stamp, H, Body, Label, Center, Rule, GeoMap, Pin, PT, Figure, ease, lin, cu, usePop} from '../../kit';
import {P, Training} from './scenesA';

const Chip: React.FC<{children: React.ReactNode; color?: string; style?: React.CSSProperties}> = ({children, color = C.gold, style}) => (
  <span style={{fontFamily: MONO, fontWeight: 600, fontSize: 26, letterSpacing: 2.5, color, border: `2px solid ${color}`, borderRadius: 8, padding: '8px 18px', background: 'rgba(11,9,7,0.7)', display: 'inline-block', whiteSpace: 'nowrap', ...style}}>{children}</span>);
const Pad: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => <AbsoluteFill style={{padding: '150px 130px', ...style}}>{children}</AbsoluteFill>;
const Big: React.FC<{n: number; at: number; color?: string; size?: number}> = ({n, at, color = C.gold, size = 190}) => <Count to={n} at={at} dur={28} style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: size, color, lineHeight: 1}} />;

// S27: the count
export const S27: React.FC<P> = ({cues}) => {
  const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2), c3 = cu(cues, 3);
  return (<Pad>
    <div style={{display: 'flex', gap: 70}}>
      <div style={{flex: 1}}>
        <Fade at={3}><Label color={C.blue}>The French side</Label></Fade>
        <Fade at={6} style={{display: 'flex', alignItems: 'baseline', gap: 24, marginTop: 10}}><Big n={8} at={6} color={C.blue} /><div><H size={56}>KILLED</H><Body size={34}>two of them gunners, hit at their guns</Body></div></Fade>
        <Fade at={c0} style={{display: 'flex', alignItems: 'baseline', gap: 24, marginTop: 24}}><Big n={26} at={c0} color={C.blue} /><H size={56}>WOUNDED</H></Fade>
      </div>
      <div style={{width: 3, background: C.line}} />
      <div style={{flex: 1.15}}>
        <Fade at={c1 - 6}><Label>The Dahomean dead, inside the lines</Label></Fade>
        <Fade at={c1} style={{display: 'flex', alignItems: 'baseline', gap: 24, marginTop: 10}}><Big n={127} at={c1} /><H size={56}>COUNTED</H></Fade>
        <Fade at={c2} style={{display: 'flex', alignItems: 'baseline', gap: 24, marginTop: 24}}><Big n={7} at={c2} color={C.cream} /><H size={56}>WERE WOMEN</H></Fade>
      </div>
    </div>
    <Fade at={c3} style={{marginTop: 46, textAlign: 'center'}}><Chip color={C.amber} style={{fontSize: 30}}>ANOTHER COUNT DIFFERS · THE PRIMARY ACCOUNT GIVES 127</Chip></Fade>
  </Pad>);
};

// S28-S30: "Nanisca": one governor's identification
export const S28: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1); const k = 0.2;
  return (<AbsoluteFill>
    <GeoMap cx={PT.cotonou[0] - 240 * k} cy={(PT.cotonou[1] + PT.abomey[1]) / 2} k={k}>
      <Draw d={`M ${PT.abomey[0]} ${PT.abomey[1]} Q ${PT.abomey[0] + 40} ${PT.abomey[1] + 50} ${PT.cotonou[0]} ${PT.cotonou[1]}`} at={c0} dur={50} w={5 * k} dash={`${10 * k} ${12 * k}`} color={C.gold} />
      <Pin p={PT.abomey} k={k} text="ABOMEY" sub="where Bayol first saw her" at={6} color={C.cream} size={34} />
      <Pin p={PT.cotonou} k={k} text="COTONOU" sub="4 March 1890" at={c0 + 30} color={C.gold} size={34} pulse />
    </GeoMap>
    <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(11,9,7,0.94) 0%, rgba(11,9,7,0.8) 42%, transparent 70%)'}} />
    <div style={{position: 'absolute', left: 120, top: 190, width: 880}}>
      <Fade at={3}><Chip color={C.amber}>ACCORDING TO GOVERNOR BAYOL</Chip></Fade>
      <Fade at={c0}><Body size={50} color={C.cream} style={{marginTop: 34}}>A young woman soldier he had watched in Abomey was at Cotonou.</Body></Fade>
      <Fade at={c1} style={{marginTop: 40}}><Label size={26} color={C.text2}>He had called her</Label><div style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 150, color: C.gold, lineHeight: 1.1}}>“Nanisca”</div></Fade>
    </div>
  </AbsoluteFill>);
};
export const S29: React.FC<P> = ({cues}) => {
  const c0 = cu(cues, 0), c1 = cu(cues, 1);
  return (<Pad>
    <Fade at={3}><Chip color={C.amber}>BAYOL'S ACCOUNT, CONTINUED</Chip></Fade>
    <Fade at={10}><Body size={54} color={C.cream} style={{marginTop: 34, maxWidth: 1500}}>He says his chief gunner was killed by a fighter he recognised as her.</Body></Fade>
    <Fade at={c0}><Body size={54} color={C.cream} style={{marginTop: 20}}>Later, he says, he found her body.</Body></Fade>
    <div style={{display: 'flex', gap: 60, marginTop: 50}}>
      <Fade at={c0 + 20} style={{display: 'flex', alignItems: 'center', gap: 24}}><svg width={200} height={120}><path d="M 20 100 Q 110 96 180 16 Q 160 96 44 114 Z" fill={C.cream} /><rect x={8} y={96} width={40} height={16} rx={5} fill={C.goldDim} /></svg><Body size={40}>a curved cleaver,<br />tied to her wrist</Body></Fade>
      <Fade at={c1} style={{display: 'flex', alignItems: 'center', gap: 24}}><svg width={240} height={120}><path d="M 10 92 L 50 70 L 230 34 L 233 44 L 62 84 L 40 110 Z" fill={C.gold} />{[0, 1, 2, 3, 4].map((i) => <ellipse key={i} cx={84 + i * 30} cy={66 - i * 6} rx={9} ry={6} fill={C.cream} />)}</svg><Body size={40}>a carbine,<br />covered in cowries</Body></Fade>
    </div>
  </Pad>);
};
export const S30: React.FC<P> = ({cues}) => {
  const c0 = cu(cues, 0), c1 = cu(cues, 1);
  const Card: React.FC<{at: number; head: string; body: React.ReactNode; color: string}> = ({at, head, body, color}) => (<Pop at={at} from={0.85} style={{flex: 1, background: 'rgba(25,19,12,0.95)', border: `2px solid ${color}`, borderRadius: 18, padding: '34px 40px'}}><Label color={color}>{head}</Label><Body size={46} color={C.cream} style={{marginTop: 16}}>{body}</Body></Pop>);
  return (<Pad>
    <div style={{display: 'flex', gap: 50, marginTop: 30}}>
      <Card at={4} head="Another French account" color={C.text2} body={<>A woman soldier killed the gunner.<br /><span style={{color: C.amber, opacity: 1}}>{' '}</span><Fade at={c0} style={{display: 'inline-block', color: C.amber}}>She is not named.</Fade></>} />
      <Card at={10} head="Governor Bayol" color={C.amber} body={<>It was the woman he called “Nanisca”.</>} />
    </div>
    <div style={{marginTop: 70, textAlign: 'center'}}><Stamp at={c1} text="The identification is Bayol's alone" color={C.amber} size={56} rot={-3} /></div>
  </Pad>);
};

// S31: Porto-Novo
export const S31: React.FC<P> = ({cues}) => {
  const c0 = cu(cues, 0); const k = 0.075;
  return (<AbsoluteFill>
    <GeoMap cx={(PT.cotonou[0] + PT.portonovo[0]) / 2 + 10 * k} cy={(PT.cotonou[1] + PT.portonovo[1]) / 2 - 60 * k} k={k}>
      <Draw d={`M ${PT.cotonou[0]} ${PT.cotonou[1]} Q ${PT.cotonou[0] + 8} ${PT.portonovo[1] - 6} ${PT.portonovo[0]} ${PT.portonovo[1]}`} at={c0} dur={40} w={6 * k} dash={`${12 * k} ${14 * k}`} color={C.amber} />
      <Pin p={PT.cotonou} k={k} text="COTONOU" at={4} color={C.gold} size={40} dx={-250} dy={14} />
      <Pin p={PT.portonovo} k={k} text="PORTO-NOVO" sub="French-allied kingdom" at={c0 + 24} color={C.cream} size={40} pulse />
    </GeoMap>
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 40%, rgba(11,9,7,0.8) 100%)'}} />
    <div style={{position: 'absolute', left: 120, top: 150}}><Fade at={4}><H size={64}>AFTER THE FIGHTING</H></Fade>
      <Fade at={c0}><Body size={42} color={C.cream} style={{marginTop: 10, maxWidth: 1100}}>The heads of the dead were sent, in sealed sacks, to the king of Porto-Novo.</Body></Fade></div>
  </AbsoluteFill>);
};

// S32: the survivors Foà records
export const S32: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2); const gone = ease(f, c2, 30);
  return (<Pad>
    <Fade at={3} style={{display: 'flex', alignItems: 'baseline', gap: 26}}><H size={84} color={C.gold}>FOÀ</H><Body size={42}>a trader who was present, records:</Body></Fade>
    <svg width={900} height={330} style={{marginTop: 30}}>{[0, 1, 2].map((i) => <Figure key={i} x={170 + i * 250} y={310} h={i === 2 ? 190 : 250} color={C.gold} gun={false} opacity={lin(f, c0 + i * 6, c0 + i * 6 + 10) * (1 - gone * 0.85)} />)}</svg>
    <Fade at={c0}><Body size={54} color={C.cream}>Two or three women were found alive on the field.</Body></Fade>
    <Fade at={c1}><Body size={54} color={C.cream} style={{marginTop: 12}}>One was very young, and gravely wounded.</Body></Fade>
    <Fade at={c2}><H size={72} color={C.red} style={{marginTop: 26}}>NONE SURVIVED.</H></Fade>
  </Pad>);
};

// section cards (S33, S36)
export const Section: React.FC<{lines: React.ReactNode; kicker?: string; at?: number}> = ({lines, kicker, at = 6}) => (<Center>
  {kicker && <Fade at={2}><Label size={30}>{kicker}</Label></Fade>}
  <Fade at={at}><div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 104, color: C.cream, textAlign: 'center', lineHeight: 1.14, marginTop: 20, maxWidth: 1600}}>{lines}</div></Fade>
  <Rule at={at + 12} w={500} />
</Center>);
export const S33: React.FC<P> = () => <Section kicker="Before the battle" lines={<>Who were these women?<br /><span style={{color: C.gold}}>What had prepared them?</span></>} />;
export const S36: React.FC<P> = ({cues}) => <Section kicker="The pictures" lines={<>The images we often see<br />are <span style={{color: C.red}}>not the battle.</span></>} />;

// S34: strength over time (estimates)
export const S34: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2);
  const bars: [string, string, number, number, string][] = [['1760s–1840s', 'about 600', 600, c0, C.goldDim], ['Under King Gezo', 'as many as 6,000', 6000, c1, C.gold], ['Late 1870s', 'perhaps 1,500', 1500, c2, C.goldDim]];
  return (<Pad>
    <Fade at={3}><H size={62}>A STANDING ARMY OF WOMEN</H></Fade>
    <Fade at={8}><Body size={38} style={{marginTop: 6}}>Probably formed as a palace guard in the 1720s</Body></Fade>
    <div style={{display: 'flex', alignItems: 'flex-end', gap: 90, height: 560, marginTop: 30, paddingLeft: 60}}>
      {bars.map(([when, lab, n, at, col]) => { const p = ease(f, at, 26); return (<div key={when} style={{textAlign: 'center', width: 420, opacity: lin(f, at - 4, at + 6)}}>
        <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 50, color: C.cream, whiteSpace: 'nowrap'}}>{lab}</div>
        <div style={{height: (n / 6000) * 300 * p + 6, background: col, borderRadius: '10px 10px 0 0', margin: '14px 60px 0'}} />
        <div style={{borderTop: `3px solid ${C.line}`, paddingTop: 14}}><Label size={28} color={C.text2}>{when}</Label></div></div>); })}
    </div>
  </Pad>);
};

// S35: an institution, not a legend
export const S35: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2), c3 = cu(cues, 3); const sw = ease(f, c0 - 8, 14);
  const Struck: React.FC<{t: string; at: number}> = ({t, at}) => (<Fade at={at} style={{position: 'relative', display: 'inline-block', marginRight: 50}}><H size={58} color={C.muted}>{t}</H><div style={{position: 'absolute', left: -6, top: '52%', height: 6, width: `${ease(f, at + 14, 12) * 104}%`, background: C.red}} /></Fade>);
  const Node: React.FC<{t: string; at: number}> = ({t, at}) => (<Pop at={at} from={0.8} style={{border: `3px solid ${C.gold}`, borderRadius: 14, padding: '20px 30px', background: 'rgba(25,19,12,0.95)'}}><H size={38} color={C.gold} style={{whiteSpace: 'nowrap'}}>{t}</H></Pop>);
  return (<AbsoluteFill>
    <Center style={{opacity: 1 - sw, transform: `translateY(${-sw * 40}px)`}}><Fade at={2} style={{marginBottom: 40}}><H size={64}>UP TO NINE DAYS IN THE FIELD</H></Fade><Training cues={[4, 12, 20]} days="of up to nine days" /></Center>
    <Center style={{opacity: sw}}>
      <div><Struck t="A NEWSPAPER LEGEND" at={c0} /><Struck t="A FILM INVENTION" at={c0 + 10} /></div>
      <Fade at={c1}><H size={110} color={C.cream} style={{marginTop: 46, fontWeight: 900}}>A REAL INSTITUTION</H></Fade>
      <div style={{display: 'flex', gap: 34, marginTop: 44, alignItems: 'center'}}><Node t="A STRUCTURE" at={c1 + 18} /><Node t="A CHAIN OF COMMAND" at={c2} /><Node t="A LONG HISTORY: 1720s → 1890s" at={c3} /></div>
    </Center>
  </AbsoluteFill>);
};

// S37-S40: catalogue cards. We describe the pictures; we do not pass them off as the battle.
const Cat: React.FC<{at?: number; kind: string; title: string; rows: [string, string][]; children?: React.ReactNode}> = ({at = 4, kind, title, rows, children}) => (
  <Pad><Fade at={at} style={{background: C.paper, borderRadius: 10, padding: '44px 56px 150px', width: 1500, margin: '10px auto 0', boxShadow: '0 30px 80px rgba(0,0,0,0.6)', position: 'relative'}}>
    <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 24, letterSpacing: 4, color: '#7A6233'}}>{kind}</div>
    <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 66, color: C.ink, lineHeight: 1.12, margin: '10px 0 22px', borderBottom: '3px solid #B9A77F', paddingBottom: 20}}>{title}</div>
    {rows.map(([a, b], i) => <Fade key={a} at={at + 10 + i * 7} dy={10} style={{display: 'flex', gap: 30, marginBottom: 12}}><span style={{fontFamily: MONO, fontWeight: 600, fontSize: 26, color: '#7A6233', width: 300, letterSpacing: 2, paddingTop: 8}}>{a}</span><span style={{fontFamily: SERIF, fontWeight: 600, fontSize: 42, color: C.ink, flex: 1, lineHeight: 1.25}}>{b}</span></Fade>)}
    {children}
  </Fade></Pad>);
export const S37: React.FC<P> = ({cues}) => (<Cat kind="ILLUSTRATION · CATALOGUE NOTE" title="“Seh-Dong-Hong-Beh, an Amazon in the Dahoman Army”" rows={[['DRAWN BY', 'Frederick E. Forbes'], ['PUBLISHED', '1851: thirty-nine years before Cotonou'], ['MEDIUM', 'Chromolithograph, not a photograph'], ['THE FULL PLATE', 'She holds a severed head. Not shown here.']]}>
  <div style={{position: 'absolute', left: 386, bottom: 34, display: 'flex', gap: 50, alignItems: 'center'}}><Stamp at={cu(cues, 1)} text="Not a photograph" size={46} rot={-3} style={{background: "rgba(204,74,50,0.07)"}} /><Stamp at={cu(cues, 2)} text="Not 1890" size={56} rot={3} style={{background: "rgba(204,74,50,0.07)"}} /></div></Cat>);
export const S38: React.FC<P> = ({cues}) => (<Cat kind="POSTCARD · CATALOGUE NOTE" title="“Les survivantes des Amazones de Béhanzin”" rows={[['PHOTOGRAPHER', 'François-Edmond Fortier'], ['DATE', 'Early 1900s'], ['CAPTIONED AS', 'Survivors of the women soldiers'], ['WHAT IT CANNOT SHOW', 'Who served where, or the fighting itself']]}>
  <div style={{position: 'absolute', left: 386, bottom: 34}}><Stamp at={cu(cues, 0)} text="Not the battle either" size={50} rot={-3} style={{background: "rgba(204,74,50,0.07)"}} /></div></Cat>);
export const S39: React.FC<P> = ({cues}) => {
  const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2);
  const Paper: React.FC<{at: number; mast: string; date: string; body: string; rot: number; children?: React.ReactNode}> = ({at, mast, date, body, rot, children}) => (<Pop at={at} from={0.8} style={{background: C.paper, width: 720, padding: '34px 40px 44px', borderRadius: 6, transform: `rotate(${rot}deg)`, boxShadow: '0 30px 70px rgba(0,0,0,0.6)', position: 'relative'}}>
    <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 58, color: C.ink, textAlign: 'center', borderBottom: '4px double #6B5A3A', paddingBottom: 10}}>{mast}</div>
    <div style={{fontFamily: MONO, fontSize: 22, color: '#7A6233', textAlign: 'center', letterSpacing: 3, margin: '10px 0 18px'}}>{date}</div>
    <div style={{fontFamily: SERIF, fontWeight: 600, fontSize: 42, color: C.ink, lineHeight: 1.25}}>{body}</div>{children}</Pop>);
  return (<Pad>
    <Fade at={3}><H size={58}>WITHIN DAYS, THE FRENCH PRESS HAD PICTURES</H></Fade>
    <div style={{display: 'flex', gap: 70, marginTop: 50, justifyContent: 'center'}}>
      <Paper at={c0} mast="French illustrated press" date="MARCH 1890" body="Women soldiers shown holding severed heads." rot={-2} />
      <Paper at={c1} mast="Le Petit Parisien" date="MARCH 1890" body="Women soldiers drawn in horned helmets." rot={2}>
        <div style={{position: 'absolute', left: 60, bottom: -50}}><Stamp at={c2} text="“Certainly fictitious”" size={46} rot={-4} style={{background: "rgba(233,223,200,0.92)"}} /></div></Paper>
    </div>
  </Pad>);
};
export const S40: React.FC<P> = ({cues}) => { const c0 = cu(cues, 0); return (<Center>
  <Fade at={3}><Label size={30}>Photographs circulating online</Label></Fade>
  <div style={{display: 'flex', alignItems: 'center', gap: 50, marginTop: 34}}>
    <Fade at={8} dx={-40} dy={0}><H size={84} color={C.blue}>PERFORMERS AT<br />EUROPEAN EXHIBITIONS</H></Fade>
    <Pop at={c0 - 8}><div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 170, color: C.red}}>≠</div></Pop>
    <Fade at={c0} dx={40} dy={0}><H size={84} color={C.gold}>SOLDIERS<br />AT WAR</H></Fade>
  </div>
  <Fade at={c0 + 20} style={{marginTop: 50}}><Chip color={C.muted}>NONE OF THOSE PHOTOGRAPHS IS USED IN THIS FILM</Chip></Fade>
</Center>); };

// S41-S42: the museum record, set out as text. No object is pictured.
export const S41: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1);
  const items = ['bag', 'horn', 'cord', 'necklace', 'amulet', 'amulet', 'amulet', 'amulet', 'amulet'];
  return (<Pad>
    <Fade at={3}><Label>Paris today · musée du quai Branly – Jacques Chirac</Label></Fade>
    <Fade at={8}><H size={64} style={{marginTop: 8}}>OBJECTS FROM THE FIELD OF 4 MARCH</H></Fade>
    <div style={{display: 'flex', gap: 18, marginTop: 40}}>{items.map((t, i) => <Pop key={i} at={c0 + i * 4} from={0.6} style={{width: 168, height: 150, border: `2px solid ${C.goldDim}`, borderRadius: 12, background: 'rgba(25,19,12,0.95)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}><div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 52, color: C.gold}}>{i + 1}</div><Label size={20} color={C.text2}>{t}</Label></Pop>)}</div>
    <Fade at={c1} style={{marginTop: 40, display: 'flex', gap: 50, alignItems: 'flex-start'}}>
      <div style={{background: C.paper, borderRadius: 8, padding: '26px 34px', width: 900}}>
        <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 22, color: '#7A6233', letterSpacing: 3}}>RECORD 71.1891.22.186 · HORN</div>
        <div style={{fontFamily: SERIF, fontWeight: 600, fontSize: 36, color: C.ink, lineHeight: 1.3, marginTop: 10}}>Fon, c. 1885. Entered the collection 13 April 1891. Donor: Édouard Foà.<br /><i>“prise à la ceinture d'un Dahoméen”</i>: taken from the belt of a Dahomean.</div>
      </div>
      <div style={{flex: 1}}><H size={44} color={C.amber}>WHAT THE RECORDS DON'T SAY</H><Body size={36} style={{marginTop: 8}}>They do not securely identify every original wearer.</Body></div>
    </Fade>
  </Pad>);
};
export const S42: React.FC<P> = ({cues}) => { const c0 = cu(cues, 0); return (<Center>
  <Fade at={3}><H size={86} style={{textAlign: 'center'}}>SOME CONTAIN HUMAN REMAINS</H></Fade>
  <Fade at={12} style={{marginTop: 22}}><Chip color={C.muted} style={{fontSize: 30}}>NOT SHOWN IN THIS FILM</Chip></Fade>
  <Fade at={c0} style={{marginTop: 60, textAlign: 'center'}}><Label size={30}>Today</Label><H size={76} color={C.gold} style={{marginTop: 8}}>RESTITUTION CLAIMS BY BENIN</H></Fade>
</Center>); };

// S43: the agreement that was never ratified
export const S43: React.FC<P> = ({cues}) => {
  const c0 = cu(cues, 0), c1 = cu(cues, 1), c2 = cu(cues, 2); const k = 0.12;
  return (<AbsoluteFill>
    <GeoMap cx={PT.cotonou[0] - 330 * k} cy={PT.cotonou[1] - 130 * k} k={k}>
      <Pin p={PT.cotonou} k={k} text="COTONOU" at={4} color={C.gold} size={34} dy={46} dx={-70} />
      <Pin p={PT.ouidah} k={k} text="OUIDAH" sub="October 1890" at={c0} color={C.cream} size={36} dx={-190} dy={-22} pulse />
      <Pin p={PT.portonovo} k={k} text="PORTO-NOVO" sub="French protectorate" at={c1} color={C.blue} size={32} dy={-18} />
    </GeoMap>
    <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(11,9,7,0.95) 0%, rgba(11,9,7,0.82) 44%, transparent 72%)'}} />
    <div style={{position: 'absolute', left: 120, top: 150, width: 860}}>
      <Fade at={3}><H size={62}>THE WAR DID NOT END AT COTONOU</H></Fade>
      <Fade at={c0}><Label style={{marginTop: 30}}>October 1890 · a deal at Ouidah</Label></Fade>
      <Fade at={c1}><Body size={42} color={C.cream} style={{marginTop: 14}}>Dahomey respects the Porto-Novo protectorate.</Body></Fade>
      <Fade at={c1 + 40}><Body size={42} color={C.cream} style={{marginTop: 10}}>France occupies Cotonou, for an annual payment.</Body></Fade>
      <div style={{marginTop: 40}}><Stamp at={c2 + 20} text="Never ratified in Paris" size={50} rot={-4} /></div>
    </div>
  </AbsoluteFill>);
};

// S44: 1892 is a different war
export const S44: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0), c1 = cu(cues, 1);
  return (<Pad>
    <svg width={1660} height={170}><Draw d="M 20 80 L 1640 80" at={2} dur={30} color={C.goldDim} w={5} />
      <circle cx={260} cy={80} r={16} fill={C.gold} /><text x={260} y={150} textAnchor="middle" fontFamily="Cinzel, serif" fontWeight={900} fontSize={52} fill={C.gold}>1890</text><text x={260} y={44} textAnchor="middle" fontFamily="Plex, monospace" fontWeight={600} fontSize={24} fill={C.text2}>COTONOU</text>
      <g opacity={ease(f, 8, 14)}><circle cx={1240} cy={80} r={20} fill={C.red} /><text x={1240} y={150} textAnchor="middle" fontFamily="Cinzel, serif" fontWeight={900} fontSize={52} fill={C.red}>1892</text><text x={1240} y={44} textAnchor="middle" fontFamily="Plex, monospace" fontWeight={600} fontSize={24} fill={C.text2}>FRANCE RETURNS</text></g></svg>
    <div style={{display: 'flex', gap: 24, marginTop: 30}}>{['A LARGER FORCE', 'GENERAL DODDS', 'THE FOREIGN LEGION', 'A NEW RIFLE'].map((t, i) => <Pop key={t} at={14 + i * 12} from={0.8}><Chip color={C.red} style={{fontSize: 30}}>{t}</Chip></Pop>)}</div>
    <Fade at={c0} style={{marginTop: 60, display: 'flex', alignItems: 'center', gap: 50}}>
      <div style={{border: `3px solid ${C.line}`, borderRadius: 16, padding: '28px 40px', background: 'rgba(25,19,12,0.95)'}}><Label color={C.text2}>The famous scene</Label><H size={54} style={{marginTop: 6, whiteSpace: 'nowrap'}}>DOGBA · THE DAWN ATTACK</H><Body size={36}>soldiers running from their tents</Body></div>
      <Stamp at={c1} text="Belongs to 1892" size={50} rot={-3} />
    </Fade>
  </Pad>);
};

// S45: a colonial voice
export const S45: React.FC<P> = ({cues}) => { const c0 = cu(cues, 0), c1 = cu(cues, 1); return (<Pad>
  <Fade at={3}><Label>A French report, April 1890</Label></Fade>
  <div style={{fontFamily: SERIF, fontStyle: 'italic', fontWeight: 400, fontSize: 128, color: C.text2, lineHeight: 1.12, marginTop: 30, minHeight: 300}}><Typed text={'“harpies drunk on trade gin”'} at={c0 - 6} cps={24} /></div>
  <div style={{marginTop: 50}}><Stamp at={c1} text="A colonial voice, not a fact" size={64} rot={-3} /></div>
</Pad>); };

// S46: both are true
export const S46: React.FC<P> = ({cues}) => { const c0 = cu(cues, 0), c1 = cu(cues, 1); return (<Center>
  <div style={{display: 'flex', gap: 60, alignItems: 'stretch'}}>
    <Fade at={4} dx={-40} dy={0} style={{width: 720, border: `3px solid ${C.gold}`, borderRadius: 18, padding: '44px 40px', textAlign: 'center'}}><Label>The Kingdom of Dahomey</Label><H size={66} style={{marginTop: 12}}>RESISTED FRENCH EXPANSION</H></Fade>
    <Fade at={c0} dx={40} dy={0} style={{width: 720, border: `3px solid ${C.red}`, borderRadius: 18, padding: '44px 40px', textAlign: 'center'}}><Label color={C.red}>The Kingdom of Dahomey</Label><H size={66} style={{marginTop: 12}}>PRACTISED SLAVERY</H></Fade>
  </div>
  <Pop at={c1} style={{marginTop: 60}}><H size={120} color={C.cream} style={{fontWeight: 900}}>BOTH ARE TRUE.</H></Pop>
</Center>); };

// S47: Nawi
export const S47: React.FC<P> = ({cues, len}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0); const p = ease(f, 6, Math.min(90, len - 40)); const year = Math.round(1890 + 89 * p);
  return (<Pad>
    <Fade at={3}><Label>The last known veteran</Label></Fade>
    <Fade at={8}><H size={170} color={C.gold} style={{fontWeight: 900, letterSpacing: 10}}>NAWI</H></Fade>
    <svg width={1660} height={170} style={{marginTop: 10}}>
      <line x1={20} y1={70} x2={1640} y2={70} stroke={C.line} strokeWidth={8} strokeLinecap="round" /><line x1={20} y1={70} x2={20 + 1620 * p} y2={70} stroke={C.gold} strokeWidth={8} strokeLinecap="round" />
      <circle cx={20 + 1620 * p} cy={70} r={16} fill={C.cream} />
      <text x={20} y={140} fontFamily="Cinzel, serif" fontWeight={700} fontSize={44} fill={C.text2}>1890</text>
      <text x={1640} y={140} textAnchor="end" fontFamily="Cinzel, serif" fontWeight={900} fontSize={56} fill={C.cream}>{year}</text>
    </svg>
    <Fade at={30}><Body size={48} color={C.cream} style={{marginTop: 10}}>Died in 1979.</Body></Fade>
    <Fade at={c0}><Body size={48} style={{marginTop: 22, maxWidth: 1400}}>A soldier of a kingdom that no longer existed, who had fought a war she did not start.</Body></Fade>
  </Pad>);
};

// S48: the battle is in the words
export const S48: React.FC<P> = ({cues}) => {
  const c0 = cu(cues, 0);
  const W: React.FC<{at: number; who: string; what: string; color: string}> = ({at, who, what, color}) => (<Fade at={at} dx={-40} dy={0} style={{display: 'flex', alignItems: 'center', gap: 34, marginTop: 26, borderLeft: `8px solid ${color}`, paddingLeft: 34}}><H size={54} color={color} style={{width: 420}}>{who}</H><Body size={44} color={C.cream}>{what}</Body></Fade>);
  return (<Pad>
    <Fade at={3}><Body size={56} color={C.muted}>The images we have are not the battle.</Body></Fade>
    <Fade at={c0}><H size={76} style={{marginTop: 10}}>THE BATTLE IS IN THE <span style={{color: C.gold}}>WORDS</span></H></Fade>
    <W at={cu(cues, 1)} who="AN OFFICER" what="who stayed at his post with a broken shoulder" color={C.blue} />
    <W at={cu(cues, 2)} who="A GOVERNOR" what="who watched a young woman he called “Nanisca”" color={C.amber} />
    <W at={cu(cues, 3)} who="A TRADER" what="who took objects from the dead to a museum" color={C.gold} />
  </Pad>);
};

// S49, S50: close
export const S49: React.FC<P> = ({cues}) => { const c0 = cu(cues, 0); return (<Center>
  <Fade at={4}><Label size={30}>The women soldiers of Dahomey</Label></Fade>
  <Pop at={12}><H size={200} color={C.gold} style={{fontWeight: 900, letterSpacing: 8, marginTop: 10}}>WERE REAL</H></Pop>
  <Rule at={c0 - 6} w={560} />
  <Fade at={c0}><Body size={50} color={C.cream} style={{textAlign: 'center', maxWidth: 1300}}>Get the date right. Get the evidence right.<br />Tell the story without inventing it.</Body></Fade>
</Center>); };
export const S50: React.FC<P> = ({cues}) => {
  const f = useCurrentFrame(); const c0 = cu(cues, 0); const s = usePop(c0);
  return (<Center>
    <Fade at={4}><div style={{width: 20, height: 20, background: C.gold, transform: 'rotate(45deg)', marginBottom: 30}} /></Fade>
    <Fade at={8}><H size={120} style={{fontWeight: 900, letterSpacing: 10}}>ORIGINEX</H></Fade>
    <Fade at={14}><H size={54} color={C.gold} style={{letterSpacing: 18}}>HUMAN ARCHIVES</H></Fade>
    <div style={{marginTop: 70, transform: `scale(${0.7 + 0.3 * s + Math.sin(f / 8) * 0.012})`, opacity: lin(f, c0, c0 + 6), background: C.red, borderRadius: 14, padding: '20px 60px'}}><span style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 56, color: '#fff', letterSpacing: 6}}>SUBSCRIBE</span></div>
    <Fade at={c0 + 14} style={{marginTop: 26}}><Body size={38} style={{fontStyle: 'italic', fontWeight: 400}}>if you think this record is worth keeping</Body></Fade>
  </Center>);
};

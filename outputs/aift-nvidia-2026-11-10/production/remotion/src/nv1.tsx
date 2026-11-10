import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Bullet, Chip, Glass, H1, Hl, MONO, Not, Num, Rv, SANS, SERIF, SP, Shell, SourceCard, T, cu, focus, lin, prog} from './theme';
import PX from './prices.json';

const label: React.CSSProperties = {fontFamily: MONO, fontSize: 24, letterSpacing: 3, textTransform: 'uppercase', color: T.gold, fontWeight: 600};
const abs = (x: number, y: number, w?: number, h?: number): React.CSSProperties => ({position: 'absolute', left: x, top: y, width: w, height: h});

// ───────────────────────── 00 Cold open ─────────────────────────
export const L01: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  return (
    <Shell len={len} kind="CONFIRMED" source="Close: Nasdaq regular session, 9 Nov 2026 · Market-value figure: Reuters, 9 Nov 2026">
      <Rv at={2} style={abs(96, 150)}>
        <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 168, letterSpacing: -6, color: T.white, lineHeight: 1}}>NVIDIA</div>
        <div style={{...label, marginTop: 14, color: T.text2}}>Nasdaq: NVDA · Monday 9 November 2026</div>
      </Rv>
      <Rv at={cu(cues, 1)} style={abs(96, 420, 900)}>
        <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 200, letterSpacing: -8, color: T.gold, lineHeight: 1}}>
          <span style={{color: T.red, fontSize: 120, verticalAlign: 18, marginRight: 12}}>▼</span>≈$<Num to={190} at={cu(cues, 1)} fmt={(v) => v.toFixed(0)} />bn
        </div>
        <div style={{fontFamily: SANS, fontSize: 40, color: T.text, fontWeight: 600, marginTop: 6}}>of market value in one session <span style={{color: T.muted, fontWeight: 500}}>— according to Reuters</span></div>
      </Rv>
      <Rv at={cu(cues, 1) + 22} x={40} y={0} style={abs(1090, 150, 734)}>
        <Glass style={{padding: '36px 44px 40px'}}>
          <div style={label}>Regular-session close · 9 Nov 2026</div>
          <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 150, color: T.white, letterSpacing: -6, lineHeight: 1.05, marginTop: 10}}>$178.67</div>
          <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 96, color: T.red, letterSpacing: -3, lineHeight: 1.05}}>▼ 4.27%</div>
          <div style={{fontFamily: SANS, fontSize: 30, color: T.text2, marginTop: 10}}>Previous close $186.64 (6 Nov)</div>
        </Glass>
      </Rv>
      <Rv at={cu(cues, 2)} style={abs(96, 770, 1728)}>
        <Glass tone="gold" style={{padding: '34px 48px'}}>
          <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 60, color: T.white, letterSpacing: -1.2}}>
            But the question goes <Hl at={cu(cues, 2) + 14}>beyond the price of a chip</Hl>.
          </div>
        </Glass>
      </Rv>
    </Shell>
  );
};

const Row: React.FC<{at: number; tag: string; kind: string; y: number; children: React.ReactNode}> = ({at, tag, kind, y, children}) => (
  <Rv at={at} x={-30} y={0} style={abs(96, y, 1728)}>
    <Glass style={{padding: '30px 44px', display: 'flex', alignItems: 'center', gap: 40, minHeight: 176}}>
      <div style={{...label, width: 330, flexShrink: 0, lineHeight: 1.35}}>{tag}</div>
      <div style={{fontFamily: SANS, fontSize: 44, fontWeight: 700, color: T.white, lineHeight: 1.16, letterSpacing: -0.6, flex: 1}}>{children}</div>
      <Chip kind={kind} size={24} style={{flexShrink: 0}} />
    </Glass>
  </Rv>
);
export const L02: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} source="NVIDIA Newsroom, 8 Nov 2026 · House Foreign Affairs Committee release, 5 Nov 2026">
    <H1 at={0} kicker="What changed">Three developments. Different levels of proof.</H1>
    <Row at={cu(cues, 0) + 8} tag="Admission · 8 Nov" kind="CONFIRMED" y={280}>Jensen Huang tells staff he was unfaithful to his wife</Row>
    <Row at={cu(cues, 1)} tag="Investigation · 8 Nov" kind="CONFIRMED" y={490}>Board opens an independent investigation, after reports of a foreign intelligence effort targeting him</Row>
    <Row at={cu(cues, 2)} tag="Washington · 4–5 Nov" kind="REQUESTED" y={722}>House committee chairs request a closed-door briefing</Row>
  </Shell>
);

export const DateCard: React.FC<{day: string; num: string; title: string; sub: string; kind: string; tone: 'gold' | 'clear'; dashed?: boolean; w?: number; h?: number}> = ({day, num, title, sub, kind, tone, dashed, w = 800, h = 560}) => (
  <Glass tone={tone} dashed={dashed} style={{width: w, height: h, padding: '38px 48px'}}>
    <div style={{display: 'flex', alignItems: 'flex-end', gap: 26}}>
      <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 230, color: T.white, letterSpacing: -10, lineHeight: 0.9}}>{num}</div>
      <div style={{paddingBottom: 12}}>
        <div style={{...label, color: T.text2}}>{day}</div>
        <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 86, color: T.gold, letterSpacing: -2, lineHeight: 1}}>NOV</div>
      </div>
    </div>
    <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 58, color: T.white, letterSpacing: -1.2, marginTop: 34, lineHeight: 1.08}}>{title}</div>
    <div style={{fontFamily: SANS, fontSize: 36, color: T.text2, marginTop: 12, lineHeight: 1.25}}>{sub}</div>
    <Chip kind={kind} size={26} style={{position: 'absolute', right: 40, top: 40}} />
  </Glass>
);
export const L03: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const p = prog(f, cu(cues, 3), 18);
  return (
    <Shell len={len} source="NVIDIA Investor Relations, 28 Oct 2026 · House Foreign Affairs Committee release, 5 Nov 2026">
      <H1 at={0}>Two dates to watch</H1>
      <Rv at={cu(cues, 1)} x={-40} y={0} style={abs(96, 250)}>
        <DateCard day="Tuesday" num="17" title="Earnings" sub="Q3 fiscal 2027 results and call" kind="SCHEDULED" tone="gold" />
      </Rv>
      <Rv at={cu(cues, 2)} x={40} y={0} style={abs(1024, 250)}>
        <DateCard day="Wednesday" num="18" title="Congressional briefing" sub="Closed-door, requested by three House committee chairs" kind="REQUESTED" tone="clear" dashed />
      </Rv>
      <div style={{...abs(960 - 62, 462, 124, 124), borderRadius: 62, background: T.lime, color: '#0A0A08', fontFamily: MONO, fontWeight: 600, fontSize: 84, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${p})`, boxShadow: '0 20px 50px rgba(0,0,0,0.6)'}}>≠</div>
      <Rv at={cu(cues, 3) + 6} style={{...abs(96, 850, 1728), textAlign: 'center', fontFamily: SANS, fontWeight: 700, fontSize: 54, color: T.white, letterSpacing: -1}}>
        They test <Hl at={cu(cues, 3) + 16}>very different things</Hl>.
      </Rv>
    </Shell>
  );
};

const Tile: React.FC<{at: number; x: number; kind: string; tone: 'lime' | 'gold' | 'clear'; dashed?: boolean; pre: string; big: string; post?: string}> = ({at, x, kind, tone, dashed, pre, big, post}) => (
  <Rv at={at} style={abs(x, 262, 556)}>
    <Glass tone={tone} dashed={dashed} style={{height: 330, padding: '32px 38px'}}>
      <Chip kind={kind} size={22} />
      <div style={{fontFamily: SANS, fontSize: 40, color: T.text2, fontWeight: 500, marginTop: 26}}>{pre}</div>
      <div style={{fontFamily: SANS, fontSize: 74, color: T.white, fontWeight: 800, letterSpacing: -2, lineHeight: 1.02}}>{big}</div>
      {post ? <div style={{fontFamily: SANS, fontSize: 40, color: T.text2, fontWeight: 500, marginTop: 6}}>{post}</div> : null}
    </Glass>
  </Rv>
);
export const L04: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} source="AIFT research pack, 10 Nov 2026 · full source slate at the end of the film">
    <H1 at={0}>By the end, you'll know</H1>
    <Tile at={cu(cues, 1)} x={96} kind="CONFIRMED" tone="lime" pre="what is" big="confirmed" />
    <Tile at={cu(cues, 2)} x={682} kind="ALLEGED" tone="gold" dashed pre="what remains" big="alleged" />
    <Tile at={cu(cues, 3)} x={1268} kind="ANALYSIS" tone="clear" pre="what could" big="change" post="the investment case" />
    <Rv at={cu(cues, 4)} style={{...abs(96, 668, 1728), display: 'flex', alignItems: 'center', gap: 30}}>
      <div style={{width: 74, height: 74, background: T.lime, borderRadius: 14}} />
      <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 104, color: T.white, letterSpacing: -3.5}}>
        AI Finance <span style={{color: T.gold}}>Toolkit</span>
      </div>
    </Rv>
    <Rv at={cu(cues, 5)} style={abs(96, 836)}>
      <Glass style={{padding: '20px 34px', display: 'inline-flex', alignItems: 'center', gap: 22}}>
        <span style={label}>Research snapshot</span>
        <span style={{fontFamily: SANS, fontWeight: 700, fontSize: 44, color: T.white}}>Morning of 10 November 2026, UK time</span>
      </Glass>
    </Rv>
  </Shell>
);

// ───────────────────────── 01 What actually happened ─────────────────────────
const NODES: [string, string][] = [
  ['29 Oct', 'NYT reporting'],
  ['8 Nov', 'Official statements'],
  ['9 Nov', 'Market close'],
  ['9 Nov · after close', 'Lawsuit filed'],
];
export const Timeline: React.FC<{at: number; active: number; y?: number}> = ({at, active, y = 262}) => {
  const f = useCurrentFrame();
  const draw = prog(f, at, 40);
  const x0 = 250;
  const x1 = 1670;
  return (
    <div style={abs(0, y, 1920, 190)}>
      <div style={{position: 'absolute', left: x0, top: 62, width: (x1 - x0) * draw, height: 5, background: `linear-gradient(90deg, ${T.gold}, ${T.white})`, borderRadius: 3}} />
      {NODES.map(([d, t], i) => {
        const x = x0 + ((x1 - x0) * i) / 3;
        const p = prog(f, at + 6 + i * 9, 16);
        const on = i === active;
        return (
          <div key={i} style={{position: 'absolute', left: x - 220, top: 0, width: 440, textAlign: 'center', opacity: p}}>
            <div style={{fontFamily: MONO, fontSize: 26, letterSpacing: 2, textTransform: 'uppercase', color: on ? T.lime : T.gold, fontWeight: 600, height: 40}}>{d}</div>
            <div style={{margin: '8px auto 0', width: on ? 40 : 28, height: on ? 40 : 28, marginTop: on ? 4 : 10, borderRadius: 20, background: on ? T.lime : T.bg, border: `4px solid ${on ? T.lime : T.white}`, boxShadow: on ? '0 0 34px rgba(201,242,62,0.7)' : 'none', boxSizing: 'border-box'}} />
            <div style={{fontFamily: SANS, fontSize: 36, fontWeight: 700, color: on ? T.white : T.text2, marginTop: on ? 14 : 20}}>{t}</div>
          </div>
        );
      })}
    </div>
  );
};
export const L05: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const act = f >= cu(cues, 1) ? 0 : -1;
  return (
    <Shell len={len} chapter="What happened" kind="REPORTED" source="The New York Times, 29 Oct 2026, as relayed by Reuters, 9 Nov 2026 — full NYT article not independently read">
      <H1 at={0} size={54}>Sequence matters: four separate developments</H1>
      <Timeline at={cu(cues, 0) + 10} active={act} />
      <Rv at={cu(cues, 1)} style={abs(96, 486, 1060)}>
        <Glass tone="gold" style={{padding: '30px 40px 34px', minHeight: 450}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div style={{...label, whiteSpace: 'nowrap'}}>The New York Times · 29 Oct 2026</div>
            <div style={{fontFamily: MONO, fontSize: 18, letterSpacing: 1.6, color: T.text2, textTransform: 'uppercase', whiteSpace: 'nowrap'}}>Designed summary</div>
          </div>
          <div style={{fontFamily: SANS, fontSize: 40, fontWeight: 600, color: T.white, lineHeight: 1.22, marginTop: 22}}>
            Reported on <b style={{fontWeight: 800}}>Alice Huang</b>, a <Hl at={cu(cues, 1) + 30}>former executive</Hl> at Singapore-based Megaspeed.
          </div>
          <Rv at={cu(cues, 2)} style={{fontFamily: SANS, fontSize: 40, fontWeight: 600, color: T.white, lineHeight: 1.22, marginTop: 22}}>
            Reported that US intelligence <Hl at={cu(cues, 2) + 16}>had assessed her</Hl> as a Chinese intelligence asset — and examined her relationship with Jensen Huang.
          </Rv>
        </Glass>
      </Rv>
      <Rv at={cu(cues, 3)} x={30} y={0} style={abs(1196, 486, 628)}>
        <Glass style={{padding: '28px 34px'}}>
          <Chip kind="REPORTED" size={22} />
          <div style={{fontFamily: SANS, fontSize: 40, fontWeight: 700, color: T.white, lineHeight: 1.18, marginTop: 16}}>Attributed reporting about an intelligence assessment</div>
          <div style={{fontFamily: SANS, fontSize: 34, color: T.text2, marginTop: 10}}>Not a court finding.</div>
        </Glass>
      </Rv>
      <Rv at={cu(cues, 4)} x={30} y={0} style={abs(1196, 770, 628)}>
        <Glass tone="dark" style={{padding: '26px 34px'}}>
          <div style={{fontFamily: SANS, fontSize: 36, fontWeight: 600, color: T.text, lineHeight: 1.22}}>We cannot independently establish the underlying intelligence.</div>
        </Glass>
      </Rv>
    </Shell>
  );
};

export const L06: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const z = prog(f, cu(cues, 1), 26);
  return (
    <Shell len={len} chapter="What happened" kind="CONFIRMED" source="NVIDIA Newsroom, “A Message to Our Company”, 8 Nov 2026 (official page, read 10 Nov 2026)">
      <Rv at={cu(cues, 0)} style={{...abs(96, 150, 1090), transform: `scale(${1 + 0.035 * z})`, transformOrigin: '20% 70%'}}>
        <SourceCard outlet="NVIDIA Newsroom" date="November 8, 2026" headline="A Message to Our Company" hsize={58} tag="Official source · short extract">
          <div style={{fontFamily: SANS, fontSize: 30, color: '#5A5546', marginTop: 16, lineHeight: 1.3}}>NVIDIA founder and CEO Jensen Huang sent the following email to NVIDIA employees earlier today.</div>
          <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 86, lineHeight: 1.1, marginTop: 34, letterSpacing: -1.6, opacity: 0.25 + 0.75 * prog(f, cu(cues, 1), 14)}}>
            <Hl at={cu(cues, 2)} color="rgba(246,196,69,0.75)">“I was unfaithful to my wife.”</Hl>
          </div>
        </SourceCard>
      </Rv>
      <Rv at={cu(cues, 0) + 14} x={30} y={0} style={abs(1250, 150, 574)}>
        <Glass tone="lime" style={{padding: '28px 34px'}}>
          <Chip kind="CONFIRMED" size={22} />
          <div style={{fontFamily: SANS, fontSize: 40, fontWeight: 700, color: T.white, lineHeight: 1.18, marginTop: 16}}>His own words, in an official staff email</div>
        </Glass>
      </Rv>
      <Rv at={cu(cues, 3)} x={30} y={0} style={abs(1250, 470, 574)}>
        <Glass style={{padding: '28px 34px'}}>
          <div style={label}>What it does not say</div>
          <div style={{fontFamily: SANS, fontSize: 44, fontWeight: 700, color: T.white, lineHeight: 1.16, marginTop: 14}}>The public email does not name the other person.</div>
        </Glass>
      </Rv>
    </Shell>
  );
};

const Ex: React.FC<{at: number; hl: number; children: React.ReactNode}> = ({at, hl, children}) => (
  <Rv at={at} y={14} style={{fontFamily: SERIF, fontWeight: 600, fontSize: 46, lineHeight: 1.2, marginTop: 30, paddingLeft: 24, borderLeft: '5px solid #C9962C'}}>
    <Hl at={hl} color="rgba(246,196,69,0.6)">{children}</Hl>
  </Rv>
);
export const L07: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} chapter="What happened" kind="CONFIRMED" source="NVIDIA Newsroom, “Statement From NVIDIA Board of Directors”, 8 Nov 2026 (official page, read 10 Nov 2026)">
    <Rv at={cu(cues, 0)} style={abs(96, 124, 1130)}>
      <SourceCard outlet="NVIDIA Newsroom" date="November 8, 2026" headline="Statement From NVIDIA Board of Directors" hsize={58} tag="Official source · short extracts">
        <Ex at={cu(cues, 0) + 16} hl={cu(cues, 0) + 30}>“…initiating an independent investigation…”</Ex>
        <Ex at={cu(cues, 1)} hl={cu(cues, 1) + 12}>“A committee of independent directors, assisted by outside independent counsel…”</Ex>
        <Ex at={cu(cues, 2)} hl={cu(cues, 2) + 12}>“…no reason to believe that either national security or NVIDIA secrets were compromised…”</Ex>
        <Ex at={cu(cues, 3)} hl={cu(cues, 3) + 12}>“…confidence in Jensen and his leadership team…”</Ex>
      </SourceCard>
    </Rv>
    <Rv at={cu(cues, 0) + 14} x={30} y={0} style={abs(1280, 130, 544)}>
      <Glass tone="lime" style={{padding: '28px 34px'}}>
        <Chip kind="CONFIRMED" size={22} />
        <div style={{fontFamily: SANS, fontSize: 40, fontWeight: 700, color: T.white, lineHeight: 1.18, marginTop: 16}}>An independent investigation is open</div>
      </Glass>
    </Rv>
    <Rv at={cu(cues, 2) + 20} x={30} y={0} style={abs(1280, 440, 544)}>
      <Glass tone="gold" dashed style={{padding: '28px 34px'}}>
        <div style={label}>Read it carefully</div>
        <div style={{fontFamily: SANS, fontSize: 42, fontWeight: 700, color: T.white, lineHeight: 1.16, marginTop: 14}}>The board's stated position — not a completed finding.</div>
      </Glass>
    </Rv>
  </Shell>
);

const Col: React.FC<{x: number; kind: string; tone: 'lime' | 'gold' | 'clear'; dashed?: boolean; items: string[]; at: number; bright: number}> = ({x, kind, tone, dashed, items, at, bright}) => (
  <Rv at={at} style={abs(x, 240, 556)}>
    <div style={{opacity: bright}}>
      <Glass tone={tone} dashed={dashed} style={{height: 500, padding: '30px 34px'}}>
        <Chip kind={kind} size={26} />
        <div style={{marginTop: 26, display: 'flex', flexDirection: 'column', gap: 22}}>
          {items.map((t, i) => (
            <Bullet key={i} at={at + 10 + i * 7} size={38} color={tone === 'lime' ? T.lime : tone === 'gold' ? T.gold : T.white}>{t}</Bullet>
          ))}
        </div>
      </Glass>
    </div>
  </Rv>
);
export const L08: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const c1 = cu(cues, 1);
  const c2 = cu(cues, 2);
  const c3 = cu(cues, 3);
  const mid = Math.round((c1 + c2) / 2);
  const all = f < c1 - 6 ? 1 : 0;
  const bC = Math.max(all, focus(f, c1, mid));
  const bR = Math.max(all, focus(f, mid, c2), focus(f, c3, 99999));
  const bU = Math.max(all, focus(f, c2, c3));
  return (
    <Shell len={len} chapter="What happened" source="NVIDIA Newsroom, 8 Nov · NYT via Reuters · China's foreign ministry via Reuters, 9–10 Nov 2026">
      <H1 at={0} size={54}>Confirmed, reported, unresolved</H1>
      <Col x={96} kind="CONFIRMED" tone="lime" items={['Personal admission', 'Board investigation opened', 'House briefing request']} at={cu(cues, 0) + 6} bright={bC} />
      <Col x={682} kind="REPORTED" tone="gold" items={['Intelligence assessment (NYT)', 'Proposed class action (Reuters)', 'Trump: FBI “looking into it”']} at={cu(cues, 0) + 14} bright={bR} />
      <Col x={1268} kind="UNRESOLVED" tone="clear" dashed items={['Were any secrets compromised?', 'What will the board find?', 'Will the briefing happen?']} at={cu(cues, 0) + 22} bright={bU} />
      <Rv at={c3} style={abs(96, 770, 1728)}>
        <Glass style={{padding: '24px 40px', display: 'flex', alignItems: 'center', gap: 40}}>
          <div style={{width: 300, flexShrink: 0}}>
            <div style={label}>The denial</div>
            <div style={{fontFamily: SANS, fontSize: 30, color: T.text2, marginTop: 6, lineHeight: 1.2}}>China's foreign ministry, via Reuters</div>
          </div>
          <div style={{fontFamily: SERIF, fontWeight: 600, fontSize: 50, color: T.white, lineHeight: 1.12, letterSpacing: -0.6}}>
            “…purely a <Hl at={c3 + 16}>groundless accusation</Hl>, slander, and a smear.”
          </div>
        </Glass>
      </Rv>
    </Shell>
  );
};

// ───────────────────────── 02 Why investors care ─────────────────────────
export const Tabs: React.FC<{at: number; active: number}> = ({at, active}) => (
  <div style={{...abs(96, 236, 1728), display: 'flex', gap: 22}}>
    {['Leadership continuity', 'Export policy', 'Legal & governance'].map((t, i) => {
      const on = i === active;
      return (
        <Rv key={i} at={at + i * 6} style={{flex: 1}}>
          <div style={{borderRadius: 16, padding: '16px 26px', display: 'flex', alignItems: 'center', gap: 18, background: on ? T.gold : 'rgba(255,255,255,0.07)', border: `1.5px solid ${on ? T.gold : 'rgba(255,255,255,0.3)'}`, boxShadow: on ? '0 18px 50px rgba(246,196,69,0.28)' : 'none'}}>
            <span style={{fontFamily: MONO, fontWeight: 600, fontSize: 36, color: on ? '#0A0A08' : T.gold}}>{i + 1}</span>
            <span style={{fontFamily: SANS, fontWeight: 700, fontSize: 36, color: on ? '#0A0A08' : T.text2}}>{t}</span>
          </div>
        </Rv>
      );
    })}
  </div>
);
const Hub: React.FC<{at: number; ripple: number}> = ({at, ripple}) => {
  const f = useCurrentFrame();
  const cx = 400;
  const cy = 300;
  const sp: [number, number, string, string][] = [
    [120, 78, 'Customer', 'relationships'],
    [690, 110, 'Product', 'direction'],
    [400, 548, 'Investor', 'confidence'],
  ];
  return (
    <div style={abs(96, 352, 800, 620)}>
      <svg width={800} height={620} style={{position: 'absolute', left: 0, top: 0}}>
        {sp.map(([x, y], i) => {
          const p = prog(f, at + i * 8, 18);
          return <line key={i} x1={cx} y1={cy} x2={cx + (x - cx) * p} y2={cy + (y - cy) * p} stroke={T.gold} strokeWidth={4} strokeDasharray="2 12" strokeLinecap="round" />;
        })}
        {[0, 1, 2].map((i) => {
          const t = ((f - ripple) / 70 + i / 3) % 1;
          if (f < ripple) return null;
          return <circle key={i} cx={cx} cy={cy} r={120 + t * 190} fill="none" stroke={T.gold} strokeWidth={3} strokeDasharray="10 14" opacity={(1 - t) * 0.7} />;
        })}
      </svg>
      <div style={{position: 'absolute', left: cx - 118, top: cy - 118, width: 236, height: 236, borderRadius: 118, background: 'linear-gradient(150deg, rgba(255,255,255,0.3), rgba(255,255,255,0.08))', border: `3px solid ${T.white}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', boxShadow: '0 30px 70px rgba(0,0,0,0.6)'}}>
        <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 40, color: T.white, lineHeight: 1.05, textAlign: 'center'}}>Founder<br />& CEO</div>
      </div>
      {sp.map(([x, y, a, b], i) => (
        <Rv key={i} at={at + 10 + i * 8} style={{position: 'absolute', left: x - 150, top: y - 52, width: 300, textAlign: 'center'}}>
          <div style={{display: 'inline-block', background: 'rgba(10,10,8,0.82)', border: `1.5px solid ${T.edge}`, borderRadius: 14, padding: '10px 20px', fontFamily: SANS, fontWeight: 700, fontSize: 36, color: T.white, lineHeight: 1.1}}>
            {a}
            <br />
            {b}
          </div>
        </Rv>
      ))}
    </div>
  );
};
export const L09: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const q = 1 - prog(f, cu(cues, 2) - 8, 14);
  return (
    <Shell len={len} chapter="Why investors care" kind="ANALYSIS" source="AIFT analysis · Board position: NVIDIA Newsroom, 8 Nov 2026">
      <div style={{opacity: q}}>
        <Rv at={0} style={{...abs(96, 330, 1728), fontFamily: SANS, fontWeight: 800, fontSize: 104, color: T.white, letterSpacing: -3, lineHeight: 1.05}}>
          Why does this become a <span style={{color: T.gold}}>stock-market</span> story?
        </Rv>
        <Rv at={cu(cues, 1)} style={abs(96, 640)}>
          <Chip kind="ANALYSIS" size={34} />
        </Rv>
        <Rv at={cu(cues, 1) + 8} style={{...abs(96, 730, 1500), fontFamily: SANS, fontSize: 44, color: T.text2}}>Three channels — our analysis, not established fact.</Rv>
      </div>
      <div style={{opacity: 1 - q}}>
        <H1 at={cu(cues, 2)} size={54}>Three channels from headline to share price</H1>
        <Tabs at={cu(cues, 2)} active={0} />
        <Hub at={cu(cues, 3)} ripple={cu(cues, 4)} />
        <Rv at={cu(cues, 5)} x={30} y={0} style={abs(950, 352, 874)}>
          <Glass tone="gold" style={{padding: '24px 34px'}}>
            <div style={label}>The term</div>
            <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 56, color: T.white, letterSpacing: -1.4, lineHeight: 1.08, marginTop: 6}}>Leadership concentration risk</div>
          </Glass>
        </Rv>
        <div style={{...abs(950, 560, 874), display: 'flex', flexDirection: 'column', gap: 22}}>
          <Bullet at={cu(cues, 6)} color={T.white} size={40}>It does <b>not</b> mean Jensen is leaving</Bullet>
          <Bullet at={cu(cues, 7)} color={T.lime} size={40}>Board's published position: “confidence in Jensen and his leadership team”</Bullet>
          <Bullet at={cu(cues, 8)} color={T.gold} size={40}>Fair questions: decisions, responsibilities, continuity — if circumstances changed</Bullet>
        </div>
      </div>
    </Shell>
  );
};

const Step: React.FC<{at: number; x: number; y: number; n: string; t: string; s: string}> = ({at, x, y, n, t, s}) => (
  <Rv at={at} style={abs(x, y, 500)}>
    <Glass style={{padding: '20px 28px'}}>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 16}}>
        <span style={{fontFamily: MONO, fontWeight: 600, fontSize: 34, color: T.gold}}>{n}</span>
        <span style={{fontFamily: SANS, fontWeight: 800, fontSize: 44, color: T.white, letterSpacing: -0.8}}>{t}</span>
      </div>
      <div style={{fontFamily: SANS, fontSize: 30, color: T.text2, marginTop: 4}}>{s}</div>
    </Glass>
  </Rv>
);
export const L10: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} chapter="Why investors care" kind="ANALYSIS" source="AIFT analysis — no new export restriction is announced in the sources reviewed for this film">
    <H1 at={0} size={54}>Three channels from headline to share price</H1>
    <Tabs at={-40} active={1} />
    <Rv at={cu(cues, 1)} style={abs(96, 356, 850)}>
      <Glass style={{padding: '26px 34px'}}>
        <div style={label}>The backdrop</div>
        <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 42, color: T.white, lineHeight: 1.16, marginTop: 8}}>Nvidia sits inside a highly sensitive debate about access to advanced computing</div>
      </Glass>
    </Rv>
    <div style={{...abs(96, 636, 850), display: 'flex', flexDirection: 'column', gap: 14}}>
      <div style={{...label, color: T.text2}}>If lawmakers respond, possible tools:</div>
      <Bullet at={cu(cues, 2) + 6} size={42}>Tighter export rules</Bullet>
      <Bullet at={cu(cues, 2) + 26} size={42}>Security requirements</Bullet>
      <Bullet at={cu(cues, 2) + 46} size={42}>Closer scrutiny of customers</Bullet>
    </div>
    <Rv at={cu(cues, 3)} style={abs(96, 906, 850)}>
      <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 38, color: T.white}}>
        A <Hl at={cu(cues, 3) + 12}>possible channel</Hl> — not a new restriction.
      </div>
    </Rv>
    <Rv at={cu(cues, 4) - 4} style={{...abs(1010, 356, 814), ...label, color: T.text2}}>Three different things</Rv>
    <Step at={cu(cues, 4)} x={1010} y={762} n="1" t="Political demand" s="Letters, statements, calls for answers" />
    <Step at={cu(cues, 4) + 22} x={1167} y={592} n="2" t="Proposed law" s="A bill — not yet binding" />
    <Step at={cu(cues, 4) + 44} x={1324} y={422} n="3" t="Enacted rule" s="Enforceable — changes what can be sold" />
  </Shell>
);

export const L11: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const p = prog(f, cu(cues, 3), 30);
  return (
    <Shell len={len} chapter="Why investors care" kind="REPORTED" source="Reuters, 9 Nov 2026 (syndicated copy read at Investing.com) — plaintiffs' allegations, not findings">
      <H1 at={0} size={54}>Three channels from headline to share price</H1>
      <Tabs at={-40} active={2} />
      <Rv at={cu(cues, 1)} style={abs(96, 356, 960)}>
        <SourceCard outlet="Reuters" date="Nov 9, 2026" headline="Nvidia, CEO Huang sued over disclosures related to suspected Chinese spy" hsize={46} tag="Verbatim headline and extract · syndicated at Investing.com">
          <div style={{fontFamily: SERIF, fontWeight: 600, fontSize: 36, lineHeight: 1.24, marginTop: 20, paddingLeft: 22, borderLeft: '5px solid #C9962C'}}>
            “…sued on Monday in a <Hl at={cu(cues, 1) + 26} color="rgba(246,196,69,0.6)">proposed class action</Hl>…”
          </div>
        </SourceCard>
      </Rv>
      <div style={{...abs(1110, 364, 714), display: 'flex', flexDirection: 'column', gap: 22}}>
        <Bullet at={cu(cues, 2)} color={T.white} size={40}>Accusations by plaintiffs — <b>not established by a court</b></Bullet>
        <Bullet at={cu(cues, 2) + 16} color={T.white} size={40}>“Proposed”: no class certified, no judgment</Bullet>
      </div>
      <Rv at={cu(cues, 3)} style={abs(1110, 700, 714)}>
        <div style={{...label, color: T.text2}}>Another process to follow</div>
        <div style={{position: 'relative', height: 120, marginTop: 20}}>
          <div style={{position: 'absolute', left: 14, top: 14, height: 5, width: 660 * p, background: `linear-gradient(90deg, ${T.gold}, rgba(255,255,255,0.25))`, borderRadius: 3}} />
          <div style={{position: 'absolute', left: 0, top: 0, width: 32, height: 32, borderRadius: 16, background: T.gold}} />
          <div style={{position: 'absolute', left: 644, top: 0, width: 32, height: 32, borderRadius: 16, border: `4px dashed ${T.white}`, boxSizing: 'border-box', opacity: p}} />
          <div style={{position: 'absolute', left: 0, top: 46, fontFamily: SANS, fontWeight: 700, fontSize: 36, color: T.white}}>Filed · 9 Nov</div>
          <div style={{position: 'absolute', right: 20, top: 46, fontFamily: SANS, fontWeight: 700, fontSize: 36, color: T.text2, opacity: p}}>Outcome: unknown</div>
        </div>
      </Rv>
    </Shell>
  );
};

// ───────────────────────── 03 The price move ─────────────────────────
export const L12: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} chapter="The price move" kind="CONFIRMED" source="Close: Nasdaq regular session, 9 Nov 2026 (USD) · Market-value estimate: Reuters, 9 Nov 2026">
    <Rv at={cu(cues, 0)} style={abs(96, 150, 850)}>
      <Glass style={{padding: '38px 48px 44px', minHeight: 600}}>
        <div style={label}>NVDA · regular-session close</div>
        <div style={{fontFamily: SANS, fontSize: 40, fontWeight: 700, color: T.white, marginTop: 6}}>Monday 9 November 2026</div>
        <Rv at={cu(cues, 1)} style={{fontFamily: MONO, fontWeight: 600, fontSize: 176, color: T.white, letterSpacing: -8, lineHeight: 1.05, marginTop: 26}}>$178.67</Rv>
        <Rv at={cu(cues, 2)} style={{fontFamily: MONO, fontWeight: 600, fontSize: 128, color: T.red, letterSpacing: -5, lineHeight: 1.05}}>▼ 4.27%</Rv>
        <Rv at={cu(cues, 2) + 10} style={{fontFamily: SANS, fontSize: 32, color: T.text2, marginTop: 16}}>Down $7.97 from $186.64 (close, 6 Nov)</Rv>
      </Glass>
    </Rv>
    <Rv at={cu(cues, 3)} x={30} y={0} style={abs(1000, 150, 824)}>
      <Glass tone="gold" style={{padding: '30px 44px 34px'}}>
        <div style={label}>One-day market-value decline · Reuters</div>
        <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 150, color: T.gold, letterSpacing: -6, lineHeight: 1.05, marginTop: 4}}>≈ $190bn</div>
      </Glass>
    </Rv>
    <Rv at={cu(cues, 4)} x={30} y={0} style={abs(1000, 478, 824)}>
      <Glass style={{padding: '24px 40px'}}>
        <div style={label}>What that number is</div>
        <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 40, color: T.white, lineHeight: 1.2, marginTop: 8}}>
          Market value = share price × shares outstanding
        </div>
        <div style={{fontFamily: SANS, fontSize: 34, color: T.text2, marginTop: 6}}>A change in how the market values the shares.</div>
      </Glass>
    </Rv>
    <Not at={cu(cues, 5)} size={40} style={abs(1000, 790, 824)}>$190bn leaving Nvidia's cash balance</Not>
  </Shell>
);

const Chart: React.FC<{at: number; shade: number; w: number; h: number}> = ({at, shade, w, h}) => {
  const f = useCurrentFrame();
  const d = PX as [string, number][];
  const lo = 170;
  const hi = 245;
  const padL = 96;
  const padR = 200;
  const padT = 78;
  const padB = 46;
  const X = (i: number) => padL + ((w - padL - padR) * i) / (d.length - 1);
  const Y = (v: number) => padT + (h - padT - padB) * (1 - (v - lo) / (hi - lo));
  const t = lin(f, at, 70);
  const n = Math.max(1, Math.floor(t * (d.length - 1)));
  const pts = d.slice(0, n + 1).map(([, v], i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
  const idx = (dt: string) => d.findIndex(([x]) => x === dt);
  const marks: [string, string, string, number, number][] = [
    ['2026-10-06', '6 Oct', '$239.24', -10, -40],
    ['2026-10-29', '29 Oct · NYT report', '$213.66', 14, -44],
    ['2026-11-09', '9 Nov', '$178.67', 16, 6],
  ];
  const sh = prog(f, shade, 24);
  const i29 = idx('2026-10-29');
  return (
    <svg width={w} height={h}>
      {[180, 200, 220, 240].map((v) => (
        <g key={v}>
          <line x1={padL} x2={w - padR} y1={Y(v)} y2={Y(v)} stroke="rgba(255,255,255,0.16)" strokeWidth={1.5} />
          <text x={padL - 14} y={Y(v) + 9} textAnchor="end" fontFamily={MONO} fontSize={26} fill={T.text2}>${v}</text>
        </g>
      ))}
      <rect x={X(0)} y={padT} width={(X(i29) - X(0)) * sh} height={h - padT - padB} fill="rgba(255,255,255,0.075)" />
      <line x1={X(i29)} x2={X(i29)} y1={padT} y2={h - padB} stroke={T.gold} strokeWidth={2.5} strokeDasharray="8 8" opacity={sh} />
      <path d={pts} fill="none" stroke={T.white} strokeWidth={5} strokeLinejoin="round" strokeLinecap="round" />
      {marks.map(([dt, a, b, dx, dy]) => {
        const i = idx(dt);
        if (i > n) return null;
        const v = d[i][1];
        return (
          <g key={dt}>
            <circle cx={X(i)} cy={Y(v)} r={10} fill={dt === '2026-11-09' ? T.red : T.gold} stroke={T.bg} strokeWidth={3} />
            <text x={X(i) + dx} y={Y(v) + dy} fontFamily={MONO} fontWeight={600} fontSize={30} fill={T.white} textAnchor={dx < 0 ? 'middle' : 'start'}>{b}</text>
            <text x={X(i) + dx} y={Y(v) + dy + 30} fontFamily={SANS} fontSize={24} fill={T.text2} textAnchor={dx < 0 ? 'middle' : 'start'}>{a}</text>
          </g>
        );
      })}
      <text x={padL} y={h - 10} fontFamily={MONO} fontSize={24} fill={T.text2}>25 Sep 2026</text>
      <text x={w - padR} y={h - 10} fontFamily={MONO} fontSize={24} fill={T.text2} textAnchor="end">9 Nov 2026</text>
    </svg>
  );
};
export const L13: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const mv = prog(f, cu(cues, 2) - 6, 22);
  const top = 1 - 0.55 * mv;
  const br = prog(f, cu(cues, 1), 18);
  return (
    <Shell len={len} chapter="The price move" source="Lawsuit timing: Reuters, 9 Nov 2026 · NVDA daily closes, USD, 25 Sep–9 Nov 2026: Financial Modeling Prep">
      <Rv at={cu(cues, 0) + 20} style={{...abs(96, 560, 1728), opacity: undefined}}>
        <div style={{opacity: (1 - mv) * prog(f, cu(cues, 0) + 20, 18), fontFamily: SANS, fontWeight: 800, fontSize: 84, color: T.white, letterSpacing: -2.6, lineHeight: 1.08}}>
          Filed <span style={{color: T.gold}}>after</span> the close.
          <div style={{fontSize: 52, fontWeight: 600, color: T.text2, letterSpacing: -1, marginTop: 18, opacity: br}}>It cannot explain trading that had already happened.</div>
        </div>
      </Rv>
      <div style={{opacity: top, transform: `translateY(${150 * (1 - mv)}px)`}}>
        <Rv at={cu(cues, 0)} style={abs(96, 128, 1728)}>
          <div style={label}>Monday 9 Nov · US Eastern time</div>
          <div style={{position: 'relative', height: 150, marginTop: 16}}>
            <div style={{position: 'absolute', left: 0, top: 22, width: 1180, height: 34, borderRadius: 8, background: 'linear-gradient(90deg, rgba(255,255,255,0.3), rgba(255,255,255,0.16))', border: `1.5px solid ${T.edge}`}} />
            <div style={{position: 'absolute', left: 16, top: 24, fontFamily: MONO, fontSize: 24, color: T.white, fontWeight: 600}}>REGULAR SESSION</div>
            <div style={{position: 'absolute', left: 1180, top: 6, width: 4, height: 66, background: T.white}} />
            <div style={{position: 'absolute', left: 1100, top: 80, width: 164, textAlign: 'center', fontFamily: MONO, fontSize: 28, color: T.white, fontWeight: 600}}>16:00 close</div>
            <div style={{position: 'absolute', left: 1252, top: 20, width: 38, height: 38, borderRadius: 19, background: T.gold, boxShadow: '0 0 30px rgba(246,196,69,0.8)'}} />
            <div style={{position: 'absolute', left: 1310, top: 8, fontFamily: SANS, fontWeight: 800, fontSize: 40, color: T.white}}>Lawsuit filed</div>
            <div style={{position: 'absolute', left: 1310, top: 60, fontFamily: SANS, fontSize: 28, color: T.text2, width: 420, lineHeight: 1.2}}>Reuters: “five minutes after the US stock market closed”</div>
            <div style={{position: 'absolute', left: 0, top: 84, width: 1040, fontFamily: SANS, fontWeight: 700, fontSize: 34, color: T.lime, opacity: br}}>← this trading had already happened</div>
          </div>
        </Rv>
      </div>
      <Rv at={cu(cues, 2)} style={abs(96, 322, 1728)}>
        <Glass style={{padding: '18px 30px 10px'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline'}}>
            <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 40, color: T.white}}>NVDA daily close, US dollars</div>
            <div style={{fontFamily: SANS, fontSize: 26, color: T.text2}}>Past performance is not a guide to future returns</div>
          </div>
          <div style={{position: 'relative'}}>
            <Chart at={cu(cues, 2) + 8} shade={cu(cues, 3)} w={1668} h={486} />
            <Rv at={cu(cues, 3)} style={{position: 'absolute', left: 430, top: 330, width: 600}}>
              <div style={{display: 'inline-block', background: 'rgba(10,10,8,0.86)', border: `1.5px solid ${T.edge}`, borderRadius: 12, padding: '10px 20px', fontFamily: SANS, fontWeight: 700, fontSize: 32, color: T.white, lineHeight: 1.2}}>
                Already falling before 29 Oct
                <div style={{fontWeight: 500, fontSize: 26, color: T.text2}}>existing concerns about AI spending</div>
              </div>
            </Rv>
          </div>
        </Glass>
      </Rv>
      <Rv at={cu(cues, 4)} style={{...abs(96, 914, 1728), fontFamily: SANS, fontWeight: 700, fontSize: 40, color: T.white, textAlign: 'center'}}>
        One compelling headline <span style={{color: T.gold, fontFamily: MONO}}>≠</span> the cause of every earlier move
      </Rv>
    </Shell>
  );
};

export const L14: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} chapter="The price move" kind="ANALYSIS" source="AIFT analysis · educational commentary, not a personal recommendation">
    <Rv at={0} style={abs(96, 190, 1728)}>
      <Glass tone="gold" style={{padding: '50px 60px'}}>
        <div style={label}>What a price is</div>
        <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 92, color: T.white, letterSpacing: -3, lineHeight: 1.06, marginTop: 10}}>
          The price tells you what investors <Hl at={18}>paid</Hl>.
        </div>
      </Glass>
    </Rv>
    <Not at={cu(cues, 1)} size={56} style={abs(140, 610, 1640)}>whether the next price is higher or lower</Not>
    <Not at={cu(cues, 2)} size={56} style={abs(140, 760, 1640)}>whether the business offers good value</Not>
  </Shell>
);

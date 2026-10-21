import React from 'react';
import {evolvePath} from '@remotion/paths';
import {makeCircle} from '@remotion/shapes';
import {A, C, F, Glass, Rv, Eyebrow, Odo, Win, Grp, Src, QHead, BarRows, useT, pr, eo, sp, clamp} from './ui';

/* ================= COLD OPEN ================= */
const Sigil: React.FC<{t: number}> = ({t}) => {
  const c1 = makeCircle({radius: 262}), c2 = makeCircle({radius: 222});
  const e1 = evolvePath(eo(pr(t, 0.1, 2.6)), c1.path), e2 = evolvePath(eo(pr(t, 0.5, 2.6)), c2.path);
  const hex = Array.from({length: 6}, (_, i) => {
    const a = (i * 60 - 90) * (Math.PI / 180);
    return [500 + Math.cos(a) * 190, 500 + Math.sin(a) * 190];
  });
  const hexPath = 'M' + hex.map((p) => p.join(',')).join(' L') + ' Z';
  const eh = evolvePath(eo(pr(t, 1.0, 2.4)), hexPath);
  return (
    <svg width={1000} height={1000} style={{position: 'absolute', left: 460, top: -105, overflow: 'visible'}}>
      <g transform="translate(238 238)"><path d={c1.path} fill="none" stroke={C.gold} strokeWidth={5} strokeDasharray={e1.strokeDasharray} strokeDashoffset={e1.strokeDashoffset} style={{filter: 'drop-shadow(0 0 14px rgba(242,184,75,.6))'}} /></g>
      <g transform="translate(278 278)"><path d={c2.path} fill="none" stroke={C.teal} strokeWidth={3} strokeDasharray={e2.strokeDasharray} strokeDashoffset={e2.strokeDashoffset} /></g>
      <path d={hexPath} fill="none" stroke="rgba(160,190,255,.45)" strokeWidth={2} strokeDasharray={eh.strokeDasharray} strokeDashoffset={eh.strokeDashoffset} />
      <circle cx={500} cy={500} r={288} fill="none" stroke="rgba(160,190,255,.5)" strokeWidth={2} strokeDasharray="3 21" strokeDashoffset={-t * 14} opacity={eo(pr(t, 0.3, 1.2)) * 0.9} />
      {hex.map((p, i) => <line key={i} x1={500} y1={500} x2={p[0]} y2={p[1]} stroke="rgba(45,212,191,.25)" strokeWidth={1.5} opacity={eo(pr(t, 1.6 + i * 0.1, 0.6))} />)}
    </svg>
  );
};

export const Cold: React.FC = () => {
  const {t, fps} = useT();
  const cos: [string, string, number][] = [['Amazon', '~$220bn', A.amazon], ['Alphabet', '$195–205bn', A.alphabet], ['Microsoft', '~$175bn*', A.microsoft], ['Meta', '$130–145bn', A.meta]];
  const qs: [string, string, string][] = [['1', 'Orders', 'Is spending turning into orders?'], ['2', 'Chips', 'Can the chips be built?'], ['3', 'Power', 'Do the buildings have power?'], ['4', 'Equipment', 'Is equipment keeping up?'], ['5', 'Payback', 'Is AI paying for itself?']];
  const val = 700 * eo(pr(t, 0.15, 2.4));
  const chipS = sp(t, A.eighty1, fps, 14, 140);
  return (
    <Win a={0} b={A.q1}>
      <Grp a={-1} b={A.fiveq}>
        <Sigil t={t} />
        <div style={{position: 'absolute', left: 0, right: 0, top: 292, display: 'flex', justifyContent: 'center'}}><Odo value={val} places={3} size={220} prefix="$" suffix="bn+" /></div>
        <div style={{position: 'absolute', left: 560, width: 800, top: 514, textAlign: 'center', font: `400 30px ${F.body}`, color: C.muted, padding: '6px 0', borderRadius: 16, background: 'rgba(7,11,20,.8)', opacity: eo(pr(t, 1.2, 0.6))}}>planned AI infrastructure spending in 2026 · four companies</div>
        <div style={{position: 'absolute', left: 740, top: 578, width: 440, height: 58, borderRadius: 29, border: '2px solid rgba(91,214,154,.75)', background: '#0b1a1a', color: C.ok, display: 'flex', alignItems: 'center', justifyContent: 'center', font: `700 30px ${F.body}`, opacity: clamp(chipS * 1.6), transform: `scale(${0.85 + 0.15 * chipS})`, boxShadow: `0 0 ${30 * (1 - pr(t, A.eighty1, 1))}px ${C.ok}`}}>▲ +79% on a year ago</div>
        {cos.map((c, i) => (
          <Glass key={i} x={105 + i * 435} y={668} w={405} h={190} t0={c[2]} kind="tilt" pad={24} hot={C.gold}>
            <div style={{font: `800 38px ${F.disp}`}}>{c[0]}</div>
            <div style={{font: `500 54px ${F.mono}`, color: C.gold, marginTop: 8}}>{c[1]}</div>
            <div style={{font: `400 24px ${F.body}`, color: C.muted, marginTop: 6}}>2026 capex guide · Q2 results</div>
          </Glass>
        ))}
        <Src text="*Microsoft: reported figure after a lease reclassification; the company says its underlying plan is unchanged. Guides per latest company results." />
      </Grp>
      <Grp a={A.fiveq} b={A.q1}>
        <div style={{position: 'absolute', left: 0, right: 0, top: 205, textAlign: 'center', font: `800 170px/1 ${F.disp}`, letterSpacing: '-0.02em', display: 'flex', justifyContent: 'center', gap: 40}}>
          {['FIVE', 'QUESTIONS'].map((w, i) => { const s = sp(t, A.fiveq + i * 0.18, fps, 16, 120); return <span key={i} style={{opacity: clamp(s * 1.6), transform: `translateY(${(1 - s) * 70}px) scale(${0.94 + 0.06 * s})`, textShadow: '0 0 60px rgba(231,236,246,.25)'}}>{w}</span>; })}
        </div>
        <div style={{position: 'absolute', left: 0, right: 0, top: 410, textAlign: 'center', font: `400 38px ${F.body}`, color: C.muted, opacity: eo(pr(t, A.fiveq + 0.6, 0.6))}}>you can check every quarter</div>
        {qs.map((q, i) => (
          <Glass key={i} x={106 + i * 342} y={520} w={320} h={300} t0={A.fiveq + 0.7 + i * 0.3} kind="tilt" pad={26}>
            <div style={{font: `500 62px ${F.mono}`, color: C.teal}}>{q[0]}</div>
            <div style={{font: `800 46px ${F.disp}`, marginTop: 6}}>{q[1]}</div>
            <div style={{font: `400 27px/1.25 ${F.body}`, color: C.muted, marginTop: 12}}>{q[2]}</div>
          </Glass>
        ))}
      </Grp>
    </Win>
  );
};

/* ================= Q1 · ORDERS ================= */
export const Q1: React.FC = () => {
  const {t, fps} = useT();
  const lx = 140 + 590 + (1640 - 590) * (79 / 250);
  const lineP = eo(pr(t, A.q1_capex + 0.3, 0.6));
  const fl: [string, string, number][] = [['THE SPENDERS', 'capex budgets', A.q1 + 3.0], ['CHIP ORDERS', 'what they buy', A.q1 + 4.6], ["SOMEONE ELSE'S REVENUE", 'what suppliers earn', A.q1_right - 1.6]];
  return (
    <Win a={A.q1} b={A.q2}>
      <QHead n={1} label="ORDERS" q="Is the spending turning into orders?" skey="ok" stext="Orders are keeping pace" st={A.q1_pace} a={A.q1} />
      <Glass x={96} y={340} w={1728} h={500} t0={A.q1 + 0.9} kind="up" />
      <Grp a={A.q1 + 1.0} b={A.q1_chip - 0.2}>
        {fl.map((f, i) => (
          <React.Fragment key={i}>
            <Glass x={140 + i * 580} y={420} w={480} h={220} t0={f[2]} kind="left" pad={26} dark={0.35}>
              <Eyebrow color={C.teal}>{f[0]}</Eyebrow>
              <div style={{font: `800 56px/1.05 ${F.disp}`, marginTop: 18}}>{f[1]}</div>
            </Glass>
            {i < 2 && <Rv x={140 + i * 580 + 485} y={508} w={90} t0={f[2] + 0.5} dx={-20} dy={0} style={{font: `800 64px ${F.disp}`, color: C.gold, textAlign: 'center'}}>→</Rv>}
          </React.Fragment>
        ))}
        <Rv x={140} y={690} w={1540} h={80} t0={A.q1_right} dy={20} style={{borderRadius: 40, border: '2px solid rgba(91,214,154,.6)', background: 'rgba(91,214,154,.16)', color: C.ok, display: 'flex', alignItems: 'center', justifyContent: 'center', font: `700 38px ${F.body}`}}>✓ Right now it is</Rv>
      </Grp>
      <Grp a={A.q1_chip - 0.3} b={A.q2}>
        <BarRows x={140} y={376} w={1640} rowH={74} gap={28} max={250} labW={590} lf={27} vf={44} t0s={[A.q1_chip, A.q1_chip + 0.5, A.q1_chip + 1.0, A.q1_capex]}
          rows={[{label: 'GPU leader · data-centre revenue', val: 117, color: C.teal}, {label: 'GPU challenger · data-centre revenue', val: 107, color: C.teal}, {label: 'Custom-chip & networking leader · AI revenue', val: 221, color: C.teal}, {label: 'The four spenders · capex growth', val: 79, color: C.gold}]} />
        <div style={{position: 'absolute', left: lx, top: 360, width: 0, height: 410 * lineP, borderLeft: `4px dashed ${C.gold}`, opacity: lineP}} />
        <Rv x={140} y={772} w={1640} h={56} t0={A.q1_pace} dy={16} style={{borderRadius: 28, background: 'rgba(91,214,154,.16)', border: '2px solid rgba(91,214,154,.6)', color: C.ok, display: 'flex', alignItems: 'center', justifyContent: 'center', font: `700 30px ${F.body}`}}>Orders are keeping pace with the cheques · for now the picks-and-shovels case holds</Rv>
      </Grp>
      <Src text="Source: company results via AIFT tracker (9 Oct 2026). Latest quarter, year on year. Dashed line = big-four capex growth, Q2 2026 vs Q2 2025." />
    </Win>
  );
};

/* ================= Q2 · CHIPS ================= */
export const Q2: React.FC = () => {
  const {t} = useT();
  const n = Math.floor(clamp((t - A.q2_but) / 1.1, 0, 99));
  return (
    <Win a={A.q2} b={A.q3}>
      <QHead n={2} label="CHIPS" q="Can the chips actually be built?" skey="warn" stext="Yes, but tightly" st={A.q2_yes} a={A.q2} />
      <Glass x={96} y={340} w={846} h={270} t0={A.q2_mem} kind="tilt" hot={C.gold}>
        <Eyebrow>MEMORY (HBM)</Eyebrow>
        <div style={{font: `800 92px ${F.disp}`, color: C.gold, marginTop: 8}}>SOLD OUT</div>
        <div style={{font: `400 28px ${F.body}`, color: C.muted, marginTop: 6}}>this year · my tracker shows it <b style={{color: C.fg}}>booked into 2027</b></div>
      </Glass>
      <Glass x={978} y={340} w={846} h={270} t0={A.q2_pack} kind="tilt" hot={C.gold}>
        <Eyebrow>ADVANCED PACKAGING</Eyebrow>
        <div style={{font: `800 92px ${F.disp}`, color: C.gold, marginTop: 8}}>SOLD OUT</div>
        <div style={{font: `400 28px ${F.body}`, color: C.muted, marginTop: 6}}>the step that <b style={{color: C.fg}}>joins the chips together</b></div>
      </Glass>
      <Rv x={96} y={636} w={1728} h={62} t0={A.q2_short} dy={16} style={{borderRadius: 31, border: '2px solid rgba(91,214,154,.6)', background: 'rgba(91,214,154,.14)', color: C.ok, display: 'flex', alignItems: 'center', justifyContent: 'center', font: `700 30px ${F.body}`}}>A shortage helps the suppliers’ pricing ▲</Rv>
      <Glass x={96} y={722} w={1728} h={122} t0={A.q2_but} kind="up" pad={0}>
        <div style={{position: 'absolute', left: 30, top: 16, font: `400 26px ${F.body}`, color: C.muted}}>…but projects wait in a queue</div>
        {Array.from({length: 18}).map((_, i) => {
          const on = i < 3 + n && i < 8;
          return <div key={i} style={{position: 'absolute', left: 30 + i * 92, top: 58, width: 72, height: 44, borderRadius: 10, border: `2px solid ${on ? C.ok : i < 12 ? 'rgba(242,184,75,.5)' : 'rgba(150,180,240,.3)'}`, background: on ? 'rgba(91,214,154,.6)' : 'transparent', boxShadow: on ? '0 0 16px rgba(91,214,154,.5)' : 'none'}} />;
        })}
      </Glass>
      <Src text="Source: company commentary (memory and packaging sold out this year); 2027 memory booking from AIFT tracker, single source." />
    </Win>
  );
};

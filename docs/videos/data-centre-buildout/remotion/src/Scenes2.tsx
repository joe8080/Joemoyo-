import React from 'react';
import {A, C, F, Glass, Rv, Eyebrow, Win, Grp, Src, QHead, Ring, useT, pr, eo, sp, clamp} from './ui';
import {Globe} from './Globe';

/* ================= Q3 · POWER ================= */
export const Q3: React.FC = () => {
  const {t, fps} = useT();
  const pPlan = eo(pr(t, A.q3_plan, 1.2)), pOp = eo(pr(t, A.q3_op, 1.0));
  const ring = 0.302 * eo(pr(t, A.q3_30, 1.2));
  const partial = eo(pr(t, A.q3_partial, 1.2));
  const baseI = A.q3_iea;
  const pa = eo(pr(t, baseI + 0.3, 1.0)), pb = eo(pr(t, baseI + 1.2, 1.1));
  const base = 725, maxH = 250;
  const hA = (maxH * 415 / 945) * pa, hB = maxH * pb;
  const uk = Array.from({length: 5});
  return (
    <Win a={A.q3} b={A.q4}>
      <Grp a={A.q3_track} b={A.q3_slip}><Globe a={A.q3_track} b={A.q3_slip} /></Grp>
      <QHead n={3} label="POWER" q="Do the buildings have power?" skey="alert" stext="Power is the bottleneck" st={A.q3_30} a={A.q3} />

      {/* A · globe with the real 106 sites + the numbers */}
      <Grp a={A.q3_track} b={A.q3_slip}>
        <Glass x={1010} y={340} w={814} h={318} t0={A.q3_track} kind="tilt" pad={0}>
          <div style={{position: 'absolute', left: 28, top: 22, display: 'flex', alignItems: 'center', gap: 28}}>
            <div style={{font: `800 120px/1 ${F.disp}`, color: C.teal, textShadow: '0 0 40px rgba(45,212,191,.35)'}}>106</div>
            <div style={{font: `400 30px/1.2 ${F.body}`, color: C.muted, width: 380}}>AI data-centre sites I track</div>
          </div>
          <Eyebrow style={{position: 'absolute', left: 28, top: 150, opacity: pPlan}}>PLANNED</Eyebrow>
          <div style={{position: 'absolute', left: 28, top: 180, width: 758, height: 54, borderRadius: 12, background: 'rgba(150,180,240,.08)', opacity: pPlan > 0.02 ? 1 : 0}}>
            <div style={{height: '100%', width: 758 * pPlan, borderRadius: 12, background: 'linear-gradient(90deg,#f2b84bcc,#f2b84b)', boxShadow: '0 0 26px rgba(242,184,75,.5)', display: 'flex', alignItems: 'center', paddingLeft: 18, font: `500 36px ${F.mono}`, color: '#1a1305', overflow: 'hidden', whiteSpace: 'nowrap'}}>{pPlan > 0.5 ? '77 GW' : ''}</div>
          </div>
          <Eyebrow style={{position: 'absolute', left: 28, top: 236, opacity: pOp}}>RUNNING TODAY</Eyebrow>
          <div style={{position: 'absolute', left: 28, top: 280, width: 758, height: 24, borderRadius: 8, background: 'rgba(150,180,240,.08)', opacity: pOp > 0.02 ? 1 : 0}}>
            <div style={{height: '100%', width: 758 * (7.826 / 77.345) * pOp, borderRadius: 8, background: C.teal, boxShadow: '0 0 20px rgba(45,212,191,.6)'}} />
            <div style={{position: 'absolute', left: 758 * (7.826 / 77.345) * pOp + 14, top: -6, font: `500 34px ${F.mono}`, opacity: pOp > 0.5 ? 1 : 0, whiteSpace: 'nowrap'}}>8 GW <span style={{font: `400 24px ${F.body}`, color: C.muted}}>· about 10%</span></div>
          </div>
        </Glass>
        <Glass x={1010} y={684} w={814} h={160} t0={A.q3_30 - 0.3} kind="tilt" pad={0} hot={C.alert}>
          <Ring cx={104} cy={80} r={52} sw={14} frac={ring} color={C.alert} />
          <Ring cx={104} cy={80} r={70} sw={5} frac={0.82 * partial} color={C.gold} track="rgba(0,0,0,0)" />
          <div style={{position: 'absolute', left: 54, top: 58, width: 100, textAlign: 'center', font: `800 36px ${F.disp}`, color: C.alert}}>{ring > 0.01 ? '30%' : ''}</div>
          <div style={{position: 'absolute', left: 216, top: 14, width: 575, font: `400 26px/1.22 ${F.body}`, color: C.muted}}>of capacity due in the next 12 months has <b style={{color: C.fg}}>documented, secured power</b></div>
          <div style={{position: 'absolute', left: 216, top: 94, width: 575, font: `700 22px/1.17 ${F.body}`, color: C.gold, opacity: partial}}>Count partial deals too: ~18% still has nothing on paper</div>
        </Glass>
        <Src text="Source: AIFT site register, 106 sites, 9 Oct 2026 (US-heavy tracker, not a census). Pillars: planned MW (gold), running MW (teal). 30% = 1,688 of 5,598 MW due within 12 months." />
      </Grp>

      {/* B · slippage, UK, car park */}
      <Grp a={A.q3_slip} b={A.q3_iea}>
        <Glass x={96} y={340} w={552} h={262} t0={A.q3_slip} kind="tilt" hot={C.alert}>
          <Eyebrow>5 GW CAMPUS</Eyebrow>
          <div style={{font: `500 56px ${F.mono}`, color: C.alert, marginTop: 14}}>2028 → ~2030</div>
          <div style={{font: `400 28px ${F.body}`, color: C.muted, marginTop: 12}}>first stage pushed back <b style={{color: C.fg}}>about 2 years</b></div>
        </Glass>
        <Glass x={684} y={340} w={552} h={262} t0={A.q3_seven} kind="tilt" hot={C.alert}>
          <Eyebrow>ANOTHER CAMPUS</Eyebrow>
          <div style={{font: `500 56px ${F.mono}`, color: C.alert, marginTop: 14}}>~7 months</div>
          <div style={{font: `400 28px ${F.body}`, color: C.muted, marginTop: 12}}>behind · <b style={{color: C.fg}}>gas pipeline refused</b></div>
        </Glass>
        <Glass x={1272} y={340} w={552} h={262} t0={A.q3_uk} kind="tilt">
          <Eyebrow>THE UK</Eyebrow>
          <div style={{font: `500 40px ${F.mono}`, marginTop: 14}}>5 sites · ~670 MW</div>
          <div style={{font: `400 28px ${F.body}`, color: C.muted, marginTop: 8}}>on paper · <b style={{color: C.alert}}>0 running yet</b></div>
          <div style={{marginTop: 16, display: 'flex', gap: 10}}>{uk.map((_, i) => <div key={i} style={{width: 40, height: 40, borderRadius: 8, border: `3px solid ${C.muted}`, opacity: clamp(sp(t, A.q3_uk + 0.3 + i * 0.12, fps) * 1.6)}} />)}</div>
        </Glass>
        <Glass x={96} y={636} w={1728} h={200} t0={A.q3_bldg} kind="up" hot={C.gold} pad={20}>
          <div style={{display: 'flex', alignItems: 'center', gap: 36, height: '100%'}}>
            <div style={{font: `800 150px/1 ${F.disp}`, color: '#4a5675', border: '6px solid #4a5675', borderRadius: 28, width: 170, height: 170, display: 'grid', placeItems: 'center'}}>P</div>
            <div style={{font: `800 60px/1.1 ${F.disp}`}}>A building without power<br /><span style={{color: C.gold}}>is a very expensive car park.</span></div>
          </div>
        </Glass>
        <Src text="Source: AIFT site register, 9 Oct 2026 (UK: 5 tracked sites, none with capacity operating). Slippage per latest reporting." />
      </Grp>

      {/* C · IEA */}
      <Grp a={A.q3_iea} b={A.q4}>
        <Glass x={96} y={340} w={880} h={500} t0={A.q3_iea} kind="tilt" pad={0}>
          <Eyebrow style={{position: 'absolute', left: 44, top: 22}}>DATA-CENTRE ELECTRICITY USE · IEA</Eyebrow>
          <div style={{position: 'absolute', left: 94, top: base - 340 - hA, width: 200, height: hA, borderRadius: '10px 10px 0 0', background: 'linear-gradient(180deg,#7fb6ff,#3b82f6)', boxShadow: '0 0 30px rgba(96,165,250,.45)'}} />
          <div style={{position: 'absolute', left: 424, top: base - 340 - hB, width: 200, height: hB, borderRadius: '10px 10px 0 0', background: 'linear-gradient(180deg,#ffd27a,#f2b84b)', boxShadow: '0 0 34px rgba(242,184,75,.5)'}} />
          <div style={{position: 'absolute', left: 64, width: 260, textAlign: 'center', top: base - 340 - hA - 60, font: `500 38px ${F.mono}`, opacity: pa > 0.5 ? 1 : 0}}>415 TWh</div>
          <div style={{position: 'absolute', left: 394, width: 260, textAlign: 'center', top: base - 340 - hB - 60, font: `500 38px ${F.mono}`, color: C.gold, opacity: pb > 0.5 ? 1 : 0}}>≈945 TWh</div>
          <div style={{position: 'absolute', left: 54, width: 280, textAlign: 'center', top: base - 340 + 10, font: `400 25px/1.25 ${F.body}`, color: C.muted, opacity: pa}}>2024<br />≈1.5% of world power</div>
          <div style={{position: 'absolute', left: 384, width: 280, textAlign: 'center', top: base - 340 + 10, font: `400 25px/1.25 ${F.body}`, color: C.muted, opacity: pb}}>2030<br />≈3% of world power</div>
          <div style={{position: 'absolute', left: 322, top: base - 340 - maxH * 0.74, font: `800 44px ${F.disp}`, opacity: pr(t, baseI + 2.2, 0.5)}}>×2.3</div>
        </Glass>
        <Glass x={1010} y={340} w={814} h={400} t0={A.q3_fifth - 1.6} kind="tilt" hot={C.alert}>
          <Eyebrow>PLANNED SITES</Eyebrow>
          <div style={{font: `800 150px/1 ${F.disp}`, color: C.alert, marginTop: 8, textShadow: '0 0 40px rgba(240,113,107,.35)'}}>1 in 5</div>
          <div style={{font: `400 30px ${F.body}`, color: C.muted, marginTop: 8}}>could face <b style={{color: C.fg}}>grid delays</b> (IEA)</div>
          <div style={{display: 'flex', gap: 28, marginTop: 40}}>{[0, 1, 2, 3, 4].map((i) => { const hot = i === 0 && t >= A.q3_fifth; return <div key={i} style={{width: 110, height: 90, borderRadius: 14, border: `3px solid ${hot ? C.alert : C.muted}`, background: hot ? C.alert : 'transparent', boxShadow: hot ? '0 0 30px rgba(240,113,107,.6)' : 'none', opacity: clamp(sp(t, A.q3_fifth - 1.4 + i * 0.1, fps) * 1.6)}} />; })}</div>
        </Glass>
        <Glass x={1010} y={764} w={814} h={76} t0={A.q3_iea + 0.6} kind="right" pad={0} dark={0.3}>
          <div style={{display: 'flex', alignItems: 'center', gap: 18, height: '100%', padding: '0 24px', font: `400 24px ${F.body}`}}>
            <div style={{width: 40, height: 48, borderRadius: 6, border: `2px solid ${C.teal}`, display: 'grid', placeItems: 'center', color: C.teal, font: `700 18px ${F.mono}`}}>PDF</div>
            <div><b>IEA · Energy and AI</b> <span style={{color: C.muted}}>· April 2025 · central case</span></div>
          </div>
        </Glass>
        <Src text="Source: IEA, Energy and AI (April 2025). Central case; a newer edition may differ." />
      </Grp>
    </Win>
  );
};

/* ================= Q4 · EQUIPMENT ================= */
export const Q4: React.FC = () => {
  const {t} = useT();
  const ax0 = 150, axw = 792, y = 620;
  const xOf = (v: number) => ax0 + axw * ((v - 0.8) / 0.8);
  const band = eo(pr(t, A.q4_12, 0.9));
  const lead = eo(pr(t, A.q4_lead, 1.6));
  const len = 700;
  return (
    <Win a={A.q4} b={A.q5}>
      <QHead n={4} label="EQUIPMENT" q="Is the electrical and cooling equipment keeping up?" skey="ok" stext="Demand is ahead of supply" st={A.q4_ahead} a={A.q4} />
      {['Transformers', 'Switchgear', 'Chillers', 'Backup power'].map((n, i) => (
        <Rv key={i} x={96 + i * 262} y={336} w={246} h={60} t0={A.q4 + 1.2 + i * 0.3} style={{borderRadius: 30, border: '2px solid rgba(190,210,255,.4)', background: 'rgba(13,19,34,.55)', backdropFilter: 'blur(14px)', display: 'flex', alignItems: 'center', justifyContent: 'center', font: `700 27px ${F.body}`}}>{n}</Rv>
      ))}
      <Glass x={96} y={420} w={900} h={350} t0={A.q4 + 0.5} kind="tilt">
        <Eyebrow>ORDERS ÷ SALES (BOOK-TO-BILL)</Eyebrow>
      </Glass>
      <Grp a={A.q4 + 0.6} b={A.q5}>
        <div style={{position: 'absolute', left: ax0, top: y, width: axw, height: 46, borderRadius: 12, background: 'rgba(150,180,240,.1)'}} />
        <div style={{position: 'absolute', left: xOf(1.2), top: y, width: (xOf(1.6) - xOf(1.2)) * band, height: 46, borderRadius: 12, background: 'linear-gradient(90deg,rgba(91,214,154,.85),rgba(91,214,154,.4))', boxShadow: '0 0 30px rgba(91,214,154,.4)'}} />
        {([[1.0, '1.0', 'orders = sales', C.muted], [1.2, '1.2', '', C.ok]] as [number, string, string, string][]).map(([v, l, s, col]) => (
          <React.Fragment key={l}>
            <div style={{position: 'absolute', left: xOf(v) - 2, top: y - 14, width: 4, height: 74, background: col}} />
            <div style={{position: 'absolute', left: xOf(v) - 90, width: 180, textAlign: 'center', top: y + 66, font: `500 28px ${F.mono}`, color: col}}>{l}{s && <><br /><span style={{font: `400 22px ${F.body}`}}>{s}</span></>}</div>
          </React.Fragment>
        ))}
        <Rv x={xOf(1.2)} y={y - 70} w={xOf(1.6) - xOf(1.2)} t0={A.q4_12} dy={14} style={{textAlign: 'center', font: `700 29px ${F.body}`, color: C.ok}}>every maker reporting: above 1.2</Rv>
      </Grp>
      <Glass x={1020} y={420} w={804} h={350} t0={A.q4_lead - 0.6} kind="tilt" pad={0}>
        <Eyebrow style={{position: 'absolute', left: 28, top: 28}}>LEAD TIMES</Eyebrow>
        <svg width={804} height={350} style={{position: 'absolute', left: 0, top: 0}}>
          <polyline points="70,290 200,262 330,230 460,190 590,150 740,96" fill="none" stroke={C.gold} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - lead)} style={{filter: 'drop-shadow(0 0 10px rgba(242,184,75,.6))'}} />
        </svg>
        <Rv x={400} y={278} w={380} t0={A.q4_lead + 0.6} dy={10} style={{textAlign: 'right', font: `700 28px ${F.body}`, color: C.gold}}>still getting longer</Rv>
      </Glass>
      <Rv x={96} y={792} w={1728} h={66} t0={A.q4_watch} dy={18} style={{borderRadius: 33, border: '2px solid rgba(242,184,75,.6)', background: 'rgba(242,184,75,.14)', color: C.gold, display: 'flex', alignItems: 'center', justifyContent: 'center', font: `700 30px ${F.body}`}}>WATCH: any maker whose orders go quiet · usually the first crack</Rv>
      <Src text="Source: AIFT tracker, equipment makers reporting book-to-bill (9 Oct 2026)." />
    </Win>
  );
};

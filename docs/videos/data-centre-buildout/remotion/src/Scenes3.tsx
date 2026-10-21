import React from 'react';
import {A, C, F, STATUS, Glass, Rv, Eyebrow, Win, Grp, Src, QHead, Ring, useT, pr, eo, sp, clamp} from './ui';

/* ================= Q5 · PAYBACK ================= */
export const Q5: React.FC = () => {
  const {t, fps} = useT();
  const base = 770, sc = 3.9, xs = [190, 520, 850];
  const defs: [string, number, string, number, string][] = [['Amazon cloud', 36.7, C.teal, A.q5_40, '+37%'], ['Microsoft cloud', 43, C.teal, A.q5_40 + 0.5, '+43%'], ['Google Cloud', 82, C.blue, A.q5_google, '+82%']];
  const cy = base - 79 * sc;
  const capP = eo(pr(t, A.q5_capex, 0.6));
  const px = [1284, 1464, 1644], py = 688;
  const ok = pr(t, A.q5_circ + 0.3, 0.5);
  const k = ((t - A.q5_circ) * 0.55) % 1;
  const x0 = px[0] + 75, x1 = px[2] + 75;
  const dot = k < 0.5 ? [x0 + (x1 - x0) * (k / 0.5), py + 25] : [x1 - (x1 - x0) * ((k - 0.5) / 0.5), py + 86];
  const tiles: [string, string, string, number, number, number][] = [['BONDS ISSUED', '~$194bn', 'Amazon, Alphabet, Meta, Oracle · 2026 to early July', A.q5_bonds, 660, 340], ['FREE CASH FLOW', '~$0.8bn', 'Meta, latest quarter', A.q5_meta, 1254, 340], ['OFF-BALANCE-SHEET', '$14bn', 'campus moved into an 80/20 joint venture', A.q5_jv, 660, 600]];
  const stamp = sp(t, A.q5_promise - 0.2, fps, 12, 180);
  return (
    <Win a={A.q5} b={A.map}>
      <QHead n={5} label="PAYBACK" q="Is AI paying for itself?" skey="warn" stext="Not yet" st={A.q5_notyet} a={A.q5} />
      <Grp a={A.q5 + 0.8} b={A.q5_40 - 0.1}>
        <Glass x={96} y={380} w={780} h={360} t0={A.q5 + 1.2} kind="left" hot={C.gold}>
          <Eyebrow color={C.gold}>WHAT AI COSTS</Eyebrow>
          <div style={{font: `800 80px/1 ${F.disp}`, marginTop: 22}}>Capex</div>
          <div style={{font: `400 30px ${F.body}`, color: C.muted, marginTop: 16}}>the spending on buildings, chips and power</div>
        </Glass>
        <Glass x={1044} y={380} w={780} h={360} t0={A.q5 + 2.6} kind="right" hot={C.teal}>
          <Eyebrow color={C.teal}>WHAT AI EARNS</Eyebrow>
          <div style={{font: `800 80px/1 ${F.disp}`, marginTop: 22}}>Cloud revenue</div>
          <div style={{font: `400 30px ${F.body}`, color: C.muted, marginTop: 16}}>what customers pay for the capacity</div>
        </Glass>
        <Rv x={900} y={520} w={120} t0={A.q5 + 2.2} style={{textAlign: 'center', font: `800 64px ${F.disp}`, color: C.muted}}>vs</Rv>
        <Rv x={560} y={770} w={800} h={76} t0={A.q5_notyet} dy={16} scale={0.9} style={{borderRadius: 38, border: `3px solid ${C.gold}`, background: 'rgba(242,184,75,.16)', color: C.gold, display: 'flex', alignItems: 'center', justifyContent: 'center', font: `800 44px ${F.disp}`}}>Paying for itself? NOT YET</Rv>
      </Grp>

      <Grp a={A.q5_40 - 0.7} b={A.q5_backlog}>
        <Glass x={96} y={340} w={1180} h={500} t0={A.q5_40 - 0.6} kind="tilt"><Eyebrow>LATEST REPORTED GROWTH, YEAR ON YEAR</Eyebrow></Glass>
        {defs.map((d, i) => {
          const p = eo(pr(t, d[3], 1.1));
          const h = d[1] * sc * p;
          return (
            <React.Fragment key={i}>
              <div style={{position: 'absolute', left: xs[i], top: base - h, width: 220, height: h, borderRadius: '12px 12px 0 0', background: `linear-gradient(180deg, ${d[2]}, ${d[2]}aa)`, boxShadow: `0 0 36px ${d[2]}66, inset 0 3px 0 rgba(255,255,255,.35)`}} />
              <div style={{position: 'absolute', left: xs[i], width: 220, textAlign: 'center', top: base - h - 62, font: `500 46px ${F.mono}`, opacity: p > 0.5 ? 1 : 0}}>{d[4]}</div>
              <Rv x={xs[i] - 30} y={base + 10} w={280} t0={A.q5_40 - 0.4 + i * 0.2} dy={10} style={{textAlign: 'center', font: `400 27px ${F.body}`, color: C.muted}}>{d[0]}</Rv>
            </React.Fragment>
          );
        })}
        <div style={{position: 'absolute', left: 150, top: cy, width: 1060 * capP, height: 0, borderTop: `5px dashed ${C.gold}`, opacity: capP}} />
        <Rv x={150} y={cy - 46} w={600} t0={A.q5_capex + 0.2} dy={10} style={{font: `700 30px ${F.body}`, color: C.gold}}>capex growth +79%</Rv>
        <Glass x={1316} y={340} w={508} h={500} t0={A.q5_capex + 0.5} kind="right" hot={C.alert}>
          <Eyebrow>THE GAP</Eyebrow>
          <div style={{font: `800 100px/1 ${F.disp}`, color: C.alert, marginTop: 14}}>~40 pts</div>
          <div style={{font: `400 28px/1.25 ${F.body}`, color: C.muted, marginTop: 14}}>capex <b style={{color: C.gold}}>+79%</b> vs the two biggest clouds <b style={{color: C.teal}}>~+40%</b></div>
          <div style={{font: `400 26px/1.25 ${F.body}`, color: C.muted, marginTop: 14}}>Google’s cloud is growing faster, but it is smaller.</div>
        </Glass>
        <Src text="Cloud: latest quarter (AWS +36.7%, Azure ~+43%, Google Cloud +82%). Capex: Amazon, Alphabet, Microsoft, Meta, Q2 2026 vs Q2 2025." />
      </Grp>

      <Grp a={A.q5_backlog - 0.1} b={A.map}>
        <Glass x={96} y={340} w={520} h={240} t0={A.q5_backlog} kind="tilt"><Eyebrow>AMAZON · ORDER BACKLOG</Eyebrow><div style={{font: `500 86px ${F.mono}`, marginTop: 18}}>$496bn</div></Glass>
        <Glass x={96} y={600} w={520} h={240} t0={A.q5_backlog + 0.5} kind="tilt"><Eyebrow>GOOGLE CLOUD · BACKLOG</Eyebrow><div style={{font: `500 86px ${F.mono}`, marginTop: 18}}>$514bn</div></Glass>
        <div style={{position: 'absolute', left: 66, top: 520, width: 580, height: 96, border: `6px solid ${C.gold}`, borderRadius: 18, background: 'rgba(7,11,20,.92)', color: C.gold, display: 'flex', alignItems: 'center', justifyContent: 'center', font: `800 44px ${F.disp}`, transform: `rotate(-5deg) scale(${0.7 + 0.3 * stamp})`, opacity: clamp(stamp * 2), boxShadow: `0 0 ${50 * (1 - pr(t, A.q5_promise, 1))}px ${C.gold}`}}>A PROMISE, NOT CASH</div>
        {tiles.map((d, i) => (
          <Glass key={i} x={d[4]} y={d[5]} w={570} h={240} t0={d[3]} kind="tilt">
            <Eyebrow>{d[0]}</Eyebrow>
            <div style={{font: `500 78px ${F.mono}`, color: C.gold, marginTop: 14}}>{d[1]}</div>
            <div style={{font: `400 25px ${F.body}`, color: C.muted, marginTop: 8}}>{d[2]}</div>
          </Glass>
        ))}
        <Glass x={1254} y={600} w={570} h={240} t0={A.q5_circ} kind="tilt"><Eyebrow>CIRCULAR MONEY</Eyebrow></Glass>
        {['Company', 'AI lab', 'Its cloud'].map((n, i) => (
          <div key={i} style={{position: 'absolute', left: px[i], top: py, width: 150, height: 50, borderRadius: 25, border: `2px solid ${C.teal}`, display: 'flex', alignItems: 'center', justifyContent: 'center', font: `700 24px ${F.body}`, background: 'rgba(7,11,20,.85)', opacity: ok}}>{n}</div>
        ))}
        {[0, 1].map((i) => <div key={i} style={{position: 'absolute', left: px[i] + 150, width: 30, top: py + 4, textAlign: 'center', font: `800 34px ${F.disp}`, color: C.gold, opacity: ok}}>→</div>)}
        <div style={{position: 'absolute', left: px[0] + 75, top: py + 50, width: px[2] - px[0], height: 36, border: `3px dashed ${C.gold}`, borderTop: 0, borderRadius: '0 0 22px 22px', opacity: ok}} />
        <div style={{position: 'absolute', left: dot[0] - 11, top: dot[1] - 11, width: 22, height: 22, borderRadius: 11, background: C.gold, boxShadow: `0 0 16px ${C.gold}`, opacity: ok}} />
        <Rv x={1270} y={792} w={540} t0={A.q5_circ + 0.6} dy={8} style={{textAlign: 'center', font: `400 24px ${F.body}`, color: C.muted}}>invest in a lab · it spends it back on your cloud</Rv>
        <Src text="Backlogs: company reports. Bonds: press tally to 7 Jul 2026. FCF: Meta Q2 2026. JV: Meta/BlackRock El Paso. Not advice." />
      </Grp>
    </Win>
  );
};

/* ================= MAP · WHERE THE MONEY LANDS ================= */
const LAYERS: [string, string, number][] = [['Chips & memory', '#38bdf8', 0], ['Networking & optics', '#2dd4bf', 0], ['Chip factories & packaging', '#f472b6', 0], ['Power & cooling equipment', '#ff8a4c', 0], ['Builders & landlords', '#a3e635', 0], ['Power generation & materials', '#fbbf24', 0], ['The spenders', '#dfe6f3', 0]];
export const MapScene: React.FC = () => {
  const {t, fps} = useT();
  const ts = [A.l_chips, A.l_net, A.l_fab, A.l_pow, A.l_build, A.l_gen, A.l_spend];
  const wait = eo(pr(t, A.l_wait, 0.7));
  const ext = (hex: string) => Array.from({length: 14}, (_, k) => `${k + 1}px ${k + 1}px 0 ${hex}55`).join(',');
  return (
    <Win a={A.map} b={A.sowhat}>
      <QHead n="$" label="" eyebrow="FOLLOW THE MONEY" q="Who gets paid, and when" a={A.map} />
      <div style={{position: 'absolute', left: 96, top: 0, width: 1728, height: 1080, transform: 'perspective(2600px) rotateY(-8deg) rotateX(3deg)', transformOrigin: '20% 60%'}}>
        {LAYERS.map((l, i) => {
          const s = sp(t, ts[i], fps, 15, 120);
          const spender = i === 6;
          const y = 782 - i * 70;
          return (
            <div key={i} style={{position: 'absolute', left: 0, top: y, width: 820, height: 62, borderRadius: 14, display: 'flex', alignItems: 'center', padding: '0 26px', font: `800 34px ${F.disp}`, color: spender ? C.fg : '#0a1020', background: spender ? 'rgba(223,230,243,.10)' : `linear-gradient(90deg, ${l[1]}, ${l[1]}dd)`, border: spender ? '3px dashed #dfe6f3' : '0', boxShadow: spender ? '0 0 30px rgba(223,230,243,.2)' : `${ext(l[1])}, 0 0 40px ${l[1]}66`, opacity: clamp(s * 1.8), transform: `translate(${-(1 - s) * 120}px, ${(1 - s) * 30}px)`}}>
              <span style={{font: `500 26px ${F.mono}`, marginRight: 18, opacity: 0.75}}>{i + 1}</span>{l[0]}
            </div>
          );
        })}
      </div>
      <div style={{position: 'absolute', left: 944, top: 432, width: 8, height: 410 * wait, borderRadius: 4, background: C.ok, boxShadow: `0 0 20px ${C.ok}`}} />
      <Rv x={990} y={540} w={800} t0={A.l_wait} dx={-30} dy={0} style={{font: `800 62px/1.08 ${F.disp}`, color: C.ok}}>PAID WHEN THE<br />SPENDING HAPPENS</Rv>
      <div style={{position: 'absolute', left: 944, top: 362, width: 8, height: 62 * eo(pr(t, A.l_spend, 0.6)), borderRadius: 4, background: C.gold}} />
      <Rv x={990} y={350} w={800} t0={A.l_spend} dx={-30} dy={0} style={{font: `800 50px/1.1 ${F.disp}`, color: C.gold}}>WAIT FOR THE PAYBACK</Rv>
      <Src text="Layers follow the AIFT AI Stack Tracker. Education only, not a ranking or a recommendation." />
    </Win>
  );
};

/* ================= SO WHAT ================= */
export const SoWhat: React.FC = () => {
  const {t} = useT();
  const layers = ['Chips', 'Memory', 'Networking', 'Power equipment', 'Buildings', 'The spenders'];
  const slice = 0.09 * eo(pr(t, A.sw3 + 0.3, 1.0));
  return (
    <Win a={A.sowhat} b={A.close}>
      <QHead n="?" label="" eyebrow="SO WHAT?" q="What a long-term UK investor does with this" a={A.sowhat} />
      <Glass x={96} y={340} w={552} h={500} t0={A.sw1} kind="tilt" pad={30}>
        <div style={{font: `500 60px ${F.mono}`, color: C.teal}}>1</div>
        <div style={{font: `800 46px/1.05 ${F.disp}`, marginTop: 6}}>Remember the layers</div>
        <div style={{font: `400 29px/1.42 ${F.body}`, marginTop: 14}}>{layers.map((l, i) => <div key={i} style={{color: i === 5 ? C.gold : C.fg, opacity: clamp((t - (A.sw1 + 0.4 + i * 0.35)) * 3)}}>● {l}</div>)}</div>
      </Glass>
      <Glass x={684} y={340} w={552} h={500} t0={A.sw2} kind="tilt" pad={30}>
        <div style={{font: `500 60px ${F.mono}`, color: C.teal}}>2</div>
        <div style={{font: `800 46px/1.05 ${F.disp}`, marginTop: 6}}>Tight layers hold the pricing power</div>
        <div style={{display: 'flex', gap: 16, marginTop: 30}}>
          <div style={{flex: 1, border: '3px solid #ff8a4c', borderRadius: 16, padding: 18, textAlign: 'center', font: `800 40px ${F.disp}`, color: '#ff8a4c', boxShadow: '0 0 30px rgba(255,138,76,.3)'}}>POWER</div>
          <div style={{flex: 1, border: '3px solid #a78bfa', borderRadius: 16, padding: 18, textAlign: 'center', font: `800 40px ${F.disp}`, color: '#a78bfa', boxShadow: '0 0 30px rgba(167,139,250,.3)'}}>MEMORY</div>
        </div>
        <div style={{font: `400 27px ${F.body}`, color: C.muted, marginTop: 22}}>right now these are the tight ones</div>
      </Glass>
      <Glass x={1272} y={340} w={552} h={500} t0={A.sw3} kind="tilt" pad={30}>
        <div style={{font: `500 60px ${F.mono}`, color: C.teal}}>3</div>
        <div style={{font: `800 46px/1.05 ${F.disp}`, marginTop: 6}}>Size it</div>
      </Glass>
      <Ring cx={1548} cy={610} r={92} sw={34} frac={slice} color={C.gold} opacity={pr(t, A.sw3 + 0.2, 0.4)} />
      <Rv x={1296} y={728} w={504} t0={A.sw3 + 0.5} dy={8} style={{textAlign: 'center', font: `400 28px ${F.body}`, color: C.muted}}>a small slice</Rv>
      <Rv x={1296} y={775} w={232} h={44} t0={A.sw_isa} dy={10} style={{borderRadius: 22, border: `2px solid ${C.ok}`, color: C.ok, display: 'flex', alignItems: 'center', justifyContent: 'center', font: `700 23px ${F.body}`}}>Stocks & Shares ISA</Rv>
      <Rv x={1544} y={775} w={256} h={44} t0={A.sw_isa + 0.4} dy={10} style={{borderRadius: 22, border: `2px solid ${C.ok}`, color: C.ok, display: 'flex', alignItems: 'center', justifyContent: 'center', font: `700 23px ${F.body}`}}>UCITS funds</Rv>
      <Src text="Education only. Not personal advice. A theme like this is volatile and many of these companies are already inside global tracker funds." />
    </Win>
  );
};

/* ================= CLOSE ================= */
export const Close: React.FC = () => {
  const {t} = useT();
  const P: [string, string, string, string][] = [['1', 'Orders', 'OK', 'ok'], ['2', 'Chips', 'WARNING', 'warn'], ['3', 'Power', 'ALERT', 'alert'], ['4', 'Equipment', 'OK', 'ok'], ['5', 'Payback', 'WARNING', 'warn']];
  const k = t - A.sub;
  const pulse = t >= A.sub ? 1 + 0.06 * Math.sin(k * 7) : 1;
  const fadeEnd = 1 - pr(t, A.end - 0.2, 0.4);
  return (
    <Win a={A.close} b={A.end + 2}>
      <QHead n="5" label="" eyebrow="THE FIVE QUESTIONS" q="Check them every quarter, not every day" a={A.close} />
      {P.map((p, i) => (
        <Glass key={i} x={106 + i * 342} y={330} w={320} h={240} t0={A.close + i * 0.25} kind="tilt" hot={STATUS[p[3]]} pad={26}>
          <div style={{font: `500 54px ${F.mono}`, color: STATUS[p[3]]}}>{p[0]}</div>
          <div style={{font: `800 46px ${F.disp}`, marginTop: 4}}>{p[1]}</div>
          <div style={{marginTop: 14, display: 'inline-flex', alignItems: 'center', gap: 10, color: STATUS[p[3]], font: `700 28px ${F.body}`}}><span style={{width: 16, height: 16, borderRadius: 8, background: STATUS[p[3]], boxShadow: `0 0 14px ${STATUS[p[3]]}`}} />{p[2]}</div>
        </Glass>
      ))}
      <Glass x={96} y={610} w={1728} h={130} t0={A.disc} kind="up" hot={C.gold} pad={0}>
        <div style={{display: 'flex', alignItems: 'center', height: '100%', padding: '0 36px', font: `700 38px/1.25 ${F.body}`}}>Education, not advice · I may hold some of the companies in this theme.</div>
      </Glass>
      <Rv x={660} y={780} w={600} h={96} t0={A.sub} scale={0.8} dy={10} style={{borderRadius: 48, background: '#e0443e', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', font: `800 46px ${F.disp}`, letterSpacing: '0.04em', transform: `scale(${pulse})`, boxShadow: `0 0 ${30 + 20 * Math.sin(k * 7)}px rgba(224,68,62,.7)`, opacity: t >= A.sub ? fadeEnd : 0}}>▶  SUBSCRIBE</Rv>
    </Win>
  );
};

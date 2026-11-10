import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Background, Bullet, Chip, Glass, H1, Hl, MONO, Not, Num, Rv, SANS, SERIF, SP, Shell, T, cu, focus, prog} from './theme';

const label: React.CSSProperties = {fontFamily: MONO, fontSize: 24, letterSpacing: 3, textTransform: 'uppercase', color: T.gold, fontWeight: 600};
const abs = (x: number, y: number, w?: number, h?: number): React.CSSProperties => ({position: 'absolute', left: x, top: y, width: w, height: h});

// ───────────────────────── 04 Check the business ─────────────────────────
export const L15: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const q = 1 - prog(f, cu(cues, 1) - 8, 14);
  const W = 1640;
  const fill = prog(f, cu(cues, 2), 34);
  const dc = prog(f, cu(cues, 3), 30);
  const dcW = (W * 89.0) / 96.2;
  return (
    <Shell len={len} chapter="Check the business" kind="CONFIRMED" source="NVIDIA Q2 fiscal 2027 results release, 26 Aug 2026 — USD billions; gross margin in %">
      <div style={{opacity: q}}>
        <Rv at={0} style={{...abs(96, 360, 1728), fontFamily: SANS, fontWeight: 800, fontSize: 104, color: T.white, letterSpacing: -3, lineHeight: 1.05}}>
          Put the headlines beside the <span style={{color: T.gold}}>financial evidence</span>.
        </Rv>
      </div>
      <div style={{opacity: 1 - q}}>
        <Rv at={cu(cues, 1)} style={abs(96, 150, 1728)}>
          <Glass style={{padding: '34px 44px 44px'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <div>
                <div style={label}>Already reported · Q2 fiscal 2027</div>
                <div style={{fontFamily: SANS, fontSize: 36, color: T.text2, marginTop: 4}}>Quarter ended 26 July 2026</div>
              </div>
              <Chip kind="CONFIRMED" size={26} />
            </div>
            <Rv at={cu(cues, 2)} style={{marginTop: 22, display: 'flex', alignItems: 'baseline', gap: 26}}>
              <span style={{fontFamily: MONO, fontWeight: 600, fontSize: 150, color: T.white, letterSpacing: -6, lineHeight: 1}}>
                $<Num to={96.2} at={cu(cues, 2)} fmt={(v) => v.toFixed(1)} />bn
              </span>
              <span style={{fontFamily: SANS, fontWeight: 700, fontSize: 48, color: T.text}}>total revenue</span>
            </Rv>
            <div style={{position: 'relative', width: W, height: 110, marginTop: 26}}>
              <div style={{position: 'absolute', left: 0, top: 0, height: 110, width: W * fill, borderRadius: 14, background: 'rgba(255,255,255,0.22)', border: `2px solid ${T.white}`, boxSizing: 'border-box'}} />
              <div style={{position: 'absolute', left: 0, top: 0, height: 110, width: dcW * dc, borderRadius: '14px 0 0 14px', background: `linear-gradient(90deg, ${T.gold2}, ${T.gold})`, overflow: 'hidden'}}>
                <div style={{position: 'absolute', left: 28, top: 22, whiteSpace: 'nowrap', fontFamily: SANS, fontWeight: 800, fontSize: 50, color: '#0A0A08'}}>Data centre · $89.0bn</div>
              </div>
            </div>
            <Rv at={cu(cues, 3) + 14} style={{width: W, display: 'flex', justifyContent: 'space-between', marginTop: 12, fontFamily: SANS, fontSize: 32, color: T.text2}}>
              <span>
                <b style={{color: T.white}}>Part of the total</b> — not on top of it
              </span>
              <span>All other revenue · $7.2bn</span>
            </Rv>
            <div style={{display: 'flex', gap: 26, marginTop: 36, alignItems: 'stretch'}}>
              <Rv at={cu(cues, 4)} style={{width: 620}}>
                <div style={{borderRadius: 20, border: `1.5px solid ${T.edge}`, background: 'rgba(0,0,0,0.35)', padding: '20px 32px', height: 196, boxSizing: 'border-box'}}>
                  <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 112, color: T.white, letterSpacing: -4, lineHeight: 1}}>75.0%</div>
                  <div style={{fontFamily: SANS, fontSize: 34, color: T.text2, marginTop: 6}}>reported gross margin</div>
                </div>
              </Rv>
              <Rv at={cu(cues, 5)} style={{flex: 1}}>
                <div style={{borderRadius: 20, border: `2.5px dashed ${T.gold}`, background: 'rgba(246,196,69,0.1)', padding: '20px 32px', height: 196, boxSizing: 'border-box'}}>
                  <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 46, color: T.white, lineHeight: 1.12}}>Reported on 26 August 2026</div>
                  <Not at={cu(cues, 6)} size={40} style={{marginTop: 18}}>this month's earnings</Not>
                </div>
              </Rv>
            </div>
          </Glass>
        </Rv>
      </div>
    </Shell>
  );
};

export const L16: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const r = prog(f, cu(cues, 1) + 16, 30);
  return (
    <Shell len={len} chapter="Check the business" kind="GUIDANCE" source="NVIDIA outlook for Q3 fiscal 2027, in the 26 Aug 2026 release — company expectations, not results">
      <Rv at={cu(cues, 0)} style={abs(96, 150, 1728)}>
        <Glass tone="gold" dashed style={{padding: '34px 44px 44px'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div>
              <div style={label}>Company guidance · Q3 fiscal 2027</div>
              <div style={{fontFamily: SANS, fontSize: 36, color: T.text2, marginTop: 4}}>Quarter ended 25 October 2026 · guidance given 26 August</div>
            </div>
            <Chip kind="GUIDANCE" size={26} />
          </div>
          <div style={{display: 'flex', gap: 40, marginTop: 26}}>
            <Rv at={cu(cues, 1)} style={{width: 960}}>
              <div style={{fontFamily: SANS, fontSize: 36, fontWeight: 700, color: T.text}}>Revenue outlook</div>
              <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 132, color: T.white, letterSpacing: -5, lineHeight: 1.05}}>
                $108.0bn <span style={{color: T.gold, fontSize: 84}}>± 2%</span>
              </div>
              <div style={{position: 'relative', height: 120, marginTop: 14}}>
                <div style={{position: 'absolute', left: 0, right: 0, top: 30, height: 6, background: 'rgba(255,255,255,0.25)', borderRadius: 3}} />
                <div style={{position: 'absolute', left: `${50 - 34 * r}%`, width: `${68 * r}%`, top: 16, height: 34, borderRadius: 10, background: `linear-gradient(90deg, rgba(246,196,69,0.5), ${T.gold}, rgba(246,196,69,0.5))`}} />
                <div style={{position: 'absolute', left: '50%', top: 4, width: 4, height: 58, background: T.white, marginLeft: -2}} />
                <div style={{position: 'absolute', left: '16%', top: 66, transform: 'translateX(-50%)', fontFamily: MONO, fontWeight: 600, fontSize: 34, color: T.white, opacity: r}}>$105.8bn</div>
                <div style={{position: 'absolute', left: '84%', top: 66, transform: 'translateX(-50%)', fontFamily: MONO, fontWeight: 600, fontSize: 34, color: T.white, opacity: r}}>$110.2bn</div>
                <div style={{position: 'absolute', left: '50%', top: 72, transform: 'translateX(-50%)', fontFamily: MONO, fontSize: 22, color: T.text2, letterSpacing: 1.5, opacity: r}}>RANGE · AIFT CALCULATION</div>
              </div>
            </Rv>
            <Rv at={cu(cues, 2)} style={{flex: 1}}>
              <div style={{fontFamily: SANS, fontSize: 36, fontWeight: 700, color: T.text}}>Gross-margin outlook</div>
              <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 132, color: T.white, letterSpacing: -5, lineHeight: 1.05}}>74.0%</div>
              <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 42, color: T.gold, marginTop: 4, whiteSpace: 'nowrap'}}>± 0.5 percentage points</div>
              <div style={{fontFamily: SANS, fontSize: 32, color: T.text2, marginTop: 8}}>That is 73.5% to 74.5%</div>
            </Rv>
          </div>
          <Rv at={cu(cues, 3)} style={{marginTop: 30}}>
            <div style={{borderRadius: 20, background: 'linear-gradient(180deg, #FFFDF6 0%, #F3EEDF 100%)', padding: '24px 36px', color: '#14130F'}}>
              <div style={{fontFamily: MONO, fontSize: 21, letterSpacing: 2, textTransform: 'uppercase', color: '#5A5546'}}>NVIDIA release, 26 Aug 2026 · verbatim</div>
              <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 46, lineHeight: 1.16, marginTop: 8, letterSpacing: -0.6}}>
                “NVIDIA is <Hl at={cu(cues, 3) + 14} color="rgba(246,196,69,0.7)">not assuming any Data Center compute revenue from China</Hl> in its outlook.”
              </div>
            </div>
          </Rv>
        </Glass>
      </Rv>
    </Shell>
  );
};

export const L17: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const x = prog(f, cu(cues, 0) + 40, 16);
  return (
    <Shell len={len} chapter="Check the business" kind="ANALYSIS" source="AIFT analysis of NVIDIA's Q3 fiscal 2027 outlook (release of 26 Aug 2026) · results scheduled 17 Nov 2026">
      <H1 at={0} size={54}>Read the forecast as it was written</H1>
      <Rv at={cu(cues, 0) + 8} style={abs(96, 240, 1010)}>
        <Glass style={{padding: '28px 36px 32px'}}>
          <div style={label}>The outlook, as guided</div>
          <div style={{display: 'flex', alignItems: 'center', gap: 18, marginTop: 18}}>
            <div style={{height: 104, flex: 1, borderRadius: 14, background: `linear-gradient(90deg, ${T.gold2}, ${T.gold})`, display: 'flex', alignItems: 'center', paddingLeft: 26, fontFamily: MONO, fontWeight: 600, fontSize: 50, color: '#0A0A08'}}>$108.0bn ± 2%</div>
            <div style={{position: 'relative', width: 300, height: 104, borderRadius: 14, border: `3px dashed ${T.white}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: SANS, fontWeight: 700, fontSize: 34, color: T.text2, opacity: 0.4 + 0.6 * prog(f, cu(cues, 0) + 20, 14)}}>
              + China?
              <svg width={300} height={104} style={{position: 'absolute', left: -3, top: -3}}>
                <line x1={16} y1={16} x2={16 + 268 * x} y2={16 + 72 * x} stroke={T.white} strokeWidth={6} strokeLinecap="round" />
                <line x1={284} y1={16} x2={284 - 268 * x} y2={16 + 72 * x} stroke={T.white} strokeWidth={6} strokeLinecap="round" />
              </svg>
            </div>
          </div>
          <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 40, color: T.white, lineHeight: 1.18, marginTop: 20}}>Don't add a China contribution to a forecast that explicitly excludes it.</div>
        </Glass>
      </Rv>
      <Rv at={cu(cues, 1)} x={30} y={0} style={abs(1150, 240, 674)}>
        <Glass tone="dark" style={{padding: '28px 36px 32px', minHeight: 404}}>
          <div style={{...label, color: T.text2}}>Excluding sales does not remove</div>
          <div style={{display: 'flex', flexDirection: 'column', gap: 16, marginTop: 18}}>
            <Bullet at={cu(cues, 1) + 10} size={44} color={T.white}>Political risk</Bullet>
            <Bullet at={cu(cues, 1) + 22} size={44} color={T.white}>Customer risk</Bullet>
            <Bullet at={cu(cues, 1) + 34} size={44} color={T.white}>Reputational risk</Bullet>
          </div>
        </Glass>
      </Rv>
      <Rv at={cu(cues, 2)} style={abs(96, 700, 760)}>
        <Glass tone="gold" dashed style={{padding: '24px 36px', height: 250}}>
          <Chip kind="GUIDANCE" size={22} />
          <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 50, color: T.white, marginTop: 14, letterSpacing: -1}}>Company expectations</div>
          <div style={{fontFamily: SANS, fontSize: 34, color: T.text2, marginTop: 4}}>Given 26 August 2026</div>
        </Glass>
      </Rv>
      <Rv at={cu(cues, 3)} s={0.6} y={0} style={{...abs(880, 776, 160), textAlign: 'center', fontFamily: MONO, fontWeight: 600, fontSize: 88, color: T.lime}}>vs</Rv>
      <Rv at={cu(cues, 3) + 6} style={abs(1064, 700, 760)}>
        <Glass style={{padding: '24px 36px', height: 250}}>
          <Chip kind="SCHEDULED" size={22} />
          <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 50, color: T.white, marginTop: 14, letterSpacing: -1}}>Results + next outlook</div>
          <div style={{fontFamily: SANS, fontSize: 34, color: T.text2, marginTop: 4}}>17 November 2026</div>
        </Glass>
      </Rv>
    </Shell>
  );
};

// ───────────────────────── 05 Two dates, different questions ─────────────────────────
const DateHead: React.FC<{day: string; num: string; title: string; kind: string}> = ({day, num, title, kind}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: 26}}>
    <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 150, color: T.white, letterSpacing: -6, lineHeight: 0.95}}>{num}</div>
    <div style={{flex: 1}}>
      <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 30, letterSpacing: 3, color: T.gold, textTransform: 'uppercase'}}>{day} · November</div>
      <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 52, color: T.white, letterSpacing: -1.2, lineHeight: 1.05, marginTop: 4}}>{title}</div>
    </div>
    <Chip kind={kind} size={24} style={{alignSelf: 'flex-start'}} />
  </div>
);
const Mini: React.FC<{x: number; num: string; a: string; b: string; kind: string; dashed?: boolean}> = ({x, num, a, b, kind, dashed}) => (
  <div style={{...abs(x, 150, 500), opacity: 0.5}}>
    <Glass dashed={dashed} style={{padding: '30px 34px', height: 800}}>
      <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 150, color: T.white, letterSpacing: -6, lineHeight: 0.95}}>{num}</div>
      <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 30, letterSpacing: 3, color: T.gold, textTransform: 'uppercase', marginTop: 10}}>{a} · Nov</div>
      <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 46, color: T.white, letterSpacing: -1, lineHeight: 1.1, marginTop: 20}}>{b}</div>
      <Chip kind={kind} size={22} style={{marginTop: 26}} />
    </Glass>
  </div>
);
export const L18: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} chapter="Two dates" kind="SCHEDULED" source="NVIDIA Investor Relations, 28 Oct 2026 — results ≈ 1:20 pm PT, call 2 pm PT; UK times converted by AIFT">
    <Rv at={0} style={abs(96, 150, 1190)}>
      <Glass tone="gold" style={{padding: '30px 40px', height: 800}}>
        <DateHead day="Tuesday" num="17" title="Earnings · Q3 fiscal 2027" kind="SCHEDULED" />
        <div style={{display: 'flex', gap: 22, marginTop: 26}}>
          <Rv at={cu(cues, 0) + 12} style={{flex: 1}}>
            <div style={{borderRadius: 18, background: 'rgba(0,0,0,0.4)', border: `1.5px solid ${T.edge}`, padding: '14px 26px'}}>
              <div style={{fontFamily: SANS, fontSize: 30, color: T.text2}}>Results, UK time</div>
              <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 80, color: T.white, letterSpacing: -2, lineHeight: 1.05}}>≈ 21:20</div>
            </div>
          </Rv>
          <Rv at={cu(cues, 1)} style={{flex: 1}}>
            <div style={{borderRadius: 18, background: 'rgba(0,0,0,0.4)', border: `1.5px solid ${T.edge}`, padding: '14px 26px'}}>
              <div style={{fontFamily: SANS, fontSize: 30, color: T.text2}}>Earnings call, UK time</div>
              <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 80, color: T.white, letterSpacing: -2, lineHeight: 1.05}}>22:00</div>
            </div>
          </Rv>
        </div>
        <div style={{...label, color: T.text, marginTop: 28}}>Questions for the business</div>
        <div style={{display: 'flex', flexDirection: 'column', gap: 14, marginTop: 14}}>
          <Bullet at={cu(cues, 2) + 8} size={40}>Did revenue meet guidance?</Bullet>
          <Bullet at={cu(cues, 3)} size={40}>Did margins hold up?</Bullet>
          <Bullet at={cu(cues, 4)} size={40}>What does management say about future demand and deliveries?</Bullet>
        </div>
        <Rv at={cu(cues, 5)} style={{marginTop: 20, fontFamily: SANS, fontWeight: 700, fontSize: 36, color: T.white, lineHeight: 1.2}}>
          Listen for <Hl at={cu(cues, 5) + 12}>evidence of changed customer behaviour</Hl> — assume neither resilience nor cancellations.
        </Rv>
      </Glass>
    </Rv>
    <Mini x={1324} num="18" a="Wednesday" b="Congressional briefing" kind="REQUESTED" dashed />
  </Shell>
);

export const L19: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} chapter="Two dates" kind="REQUESTED" source="House Foreign Affairs Committee release, 5 Nov 2026 (letter dated 4 Nov) — attendance not confirmed at snapshot">
    <Mini x={96} num="17" a="Tuesday" b="Earnings · Q3 fiscal 2027" kind="SCHEDULED" />
    <Rv at={0} style={abs(634, 150, 1190)}>
      <Glass dashed style={{padding: '30px 40px', height: 800}}>
        <DateHead day="Wednesday" num="18" title="Closed-door briefing" kind="REQUESTED" />
        <Rv at={cu(cues, 1)} style={{display: 'flex', gap: 14, marginTop: 24}}>
          {[
            ['Brian Mast', 'Foreign Affairs'],
            ['John Moolenaar', 'Select Cttee on China'],
            ['Rick Crawford', 'Intelligence'],
          ].map(([n, c]) => (
            <div key={n} style={{flex: 1, borderRadius: 16, background: 'rgba(0,0,0,0.4)', border: `1.5px solid ${T.edge}`, padding: '12px 20px'}}>
              <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 34, color: T.white}}>{n}</div>
              <div style={{fontFamily: SANS, fontSize: 26, color: T.text2}}>Chair · {c}</div>
            </div>
          ))}
        </Rv>
        <Rv at={cu(cues, 2)} style={{marginTop: 18, fontFamily: SANS, fontSize: 38, fontWeight: 600, color: T.text}}>
          Reply, or an alternative date, requested by <b style={{color: T.gold}}>11 November</b>
        </Rv>
        <Rv at={cu(cues, 3)} style={{marginTop: 20}}>
          <div style={{borderRadius: 18, background: T.gold, padding: '14px 30px', fontFamily: SANS, fontWeight: 800, fontSize: 54, color: '#0A0A08', letterSpacing: -1.2}}>
            Requested <span style={{fontFamily: MONO}}>≠</span> confirmed attendance
          </div>
        </Rv>
        <div style={{...label, color: T.text, marginTop: 24}}>Their questions</div>
        <div style={{display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12}}>
          <Bullet at={cu(cues, 4) + 6} size={38} color={T.white}>Security protocols against foreign espionage</Bullet>
          <Bullet at={cu(cues, 4) + 20} size={38} color={T.white}>The reported relationships</Bullet>
        </div>
        <Not at={cu(cues, 5)} size={36} style={{marginTop: 18}}>whether quarterly sales beat expectations</Not>
      </Glass>
    </Rv>
  </Shell>
);

export const L20: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} chapter="Two dates" kind="ANALYSIS" source="AIFT analysis · educational commentary, not a personal recommendation">
    <H1 at={0} size={54}>A revenue beat does not close the investigation</H1>
    <Rv at={cu(cues, 0) + 6} style={abs(96, 250, 800)}>
      <Glass tone="lime" style={{padding: '34px 40px', height: 560}}>
        <div style={{...label, color: T.lime}}>A strong report could</div>
        <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 76, color: T.white, letterSpacing: -2.4, lineHeight: 1.06, marginTop: 20}}>Support confidence in demand</div>
        <div style={{fontFamily: SANS, fontSize: 38, color: T.text2, marginTop: 24, lineHeight: 1.25}}>Revenue, margins and outlook speak to the operating business.</div>
      </Glass>
    </Rv>
    <Rv at={cu(cues, 1)} x={30} y={0} style={abs(940, 250, 884)}>
      <Glass style={{padding: '34px 40px', height: 560}}>
        <div style={{...label, color: T.text}}>It would not</div>
        <div style={{display: 'flex', flexDirection: 'column', gap: 34, marginTop: 34}}>
          <Not at={cu(cues, 1) + 8} size={46}>complete the board's investigation</Not>
          <Not at={cu(cues, 2)} size={46}>settle the lawsuit</Not>
          <Not at={cu(cues, 3)} size={46}>answer every congressional question</Not>
        </div>
      </Glass>
    </Rv>
  </Shell>
);

export const L21: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} chapter="Two dates" kind="REPORTED" source="Reuters, 9–10 Nov 2026 (syndicated copy read at ThePrint) — the FBI has not been independently confirmed here">
    <Rv at={0} style={abs(96, 150, 960)}>
      <Glass tone="gold" style={{padding: '30px 40px 36px', minHeight: 640}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div style={label}>Reuters · 9–10 Nov 2026</div>
          <div style={{fontFamily: MONO, fontSize: 18, letterSpacing: 1.6, color: T.text2, textTransform: 'uppercase'}}>Designed summary</div>
        </div>
        <div style={{fontFamily: SANS, fontSize: 36, color: T.text2, marginTop: 20}}>President Trump, speaking to reporters:</div>
        <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 78, color: T.white, lineHeight: 1.1, letterSpacing: -1.4, marginTop: 12}}>
          “I know the FBI is <Hl at={cu(cues, 0) + 26}>looking into it</Hl>.”
        </div>
        <Rv at={cu(cues, 1)} style={{fontFamily: SANS, fontSize: 40, fontWeight: 600, color: T.text, lineHeight: 1.22, marginTop: 30}}>
          Trump also said Huang told him he had no idea the woman was a spy.
        </Rv>
      </Glass>
    </Rv>
    <Rv at={cu(cues, 2)} x={30} y={0} style={abs(1110, 150, 714)}>
      <Glass style={{padding: '28px 34px'}}>
        <Chip kind="REPORTED" size={22} />
        <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 46, color: T.white, lineHeight: 1.12, marginTop: 14, letterSpacing: -0.8}}>Trump's account of a private conversation</div>
      </Glass>
    </Rv>
    <Not at={cu(cues, 3)} size={44} style={abs(1110, 500, 714)}>independent FBI confirmation</Not>
    <Not at={cu(cues, 4)} size={44} style={abs(1110, 630, 714)}>a finding about what Jensen knew</Not>
  </Shell>
);

// ───────────────────────── 06 Three scenarios ─────────────────────────
type SC = {tag: string; title: string; tone: 'lime' | 'gold' | 'clear'; items: string[]; foot?: string};
const SCN: SC[] = [
  {tag: 'Scenario A', title: 'Uncertainty eases', tone: 'lime', items: ['Investigation gives credible clarity', 'Leadership remains stable', 'Results support continuing customer demand']},
  {tag: 'Scenario B', title: 'Overhang persists', tone: 'gold', items: ['Demand holds up', 'Investigation and political scrutiny continue']},
  {tag: 'Scenario C', title: 'Adverse', tone: 'clear', items: ['New findings materially change the governance picture', 'Policy becomes more restrictive', 'Operating guidance weakens']},
];
const Scenarios: React.FC<{active: number; show: number[][]; foot?: React.ReactNode; title: string; len: number; source: string}> = ({active, show, foot, title, len, source}) => {
  const f = useCurrentFrame();
  return (
    <Shell len={len} chapter="Three scenarios" kind="SCENARIO" source={source}>
      <H1 at={0} size={54}>{title}</H1>
      {SCN.map((s, i) => {
        const on = i === active;
        const done = i < active;
        const col = s.tone === 'lime' ? T.lime : s.tone === 'gold' ? T.gold : T.white;
        return (
          <div key={i} style={{...abs(96 + i * 586, 236, 556), opacity: on ? 1 : done ? 0.62 : 0.3, transform: `translateY(${on ? -8 * prog(f, 4, 18) : 0}px)`}}>
            <Glass tone={on ? s.tone : 'clear'} dashed style={{height: 560, padding: '26px 30px'}}>
              <div style={{...label, color: col}}>{s.tag}</div>
              <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 54, color: T.white, letterSpacing: -1.4, lineHeight: 1.05, marginTop: 6}}>{s.title}</div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 16, marginTop: 24}}>
                {s.items.map((t, k) => (i > active ? null : <Bullet key={k} at={done ? -100 : show[i]?.[k] ?? 99999} size={36} color={col}>{t}</Bullet>))}
              </div>
            </Glass>
          </div>
        );
      })}
      {foot}
    </Shell>
  );
};
const Foot: React.FC<{at: number; x?: number; w?: number; y?: number; tone?: 'clear' | 'gold' | 'dark' | 'lime'; children: React.ReactNode}> = ({at, x = 96, w = 1728, y = 820, tone = 'clear', children}) => (
  <Rv at={at} style={abs(x, y, w)}>
    <Glass tone={tone} style={{padding: '18px 34px', fontFamily: SANS, fontWeight: 700, fontSize: 40, color: T.white, lineHeight: 1.2}}>{children}</Glass>
  </Rv>
);
export const L22: React.FC<SP> = ({len, cues}) => (
  <Scenarios
    len={len}
    title="Think in scenarios, not promises"
    active={0}
    show={[[cu(cues, 2), cu(cues, 3), cu(cues, 4)]]}
    source="AIFT scenarios — illustrative, with no probabilities and no price targets"
    foot={
      <>
        <Foot at={cu(cues, 5)} w={700} tone="lime">Could reduce uncertainty</Foot>
        <Foot at={cu(cues, 6)} x={820} w={1004}>
          <span style={{color: T.gold}}>No guarantee</span> of an immediate share-price recovery
        </Foot>
      </>
    }
  />
);
export const L23: React.FC<SP> = ({len, cues}) => (
  <Scenarios
    len={len}
    title="Think in scenarios, not promises"
    active={1}
    show={[[], [cu(cues, 0) + 20, cu(cues, 0) + 56]]}
    source="AIFT scenarios — illustrative, with no probabilities and no price targets"
    foot={<Foot at={cu(cues, 1)} tone="gold">A strong business can still trade under a cloud of uncertainty — for a long time.</Foot>}
  />
);
export const L24: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  const sw = prog(f, cu(cues, 6) - 6, 14);
  return (
    <Scenarios
      len={len}
      title="Think in scenarios, not promises"
      active={2}
      show={[[], [], [cu(cues, 1), cu(cues, 2), cu(cues, 3)]]}
      source="AIFT scenarios — illustrative; none of these events has occurred at the research snapshot"
      foot={
        <>
          <div style={{opacity: 1 - sw}}>
            <Foot at={cu(cues, 4)} w={830}>Any of these → a fresh assessment</Foot>
            <Foot at={cu(cues, 5)} x={950} w={874} tone="dark">
              <span style={{color: T.gold}}>None has occurred.</span> Don't state it as fact.
            </Foot>
          </div>
          <div style={{opacity: sw}}>
            <Foot at={cu(cues, 6)} w={830} tone="gold">No probabilities. No price targets.</Foot>
            <Foot at={cu(cues, 7)} x={950} w={874}>Only the evidence that makes each more plausible.</Foot>
          </div>
        </>
      }
    />
  );
};

// ───────────────────────── 07 Investor checklist + close ─────────────────────────
const Q: React.FC<{at: number; n: number; x: number; y: number; children: React.ReactNode}> = ({at, n, x, y, children}) => (
  <Rv at={at} style={abs(x, y, 850)}>
    <Glass style={{padding: '28px 36px', height: 300, display: 'flex', gap: 28, alignItems: 'center'}}>
      <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 150, color: T.gold, lineHeight: 1, letterSpacing: -6, flexShrink: 0}}>{n}</div>
      <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 46, color: T.white, lineHeight: 1.14, letterSpacing: -0.8}}>{children}</div>
    </Glass>
  </Rv>
);
export const L25: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} chapter="Investor checklist" kind="ANALYSIS" source="AIFT checklist · educational commentary, not a personal recommendation to buy or sell">
    <H1 at={0} size={54}>Before making a decision, ask four questions</H1>
    <Q at={cu(cues, 1)} n={1} x={96} y={238}>What has actually been confirmed since my last review?</Q>
    <Q at={cu(cues, 2)} n={2} x={974} y={238}>Has the earnings outlook changed?</Q>
    <Q at={cu(cues, 3)} n={3} x={96} y={566}>Has a political proposal become an enforceable rule?</Q>
    <Q at={cu(cues, 4)} n={4} x={974} y={566}>Is my exposure small enough to handle an uncertain outcome?</Q>
  </Shell>
);

export const L26: React.FC<SP> = ({len, cues}) => {
  const f = useCurrentFrame();
  return (
    <Shell len={len} chapter="Investor checklist" source="NVIDIA Newsroom, 8 Nov 2026 · NVIDIA Investor Relations · House Foreign Affairs Committee · Reuters">
      <H1 at={0} size={54}>The verified story, right now</H1>
      <div style={{...abs(96, 232, 1728), display: 'flex', gap: 22}}>
        {[
          ['An admission', 1],
          ['An open investigation', 2],
          ['Growing scrutiny', 3],
        ].map(([t, k]) => (
          <Rv key={t as string} at={cu(cues, k as number)} style={{flex: 1}}>
            <Glass tone="lime" style={{padding: '26px 30px', height: 170, display: 'flex', alignItems: 'center'}}>
              <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 50, color: T.white, letterSpacing: -1.2, lineHeight: 1.08}}>{t}</div>
            </Glass>
          </Rv>
        ))}
      </div>
      <Rv at={cu(cues, 4)} style={abs(96, 428, 1728)}>
        <Glass tone="gold" style={{padding: '24px 34px', display: 'flex', alignItems: 'center', gap: 30}}>
          <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 78, color: T.gold, lineHeight: 1}}>+</div>
          <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 46, color: T.white, letterSpacing: -0.8}}>a very large operating business, awaiting its next results</div>
        </Glass>
      </Rv>
      <div style={{...abs(96, 626, 1728), display: 'flex', flexDirection: 'column', gap: 26, opacity: 0.999 + 0 * f}}>
        <Bullet at={cu(cues, 5)} size={54} color={T.gold}>Treat the allegations seriously</Bullet>
        <Bullet at={cu(cues, 6)} size={54} color={T.gold}>Keep their attribution intact</Bullet>
        <Bullet at={cu(cues, 7)} size={54} color={T.lime}>Judge the business on evidence, as it arrives</Bullet>
      </div>
    </Shell>
  );
};

const SLATE: [string, string][] = [
  ['NVIDIA Newsroom', '“A Message to Our Company” · 8 Nov 2026'],
  ['NVIDIA Newsroom', '“Statement From NVIDIA Board of Directors” · 8 Nov 2026'],
  ['NVIDIA Investor Relations', 'Q2 fiscal 2027 results and Q3 outlook · 26 Aug 2026'],
  ['NVIDIA Investor Relations', 'Q3 fiscal 2027 conference-call notice · 28 Oct 2026'],
  ['House Foreign Affairs Cttee', 'Briefing request release · 5 Nov 2026 (letter 4 Nov)'],
  ['Reuters', 'Shareholder lawsuit and market value · 9 Nov 2026'],
  ['Reuters', 'Trump remarks; China response · 9–10 Nov 2026'],
  ['The New York Times', 'Reporting of 29 Oct & 8 Nov 2026, as relayed by Reuters'],
  ['Financial Modeling Prep', 'NVDA daily closing prices · 25 Sep–9 Nov 2026'],
];
export const L27: React.FC<SP> = ({len, cues}) => (
  <Shell len={len} source="Full links are in the video description · no publishing date or later prices are implied">
    <Rv at={0} style={{...abs(96, 130, 1728), display: 'flex', alignItems: 'center', gap: 26}}>
      <div style={{width: 62, height: 62, background: T.lime, borderRadius: 12}} />
      <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 86, color: T.white, letterSpacing: -3}}>
        AI Finance <span style={{color: T.gold}}>Toolkit</span>
      </div>
      <div style={{flex: 1}} />
      <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 36, color: T.text2, textAlign: 'right', lineHeight: 1.2, width: 620}}>Follow for clear explanations of the companies behind the headlines</div>
    </Rv>
    <Rv at={20} style={abs(96, 268, 1728)}>
      <Glass style={{padding: '24px 34px 28px'}}>
        <div style={label}>Sources used in this film</div>
        <div style={{display: 'flex', flexDirection: 'column', gap: 9, marginTop: 14}}>
          {SLATE.map(([a, b], i) => (
            <div key={i} style={{display: 'flex', gap: 24, fontFamily: SANS, fontSize: 30, lineHeight: 1.2}}>
              <span style={{width: 440, flexShrink: 0, fontWeight: 700, color: T.white}}>{a}</span>
              <span style={{color: T.text2}}>{b}</span>
            </div>
          ))}
        </div>
      </Glass>
    </Rv>
    <Rv at={cu(cues, 1)} style={abs(96, 836, 1728)}>
      <Glass tone="gold" style={{padding: '20px 34px', fontFamily: SANS, fontWeight: 700, fontSize: 42, color: T.white, letterSpacing: -0.6}}>
        Educational commentary — not a personal recommendation to buy or sell.
      </Glass>
    </Rv>
  </Shell>
);

// ───────────────────────── Thumbnail (1280×720 still) ─────────────────────────
export const Thumb: React.FC = () => (
  <AbsoluteFill style={{background: T.bg}}>
    <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, transform: 'scale(0.6667)', transformOrigin: '0 0'}}>
      <Background />
      <div style={{position: 'absolute', left: 80, top: 70, display: 'flex', alignItems: 'center', gap: 20}}>
        <div style={{width: 44, height: 44, background: T.lime, borderRadius: 9}} />
        <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 40, letterSpacing: 5, color: T.white}}>AI FINANCE TOOLKIT</div>
      </div>
      <div style={{position: 'absolute', left: 80, top: 170, fontFamily: SANS, fontWeight: 800, fontSize: 150, letterSpacing: -6, color: T.white, lineHeight: 1}}>NVIDIA</div>
      <div style={{position: 'absolute', left: 80, top: 380, width: 1100, fontFamily: SANS, fontWeight: 800, fontSize: 196, letterSpacing: -9, color: T.gold, lineHeight: 0.92}}>
        WHAT
        <br />
        CHANGED?
      </div>
      <div style={{position: 'absolute', left: 80, top: 880}}>
        <span style={{display: 'inline-flex', alignItems: 'center', gap: 22, border: `5px solid ${T.lime}`, borderRadius: 16, padding: '18px 34px', background: 'rgba(0,0,0,0.55)', fontFamily: MONO, fontWeight: 600, fontSize: 56, letterSpacing: 3, color: T.lime}}>
          <span style={{width: 26, height: 26, background: T.lime, borderRadius: 4}} />
          BOARD INVESTIGATION: OPEN
        </span>
      </div>
      <div style={{position: 'absolute', left: 1130, top: 120, width: 700, transform: 'rotate(2deg)'}}>
        <Glass style={{padding: '40px 48px 50px', background: 'linear-gradient(150deg, #4A1616 0%, #241010 55%, #151210 100%)', border: `4px solid ${T.red}`}}>
          <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 40, letterSpacing: 3, color: T.white}}>9 NOV 2026 · CLOSE</div>
          <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 148, color: T.white, letterSpacing: -8, lineHeight: 1.05, marginTop: 14}}>$178.67</div>
          <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 150, color: T.red, letterSpacing: -8, lineHeight: 1.05}}>▼4.27%</div>
          <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 44, color: T.white, marginTop: 22, whiteSpace: 'nowrap'}}>≈ $190bn value, one day</div>
          <div style={{fontFamily: SANS, fontSize: 30, color: T.text2, marginTop: 6}}>Reuters estimate</div>
        </Glass>
      </div>
    </div>
  </AbsoluteFill>
);

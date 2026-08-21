import { getBrand } from '@/lib/server/runtime';
import { saveBrand } from '../actions';

export const dynamic = 'force-dynamic';

const ALLOWLIST: Array<{ key: string; label: string; note: string; locked?: boolean }> = [
  { key: 'research_topics', label: 'Research topics', note: 'Topic line, ticker and requested fields from the research queue. No requester, no rationale.' },
  { key: 'agent_rules', label: 'Guardrails', note: 'Existing investment and research rules, shown in the job audit trail.' },
  { key: 'intelligence_flags', label: 'Intelligence flags', note: 'Label and strength only. A flag prioritises private research; it never becomes a public claim.' },
  { key: 'market_snapshots', label: 'Market snapshots', note: 'Symbol, metric, value, unit, date, source. Never a quantity held or a position value.' },
  { key: 'macro_indicators', label: 'Macro indicators', note: 'Dated indicator readings with their source.' },
  { key: 'portfolio_themes', label: 'Portfolio themes', note: 'Bucket labels only, and only where more than one bucket shares a label so it cannot identify a position.' },
  { key: 'portfolio_values', label: 'Portfolio values', note: 'Permanently off. There is no code path that puts a portfolio value into a model payload, and a database constraint refuses the setting.', locked: true },
];

export default async function BrandStudio() {
  const brand = await getBrand();
  const allow = brand.private_context_allowlist as unknown as Record<string, boolean>;

  return (
    <>
      <div className="pagehead">
        <div>
          <h1>Brand studio</h1>
          <p className="sub">
            Channel voice, visual tokens, disclosure wording, approved sources and banned phrases.
            These are not suggestions to a model — the compliance and brand gates read them directly.
          </p>
        </div>
      </div>

      <form action={saveBrand}>
        <div className="grid g2">
          <div className="card">
            <h2>Channel</h2>
            <div className="field">
              <label htmlFor="channel_name">Channel name</label>
              <input id="channel_name" name="channel_name" defaultValue={brand.channel_name} />
            </div>
            <div className="field">
              <label htmlFor="voice_guide">Voice guide</label>
              <textarea id="voice_guide" name="voice_guide" defaultValue={brand.voice_guide} style={{ minHeight: 130 }} />
            </div>
            <div className="field">
              <label htmlFor="audience_profile">Audience</label>
              <textarea id="audience_profile" name="audience_profile" defaultValue={brand.audience_profile} />
            </div>
            <div className="row" style={{ marginTop: 14 }}>
              <div className="field" style={{ flex: 1 }}>
                <label htmlFor="default_video_length_minutes">Default length (minutes)</label>
                <input id="default_video_length_minutes" name="default_video_length_minutes"
                  type="number" min={1} max={60} defaultValue={brand.default_video_length_minutes} />
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, textTransform: 'none', letterSpacing: 0, marginTop: 18 }}>
                <input type="checkbox" name="shorts_enabled" defaultChecked={brand.shorts_enabled} style={{ width: 'auto' }} />
                Shorts enabled
              </label>
            </div>
          </div>

          <div className="card">
            <h2>Disclosure</h2>
            <div className="field">
              <label htmlFor="disclosure_text">Spoken and written verbatim in every pack</label>
              <textarea id="disclosure_text" name="disclosure_text" defaultValue={brand.disclosure_text} required />
              <p className="hint">
                The compliance gate checks this appears in the narration and again in the description.
                A pack without it cannot reach review.
              </p>
            </div>
            <div className="divider" />
            <h2>Banned phrases</h2>
            <div className="field">
              <label htmlFor="banned_phrases">One per line</label>
              <textarea id="banned_phrases" name="banned_phrases" style={{ minHeight: 150 }}
                defaultValue={brand.banned_phrases.join('\n')} />
              <p className="hint">
                Matched as whole phrases against every public-facing surface, so ordinary discussion
                is not caught but instruction-shaped language is.
              </p>
            </div>
          </div>
        </div>

        <div className="grid g2" style={{ marginTop: 14 }}>
          <div className="card">
            <h2>Visual tokens</h2>
            <p className="hint" style={{ marginBottom: 12 }}>
              These are written straight into the render stylesheet. Changing one changes every frame.
            </p>
            <div className="grid g2">
              {([['c_background', 'Background', brand.visual_style.background],
                 ['c_ink', 'Ink', brand.visual_style.ink],
                 ['c_accent', 'Accent', brand.visual_style.accent],
                 ['c_accent_2', 'Accent 2', brand.visual_style.accent_2]] as const).map(([name, label, value]) => (
                <div className="field" key={name} style={{ marginTop: 0 }}>
                  <label htmlFor={name}>{label}</label>
                  <div className="row" style={{ gap: 8 }}>
                    <span style={{ width: 30, height: 30, borderRadius: 6, background: value, border: '1px solid var(--line-2)', flex: 'none' }} />
                    <input id={name} name={name} defaultValue={value} className="mono" />
                  </div>
                </div>
              ))}
            </div>
            <div className="divider" />
            <dl className="kv">
              <dt>Display</dt><dd>{brand.visual_style.display_font}</dd>
              <dt>Body</dt><dd>{brand.visual_style.body_font}</dd>
              <dt>Mono</dt><dd>{brand.visual_style.mono_font}</dd>
            </dl>
          </div>

          <div className="card">
            <h2>Approved source domains</h2>
            <div className="field">
              <label htmlFor="approved_source_domains">One per line</label>
              <textarea id="approved_source_domains" name="approved_source_domains" style={{ minHeight: 210 }}
                defaultValue={brand.approved_source_domains.join('\n')} />
              <p className="hint">
                Discovery may look anywhere; only fetched-and-stored documents can be cited, and
                primary sources on this list outrank everything else.
              </p>
            </div>
          </div>
        </div>

        <div className="grid g2" style={{ marginTop: 14 }}>
          <div className="card">
            <h2>Audio</h2>
            <p className="hint" style={{ marginBottom: 14 }}>
              Delivery loudness, not peak level. YouTube normalises playback to about −14 LUFS, so a
              pack far from target gets re-levelled and the balance you approved is not the balance
              anyone hears.
            </p>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, textTransform: 'none', letterSpacing: 0 }}>
              <input type="checkbox" name="music_enabled" defaultChecked={brand.audio.music_enabled} style={{ width: 'auto' }} />
              Music bed under narration
            </label>
            <div className="row" style={{ marginTop: 14 }}>
              <div className="field" style={{ flex: 1, marginTop: 0 }}>
                <label htmlFor="music_mood">Mood</label>
                <select id="music_mood" name="music_mood" defaultValue={brand.audio.music_mood}>
                  <option value="analytical">Analytical</option>
                  <option value="tense">Tense</option>
                  <option value="open">Open</option>
                </select>
              </div>
              <div className="field" style={{ flex: 1, marginTop: 0 }}>
                <label htmlFor="target_lufs">Target loudness (LUFS)</label>
                <input id="target_lufs" name="target_lufs" type="number" step="0.5" min={-24} max={-8}
                  defaultValue={brand.audio.target_lufs} />
              </div>
            </div>
            <div className="row">
              <div className="field" style={{ flex: 1 }}>
                <label htmlFor="bed_db">Bed level (dB)</label>
                <input id="bed_db" name="bed_db" type="number" step="1" min={-40} max={0}
                  defaultValue={brand.audio.bed_db} />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label htmlFor="duck_db">Duck under speech (dB)</label>
                <input id="duck_db" name="duck_db" type="number" step="1" min={-30} max={-6}
                  defaultValue={brand.audio.duck_db} />
                <p className="hint">A gate fails below 6 dB: the narration would fight the bed.</p>
              </div>
            </div>
          </div>

          <div className="card">
            <h2>Private research context — allow-list</h2>
          <p className="hint" style={{ marginBottom: 14 }}>
            What the server may read from the finance database and pass, redacted, to a model. Every
            flag starts off. Turning one on widens what a model can see, so turn on the least you need.
          </p>
            {ALLOWLIST.map((a) => (
            <div key={a.key} style={{ padding: '11px 0', borderBottom: '1px solid var(--line)' }}>
              <label style={{ display: 'flex', gap: 10, alignItems: 'flex-start', textTransform: 'none', letterSpacing: 0, marginBottom: 0 }}>
                <input
                  type="checkbox"
                  name={`allow_${a.key}`}
                  defaultChecked={Boolean(allow[a.key])}
                  disabled={a.locked}
                  style={{ width: 'auto', marginTop: 3 }}
                />
                <span>
                  <b style={{ fontSize: 13, color: a.locked ? 'var(--dimmer)' : 'var(--ink)' }}>{a.label}</b>
                  {a.locked && <span className="pill fail" style={{ marginLeft: 8 }}>locked off</span>}
                  <span style={{ display: 'block', fontSize: 12, color: 'var(--dim)', marginTop: 3 }}>{a.note}</span>
                </span>
              </label>
            </div>
            ))}
          </div>
        </div>

        <div className="row" style={{ marginTop: 18 }}>
          <button className="primary" type="submit">Save brand settings</button>
        </div>
      </form>
    </>
  );
}

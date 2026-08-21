import type { BrandSettings } from '@/lib/domain';

export const DISCLOSURE_TEXT =
  'This video is for research and education only, not personalised financial advice. ' +
  'Always do your own research and consider professional advice where appropriate.';

/**
 * Instruction-shaped language that may not appear in public copy. The compliance
 * gate matches these as whole phrases so ordinary discussion ("the company sold
 * its stake") is not caught, but "you should buy" is.
 */
export const DEFAULT_BANNED_PHRASES: string[] = [
  'you should buy', 'you should sell', 'i recommend buying', 'i recommend selling',
  'buy now', 'sell now', 'load up on', 'back up the truck', 'add to your position',
  'trim your position', 'cut your losses', 'get in before', 'guaranteed return',
  'guaranteed profit', 'risk free', 'risk-free', 'will definitely', 'can\'t lose',
  'to the moon', 'my price target', 'this is financial advice', 'take my word for it',
  'you can\'t go wrong', 'easy money', 'sure thing',
];

// Note: "financial advice" on its own is deliberately absent. The required
// disclosure contains the phrase ("not personalised financial advice"), so
// banning the bare string would block every compliant script.

export const DEFAULT_BRAND_SETTINGS: BrandSettings = {
  user_id: '',
  channel_name: 'AI Finance Toolkit',
  voice_guide:
    'Calm, precise, British English. Explain the mechanism before the conclusion. Name the source and the date ' +
    'in the sentence, not in a caption. Give the counter-case its own airtime. Never instruct; always describe ' +
    'evidence. Short sentences carry the numbers; longer ones carry the reasoning.',
  audience_profile:
    'Financially literate adults who can read a chart but have not read a filing. They want the mechanism and the ' +
    'caveats, not a verdict. UK and US mix. Watching on a laptop or a TV, usually at 1x.',
  visual_style: {
    background: '#07090d',
    surface: '#0e1219',
    ink: '#f2f5f9',
    ink_dim: '#8c97a8',
    accent: '#4cc2ff',
    accent_2: '#7b6bff',
    positive: '#37d39a',
    negative: '#ff6b6b',
    display_font: '"Georgia", "Times New Roman", serif',
    body_font: '"Inter", "Helvetica Neue", Arial, sans-serif',
    mono_font: '"JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace',
    grain: 0.045,
  },
  approved_source_domains: [
    'sec.gov', 'investor.gov', 'federalreserve.gov', 'bls.gov', 'bea.gov',
    'fca.org.uk', 'bankofengland.co.uk', 'ons.gov.uk', 'ecb.europa.eu',
    'imf.org', 'worldbank.org', 'oecd.org',
  ],
  banned_phrases: DEFAULT_BANNED_PHRASES,
  disclosure_text: DISCLOSURE_TEXT,
  default_video_length_minutes: 10,
  shorts_enabled: true,
  audio: {
    music_enabled: true,
    music_mood: 'analytical',
    duck_db: -11,
    bed_db: -19,
    target_lufs: -14,
  },
  private_context_allowlist: {
    research_topics: true,
    agent_rules: true,
    intelligence_flags: false,
    market_snapshots: false,
    macro_indicators: false,
    portfolio_themes: false,
    portfolio_values: false,
  },
};

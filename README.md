# JoeMoyo Business Agent System

AI-powered agents for your multi-brand business — built with Python and Claude AI.

## Your Businesses

| Business | Agent |
|---|---|
| YouTube Historical Channel | ContentResearchAgent + ScriptWriterAgent |
| YouTube Finance Channel | FinancialContentAgent + ScriptWriterAgent |
| Music Studio | LeadGeneratorAgent |
| Shopify Store | ShopifyReportingAgent |

All brands → **MarketingAgent**

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up your API keys

```bash
cp .env.example .env
```

Open `.env` and add your keys:

```
ANTHROPIC_API_KEY=sk-ant-...       # Required — get from console.anthropic.com
BRAVE_SEARCH_API_KEY=BSA...        # For web search — get from api.search.brave.com
SHOPIFY_SHOP_NAME=yourstore.myshopify.com   # For Shopify reports
SHOPIFY_ACCESS_TOKEN=shpat_...     # From Shopify Admin > Apps > Develop apps
```

### 3. Run your first agent

```bash
python main.py history --topic "The Fall of the Roman Empire"
```

---

## Commands

### History YouTube Channel

```bash
# Full pipeline: research + script + social media bundle
python main.py history --topic "The Fall of Constantinople"

# Write script only (no web research)
python main.py history --topic "Ancient Egypt" --script-only
```

### Finance YouTube Channel

```bash
# Full pipeline: analysis + script + social media bundle
python main.py finance --topic "Bitcoin ETF Impact on Retail Investors"

# Generate video ideas
python main.py finance --topic "stock market investing" --ideas-only --count 15
```

### Shopify Reporting

```bash
# Weekly report
python main.py shopify --report weekly

# Monthly report
python main.py shopify --report monthly
```

### Lead Generation

```bash
# Music studio client outreach
python main.py leads --type studio --name "The Jazz Quartet" --genre "Jazz" --followers "5k Instagram"

# YouTube sponsorship pitch
python main.py leads --type sponsor --name "Squarespace" --industry "website builder" --channel history_channel
```

### Marketing Content

```bash
# Social media bundle for any brand
python main.py market --brand history_channel --topic "New video: Fall of Rome"
python main.py market --brand music_studio --topic "Studio summer special offer"
python main.py market --brand shopify_store --topic "New product launch"

# Email newsletter
python main.py market --brand finance_channel --topic "This week's market recap" --type email

# Ad copy
python main.py market --brand music_studio --topic "Recording studio services" --type ads
```

### Content Calendar

```bash
# Generate 4-week content ideas for both YouTube channels
python main.py ideas --weeks 4
```

### 🎬 Video Production Crew

A team of role-specialized agents that take a topic all the way to a finished
video. Each agent owns one job, and **Supabase (ORIGINEX HUMAN ARCHIVES) is the
source of truth** — every episode, output, asset, and render is persisted there.

```bash
# Full crew: research → script → packaging → thumbnail → visuals →
#            voiceover → motion → manifest, persisted + materialized
python main.py produce --topic "Great Zimbabwe" --channel history_channel

# Also render the mp4 (needs ElevenLabs narration; uses Remotion, falls back to ffmpeg)
python main.py produce -t "Great Zimbabwe" -c history_channel --render

# Re-export an existing episode's package from Supabase
python main.py materialize <episode_id>
```

The crew:

| Role | Agent | Produces |
|---|---|---|
| Research | `ContentResearchAgent` (+ archive) | sourced research outline |
| Script | `ScriptWriterAgent` | full narration script |
| Packaging | `TitlePackagingAgent` | titles (A/B), tags, description, chapters |
| Thumbnail | `ThumbnailAgent` | concept + image-gen prompt |
| Visuals | `VisualDirectorAgent` | ordered shot list / image prompts |
| Voiceover | `VoiceoverAgent` | clean narration + ElevenLabs mp3 |
| Motion | `MotionGraphicsAgent` | Remotion cards (intro, lower-thirds, stats, quotes) |
| Edit | `ManifestEditorAgent` | `manifest.json` + `captions.srt` (no Ken Burns "pop") |
| Director | `VideoProducer` | runs all of the above, persists, renders |

Each video becomes a self-contained package under `outputs/videos/<...>/`
(research/script/packaging/shotlist/manifest/captions/narration + generated
`img/` and `out.mp4`), mirrored from its Supabase episode row.

**Extra keys** (all optional — without them the crew runs in specs-only mode):
`SUPABASE_URL` / `SUPABASE_SERVICE_KEY`, `OPENAI_API_KEY` or `GEMINI_API_KEY`
(`IMAGE_PROVIDER`), `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID`. See
`.env.example`. The Remotion compositor lives in `remotion/` (run `npm install`
there first); the Supabase schema is `migrations/drafts/001_*`.

---

## Output Files

All generated content is saved to `outputs/`:

```
outputs/
├── scripts/      # YouTube research outlines and scripts
├── marketing/    # Social posts, emails, ad copy
├── leads/        # Outreach sequences and sponsorship pitches
└── reports/      # Shopify performance reports
```

---

## Customize Your Brands

Edit `config/brand_profiles.py` to update your channel names, tone, audience, and CTAs.

---

## Architecture

```
main.py (CLI)
    ├── orchestrator/orchestrator.py (business workflows)
    │       ├── agents/content_research.py  → tools/web_search.py
    │       ├── agents/script_writer.py
    │       ├── agents/financial_content.py → tools/web_search.py
    │       ├── agents/marketing.py
    │       ├── agents/shopify_reporting.py → tools/shopify_client.py
    │       └── agents/lead_generator.py   → tools/web_search.py
    │
    └── orchestrator/video_producer.py (video crew, Supabase = truth)
            ├── agents/video/title_packaging.py
            ├── agents/video/thumbnail.py
            ├── agents/video/visual_director.py
            ├── agents/video/motion_graphics.py
            ├── agents/video/voiceover.py      → tools/elevenlabs.py
            ├── agents/video/manifest_editor.py
            ├── tools/supabase_client.py  (ORIGINEX HUMAN ARCHIVES)
            ├── tools/images.py           (openai / gemini)
            ├── video_agent/  (ffmpeg Ken Burns render engine)
            └── remotion/     (motion-graphics render engine)
```

All agents inherit from `agents/base_agent.py` which handles the Claude tool-use loop automatically.

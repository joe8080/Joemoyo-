"""
Brand voice profiles for all JoeMoyo businesses.
Each agent reads from here to ensure consistent tone and messaging.
Update the values below to match your brand preferences.
"""

BRAND_PROFILES = {
    "history_channel": {
        "name": "Chronicles of Time",
        "tone": "authoritative, engaging, narrative-driven, research-backed, cinematic",
        "audience": "history enthusiasts, students, curious learners aged 25-55",
        "style": "documentary-style storytelling with academic rigor",
        "cta": "Like and subscribe so you never miss a story from history",
        "keywords": ["historical facts", "primary sources", "timeline", "impact", "legacy"],
        "niches": ["ancient civilizations", "wars", "empires", "biographies", "revolutions"],
    },
    # OrigineX Human Archives — the OGX channel. Unlike the profiles above, this
    # one is evidence-gated: every claim is checked against the OGX research
    # database before it reaches a script, card, thumbnail, or description.
    "origine_x": {
        "name": "OrigineX Human Archives",
        "handle": "@originexhumanarchives",
        "channel_id": "UC_VwS819y4GZgNmYajBvm3Q",
        "tone": "authoritative, cinematic, evidence-first, unflinching, UK English",
        "audience": "UK/US viewers 25-45, African and world history, diaspora audiences",
        "style": "faceless prestige documentary — gold-on-near-black, receipts over rhetoric",
        "cta": (
            "Subscribe. Share with someone who was never taught this. "
            "Next episode — {next_video}."
        ),
        "keywords": ["declassified", "primary sources", "suppressed history",
                     "African civilisation", "statecraft", "archives"],
        "niches": ["African empires", "statecraft and covert policy", "biographies",
                   "ancient civilisations", "colonial and post-colonial history"],
        # Two locked looks. "archives" is the default house style; "declassified"
        # is the receipts-documentary variant (the West Sabotage formula).
        "palette": {
            "gold": "#C9A84C",
            "dark": "#1A1A2E",
            "crimson": "#8B1A1A",
            "amber": "#FFF3CD",
            "teal": "#0F4C75",
            "white": "#FFFFFF",
        },
        "declassified_palette": {
            "gold": "#C9A24B",
            "dark": "#0A0A0A",
            "red": "#B0231F",
            "body": "#F2EDE4",
            "box_fill": "#0E0E10",
            "box_border": "#C9A24B",
        },
        # Brand-anchor thumbnails passed as reference images at generation time.
        "thumbnail_references": [
            "https://i.ytimg.com/vi/t0B1-f8JH-s/maxresdefault.jpg",
            "https://i.ytimg.com/vi/YVW5lv94K9Q/maxresdefault.jpg",
        ],
        # Locked narration voice. Chosen by A/B on the Mansa Musa cold open
        # against Cillian and Fraser; Fraser read the same text 10 seconds
        # faster, which is wrong for a prestige documentary.
        "voice": {
            "name": "Arthur",
            "provider": "highfield",
            "model": "seed_audio",
            "voice_id": "30fc8796-ceb6-4a66-b3a7-4a145ef7f346",
            "voice_type": "preset",
            "register": "male, older — elder-statesman documentary read",
            # Measured over the full 2,577-word Mansa Musa narration, not
            # estimated: Arthur reads at 141 wpm at default speech_rate. The
            # script prompts assume 130, so scripts run ~8% long — a 14:00
            # target came out at 18:17. Budget words against 141.
            "pace_wpm": 141,
        },
        "cadence": "Tue = person/biographical, Thu = civilisation/topic, ~19:00 Europe/London",
        "language": "UK English (honour, civilisation, recognised, manoeuvre)",
    },
    "finance_channel": {
        "name": "Capital Edge",
        "tone": "analytical, confident, balanced, plain-English, actionable",
        "audience": "retail investors, working professionals, ages 28-50",
        "style": "data-driven insights with clear takeaways, no fluff",
        "cta": "Subscribe for weekly market analysis — hit the bell so you never miss a video",
        "keywords": ["ROI", "portfolio", "market analysis", "risk management", "investing"],
        "niches": ["stocks", "crypto", "real estate", "ETFs", "personal finance", "economy"],
    },
    "music_studio": {
        "name": "JoeMoyo Studios",
        "tone": "creative, professional, collaborative, warm, passionate",
        "audience": "independent artists, bands, content creators, podcasters",
        "style": "creative partnership focused on world-class sound quality",
        "cta": "Book a free consultation — let's create something amazing together",
        "services": ["recording", "mixing", "mastering", "music production", "vocal coaching"],
        "usp": "Professional results at independent artist prices",
    },
    "shopify_store": {
        "name": "JoeMoyo Store",
        "tone": "friendly, enthusiastic, benefit-focused, trustworthy",
        "audience": "general online shoppers looking for quality and value",
        "style": "clear, benefit-driven product copy with strong social proof",
        "cta": "Shop now — free shipping on all orders",
        "usp": "Quality products with fast shipping and easy returns",
    },
}

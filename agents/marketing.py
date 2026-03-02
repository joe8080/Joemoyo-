"""
MarketingAgent: Creates marketing content for all JoeMoyo brands.

Generates social media posts, email newsletters, and ad copy
with brand-specific voice and tone for each business.
"""

from agents.base_agent import BaseAgent
from config.brand_profiles import BRAND_PROFILES
from prompts.marketing_prompts import MARKETING_SYSTEM_PROMPT


class MarketingAgent(BaseAgent):

    @property
    def system_prompt(self) -> str:
        return MARKETING_SYSTEM_PROMPT

    def _define_tools(self) -> list:
        return []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return "No tools defined for this agent"

    def create_social_bundle(
        self,
        brand: str,
        topic: str,
        platforms: list | None = None,
    ) -> str:
        """
        Create a full social media content bundle for a brand + topic.

        Args:
            brand: One of 'history_channel', 'finance_channel', 'music_studio', 'shopify_store'
            topic: The content topic or angle (e.g. "New YouTube video: Fall of Rome")
            platforms: List of platforms. Defaults to all major platforms.

        Returns: Complete social media bundle as markdown
        """
        if platforms is None:
            platforms = ["instagram", "twitter_x", "linkedin", "facebook", "tiktok"]

        brand_profile = BRAND_PROFILES.get(brand, {})
        prompt = f"""
Create a complete social media content bundle:

BRAND: {brand_profile.get('name', brand)}
TONE: {brand_profile.get('tone', 'professional')}
AUDIENCE: {brand_profile.get('audience', 'general')}
TOPIC/ANGLE: {topic}
CTA: {brand_profile.get('cta', 'Follow for more')}

Create native content for: {', '.join(platforms)}

For each platform, write:

INSTAGRAM:
- Caption (engaging, storytelling-style)
- 15 relevant hashtags
- Story slide text (3 slides)

TWITTER/X:
- Standalone viral tweet (under 280 chars)
- A thread version (5 tweets)

LINKEDIN:
- Professional long-form post (250-300 words, first-person perspective)

FACEBOOK:
- Engaging post with a question that drives comments

TIKTOK:
- Hook script (first 3 seconds — this determines if they keep watching)
- Full video caption

Also include:
CONTENT CALENDAR: Best days/times to post each platform for this brand's audience.
"""
        result = self.run(prompt)
        safe_brand = brand.replace("_", "-")
        self.save_output(result, "marketing", f"{safe_brand}_social_{self._timestamp()}.md")
        return result

    def write_email_newsletter(
        self,
        brand: str,
        topic: str,
        segment: str = "general subscribers",
    ) -> str:
        """
        Write a complete email newsletter.

        Args:
            brand: The brand to write for
            topic: Newsletter topic
            segment: Subscriber segment (e.g. "new subscribers", "VIP customers")

        Returns: Complete newsletter as markdown
        """
        brand_profile = BRAND_PROFILES.get(brand, {})
        prompt = f"""
Write a complete email newsletter:

BRAND: {brand_profile.get('name', brand)}
TONE: {brand_profile.get('tone', 'professional')}
TOPIC: {topic}
SUBSCRIBER SEGMENT: {segment}

Deliver:

SUBJECT LINES: (5 variations for A/B testing, ordered by predicted open rate)
PREVIEW TEXT: (under 90 characters, complements subject line)

EMAIL BODY:
- Header/greeting
- Opening hook (2-3 sentences)
- Main content (3 sections with subheadings, ~200 words total)
- Value section (tip, insight, or exclusive offer)
- CTA section with button text + what they land on
- P.S. line (P.S. lines get read almost as often as the subject line)

FORMAT: Clean markdown ready to paste into an email platform.
"""
        result = self.run(prompt)
        safe_brand = brand.replace("_", "-")
        self.save_output(result, "marketing", f"{safe_brand}_email_{self._timestamp()}.md")
        return result

    def write_ad_copy(
        self,
        brand: str,
        product_or_service: str,
        ad_platform: str = "facebook",
    ) -> str:
        """
        Write conversion-focused ad copy.

        Args:
            brand: The brand to write for
            product_or_service: What is being advertised
            ad_platform: 'facebook', 'google', 'youtube', 'tiktok'

        Returns: Complete ad copy variations as markdown
        """
        brand_profile = BRAND_PROFILES.get(brand, {})
        prompt = f"""
Write {ad_platform} ad copy for:

BRAND: {brand_profile.get('name', brand)}
PRODUCT/SERVICE: {product_or_service}
AUDIENCE: {brand_profile.get('audience', 'general')}
TONE: {brand_profile.get('tone', 'professional')}

Deliver 3 full ad variations using AIDA (Attention, Interest, Desire, Action):

For each variation:
- HEADLINE: (3 options, platform character limit)
- PRIMARY TEXT: (short / medium / long versions)
- DESCRIPTION: (under 30 words)
- CTA BUTTON: (choose best option for this goal)

Also include:
- TARGETING NOTES: Suggested Facebook/Google audience targeting
- CREATIVE BRIEF: What the image/video should show
- WINNING CRITERIA: How to know which ad is performing best
"""
        result = self.run(prompt)
        safe_brand = brand.replace("_", "-")
        self.save_output(result, "marketing", f"{safe_brand}_ads_{self._timestamp()}.md")
        return result

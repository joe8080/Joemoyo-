"""
LeadGeneratorAgent: Creates sales outreach sequences and lead qualification tools.

Generates cold outreach emails, follow-up sequences, and lead qualification
questionnaires for:
- Music studio client acquisition (recording, mixing, mastering, production)
- YouTube channel sponsorship deals
"""

from agents.base_agent import BaseAgent
from config.brand_profiles import BRAND_PROFILES
from prompts.lead_gen_prompts import LEAD_GEN_SYSTEM_PROMPT
from tools.web_search import web_search, format_search_results


class LeadGeneratorAgent(BaseAgent):

    @property
    def system_prompt(self) -> str:
        return LEAD_GEN_SYSTEM_PROMPT

    def _define_tools(self) -> list:
        return [
            {
                "name": "research_prospect",
                "description": (
                    "Research a specific prospect or company before writing outreach. "
                    "Use to find their music genre, social following, recent releases, "
                    "or business details to personalize the pitch."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "prospect_name": {
                            "type": "string",
                            "description": "Name of the artist, band, or company to research",
                        },
                        "prospect_type": {
                            "type": "string",
                            "description": "Type of prospect",
                            "enum": ["music_artist", "band", "brand_sponsor", "podcast"],
                        },
                    },
                    "required": ["prospect_name", "prospect_type"],
                },
            },
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "research_prospect":
            query = f"{tool_input['prospect_name']} {tool_input['prospect_type']} music social media"
            results = web_search(query, num_results=5)
            return format_search_results(results)
        return f"Unknown tool: {tool_name}"

    def create_studio_outreach(self, prospect: dict) -> str:
        """
        Create a full outreach sequence for a music studio prospect.

        Args:
            prospect: dict with keys like 'name', 'genre', 'followers', 'recent_work'

        Returns: Complete 4-email outreach sequence as markdown
        """
        studio = BRAND_PROFILES["music_studio"]
        prompt = f"""
Create a 4-email cold outreach sequence to get a recording client for {studio['name']}.

STUDIO INFO:
- Name: {studio['name']}
- Services: {', '.join(studio.get('services', []))}
- USP: {studio.get('usp', 'Professional quality at indie prices')}
- Tone: {studio['tone']}
- CTA: {studio['cta']}

PROSPECT INFO:
{prospect}

Research the prospect if you need more context.

EMAIL SEQUENCE:
- Email 1 (Day 1): Cold intro — lead with THEIR music, not our services. Soft CTA.
- Email 2 (Day 4): Follow-up — add value (a tip, insight, or resource). Medium CTA.
- Email 3 (Day 9): Social proof — share a result or testimonial relevant to them.
- Email 4 (Day 15): Breakup email — respectful close, leave door open.

For each email:
SUBJECT LINE: (3 variations)
BODY: (full email text with [PERSONALIZATION] placeholders)
SEND TIME: (best day/time to send)
GOAL: (what this email is trying to achieve)

Also create:
LEAD QUALIFICATION QUESTIONNAIRE: 8 questions to send after a positive reply
to determine budget, timeline, vision, and fit.
"""
        result = self.run(prompt)
        name = str(prospect.get("name", "prospect")).replace(" ", "_")[:30]
        self.save_output(result, "leads", f"studio_{name}_{self._timestamp()}.md")
        return result

    def create_sponsorship_pitch(self, brand_info: dict, channel: str = "history_channel") -> str:
        """
        Create a YouTube sponsorship pitch for a brand.

        Args:
            brand_info: dict with 'name', 'industry', 'product' etc.
            channel: 'history_channel' or 'finance_channel'

        Returns: Sponsorship pitch package as markdown
        """
        channel_profile = BRAND_PROFILES[channel]
        prompt = f"""
Create a complete YouTube sponsorship pitch package.

OUR CHANNEL:
- Name: {channel_profile['name']}
- Audience: {channel_profile['audience']}
- Tone: {channel_profile['tone']}

BRAND TO PITCH:
{brand_info}

Research the brand to understand their products and marketing.

DELIVER:
1. COLD OUTREACH EMAIL (to their marketing/partnerships team)
   - 3 subject line options
   - Full email (~200 words — short enough to read, long enough to sell)
   - Why this brand fits this channel's audience

2. SPONSORSHIP MEDIA KIT OUTLINE
   - Channel stats section (placeholder for real numbers)
   - Audience demographics
   - Content categories and engagement highlights
   - Sponsorship packages (pre-roll, mid-roll, dedicated video)
   - Pricing placeholder guidance

3. FOLLOW-UP SEQUENCE
   - 2-week follow-up
   - 1-month follow-up (final)

4. SPONSOR INTEGRATION SCRIPT TEMPLATE
   - 60-second mid-roll read template
   - 30-second pre-roll template
"""
        result = self.run(prompt)
        brand_name = str(brand_info.get("name", "brand")).replace(" ", "_")[:30]
        self.save_output(result, "leads", f"sponsorship_{brand_name}_{self._timestamp()}.md")
        return result

    def qualify_lead(self, lead_info: dict) -> str:
        """
        Score and qualify an inbound lead, and draft a response email.

        Args:
            lead_info: dict with details about the inbound inquiry

        Returns: Lead qualification assessment + response draft
        """
        studio = BRAND_PROFILES["music_studio"]
        prompt = f"""
Analyze and qualify this inbound lead for {studio['name']}:

LEAD INFORMATION:
{lead_info}

Provide:
1. LEAD SCORE: (1-10) with reasoning
2. ICP MATCH: How well do they match our ideal client profile?
3. ESTIMATED DEAL VALUE: (range)
4. RECOMMENDED NEXT ACTION: (immediate call, email discovery, schedule demo, politely decline, nurture)
5. RESPONSE EMAIL: Personalized reply to send immediately
6. CRM NOTES: Internal notes for follow-up (next steps, flags, timeline)
"""
        result = self.run(prompt)
        self.save_output(result, "leads", f"lead_qual_{self._timestamp()}.md")
        return result

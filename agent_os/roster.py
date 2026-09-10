"""
The repo's agents, described the way the Agent OS roster expects them.

The OS (Supabase `agent_ops_roster`) already holds the Chief (Mary Jane), her
supervisors and the Grok workers. These entries plug the JoeMoyo Python agents
into that same hierarchy: each one reports to an existing supervisor, gets its
own x-agent-key, and shows up on the board under that supervisor.

Field guide (roster columns):
    agent_key     lowercase, underscores — used in every API call
    display_name  what the board shows
    role          worker | venture | supervisor | chief   (roster CHECK)
    domain        investing | content | originex | studio | shopify | systems
    reports_to    an existing supervisor's agent_key
    provider      claude (Claude agents) | python (deterministic bots)
    capabilities  what it can do (shown as chips; also the key's scopes)
    notes         one-line job description

Board config (stored in agent_connections.metadata.board):
    schedule      human sentence
    url           link to its logs / workflow
    stale_after_s continuously-running agents: quiet for this long → offline
    runner        the OS Runner can execute tasks for it (see runners.py)
    run_label     what the board's Run button says
    input_hint    what the Run box asks for (None → no input needed)
"""

ROSTER: list[dict] = [
    {
        "agent_key": "agent_os_runner",
        "display_name": "OS Runner (Claude)",
        "role": "worker", "domain": "systems", "reports_to": "systems_supervisor",
        "provider": "claude",
        "capabilities": ["run_tasks", "heartbeat", "python_agents"],
        "notes": "Runs the JoeMoyo Python agents: pulls their tasks from the OS, executes, reports back.",
        "board": {"schedule": "Always on while `python main.py os worker` runs",
                  "stale_after_s": 180},
    },
    # ---- Trading desk (finance_supervisor) ------------------------------ #
    {
        "agent_key": "swing_trader",
        "display_name": "Swing Trader",
        "role": "worker", "domain": "investing", "reports_to": "finance_supervisor",
        "provider": "python",
        "capabilities": ["paper_trading", "sma_crossover", "risk_exits"],
        "notes": "SMA 20/50 crossover over 10 mega-caps on the Alpaca paper account, 8% trailing stop. Paper only.",
        "board": {"schedule": "Every 30 min, US market hours (GitHub Actions)",
                  "url": "https://github.com/joe8080/Joemoyo-/actions/workflows/autotrade.yml",
                  "runner": True, "run_label": "Dry-run cycle", "input_hint": None},
    },
    {
        "agent_key": "intraday_trader",
        "display_name": "Intraday Engine",
        "role": "worker", "domain": "investing", "reports_to": "finance_supervisor",
        "provider": "python",
        "capabilities": ["paper_trading", "opening_range_breakout", "flatten_eod"],
        "notes": "Opening-range breakout on NFLX/AVGO/COIN/IWM/SMH, flattens before the bell. Paper only.",
        "board": {"schedule": "Always on (Railway) — trades every 5 min while the market is open",
                  "url": "https://railway.app", "stale_after_s": 25 * 60},
    },
    {
        "agent_key": "trading_coach",
        "display_name": "Trading Coach",
        "role": "worker", "domain": "investing", "reports_to": "finance_supervisor",
        "provider": "claude",
        "capabilities": ["journal", "review", "tendencies"],
        "notes": "Reviews the day's paper round trips, writes the coach note and recurring tendencies.",
        "board": {"schedule": "Weekdays 21:20 UK, after the US close (GitHub Actions)",
                  "url": "https://github.com/joe8080/Joemoyo-/actions/workflows/daily-close.yml",
                  "runner": True, "run_label": "Write coach note", "input_hint": None},
    },
    {
        "agent_key": "trading_analyst",
        "display_name": "Trading Analyst",
        "role": "worker", "domain": "investing", "reports_to": "finance_supervisor",
        "provider": "claude",
        "capabilities": ["paper_account_overview", "ticker_analysis"],
        "notes": "Claude desk analyst on the paper account: overview, ticker analysis. Never places orders from the board.",
        "board": {"schedule": "On demand", "runner": True, "run_label": "Account overview",
                  "input_hint": "Optional ticker, e.g. NVDA — leave blank for the account overview"},
    },
    # ---- OrigineX (originex_supervisor) --------------------------------- #
    {
        "agent_key": "history_researcher",
        "display_name": "History Researcher",
        "role": "worker", "domain": "originex", "reports_to": "originex_supervisor",
        "provider": "claude",
        "capabilities": ["research", "web_search", "sources"],
        "notes": "Deep-researches a historical topic for the OrigineX channel with cited sources.",
        "board": {"schedule": "On demand", "runner": True, "run_label": "Research topic",
                  "input_hint": "Topic, e.g. The Kingdom of Kush"},
    },
    {
        "agent_key": "history_script_writer",
        "display_name": "History Script Writer",
        "role": "worker", "domain": "originex", "reports_to": "originex_supervisor",
        "provider": "claude",
        "capabilities": ["script", "narration"],
        "notes": "Turns research (or a topic) into a 12-minute narration script.",
        "board": {"schedule": "On demand", "runner": True, "run_label": "Write script",
                  "input_hint": "Topic or pasted research"},
    },
    # ---- Finance channel & growth (content_supervisor) ------------------- #
    {
        "agent_key": "finance_analyst_writer",
        "display_name": "Finance Analyst",
        "role": "worker", "domain": "content", "reports_to": "content_supervisor",
        "provider": "claude",
        "capabilities": ["analysis", "uk_translation", "video_ideas"],
        "notes": "Analyses a finance topic for the finance channel, translated to the UK context.",
        "board": {"schedule": "On demand", "runner": True, "run_label": "Analyse topic",
                  "input_hint": "Topic, e.g. Bitcoin ETF impact on UK retail investors"},
    },
    {
        "agent_key": "finance_script_writer",
        "display_name": "Finance Script Writer",
        "role": "worker", "domain": "content", "reports_to": "content_supervisor",
        "provider": "claude",
        "capabilities": ["script", "narration"],
        "notes": "Turns analysis (or a topic) into a 15-minute finance script.",
        "board": {"schedule": "On demand", "runner": True, "run_label": "Write script",
                  "input_hint": "Topic or pasted analysis"},
    },
    {
        "agent_key": "marketing_writer",
        "display_name": "Marketing",
        "role": "worker", "domain": "content", "reports_to": "content_supervisor",
        "provider": "claude",
        "capabilities": ["social_bundle", "newsletter", "ad_copy"],
        "notes": "Social bundles, newsletters and ad copy for every brand. Drafts only — nothing is posted.",
        "board": {"schedule": "On demand", "runner": True, "run_label": "Social bundle",
                  "input_hint": "Topic — prefix with a brand to target it: history_channel: New video out"},
    },
    # ---- Ventures (venture_supervisor) ---------------------------------- #
    {
        "agent_key": "studio_lead_generator",
        "display_name": "Studio Lead Generator",
        "role": "worker", "domain": "studio", "reports_to": "venture_supervisor",
        "provider": "claude",
        "capabilities": ["outreach_sequences", "sponsor_pitches"],
        "notes": "Cold outreach sequences for music studio clients and YouTube sponsor pitches. Drafts only.",
        "board": {"schedule": "On demand", "runner": True, "run_label": "Studio outreach",
                  "input_hint": "Prospect, e.g. The Jazz Quartet, Jazz, 5k Instagram"},
    },
    {
        "agent_key": "shopify_reporter",
        "display_name": "Shopify Reporter",
        "role": "worker", "domain": "shopify", "reports_to": "venture_supervisor",
        "provider": "claude",
        "capabilities": ["sales_report", "weekly", "monthly"],
        "notes": "Weekly and monthly Shopify store performance reports.",
        "board": {"schedule": "On demand (weekly report by default)", "runner": True,
                  "run_label": "Weekly report", "input_hint": "Leave blank for weekly, or type: monthly"},
    },
]

# Class name → agent_key, for agents that report through BaseAgent.
CLASS_KEYS = {
    "ContentResearchAgent": "history_researcher",
    "FinancialContentAgent": "finance_analyst_writer",
    "MarketingAgent": "marketing_writer",
    "LeadGeneratorAgent": "studio_lead_generator",
    "ShopifyReportingAgent": "shopify_reporter",
    "TradingAgent": "trading_analyst",
}

# Agents already in the OS that the built-ins report to (must exist there).
SUPERVISORS = ["chief", "finance_supervisor", "content_supervisor", "originex_supervisor",
               "venture_supervisor", "systems_supervisor", "household_supervisor", "memory_steward"]


def by_key() -> dict[str, dict]:
    return {a["agent_key"]: a for a in ROSTER}

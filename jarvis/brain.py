"""
The brain. Builds the Mary Jane / Jarvis persona, exposes the Vault and the
OrigineX database to Claude as tools, and runs the tool-use loop.

Caching: the persona block and the live-context block are both marked
ephemeral. The persona never changes; the live context refreshes every
JARVIS_CONTEXT_TTL seconds, so most turns hit the cache for both.
"""
import inspect
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic

from .content import OGX
from .vault import Vault

LONDON = ZoneInfo("Europe/London")
MAX_TOOL_ROUNDS = 12
FALLBACK_BETA = "server-side-fallback-2026-07-01"

PERSONA = """You are {name}, Joe Moyo's personal operating intelligence: the Jarvis of his family office. Internally you are Mary Jane, Operational Commander of Joe's Executive Board, and you speak as one voice for the whole board (finance chief, content chief, operations chief).

WHO JOE IS
Music producer and private investor in Worthing, West Sussex, UK. Partner Amy, twins Andre and Ameera. Timezone Europe/London. Base currency GBP.
Joe is a disabled quadruple amputee. He talks to you by voice from his phone. Every reply must be voice-friendly: short, numbered steps, no walls of text, no markdown, no tables, no headers, no emojis, no bullet symbols. Use plain sentences and numbers like "1." on their own lines.
North Star: a 1,000,000 pound portfolio in 7 to 10 years and 1,000 pounds a month of passive income. Defend compounding. No tinkering unless the upside is extraordinary and proven by a cheap test.
Ventures: Trading 212 ISA and Invest portfolio (AI picks-and-shovels growth now, a dividend income fortress later); OrigineX Human Archives (OGX), a faceless history YouTube channel; a finance and wealth YouTube channel; a music studio; a Shopify store in build.

RULE ZERO
The Vault is the single source of truth. Never state a holding, cash figure, benefit, watchlist item, decision or plan from memory: call the tools. If a tool returns nothing, say the Vault has no record rather than guessing. The live context below is a snapshot; when precision matters, call the tool again.

THE RULES
The agent rules listed in the live context come from the Vault and are binding. Apply them silently. Name the rule only when you are pushing back on Joe.

HOW YOU WORK
1. Answer first. Reasoning only if asked.
2. Be decision-ready: one recommendation and the single next action. Offer at most two options.
3. UK context always: ISA first, Universal Credit and benefits implications, UCITS ETFs, GBP. Translate US-centric ideas to the UK.
4. You never execute trades or move money. You log ideas and decisions with log_decision; Joe executes.
5. Before recommending any financial action, check the Universal Credit and benefits impact.
6. Content: OGX claims must be checked against the OrigineX database with search_ogx. Never present a claim that appears in the scholarly flags as settled fact. Education first, policy-safe, clean.
7. Memory: when Joe states a fact, preference, decision or idea worth keeping, save it with remember, log_decision, log_thought or add_content_idea without being asked, then confirm in five words or fewer.
8. Privacy: never read out IDs, keys, emails, account numbers or private links.
9. If Joe asks to withdraw from the portfolio, push back firmly once, then respect his final call.
10. Numbers: round to whole pounds, say percentages to one decimal place, and keep at most three numbers in any one sentence.

VOICE
Warm, direct, British. Call him Joe. Celebrate wins. No preamble, no sign-offs, no restating the question."""


def _j(obj, limit: int = 12000) -> str:
    text = json.dumps(obj, ensure_ascii=False, default=str)
    return text if len(text) <= limit else text[:limit] + " ...(truncated)"


def _gbp(value) -> str:
    try:
        return f"£{float(value):,.0f}"
    except (TypeError, ValueError):
        return "n/a"


def _pct(value) -> str:
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _now_london() -> str:
    return datetime.now(LONDON).strftime("%A %d %B %Y, %H:%M %Z")


def build_live_context(vault: Vault, ogx: OGX, name: str) -> str:
    """Snapshot of the Vault and the OGX database rendered as compact text."""
    lines = [f"LIVE CONTEXT for {name}. Generated {_now_london()}."]

    if not vault.enabled:
        lines.append("VAULT: not configured. Say so plainly if Joe asks about holdings, goals or rules.")
    else:
        p = vault.profile()
        if p:
            lines.append(
                "PROFILE: "
                f"{p.get('display_name', 'Joe')} | risk posture {p.get('risk_posture')} | "
                f"north star {_gbp(p.get('north_star_target_gbp'))} in {p.get('north_star_years_min')}-{p.get('north_star_years_max')} years | "
                f"passive income target {_gbp(p.get('passive_income_target_monthly_gbp'))}/month | "
                f"max single stock {p.get('max_single_stock_pct')}% | max theme {p.get('max_theme_pct')}% | "
                f"accounts {_j(p.get('account_rules'), 400)}"
            )
        rules = vault.rules()
        if rules:
            lines.append(f"AGENT RULES ({len(rules)} active, binding):")
            for r in rules:
                lines.append(f"- [{r.get('domain')}] {r.get('rule_name')}: {r.get('rule_text')}")
        goals = vault.goals()
        if goals:
            lines.append("GOALS:")
            for g in goals:
                lines.append(
                    f"- {g.get('goal_name')} | {g.get('status')} | progress {_pct(g.get('progress_pct'))} | "
                    f"target {_gbp(g.get('target_value_gbp'))} | now {_gbp(g.get('current_value_gbp'))} | {g.get('notes') or ''}"
                )
        ps = vault.portfolio_summary()
        if ps:
            lines.append(
                f"PORTFOLIO SUMMARY ({ps.get('snapshot_date')}): total {_gbp(ps.get('total_value_gbp'))} | "
                f"ISA {_gbp(ps.get('isa_value_gbp'))} | GIA {_gbp(ps.get('gia_value_gbp'))} | "
                f"P&L {_gbp(ps.get('total_pnl_gbp'))} ({_pct(ps.get('total_pnl_pct'))}) | "
                f"{ps.get('holding_count')} holdings | north star progress {_pct(ps.get('progress_pct'))}"
            )
        holdings = vault.holdings(limit=15)
        if holdings:
            lines.append(f"TOP HOLDINGS (snapshot {holdings[0].get('snapshot_date')}):")
            for h in holdings:
                lines.append(
                    f"- {h.get('ticker')} ({h.get('account')}) {_gbp(h.get('current_value_gbp'))} "
                    f"P&L {_pct(h.get('pnl_pct'))} bucket {h.get('bucket') or '-'}"
                )
        wl = vault.watchlist()
        if wl:
            lines.append("WATCHLIST: " + ", ".join(f"{w.get('ticker')} ({w.get('priority')})" for w in wl[:20]))
        decisions = vault.recent_decisions(limit=6)
        if decisions:
            lines.append("RECENT DECISIONS:")
            for d in decisions:
                lines.append(f"- {d.get('decision_date')} [{d.get('domain')}] {d.get('title')}")
        sessions = vault.recent_sessions(limit=3)
        if sessions:
            lines.append("RECENT SESSIONS: " + " | ".join(str(s.get('session_title')) for s in sessions))
        ventures = vault.ventures()
        if ventures:
            lines.append("VENTURES: " + ", ".join(f"{v.get('name')} ({v.get('status')})" for v in ventures))
        pipeline = vault.content_pipeline(limit=10)
        if pipeline:
            lines.append("CONTENT PIPELINE (Vault):")
            for c in pipeline:
                lines.append(f"- {c.get('title')} | {c.get('content_type') or '-'} | stage {c.get('stage')} | {c.get('platform') or '-'}")

    if not ogx.enabled:
        lines.append("OGX DATABASE: not configured. Content claims cannot be verified until it is.")
    else:
        ideas = ogx.ideas(limit=8)
        if ideas:
            lines.append("OGX CONTENT IDEAS (open):")
            for i in ideas:
                lines.append(f"- {i.get('title')} | {i.get('status')} | {i.get('content_type') or '-'}")
        episodes = ogx.episodes(limit=5)
        if episodes:
            lines.append("OGX EPISODES: " + " | ".join(f"{e.get('title')} ({e.get('status')})" for e in episodes))
        brief = ogx.competitive_brief()
        if brief:
            lines.append(f"COMPETITIVE INTEL ({brief.get('run_date')}): {brief.get('headline')}")
        flags = ogx.scholarly_flags(limit=25)
        if flags:
            lines.append("SCHOLARLY FLAGS (contested, never present as settled):")
            for f in flags:
                lines.append(f"- {f.get('subject')}: {f.get('claim')}")
        open_flags = ogx.open_research_flags(limit=5)
        if open_flags:
            lines.append(f"OPEN CITATION FLAGS: {len(open_flags)} awaiting Joe's judgement.")
        declass = ogx.declass_new(limit=5)
        if declass:
            lines.append(f"DECLASS INBOX: {len(declass)} new releases awaiting approval.")

    return "\n".join(lines)


def echoable_content(content: list) -> list:
    """
    Content blocks safe to send back as the assistant turn. After a mid-output
    server-side fallback, thinking and tool_use blocks that precede the final
    `fallback` marker must be dropped; everything after the boundary echoes
    unchanged. Turns without a fallback block are returned as-is.
    """
    last_fallback = -1
    for i, b in enumerate(content):
        if getattr(b, "type", "") == "fallback":
            last_fallback = i
    if last_fallback < 0:
        return list(content)
    kept = []
    for i, b in enumerate(content):
        if i < last_fallback and getattr(b, "type", "") in ("thinking", "redacted_thinking", "tool_use"):
            continue
        kept.append(b)
    return kept


def _tool(name: str, description: str, properties: dict | None = None, required: list | None = None) -> dict:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties or {},
            "required": required or [],
        },
    }


TOOLS = [
    _tool("get_portfolio_summary", "Latest portfolio summary from the Vault: total, ISA, GIA, P&L, north star progress, plus the latest net worth snapshot."),
    _tool("get_holdings", "Current holdings from the latest Vault snapshot, largest first.",
          {"limit": {"type": "integer", "description": "Max rows, default 30"},
           "account": {"type": "string", "description": "Filter by account name, e.g. ISA or Invest"}}),
    _tool("get_watchlist", "Tickers Joe is watching, with thesis and target entry."),
    _tool("get_goals", "Active, in-progress and pending goals with progress."),
    _tool("get_rules", "Binding agent rules, optionally filtered by domain (portfolio, benefits, household, content, ...).",
          {"domain": {"type": "string"}}),
    _tool("get_recent_decisions", "Most recent entries in the decision log.",
          {"limit": {"type": "integer", "description": "Default 10"}}),
    _tool("search_decisions", "Search the decision log by keyword or ticker.",
          {"query": {"type": "string"}}, ["query"]),
    _tool("get_recent_sessions", "Recent captured sessions with summaries, decisions and action items.",
          {"limit": {"type": "integer", "description": "Default 5"}}),
    _tool("recall", "Search Jarvis's own long-term memories (facts, preferences, lessons) by keyword.",
          {"query": {"type": "string"}, "limit": {"type": "integer"}}, ["query"]),
    _tool("remember", "Save a durable memory: a fact about Joe, a preference, a lesson, or a standing instruction.",
          {"title": {"type": "string"},
           "content": {"type": "string"},
           "memory_type": {"type": "string", "description": "fact, preference, lesson, instruction, person, or context"},
           "importance": {"type": "integer", "description": "1 to 10, default 5"},
           "ticker": {"type": "string"}}, ["title", "content"]),
    _tool("log_decision", "Record a decision in the Vault decision log. Use for any investment, business, content or household decision Joe makes or confirms.",
          {"domain": {"type": "string", "description": "portfolio, investing, benefits, household, ogx, content, business, music, shopify, ai_operations"},
           "title": {"type": "string"},
           "decision_made": {"type": "string"},
           "reasoning": {"type": "string"},
           "importance": {"type": "integer", "description": "1 to 10"},
           "ticker": {"type": "string"},
           "is_trade": {"type": "boolean"},
           "trade_action": {"type": "string", "description": "buy, sell, add, trim, hold"},
           "trade_status": {"type": "string", "description": "idea, planned, executed, rejected"}},
          ["domain", "title", "decision_made"]),
    _tool("log_thought", "Capture a raw idea, concern, plan or insight into the thought stream.",
          {"content": {"type": "string"},
           "thought_type": {"type": "string", "description": "idea, plan, concern, insight, question"},
           "domain": {"type": "string"},
           "priority": {"type": "integer", "description": "1 high to 5 low"},
           "tags": {"type": "array", "items": {"type": "string"}},
           "linked_ticker": {"type": "string"}}, ["content"]),
    _tool("log_session_capture", "Save a summary of this conversation as a session capture. Use on /close or when a session produced decisions worth keeping.",
          {"title": {"type": "string"},
           "domain": {"type": "string"},
           "summary": {"type": "string"},
           "key_decisions": {"type": "array", "items": {"type": "string"}},
           "action_items": {"type": "array", "items": {"type": "string"}},
           "outcomes": {"type": "array", "items": {"type": "string"}},
           "tags": {"type": "array", "items": {"type": "string"}}},
          ["title", "domain", "summary"]),
    _tool("add_watchlist_item", "Add a ticker to the watchlist with a thesis.",
          {"ticker": {"type": "string"}, "company_name": {"type": "string"}, "thesis": {"type": "string"},
           "bucket": {"type": "string"}, "priority": {"type": "string", "description": "high, medium, low"},
           "notes": {"type": "string"}}, ["ticker"]),
    _tool("get_content_pipeline", "Content pipeline and recent content performance from the Vault (OGX and finance channels)."),
    _tool("add_content_pipeline_item", "Add a video or post to the Vault content pipeline.",
          {"title": {"type": "string"}, "content_type": {"type": "string"}, "topic": {"type": "string"},
           "stage": {"type": "string", "description": "research, script, production, publish, published"},
           "platform": {"type": "string"}, "notes": {"type": "string"}}, ["title"]),
    _tool("get_content_ideas", "Open content ideas and recent episodes from the OrigineX database.",
          {"limit": {"type": "integer"}}),
    _tool("add_content_idea", "Save a new OGX content idea to the OrigineX database.",
          {"title": {"type": "string"}, "description": {"type": "string"}, "hook": {"type": "string"},
           "content_type": {"type": "string", "description": "long_form, short, reel, carousel"},
           "key_points": {"type": "array", "items": {"type": "string"}},
           "target_audience": {"type": "string"}}, ["title"]),
    _tool("search_ogx", "Search the OrigineX research database. kind: citations (sources and quotes), people (historical figures), documents (research articles).",
          {"query": {"type": "string"}, "kind": {"type": "string", "description": "citations, people, or documents"}},
          ["query"]),
    _tool("get_scholarly_flags", "Contested historical claims that must never be presented as settled fact."),
    _tool("get_competitive_brief", "Latest weekly competitive intelligence sweep for the OGX channel."),
    _tool("get_open_content_flags", "Citation flags awaiting Joe's judgement and new declassified releases awaiting approval."),
    _tool("shopify_summary", "Sales summary from the Shopify store for the last N days (needs Shopify credentials).",
          {"days_back": {"type": "integer", "description": "Default 7"}}),
    _tool("web_search", "Search the web for current information (news, prices, releases). Needs BRAVE_SEARCH_API_KEY.",
          {"query": {"type": "string"}, "freshness": {"type": "string", "description": "pd (day), pw (week), pm (month), or empty"}},
          ["query"]),
]


class Jarvis:
    def __init__(self, cfg, vault: Vault, ogx: OGX, client=None):
        self.cfg = cfg
        self.vault = vault
        self.ogx = ogx
        self.client = client or anthropic.Anthropic(api_key=cfg.anthropic_api_key or None)
        self.owner_key = cfg.owner_key or (vault.owner_key() if vault.enabled else "") or "owner"
        self.conversation_id = None
        self._live = None
        self._live_at = 0.0
        self._fallbacks = bool(cfg.fallbacks and self._sdk_supports_fallbacks())

    # ---- context ---------------------------------------------------------- #

    def _sdk_supports_fallbacks(self) -> bool:
        try:
            return "fallbacks" in inspect.signature(self.client.beta.messages.stream).parameters
        except Exception:  # noqa: BLE001
            return False

    @property
    def fallbacks_enabled(self) -> bool:
        return self._fallbacks

    def refresh_context(self) -> str:
        self._live = build_live_context(self.vault, self.ogx, self.cfg.assistant_name)
        self._live_at = time.time()
        return self._live

    def live_context(self) -> str:
        if self._live is None or (time.time() - self._live_at) > self.cfg.context_ttl_seconds:
            self.refresh_context()
        return self._live

    def system_blocks(self) -> list:
        return [
            {"type": "text", "text": PERSONA.replace("{name}", self.cfg.assistant_name),
             "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": self.live_context(),
             "cache_control": {"type": "ephemeral"}},
        ]

    # ---- Claude ----------------------------------------------------------- #

    def _call(self, messages: list):
        kwargs = dict(
            model=self.cfg.model,
            max_tokens=self.cfg.max_tokens,
            system=self.system_blocks(),
            tools=TOOLS,
            messages=messages,
            thinking={"type": "adaptive"},
            output_config={"effort": self.cfg.effort},
        )
        if self._fallbacks:
            try:
                with self.client.beta.messages.stream(
                    **kwargs, betas=[FALLBACK_BETA], fallbacks="default",
                ) as stream:
                    return stream.get_final_message()
            except anthropic.BadRequestError as e:
                # Fallbacks are not available on every platform or plan. Switch
                # them off for the rest of the process rather than fail every turn.
                print(f"[jarvis] server-side fallbacks rejected, disabling: {getattr(e, 'message', e)}")
                self._fallbacks = False
        with self.client.messages.stream(**kwargs) as stream:
            return stream.get_final_message()

    def reply(self, user_text: str, history: list) -> tuple[str, list]:
        """Run one turn. Returns (assistant_text, names_of_tools_called)."""
        messages = list(history) + [{"role": "user", "content": user_text}]
        tool_log: list[str] = []
        response = None
        for _ in range(MAX_TOOL_ROUNDS):
            response = self._call(messages)
            if response.stop_reason == "refusal":
                return "I can't help with that one, Joe.", tool_log
            content = echoable_content(response.content)
            if response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": content})
                continue
            tool_uses = [b for b in content if getattr(b, "type", "") == "tool_use"]
            if response.stop_reason != "tool_use" or not tool_uses:
                text = "".join(getattr(b, "text", "") for b in content if getattr(b, "type", "") == "text")
                return text.strip() or "Done.", tool_log
            messages.append({"role": "assistant", "content": content})
            results = []
            for tu in tool_uses:
                tool_log.append(tu.name)
                try:
                    output = self.execute_tool(tu.name, tu.input or {})
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": output})
                except Exception as e:  # noqa: BLE001
                    results.append({"type": "tool_result", "tool_use_id": tu.id,
                                    "content": f"Error: {e}", "is_error": True})
            messages.append({"role": "user", "content": results})
        return "I ran out of steps on that one. Ask me again more narrowly.", tool_log

    # ---- tools ------------------------------------------------------------ #

    def execute_tool(self, name: str, args: dict) -> str:
        v, o = self.vault, self.ogx
        if name == "get_portfolio_summary":
            return _j({"summary": v.portfolio_summary(), "net_worth": v.net_worth()})
        if name == "get_holdings":
            return _j(v.holdings(limit=int(args.get("limit") or 30), account=args.get("account")))
        if name == "get_watchlist":
            return _j(v.watchlist())
        if name == "get_goals":
            return _j(v.goals())
        if name == "get_rules":
            return _j(v.rules(args.get("domain")))
        if name == "get_recent_decisions":
            return _j(v.recent_decisions(limit=int(args.get("limit") or 10)))
        if name == "search_decisions":
            return _j(v.search_decisions(args["query"]))
        if name == "get_recent_sessions":
            return _j(v.recent_sessions(limit=int(args.get("limit") or 5)))
        if name == "recall":
            return _j(v.recall(args["query"], limit=int(args.get("limit") or 8)))
        if name == "remember":
            ok = v.remember(self.owner_key, args["title"], args["content"],
                            memory_type=args.get("memory_type") or "fact",
                            importance=int(args.get("importance") or 5),
                            ticker=args.get("ticker"), conversation_id=self.conversation_id)
            return "saved" if ok else "not saved (Vault unavailable)"
        if name == "log_decision":
            ok = v.log_decision(args["domain"], args["title"], args["decision_made"],
                                reasoning=args.get("reasoning"), importance=args.get("importance"),
                                ticker=args.get("ticker"), is_trade=bool(args.get("is_trade")),
                                trade_action=args.get("trade_action"), trade_status=args.get("trade_status"))
            if ok:
                v.log_memory_event(self.owner_key, args["title"], args["decision_made"], args["domain"],
                                   decision=args["decision_made"], rationale=args.get("reasoning"),
                                   source_conversation_id=self.conversation_id)
            return "logged" if ok else "not logged (Vault unavailable)"
        if name == "log_thought":
            ok = v.log_thought(args["content"], thought_type=args.get("thought_type") or "idea",
                               domain=args.get("domain") or "general", priority=int(args.get("priority") or 3),
                               tags=args.get("tags"), linked_ticker=args.get("linked_ticker"))
            return "captured" if ok else "not captured (Vault unavailable)"
        if name == "log_session_capture":
            ok = v.log_session(args["title"], args["domain"], args["summary"],
                               key_decisions=args.get("key_decisions"), action_items=args.get("action_items"),
                               outcomes=args.get("outcomes"), tags=args.get("tags"))
            return "session saved" if ok else "not saved (Vault unavailable)"
        if name == "add_watchlist_item":
            ok = v.add_watchlist(args["ticker"], company_name=args.get("company_name"), thesis=args.get("thesis"),
                                 bucket=args.get("bucket"), priority=args.get("priority") or "medium",
                                 notes=args.get("notes"))
            return "added" if ok else "not added (Vault unavailable)"
        if name == "get_content_pipeline":
            return _j({"pipeline": v.content_pipeline(), "recent_performance": v.content_log()})
        if name == "add_content_pipeline_item":
            ok = v.add_content_pipeline(args["title"], content_type=args.get("content_type"), topic=args.get("topic"),
                                        stage=args.get("stage") or "research", platform=args.get("platform"),
                                        notes=args.get("notes"))
            return "added to pipeline" if ok else "not added (Vault unavailable)"
        if name == "get_content_ideas":
            return _j({"ideas": o.ideas(limit=int(args.get("limit") or 15)), "episodes": o.episodes()})
        if name == "add_content_idea":
            ok = o.add_idea(args["title"], description=args.get("description"), hook=args.get("hook"),
                            content_type=args.get("content_type") or "long_form", key_points=args.get("key_points"),
                            target_audience=args.get("target_audience"))
            return "idea saved" if ok else "not saved (OGX database unavailable)"
        if name == "search_ogx":
            kind = (args.get("kind") or "citations").lower()
            if kind.startswith("people"):
                return _j(o.search_people(args["query"]))
            if kind.startswith("doc"):
                return _j(o.search_documents(args["query"]))
            return _j(o.search_citations(args["query"]))
        if name == "get_scholarly_flags":
            return _j(o.scholarly_flags())
        if name == "get_competitive_brief":
            return _j(o.competitive_brief())
        if name == "get_open_content_flags":
            return _j({"citation_flags": o.open_research_flags(), "declass_inbox": o.declass_new()})
        if name == "shopify_summary":
            return self._shopify(int(args.get("days_back") or 7))
        if name == "web_search":
            return self._web_search(args["query"], args.get("freshness") or "")
        raise ValueError(f"unknown tool {name}")

    @staticmethod
    def _shopify(days_back: int) -> str:
        try:
            from tools.shopify_client import ShopifyClient  # lazy: needs Shopify env
            client = ShopifyClient()
            orders = client.get_orders(days_back=days_back)
            return _j({"days_back": days_back, "summary": client.compute_sales_summary(orders),
                       "orders": client.simplify_orders(orders)[:20]})
        except Exception as e:  # noqa: BLE001
            return f"Shopify not available: {e}"

    @staticmethod
    def _web_search(query: str, freshness: str) -> str:
        try:
            from tools.web_search import web_search  # lazy: needs Brave env
            return _j(web_search(query, num_results=6, freshness=freshness, country="GB"))
        except Exception as e:  # noqa: BLE001
            return f"Web search not available: {e}"

"""
The Vault: Joe's finance-chief Supabase project. Single source of truth for
identity, rules, goals, holdings, decisions and memory (Rule Zero: query the
Vault before answering, never quote holdings or cash from memory).

Read helpers return plain dicts/lists. Write helpers return True/False or the
new row id, and never raise.
"""
import hashlib
from datetime import date

from .supabase_client import SupabaseREST

ACTIVE_GOAL_STATES = ("active", "in_progress", "pending")


class Vault:
    def __init__(self, url: str, key: str):
        self.db = SupabaseREST(url, key, label="vault")

    @property
    def enabled(self) -> bool:
        return self.db.enabled

    # ---- identity --------------------------------------------------------- #

    def profile(self) -> dict:
        rows = self.db.select("mj_context_profiles", limit=1)
        return rows[0] if rows else {}

    def owner_key(self) -> str:
        return str(self.profile().get("owner_key") or "")

    def identity(self) -> list:
        return self.db.select("identity_core", {"order": "category.asc,key.asc"})

    def ventures(self) -> list:
        return self.db.select("ventures", {"order": "name.asc"})

    def telegram_chat_id(self) -> str:
        rows = self.db.select("telegram_config", {"id": "eq.1"}, limit=1)
        if rows and rows[0].get("enabled"):
            return str(rows[0].get("chat_id") or "")
        return ""

    # ---- rules and goals -------------------------------------------------- #

    def rules(self, domain: str | None = None) -> list:
        params = {"active": "eq.true", "order": "priority.asc,domain.asc"}
        if domain:
            params["domain"] = f"eq.{domain}"
        return self.db.select("agent_rules", params)

    def goals(self) -> list:
        states = ",".join(ACTIVE_GOAL_STATES)
        return self.db.select("goals", {"status": f"in.({states})", "order": "updated_at.desc"})

    # ---- portfolio -------------------------------------------------------- #

    def portfolio_summary(self) -> dict:
        rows = self.db.select("portfolio_summary", {"order": "snapshot_date.desc"}, limit=1)
        return rows[0] if rows else {}

    def net_worth(self) -> dict:
        rows = self.db.select("net_worth_snapshots", {"order": "snapshot_date.desc"}, limit=1)
        return rows[0] if rows else {}

    def latest_holdings_date(self):
        rows = self.db.select(
            "holdings",
            {"select": "snapshot_date", "status": "eq.active", "order": "snapshot_date.desc"},
            limit=1,
        )
        return rows[0].get("snapshot_date") if rows else None

    def holdings(self, limit: int = 30, account: str | None = None) -> list:
        snap = self.latest_holdings_date()
        if not snap:
            return []
        params = {
            "select": "ticker,company_name,account,bucket,shares,current_value_gbp,pnl_gbp,pnl_pct,snapshot_date",
            "snapshot_date": f"eq.{snap}",
            "status": "eq.active",
            "order": "current_value_gbp.desc.nullslast",
        }
        if account:
            params["account"] = f"ilike.{SupabaseREST.like(account)}"
        return self.db.select("holdings", params, limit=limit)

    def watchlist(self) -> list:
        return self.db.select(
            "watchlist",
            {"status": "eq.watching", "order": "priority.asc,ticker.asc",
             "select": "ticker,company_name,sector,bucket,thesis,priority,target_entry_gbp,target_entry_usd,notes"},
        )

    # ---- decisions and memory --------------------------------------------- #

    def recent_decisions(self, limit: int = 10) -> list:
        return self.db.select(
            "decision_log",
            {"order": "decision_date.desc,created_at.desc",
             "select": "decision_date,domain,title,decision_made,reasoning,outcome,ticker,is_trade,trade_action,trade_status,importance"},
            limit=limit,
        )

    def search_decisions(self, query: str, limit: int = 10) -> list:
        return self.db.select(
            "decision_log",
            {"or": SupabaseREST.any_of(query, ["title", "decision_made", "reasoning", "ticker"]),
             "order": "decision_date.desc",
             "select": "decision_date,domain,title,decision_made,reasoning,outcome,ticker"},
            limit=limit,
        )

    def recent_sessions(self, limit: int = 5) -> list:
        return self.db.select(
            "session_captures",
            {"order": "session_date.desc",
             "select": "session_date,session_title,domain,summary,key_decisions,action_items"},
            limit=limit,
        )

    def recent_memory_events(self, limit: int = 10) -> list:
        return self.db.select(
            "ai_memory_events",
            {"status": "eq.ACTIVE", "order": "occurred_at.desc",
             "select": "occurred_at,domain,title,summary,decision"},
            limit=limit,
        )

    def recall(self, query: str, limit: int = 8) -> list:
        return self.db.select(
            "mj_semantic_memories",
            {"active": "eq.true",
             "or": SupabaseREST.any_of(query, ["title", "content", "ticker"]),
             "order": "importance.desc,created_at.desc",
             "select": "memory_type,title,content,ticker,importance,source_date"},
            limit=limit,
        )

    # ---- content (finance-chief side) ------------------------------------- #

    def content_pipeline(self, limit: int = 20) -> list:
        return self.db.select("ogx_content_pipeline", {"order": "updated_at.desc"}, limit=limit)

    def content_log(self, limit: int = 10) -> list:
        return self.db.select("content_log", {"order": "publish_date.desc.nullslast"}, limit=limit)

    # ---- conversations ---------------------------------------------------- #

    def start_conversation(self, owner_key: str, title: str):
        rows = self.db.insert("mj_conversations", {"owner_key": owner_key, "title": title}, returning=True)
        return rows[0].get("id") if rows else None

    def latest_conversation(self, owner_key: str, title_prefix: str) -> dict:
        rows = self.db.select(
            "mj_conversations",
            {"owner_key": f"eq.{owner_key}", "title": f"like.{title_prefix}*", "order": "created_at.desc"},
            limit=1,
        )
        return rows[0] if rows else {}

    def conversation_messages(self, conversation_id: str, limit: int = 40) -> list:
        rows = self.db.select(
            "mj_messages",
            {"conversation_id": f"eq.{conversation_id}", "order": "created_at.desc", "select": "role,content,created_at"},
            limit=limit,
        )
        return list(reversed(rows))

    def log_message(self, owner_key: str, conversation_id, role: str, content: str, page_context: dict | None = None) -> bool:
        if not conversation_id:
            return False
        return self.db.insert("mj_messages", {
            "owner_key": owner_key,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "page_context": page_context or {},
        })

    # ---- writes ----------------------------------------------------------- #

    def log_decision(self, domain: str, title: str, decision_made: str, reasoning: str | None = None,
                     importance: int | None = None, ticker: str | None = None, is_trade: bool = False,
                     trade_action: str | None = None, trade_status: str | None = None) -> bool:
        row = {
            "decision_date": date.today().isoformat(),
            "domain": domain,
            "title": title,
            "decision_made": decision_made,
            "reasoning": reasoning,
            "importance": importance,
            "ticker": ticker,
            "is_trade": bool(is_trade),
            "trade_action": trade_action,
            "trade_status": trade_status,
        }
        return self.db.insert("decision_log", {k: v for k, v in row.items() if v is not None})

    def log_thought(self, content: str, thought_type: str = "idea", domain: str = "general",
                    priority: int = 3, tags: list | None = None, linked_ticker: str | None = None) -> bool:
        row = {
            "content": content,
            "thought_type": thought_type,
            "domain": domain,
            "priority": priority,
            "tags": tags or [],
            "linked_ticker": linked_ticker,
        }
        return self.db.insert("thought_stream", {k: v for k, v in row.items() if v is not None})

    def log_session(self, title: str, domain: str, summary: str, key_decisions: list | None = None,
                    action_items: list | None = None, outcomes: list | None = None,
                    tags: list | None = None, full_content: str | None = None) -> bool:
        row = {
            "session_title": title,
            "domain": domain,
            "summary": summary,
            "key_decisions": key_decisions or [],
            "action_items": action_items or [],
            "outcomes": outcomes or [],
            "tags": tags or [],
            "tool_used": "jarvis",
            "full_content": full_content,
        }
        return self.db.insert("session_captures", {k: v for k, v in row.items() if v is not None})

    def remember(self, owner_key: str, title: str, content: str, memory_type: str = "fact",
                 importance: int = 5, ticker: str | None = None, conversation_id=None) -> bool:
        row = {
            "owner_key": owner_key,
            "conversation_id": conversation_id,
            "memory_type": memory_type,
            "ticker": ticker,
            "title": title,
            "content": content,
            "importance": importance,
            "source_date": date.today().isoformat(),
            "metadata": {"source": "jarvis"},
        }
        return self.db.insert("mj_semantic_memories", {k: v for k, v in row.items() if v is not None})

    def add_watchlist(self, ticker: str, company_name: str | None = None, thesis: str | None = None,
                      bucket: str | None = None, priority: str = "medium", notes: str | None = None) -> bool:
        row = {
            "ticker": ticker.upper(),
            "company_name": company_name,
            "thesis": thesis,
            "bucket": bucket,
            "priority": priority,
            "notes": notes,
        }
        return self.db.insert("watchlist", {k: v for k, v in row.items() if v is not None})

    def add_content_pipeline(self, title: str, content_type: str | None = None, topic: str | None = None,
                             stage: str = "research", platform: str | None = None, notes: str | None = None) -> bool:
        row = {
            "title": title,
            "content_type": content_type,
            "topic": topic,
            "stage": stage,
            "platform": platform,
            "notes": notes,
        }
        return self.db.insert("ogx_content_pipeline", {k: v for k, v in row.items() if v is not None})

    def log_memory_event(self, owner_key: str, title: str, summary: str, domain: str,
                         decision: str | None = None, rationale: str | None = None,
                         event_type: str = "decision", source_conversation_id=None) -> bool:
        digest = hashlib.sha256(f"{title}\n{summary}".encode("utf-8")).hexdigest()
        row = {
            "owner_key": owner_key,
            "event_type": event_type,
            "title": title,
            "summary": summary,
            "domain": domain,
            "decision": decision,
            "rationale": rationale,
            "source_platform": "jarvis",
            "source_conversation_id": str(source_conversation_id) if source_conversation_id else None,
            "content_hash": digest,
        }
        return self.db.insert("ai_memory_events", {k: v for k, v in row.items() if v is not None})

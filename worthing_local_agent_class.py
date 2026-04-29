"""
WorthingLocalAgent class wrapper (Phase 2)
==========================================
Single-entry-point class around the Phase 1 read-only helper functions
in worthing_local_agent.py.

Usage:
    from worthing_local_agent_class import WorthingLocalAgent
    agent = WorthingLocalAgent()
    agent.query("house_prices", {"district": "Worthing"})
    agent.snapshot()
"""

import os
from datetime import datetime, timezone
from typing import Optional

from supabase import Client

from worthing_local_agent import (
    PROJECT_REF,
    _get_client,
    get_arts_businesses,
    get_employment_stats,
    get_epc_data,
    get_house_price_trends,
    get_licensed_venues,
    health_check,
)

SUPPORTED_INTENTS = [
    "licensed_venues",
    "arts_businesses",
    "epc_data",
    "house_prices",
    "employment",
    "health_check",
    "content_brief",
]


class WorthingLocalAgent:
    """Read-only intelligence agent over the Worthing/Adur Supabase project."""

    def __init__(self, debug: bool = False):
        self.debug = debug
        if debug:
            os.environ["DEBUG"] = "true"
        self._client: Optional[Client] = None
        self._connected: bool = False
        self._connect_error: Optional[str] = None
        self._last_query_at: Optional[str] = None
        try:
            self._client = _get_client()
            self._connected = True
        except Exception as e:
            self._connect_error = str(e)

    def __repr__(self) -> str:
        status = "connected" if self._connected else f"disconnected ({self._connect_error})"
        last = self._last_query_at or "never"
        return f"<WorthingLocalAgent project={PROJECT_REF} status={status} last_query={last}>"

    def _stamp(self) -> None:
        self._last_query_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def query(self, intent: str, params: Optional[dict] = None) -> dict:
        """Single-entry routing. Returns an error dict on unknown intents or failures."""
        params = params or {}
        self._stamp()
        try:
            if not self._connected:
                return {
                    "error": "Not connected to Supabase",
                    "details": self._connect_error,
                    "intent": intent,
                }

            if intent == "licensed_venues":
                return get_licensed_venues(**params, supabase_client=self._client)
            if intent == "arts_businesses":
                return get_arts_businesses(**params, supabase_client=self._client)
            if intent == "epc_data":
                return get_epc_data(**params, supabase_client=self._client)
            if intent == "house_prices":
                return get_house_price_trends(**params, supabase_client=self._client)
            if intent == "employment":
                return get_employment_stats(**params, supabase_client=self._client)
            if intent == "health_check":
                return health_check(supabase_client=self._client)
            if intent == "content_brief":
                from content_pipeline_brief import content_pipeline_brief
                return content_pipeline_brief(**params)

            return {
                "error": "Unknown intent",
                "intent": intent,
                "supported_intents": SUPPORTED_INTENTS,
            }
        except TypeError as e:
            return {"error": f"Invalid params: {e}", "intent": intent, "params": params}
        except Exception as e:
            return {"error": str(e), "intent": intent, "params": params}

    def snapshot(self) -> dict:
        """Combined health-check + house prices + employment, used by the scheduler."""
        self._stamp()
        return {
            "generated_at": self._last_query_at,
            "project": PROJECT_REF,
            "health": self.query("health_check"),
            "house_prices": self.query("house_prices", {"district": "Worthing"}),
            "employment": self.query("employment", {"geography": "Worthing"}),
        }


if __name__ == "__main__":
    import json
    agent = WorthingLocalAgent()
    print(repr(agent))
    print(json.dumps(agent.snapshot(), indent=2, default=str))

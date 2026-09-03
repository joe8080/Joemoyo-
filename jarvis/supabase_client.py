"""
Thin PostgREST client shared by both Supabase projects.

Reads return [] and writes return False/None when the project is not
configured or the network fails. Jarvis must keep answering even if a
database is briefly unreachable, and must say so rather than crash.
"""
import re

import requests

_TIMEOUT = 15


class SupabaseREST:
    def __init__(self, url: str, key: str, label: str = "supabase"):
        self.url = (url or "").rstrip("/")
        self.key = key or ""
        self.label = label

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.key)

    def _headers(self, extra: dict | None = None) -> dict:
        h = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    # ---- reads ------------------------------------------------------------ #

    def select(self, table: str, params: dict | None = None, limit: int | None = None) -> list:
        """GET rows. `params` uses PostgREST syntax, e.g. {"status": "eq.active"}."""
        if not self.enabled:
            return []
        query = {"select": "*"}
        if params:
            query.update(params)
        if limit:
            query["limit"] = str(limit)
        try:
            r = requests.get(
                f"{self.url}/rest/v1/{table}",
                params=query, headers=self._headers(), timeout=_TIMEOUT,
            )
            if r.status_code >= 300:
                print(f"[{self.label}] read {table} failed {r.status_code}: {r.text[:200]}")
                return []
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception as e:  # noqa: BLE001 - reads must never crash the bot
            print(f"[{self.label}] read {table} error: {e}")
            return []

    # ---- writes ----------------------------------------------------------- #

    def insert(self, table: str, rows, on_conflict: str | None = None, returning: bool = False):
        """POST rows. Returns True/False, or the inserted rows when returning=True."""
        if not self.enabled:
            return None if returning else False
        params = {}
        prefer = "return=representation" if returning else "return=minimal"
        if on_conflict:
            params["on_conflict"] = on_conflict
            prefer += ",resolution=merge-duplicates"
        try:
            r = requests.post(
                f"{self.url}/rest/v1/{table}",
                params=params, headers=self._headers({"Prefer": prefer}),
                json=rows if isinstance(rows, list) else [rows],
                timeout=_TIMEOUT,
            )
            if r.status_code >= 300:
                print(f"[{self.label}] write {table} failed {r.status_code}: {r.text[:200]}")
                return None if returning else False
            if returning:
                data = r.json()
                return data if isinstance(data, list) else []
            return True
        except Exception as e:  # noqa: BLE001
            print(f"[{self.label}] write {table} error: {e}")
            return None if returning else False

    def update(self, table: str, match: dict, values: dict) -> bool:
        """PATCH rows matching `match` (PostgREST filters) with `values`."""
        if not self.enabled:
            return False
        try:
            r = requests.patch(
                f"{self.url}/rest/v1/{table}",
                params=match, headers=self._headers({"Prefer": "return=minimal"}),
                json=values, timeout=_TIMEOUT,
            )
            if r.status_code >= 300:
                print(f"[{self.label}] update {table} failed {r.status_code}: {r.text[:200]}")
                return False
            return True
        except Exception as e:  # noqa: BLE001
            print(f"[{self.label}] update {table} error: {e}")
            return False

    # ---- helpers ---------------------------------------------------------- #

    @staticmethod
    def like(term: str) -> str:
        """Sanitise a search term for an ilike filter (letters, digits, spaces, dashes)."""
        clean = re.sub(r"[^\w\s-]", " ", term or "").strip()
        clean = re.sub(r"\s+", " ", clean)
        return f"*{clean}*" if clean else "*"

    @staticmethod
    def any_of(term: str, columns: list[str]) -> str:
        """Build a PostgREST `or` filter matching `term` in any of `columns`."""
        pattern = SupabaseREST.like(term)
        return "(" + ",".join(f"{c}.ilike.{pattern}" for c in columns) + ")"

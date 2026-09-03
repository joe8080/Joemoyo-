"""
OrigineX Human Archives (OGX) research database: citations, people, documents,
content ideas, episodes, scholarly debates and competitive intelligence.

Brand rule carried from the database: any claim listed in scholarly_debates
with permanent_flag=true is contested and must never be presented as settled.
"""
from .supabase_client import SupabaseREST


class OGX:
    def __init__(self, url: str, key: str):
        self.db = SupabaseREST(url, key, label="ogx")

    @property
    def enabled(self) -> bool:
        return self.db.enabled

    # ---- pipeline --------------------------------------------------------- #

    def ideas(self, limit: int = 15) -> list:
        return self.db.select(
            "content_ideas",
            {"status": "neq.published", "order": "created_at.desc",
             "select": "title,status,content_type,hook,description,target_audience,created_at"},
            limit=limit,
        )

    def episodes(self, limit: int = 10) -> list:
        return self.db.select(
            "video_episodes",
            {"order": "updated_at.desc", "select": "title,channel,status,topic,target_minutes,updated_at"},
            limit=limit,
        )

    def competitive_brief(self) -> dict:
        rows = self.db.select(
            "competitive_intel_runs",
            {"order": "run_date.desc", "select": "run_date,headline,brief,recommendations,slate_actions"},
            limit=1,
        )
        return rows[0] if rows else {}

    def scholarly_flags(self, limit: int = 40) -> list:
        return self.db.select(
            "scholarly_debates",
            {"permanent_flag": "eq.true", "order": "subject.asc",
             "select": "subject,claim,current_consensus,status"},
            limit=limit,
        )

    def open_research_flags(self, limit: int = 10) -> list:
        return self.db.select(
            "citation_research_list",
            {"resolved": "eq.false", "order": "created_at.desc",
             "select": "subject,flag_type,reason,suggested_action,created_at"},
            limit=limit,
        )

    def declass_new(self, limit: int = 10) -> list:
        return self.db.select(
            "declass_inbox",
            {"status": "eq.new", "order": "relevance_score.desc.nullslast",
             "select": "title,region,relevance_score,summary,url"},
            limit=limit,
        )

    # ---- search ----------------------------------------------------------- #

    def search_citations(self, query: str, limit: int = 8) -> list:
        return self.db.select(
            "citations",
            {"or": SupabaseREST.any_of(query, ["title", "author", "quote", "notes", "publication"]),
             "is_duplicate": "eq.false", "order": "verified.desc,year.desc.nullslast",
             "select": "title,author,publication,year,quote,reliability,verified,url,page_reference"},
            limit=limit,
        )

    def search_people(self, query: str, limit: int = 6) -> list:
        return self.db.select(
            "people",
            {"or": SupabaseREST.any_of(query, ["name", "significance", "biography"]),
             "order": "verified.desc",
             "select": "name,birth_date,death_date,significance,regions,civilizations,verified,confidence_score"},
            limit=limit,
        )

    def search_documents(self, query: str, limit: int = 6) -> list:
        return self.db.select(
            "documents",
            {"or": SupabaseREST.any_of(query, ["title", "excerpt"]),
             "order": "updated_at.desc",
             "select": "title,excerpt,era,document_type,status,regions,word_count"},
            limit=limit,
        )

    # ---- writes ----------------------------------------------------------- #

    def add_idea(self, title: str, description: str | None = None, hook: str | None = None,
                 content_type: str = "long_form", key_points: list | None = None,
                 target_audience: str | None = None) -> bool:
        row = {
            "title": title,
            "description": description,
            "hook": hook,
            "content_type": content_type,
            "key_points": key_points or [],
            "target_audience": target_audience,
            "status": "idea",
        }
        return self.db.insert("content_ideas", {k: v for k, v in row.items() if v is not None})

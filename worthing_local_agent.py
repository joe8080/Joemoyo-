"""
WorthingLocalAgent v1
=====================
Read-only query layer over the `worthing database` Supabase project
(ref: ympbtirltohryxrcqhlm).

Exposes 5 query helpers + a health check. All queries are SELECT only.
No outreach, no exports, no writes.

Importable as:

    from worthing_local_agent import (
        get_licensed_venues,
        get_arts_businesses,
        get_epc_data,
        get_house_price_trends,
        get_employment_stats,
        health_check,
    )

Required env vars (in .env):
    WORTHING_SUPABASE_URL
    WORTHING_SUPABASE_KEY

Optional:
    DEBUG=true   # log every query to stdout
"""

import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

PROJECT_REF = "ympbtirltohryxrcqhlm"
_DEBUG = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")


def _get_client(supabase_client: Optional[Client] = None) -> Client:
    if supabase_client is not None:
        return supabase_client
    url = os.environ.get("WORTHING_SUPABASE_URL")
    key = os.environ.get("WORTHING_SUPABASE_KEY")
    if not url or not key:
        raise EnvironmentError(
            "WORTHING_SUPABASE_URL and WORTHING_SUPABASE_KEY must be set in .env"
        )
    return create_client(url, key)


def _log(fn_name: str, params: dict) -> None:
    if _DEBUG:
        print(f"[worthing] {fn_name}({params})")


def _err(fn_name: str, params: dict, exc: Exception) -> dict:
    return {"error": str(exc), "function": fn_name, "params": params}


# --------------------------------------------------------------------- #
# 1. Licensed venues                                                    #
# --------------------------------------------------------------------- #
def get_licensed_venues(
    postcode_prefix: Optional[str] = None,
    entertainment_type: Optional[str] = None,
    alcohol_only: bool = False,
    limit: int = 500,
    supabase_client: Optional[Client] = None,
) -> dict:
    """Active licensed premises with entertainment / alcohol / late-night licences."""
    params = {
        "postcode_prefix": postcode_prefix,
        "entertainment_type": entertainment_type,
        "alcohol_only": alcohol_only,
        "limit": limit,
    }
    _log("get_licensed_venues", params)
    try:
        client = _get_client(supabase_client)
        cols = (
            "PremisesName,LocationText,Postcode,EntertainmentTypeLabel,"
            "AlcoholSupply,LateNightRefreshment,OnPremisesAlcoholSale,"
            "StatusLabel,OpeningHours,LicenceHolder"
        )
        q = client.table("licensing_data").select(cols)
        q = q.ilike("StatusLabel", "%grant%")

        if alcohol_only:
            q = q.eq("AlcoholSupply", "TRUE")
        else:
            q = q.or_(
                "EntertainmentTypeLabel.not.is.null,"
                "AlcoholSupply.eq.TRUE,"
                "LateNightRefreshment.eq.TRUE"
            )

        if postcode_prefix:
            q = q.ilike("Postcode", f"{postcode_prefix}%")
        if entertainment_type:
            q = q.ilike("EntertainmentTypeLabel", f"%{entertainment_type}%")

        rows = q.order("PremisesName").limit(limit).execute().data or []

        venues = [
            {
                "name": r.get("PremisesName"),
                "address": r.get("LocationText"),
                "postcode": r.get("Postcode"),
                "entertainment_type": r.get("EntertainmentTypeLabel"),
                "alcohol": (r.get("AlcoholSupply") or "").upper() == "TRUE",
                "late_night": (r.get("LateNightRefreshment") or "").upper() == "TRUE",
                "on_premises_alcohol": (r.get("OnPremisesAlcoholSale") or "").upper() == "TRUE",
                "licence_holder": r.get("LicenceHolder"),
                "status": r.get("StatusLabel"),
                "opening_hours": r.get("OpeningHours"),
            }
            for r in rows
        ]
        return {"total": len(venues), "filters_applied": params, "venues": venues}
    except Exception as e:
        return _err("get_licensed_venues", params, e)


# --------------------------------------------------------------------- #
# 2. Arts / music / creative businesses                                 #
# --------------------------------------------------------------------- #
def get_arts_businesses(
    category: Optional[str] = None,
    area: Optional[str] = None,
    postcode_prefix: Optional[str] = None,
    limit: int = 200,
    supabase_client: Optional[Client] = None,
) -> dict:
    """Music / arts / entertainment / creative businesses from the Worthing/Adur dataset."""
    params = {
        "category": category,
        "area": area,
        "postcode_prefix": postcode_prefix,
        "limit": limit,
    }
    _log("get_arts_businesses", params)
    try:
        client = _get_client(supabase_client)
        cols = "name,type,category,area,address,postcode,phone,website,latitude,longitude"
        q = client.table("businesses").select(cols)

        q = q.or_(
            "category.ilike.%music%,category.ilike.%arts%,"
            "category.ilike.%entertainment%,category.ilike.%media%,"
            "category.ilike.%creative%,category.ilike.%studio%,"
            "type.ilike.%music%,type.ilike.%venue%,"
            "type.ilike.%theatre%,type.ilike.%gallery%,"
            "name.ilike.%studio%,name.ilike.%music%,"
            "name.ilike.%record%,name.ilike.%creative%"
        )

        if category:
            q = q.ilike("category", f"%{category}%")
        if area:
            q = q.ilike("area", f"%{area}%")
        if postcode_prefix:
            q = q.ilike("postcode", f"{postcode_prefix}%")

        rows = q.order("name").limit(limit).execute().data or []
        return {"total": len(rows), "filters_applied": params, "businesses": rows}
    except Exception as e:
        return _err("get_arts_businesses", params, e)


# --------------------------------------------------------------------- #
# 3. EPC certificates                                                   #
# --------------------------------------------------------------------- #
def get_epc_data(
    postcode_prefix: Optional[str] = None,
    rating: Optional[str] = None,
    limit: int = 100,
    supabase_client: Optional[Client] = None,
) -> dict:
    """EPC certificates with energy-rating breakdown summary."""
    params = {"postcode_prefix": postcode_prefix, "rating": rating, "limit": limit}
    _log("get_epc_data", params)
    try:
        client = _get_client(supabase_client)

        detail_cols = (
            "address,postcode,energy_letter_current,energy_letter_potential,"
            "energy_rating_current,energy_rating_potential,property_type,"
            "construction_age_band,total_floor_area,inspection_date,"
            "heating_cost_current,tenure"
        )
        q = client.table("epc_certificates").select(detail_cols)
        if postcode_prefix:
            q = q.ilike("postcode", f"{postcode_prefix}%")
        if rating:
            q = q.eq("energy_letter_current", rating)
        certificates = q.order("inspection_date", desc=True).limit(limit).execute().data or []

        rating_breakdown: dict[str, int] = {}
        total_matched = 0
        for letter in ["A", "B", "C", "D", "E", "F", "G"]:
            cq = client.table("epc_certificates").select("uprn", count="exact").limit(1)
            if postcode_prefix:
                cq = cq.ilike("postcode", f"{postcode_prefix}%")
            cq = cq.eq("energy_letter_current", letter)
            count = cq.execute().count or 0
            rating_breakdown[letter] = count
            total_matched += count

        return {
            "summary": {
                "postcode_filter": postcode_prefix,
                "total_matched": total_matched,
                "rating_breakdown": rating_breakdown,
                "notes": "avg_score per rating not computed in v1 (no GROUP BY in supabase-py).",
            },
            "certificates": certificates,
        }
    except Exception as e:
        return _err("get_epc_data", params, e)


# --------------------------------------------------------------------- #
# 4. House price trends                                                 #
# --------------------------------------------------------------------- #
def get_house_price_trends(
    district: Optional[str] = None,
    year: Optional[int] = None,
    supabase_client: Optional[Client] = None,
) -> dict:
    """SCIP house price index by district / year."""
    params = {"district": district, "year": year}
    _log("get_house_price_trends", params)
    try:
        client = _get_client(supabase_client)
        cols = (
            "district,year,month,date,average_price,monthly_change_pct,"
            "annual_change_pct,detached_avg,semi_avg,terraced_avg,flat_avg"
        )
        q = client.table("scip_house_price_index").select(cols)
        if district:
            q = q.eq("district", district)
        if year:
            q = q.eq("year", year)
        rows = (
            q.order("year", desc=True)
            .order("month", desc=True)
            .limit(100)
            .execute()
            .data
            or []
        )

        latest = None
        if rows:
            top = rows[0]
            latest = {
                "date": top.get("date"),
                "average_price": top.get("average_price"),
                "annual_change_pct": top.get("annual_change_pct"),
            }
        return {
            "district": district,
            "filters_applied": params,
            "latest": latest,
            "history": rows,
        }
    except Exception as e:
        return _err("get_house_price_trends", params, e)


# --------------------------------------------------------------------- #
# 5. Employment statistics                                              #
# --------------------------------------------------------------------- #
def get_employment_stats(
    geography: Optional[str] = None,
    indicator: Optional[str] = None,
    supabase_client: Optional[Client] = None,
) -> dict:
    """Employment indicators by geography."""
    params = {"geography": geography, "indicator": indicator}
    _log("get_employment_stats", params)
    try:
        client = _get_client(supabase_client)
        cols = "date,geography,geography_code,indicator_name,value,measure_type"
        q = client.table("employment_statistics").select(cols)
        if geography:
            q = q.ilike("geography", f"%{geography}%")
        if indicator:
            q = q.ilike("indicator_name", f"%{indicator}%")
        rows = q.order("date", desc=True).limit(100).execute().data or []
        return {"total": len(rows), "filters_applied": params, "stats": rows}
    except Exception as e:
        return _err("get_employment_stats", params, e)


# --------------------------------------------------------------------- #
# Health check                                                          #
# --------------------------------------------------------------------- #
_CORE_TABLES = [
    "licensing_data",
    "businesses",
    "epc_certificates",
    "scip_house_price_index",
    "employment_statistics",
]


def health_check(supabase_client: Optional[Client] = None) -> dict:
    """Confirm connectivity by counting rows in each core table."""
    _log("health_check", {})
    counts: dict[str, object] = {}
    ok = True
    try:
        client = _get_client(supabase_client)
    except Exception as e:
        return {"project": PROJECT_REF, "ok": False, "error": str(e)}

    for table in _CORE_TABLES:
        try:
            res = client.table(table).select("*", count="exact").limit(1).execute()
            counts[table] = res.count
        except Exception as e:
            counts[table] = {"error": str(e)}
            ok = False
    return {"project": PROJECT_REF, "ok": ok, "tables": counts}


if __name__ == "__main__":
    import json
    print(json.dumps(health_check(), indent=2, default=str))

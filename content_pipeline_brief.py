"""
Content pipeline brief (Phase 2)
================================
Pulls live data from the worthing database (Supabase) and returns a
structured brief ready to feed into the OGX YouTube content engine.

Importable standalone:
    from content_pipeline_brief import content_pipeline_brief
"""

from datetime import datetime, timezone
from typing import Optional

from worthing_local_agent import (
    get_employment_stats,
    get_epc_data,
    get_house_price_trends,
)

LOCATION = "Worthing / Adur"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _gbp(n) -> str:
    try:
        return f"£{int(n):,}"
    except (TypeError, ValueError):
        return "£?"


def _pct(n) -> str:
    try:
        return f"{float(n):+.1f}%"
    except (TypeError, ValueError):
        return "?%"


# --------------------------------------------------------------------- #
# House prices brief                                                    #
# --------------------------------------------------------------------- #
def _house_prices_brief(district: str = "Worthing") -> dict:
    raw = get_house_price_trends(district=district)
    latest = raw.get("latest") or {}
    history = raw.get("history") or []
    top = history[0] if history else {}

    avg_price = latest.get("average_price")
    annual = latest.get("annual_change_pct")
    monthly = top.get("monthly_change_pct")
    detached = top.get("detached_avg")
    flat = top.get("flat_avg")
    semi = top.get("semi_avg")
    terraced = top.get("terraced_avg")
    period = latest.get("date") or "the latest period"
    year = top.get("year") or datetime.now().year

    headline = f"Average {district} house price: {_gbp(avg_price)} ({_pct(annual)} annual)"

    supporting = []
    if detached is not None:
        supporting.append(f"Detached average: {_gbp(detached)}")
    if semi is not None:
        supporting.append(f"Semi-detached average: {_gbp(semi)}")
    if terraced is not None:
        supporting.append(f"Terraced average: {_gbp(terraced)}")
    if flat is not None:
        supporting.append(f"Flat average: {_gbp(flat)}")
    if monthly is not None:
        supporting.append(f"Monthly change: {_pct(monthly)}")
    if period:
        supporting.append(f"Reporting period: {period}")

    direction = "Rising" if (annual or 0) > 0 else "Falling" if (annual or 0) < 0 else "Flat"

    titles = [
        f"{district} House Prices {year} — {direction} {_pct(annual)} a Year",
        f"How Much Does a Home Cost in {district} Right Now? ({_gbp(avg_price)})",
        f"{district} Property: Detached {_gbp(detached)} vs Flat {_gbp(flat)} — The Gap",
    ]

    hooks = [
        f"If you bought in {district} a year ago, here's what your home is worth today: {_gbp(avg_price)}, {_pct(annual)}.",
        f"A flat in {district} now averages {_gbp(flat)}. A detached house? {_gbp(detached)}. Most people don't realise the gap.",
        f"{district} house prices moved {_pct(monthly)} last month. Here's why that number matters.",
    ]

    return {
        "topic": "house_prices",
        "generated_at": _now(),
        "location": LOCATION,
        "headline_stat": headline,
        "supporting_stats": supporting,
        "suggested_video_titles": titles,
        "suggested_hooks": hooks,
        "data_source": "Worthing Database / scip_house_price_index",
        "raw_data_snapshot": {"latest": latest, "top_row": top},
    }


# --------------------------------------------------------------------- #
# EPC brief                                                             #
# --------------------------------------------------------------------- #
def _epc_brief(postcode_prefix: str = "BN") -> dict:
    raw = get_epc_data(postcode_prefix=postcode_prefix, limit=10)
    summary = raw.get("summary") or {}
    breakdown: dict = summary.get("rating_breakdown") or {}
    total = summary.get("total_matched") or 0
    sample = (raw.get("certificates") or [])[:5]

    sorted_ratings = sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True)
    top_rating = sorted_ratings[0][0] if sorted_ratings and sorted_ratings[0][1] else "?"
    poor_ratings = (breakdown.get("E", 0) or 0) + (breakdown.get("F", 0) or 0) + (breakdown.get("G", 0) or 0)
    poor_pct = (poor_ratings / total * 100) if total else 0

    headline = (
        f"{total:,} EPC certificates in {postcode_prefix}* — most common rating: {top_rating}"
    )

    supporting = []
    for letter, count in sorted_ratings:
        if count:
            pct = (count / total * 100) if total else 0
            supporting.append(f"Rating {letter}: {count:,} ({pct:.1f}%)")
    if total:
        supporting.append(f"E/F/G (poor) ratings: {poor_ratings:,} ({poor_pct:.1f}%)")

    titles = [
        f"Energy Ratings in {postcode_prefix}* — {total:,} Homes Surveyed",
        f"Why So Many {postcode_prefix} Homes Are Rated {top_rating} (And What That Costs You)",
        f"{poor_pct:.0f}% of {postcode_prefix} Homes Have Poor Energy Ratings — Here's the Map",
    ]

    hooks = [
        f"There are {total:,} EPC-rated homes in {postcode_prefix}. The most common rating? {top_rating}. Here's what that means for your bills.",
        f"{poor_ratings:,} homes around {postcode_prefix} are rated E, F or G. If yours is one, this is what you can do about it.",
        f"Energy ratings affect resale value. {postcode_prefix} averages a {top_rating}. Is yours above or below the curve?",
    ]

    return {
        "topic": "epc",
        "generated_at": _now(),
        "location": LOCATION,
        "headline_stat": headline,
        "supporting_stats": supporting,
        "suggested_video_titles": titles,
        "suggested_hooks": hooks,
        "data_source": "Worthing Database / epc_certificates",
        "raw_data_snapshot": {"summary": summary, "sample": sample},
    }


# --------------------------------------------------------------------- #
# Employment brief                                                      #
# --------------------------------------------------------------------- #
def _employment_brief(geography: str = "Worthing") -> dict:
    raw = get_employment_stats(geography=geography)
    stats = raw.get("stats") or []

    by_indicator: dict[str, dict] = {}
    for row in stats:
        name = row.get("indicator_name")
        if name and name not in by_indicator:
            by_indicator[name] = row
    indicators = list(by_indicator.values())

    latest = stats[0] if stats else {}
    latest_value = latest.get("value")
    latest_indicator = latest.get("indicator_name") or "employment indicator"
    latest_date = latest.get("date") or "latest"
    measure = latest.get("measure_type") or ""

    headline = (
        f"Latest {geography} {latest_indicator}: {latest_value} {measure} ({latest_date})".strip()
    )

    supporting = []
    for row in indicators[:5]:
        name = row.get("indicator_name") or "indicator"
        val = row.get("value")
        m = row.get("measure_type") or ""
        d = row.get("date") or ""
        supporting.append(f"{name}: {val} {m} ({d})".strip())

    titles = [
        f"{geography} Jobs Update — {latest_indicator} at {latest_value}{(' ' + measure) if measure else ''}",
        f"What the Latest {geography} Employment Numbers Actually Mean",
        f"{geography} Labour Market {latest_date}: 5 Numbers You Should Know",
    ]

    hooks = [
        f"The latest {geography} {latest_indicator} reading is {latest_value}{(' ' + measure) if measure else ''}. Here's why that matters if you live or work here.",
        f"{len(indicators)} different employment indicators just updated for {geography}. Here are the ones to watch.",
        f"If you're hiring, job-hunting, or running a business in {geography}, these numbers from {latest_date} change the picture.",
    ]

    return {
        "topic": "employment",
        "generated_at": _now(),
        "location": LOCATION,
        "headline_stat": headline,
        "supporting_stats": supporting,
        "suggested_video_titles": titles,
        "suggested_hooks": hooks,
        "data_source": "Worthing Database / employment_statistics",
        "raw_data_snapshot": {"latest": latest, "distinct_indicators": len(indicators)},
    }


# --------------------------------------------------------------------- #
# Public entry point                                                    #
# --------------------------------------------------------------------- #
def content_pipeline_brief(topic: str, postcode_prefix: str = "BN") -> dict:
    """Generate a content brief for the requested topic.

    Topics: "house_prices" | "epc" | "employment" | anything else → all three.
    """
    topic = (topic or "").lower().strip()

    if topic == "house_prices":
        return _house_prices_brief()
    if topic == "epc":
        return _epc_brief(postcode_prefix=postcode_prefix)
    if topic == "employment":
        return _employment_brief()

    return {
        "topic": "all",
        "generated_at": _now(),
        "location": LOCATION,
        "briefs": {
            "house_prices": _house_prices_brief(),
            "epc": _epc_brief(postcode_prefix=postcode_prefix),
            "employment": _employment_brief(),
        },
    }


if __name__ == "__main__":
    import json
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(json.dumps(content_pipeline_brief(topic), indent=2, default=str))

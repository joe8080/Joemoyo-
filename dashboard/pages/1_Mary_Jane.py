"""
Mary Jane — investment command page.

Live view of the finance chief database with the Mary Jane agent on top:
portfolio and North Star progress, a chat box (Claude with read-only access to
the database), her graded track record, the lessons she has learned, and the
cost of each run. Everything goes through the `mj-agent` Supabase edge
function, so this page never holds a database key.

Secrets (Streamlit Cloud -> App settings -> Secrets, or .env locally):
    MJ_DASHBOARD_TOKEN = "mjt_..."           # required
    MJ_API_URL = "https://<project>.supabase.co/functions/v1/mj-agent"  # optional
"""

import os

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(page_title="Mary Jane — Investment Command", page_icon="🧠", layout="wide")

DEFAULT_API_URL = "https://qxwfrsoztfddwicqtuar.supabase.co/functions/v1/mj-agent"
SERIES_COLOUR = "#2a78d6"
QUICK_ASKS = [
    ("Morning brief", "Give me my morning brief: portfolio, risk state, open alerts and anything I need to decide today."),
    ("Am I on track?", "Am I on track for £1,000,000 and £1,000 a month passive income? What is the single biggest lever?"),
    ("Biggest risk", "What is the single biggest risk in my portfolio right now, and what would you do about it?"),
    ("New cash", "If I add new cash this month, where should it go and why? Respect my rules and the risk state."),
]


def _setting(name: str, default: str = "") -> str:
    value = os.environ.get(name, "")
    if not value:
        try:
            value = str(st.secrets.get(name, ""))
        except FileNotFoundError:
            value = ""
    return value.strip() or default


API_URL = _setting("MJ_API_URL", DEFAULT_API_URL)
TOKEN = _setting("MJ_DASHBOARD_TOKEN")

ERROR_HELP = {
    "unauthorised": "The dashboard token was rejected. Check MJ_DASHBOARD_TOKEN in the app secrets.",
    "anthropic_key_missing": "Mary Jane has no Anthropic key yet. Add ANTHROPIC_API_KEY in Supabase → Edge Functions → Secrets.",
}


def call(action: str, timeout: int = 60, **payload) -> tuple[dict | None, str | None]:
    """POST one action to the agent. Returns (data, error message in plain words)."""
    try:
        r = requests.post(API_URL, json={"action": action, **payload},
                          headers={"x-mj-token": TOKEN}, timeout=timeout)
    except requests.Timeout:
        return None, "Mary Jane took too long to answer. Try again, or ask a narrower question."
    except requests.RequestException as e:
        return None, f"Could not reach Mary Jane: {e}"
    try:
        data = r.json()
    except ValueError:
        return None, f"Unexpected reply (HTTP {r.status_code})."
    if r.status_code >= 300:
        code = data.get("error", "error")
        detail = data.get("detail") or data.get("hint") or ""
        return None, ERROR_HELP.get(code, f"{code}: {detail}".strip(": "))
    return data, None


@st.cache_data(ttl=120, show_spinner=False)
def load_overview(_nonce: int) -> tuple[dict | None, str | None]:
    return call("overview")


def gbp(value) -> str:
    try:
        return f"£{float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"


# --------------------------------------------------------------------- setup

st.title("🧠 Mary Jane — Investment Command")

if not TOKEN:
    st.warning("Mary Jane is not connected yet.")
    st.markdown(
        "1. In Streamlit, open **App settings → Secrets**.\n"
        "2. Add `MJ_DASHBOARD_TOKEN = \"mjt_...\"` (the token from your setup notes).\n"
        "3. Save. The page reloads and connects."
    )
    st.stop()

st.session_state.setdefault("nonce", 0)
st.session_state.setdefault("conversation_id", None)
st.session_state.setdefault("messages", [])
top_left, top_right = st.columns([5, 1])
with top_right:
    if st.button("🔄 Refresh", use_container_width=True):
        st.session_state.nonce += 1

data, error = load_overview(st.session_state.nonce)
if error:
    st.error(error)
    st.stop()

fresh = data.get("freshness") or {}
with top_left:
    st.caption(f"Holdings synced: {str(fresh.get('portfolio_snapshot') or 'unknown')[:16].replace('T', ' ')} UTC"
               f" · Prices: {fresh.get('prices_date') or 'unknown'}")

# ------------------------------------------------------------------ KPI row

ns = data.get("north_star") or {}
income = data.get("income") or {}
risk = data.get("risk") or {}
k1, k2, k3, k4 = st.columns(4)
k1.metric("Portfolio (live)", gbp(ns.get("live_total_gbp")))
k2.metric("North Star progress", f"{(ns.get('progress_pct') or 0):.1f}%",
          help=f"Of {gbp(ns.get('target_gbp'))}")
k3.metric("Passive income now", f"{gbp(income.get('est_income_now_gbp_per_month'))}/mo",
          help=f"Target {gbp(income.get('target_monthly_income_gbp'))}/mo at "
               f"{income.get('assumed_portfolio_yield_pct', '—')}% assumed yield")
k4.metric("Risk regime", str(risk.get("regime") or "unknown"),
          help=f"Deployment bias: {risk.get('deployment_bias') or '—'}")
st.progress(min(max((ns.get("progress_pct") or 0) / 100, 0.0), 1.0),
            text=f"{gbp(ns.get('live_total_gbp'))} of {gbp(ns.get('target_gbp'))}")

tab_chat, tab_pf, tab_record, tab_lessons, tab_runs = st.tabs(
    ["💬 Ask Mary Jane", "📈 Portfolio", "🎯 Track record", "🧠 Lessons", "⚙️ Runs & cost"])

# ---------------------------------------------------------------------- chat

with tab_chat:
    conversations = data.get("conversations") or []
    options = {"➕ New conversation": None}
    options.update({f"{c['title'] or 'Untitled'} · {c['updated_at'][:10]}": c["id"] for c in conversations})
    current = st.session_state.get("conversation_id")
    if current and current not in options.values():
        options["Current conversation"] = current
    ids = list(options.values())
    choice = st.selectbox("Conversation", list(options), index=ids.index(current) if current in ids else 0)
    chosen_id = options[choice]

    if st.session_state.get("conversation_id") != chosen_id:
        st.session_state.conversation_id = chosen_id
        st.session_state.messages = []
        if chosen_id:
            past, past_error = call("conversation", conversation_id=chosen_id)
            if past_error:
                st.error(past_error)
            else:
                st.session_state.messages = [
                    {"role": m["role"], "content": m["content"], "trace": m.get("citations") or []}
                    for m in past.get("messages", [])]

    quick_cols = st.columns(len(QUICK_ASKS))
    for col, (label, prompt) in zip(quick_cols, QUICK_ASKS):
        if col.button(label, use_container_width=True):
            st.session_state.pending = prompt

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🧠" if m["role"] == "assistant" else None):
            st.markdown(m["content"])
            if m.get("trace"):
                with st.expander("What I checked"):
                    for t in m["trace"]:
                        st.markdown(f"- {'✅' if t.get('ok') else '⚠️'} **{t.get('tool')}** — {t.get('summary')}")

    typed = st.chat_input("Ask Mary Jane about your portfolio… (dictation works here)")
    question = typed or st.session_state.pop("pending", None)
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Mary Jane is checking your data…"):
                reply, reply_error = call("chat", timeout=300, message=question,
                                          conversation_id=st.session_state.conversation_id)
            if reply_error:
                st.error(reply_error)
            else:
                st.session_state.conversation_id = reply["conversation_id"]
                st.markdown(reply["reply"])
                for rec in reply.get("recommendations") or []:
                    st.success(f"Logged for grading: {rec['action']} {rec['ticker']} "
                               f"at {rec['confidence']}% confidence")
                for lesson in reply.get("lessons") or []:
                    st.info(f"New lesson saved: {lesson['title']}")
                if reply.get("trace"):
                    with st.expander("What I checked"):
                        for t in reply["trace"]:
                            st.markdown(f"- {'✅' if t.get('ok') else '⚠️'} **{t.get('tool')}** — {t.get('summary')}")
                st.caption(f"Cost of this answer: about ${reply.get('est_cost_usd', 0):.2f}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply["reply"], "trace": reply.get("trace") or []})
                # Keep the selector on this conversation after the overview refreshes.
                st.session_state.nonce += 1

# ----------------------------------------------------------------- portfolio

with tab_pf:
    history = pd.DataFrame(ns.get("history") or [])
    if not history.empty:
        history["snapshot_date"] = pd.to_datetime(history["snapshot_date"])
        fig = go.Figure(go.Scatter(
            x=history["snapshot_date"], y=history["total_value_gbp"], mode="lines+markers",
            line=dict(color=SERIES_COLOUR, width=2), marker=dict(size=8),
            hovertemplate="%{x|%d %b %Y}<br>£%{y:,.0f}<extra></extra>"))
        fig.update_layout(title="Portfolio value", height=320, margin=dict(l=10, r=10, t=40, b=10),
                          yaxis=dict(tickprefix="£", tickformat=",.0f", gridcolor="rgba(128,128,128,0.15)"),
                          xaxis=dict(showgrid=False), hovermode="x unified",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    holdings = pd.DataFrame(data.get("holdings") or [])
    st.subheader("Holdings")
    if holdings.empty:
        st.info("No holdings in v_live_portfolio.")
    else:
        st.dataframe(holdings[["account", "ticker", "bucket", "shares", "current_value_gbp", "pnl_gbp", "pnl_pct", "weight_pct"]],
                     hide_index=True, use_container_width=True,
                     column_config={"current_value_gbp": st.column_config.NumberColumn("Value £", format="localized"),
                                    "pnl_gbp": st.column_config.NumberColumn("P&L £", format="localized"),
                                    "pnl_pct": st.column_config.NumberColumn("P&L %", format="%.1f%%"),
                                    "weight_pct": st.column_config.NumberColumn("Weight", format="%.1f%%")})

    left, right = st.columns(2)
    with left:
        st.subheader("Risk state")
        if risk:
            st.markdown(f"**{risk.get('regime')}** · pressure {risk.get('risk_pressure_score')} · "
                        f"bias {risk.get('deployment_bias')} · max new cash {risk.get('max_new_cash_pct')}%")
            if risk.get("signal_summary"):
                st.write(risk["signal_summary"])
        else:
            st.info("No risk state recorded.")
    with right:
        st.subheader("Open alerts")
        alerts = data.get("alerts") or []
        if not alerts:
            st.success("No open alerts.")
        for a in alerts:
            st.markdown(f"- **{a.get('severity') or 'info'}** · {a.get('ticker') or ''} {a.get('headline')}")

# -------------------------------------------------------------- track record

with tab_record:
    st.markdown("Every call Mary Jane logs is graded against SPY at 30, 90 and 365 days. "
                "**Edge** is how many percentage points the call beat (or, for trims and sells, avoided) the market by.")
    calibration = pd.DataFrame(data.get("calibration") or [])
    st.subheader("Calibration")
    if calibration.empty:
        st.info("No calls graded yet. The first grades arrive 30 days after the first logged call.")
    else:
        st.dataframe(calibration, hide_index=True, use_container_width=True)

    record = pd.DataFrame(data.get("track_record") or [])
    st.subheader("Logged calls")
    if record.empty:
        st.info("No calls logged yet. Ask Mary Jane for a view on a holding and she will log it.")
    else:
        record["created_at"] = record["created_at"].str[:10]
        st.dataframe(record.drop(columns=["id"]), hide_index=True, use_container_width=True)

    if st.button("🔁 Run reflection now (grades due calls, updates lessons)"):
        with st.spinner("Reflecting on the track record and your trading history…"):
            result, reflect_error = call("reflect", timeout=300)
        if reflect_error:
            st.error(reflect_error)
        else:
            st.success(result.get("summary", "Done."))
            st.caption(f"Lessons added {result.get('lessons_added', 0)}, retired {result.get('lessons_retired', 0)} · "
                       f"grader: {result.get('grader')} · cost about ${result.get('est_cost_usd', 0):.2f}")
            st.session_state.nonce += 1

# ------------------------------------------------------------------- lessons

with tab_lessons:
    lessons = data.get("lessons") or []
    st.markdown("These are read by Mary Jane at the start of every conversation. "
                "She adds them when you state a lasting preference, and in her weekly reflection.")
    if not lessons:
        st.info("No lessons yet. The first weekly reflection mines your trade history for them.")
    for lesson in lessons:
        source = (lesson.get("metadata") or {}).get("source", "")
        ticker = f" · {lesson['ticker']}" if lesson.get("ticker") else ""
        st.markdown(f"**{lesson.get('title') or 'Lesson'}** ({lesson['memory_type']}, importance {lesson['importance']}{ticker})  \n"
                    f"{lesson['content']}  \n<small>{source} · {lesson.get('source_date') or ''}</small>",
                    unsafe_allow_html=True)

# ---------------------------------------------------------------- runs & cost

with tab_runs:
    runs = pd.DataFrame(data.get("runs") or [])
    if runs.empty:
        st.info("No runs yet.")
    else:
        runs["est_cost_usd"] = runs["stats"].apply(lambda s: (s or {}).get("est_cost_usd"))
        runs["started_at"] = pd.to_datetime(runs["started_at"])
        week = runs[runs["started_at"] > pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)]
        st.metric("Agent cost, last 7 days", f"${week['est_cost_usd'].fillna(0).sum():.2f}",
                  help="Estimated from token usage at Claude Opus 5.5 list prices.")
        st.dataframe(runs[["started_at", "run_type", "status", "tool_calls", "est_cost_usd", "summary", "error"]],
                     hide_index=True, use_container_width=True)

"""Chenora pipeline tracker: one file, one CSV.
Darren adds prospects, the app checks the ICP gates, values each prospect at the new pricing,
and estimates whether five paid Kenya contracts by 31 January is realistic.
Use prospect CODES (KE-014), never people's names."""
import hmac
import math
import os
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------- settings
# Pricing and gates come from Darren and the investor deck. Win rates and signing times are
# ASSUMPTIONS: replace them as real outcomes arrive.
PER_ACCOUNT_MONTH = 1.0        # USD per account per month
MIN_ANNUAL_FEE = 12_000        # USD, = 1,000 accounts x $1 x 12
REVENUE_SHARE = 0.15           # share of revenue won back
REVENUE_WON_BACK = 0.02        # assumed share of a prospect's annual revenue won back (deck: 2% to 3%)
MIN_ACCOUNTS = 1_000           # ICP gate
TARGET_DATE = date(2027, 1, 31)
TARGET_CONTRACTS = 5

SEGMENTS = {"b2b_software": "B2B software / SaaS", "payments": "Payments and fintech",
            "logistics": "B2B logistics and freight", "travel_tech": "B2B travel-tech",
            "distributors": "Distributors and wholesalers", "manufacturers": "Manufacturers with dealer networks",
            "insurance_brokers": "Insurance brokers", "other": "Other"}
STAGES = ["Identified", "Contacted", "Scoping call", "Quote sent", "Negotiation", "Won", "Lost", "On hold"]
ACTIVE = STAGES[:5]
SOURCES = ["Founder network", "Referral", "Outbound email", "Partner introduction", "Event", "Registry list"]
COLUMNS = ["prospect_code", "segment", "accounts_managed", "annual_revenue_usd", "has_digital_records",
           "decision_maker_access", "lead_source", "stage", "date_added", "last_stage_change", "owner", "why_won_or_lost"]

# Assumed chance a prospect at each stage ends as a paid contract, and median days to sign.
SCENARIOS = {
    "Pessimistic": {"win": [0.01, 0.02, 0.08, 0.20, 0.40], "days": [120, 100, 75, 45, 21]},
    "Base":        {"win": [0.02, 0.04, 0.15, 0.30, 0.55], "days": [75, 60, 45, 28, 14]},
    "Optimistic":  {"win": [0.04, 0.08, 0.25, 0.45, 0.70], "days": [50, 40, 30, 20, 10]},
}
SIGMA = 0.5                    # spread of signing time (log scale), assumption
ASSUMED_MIX = [55, 25, 12, 6, 2]   # Darren gave 100 prospects but not their stages. THIS IS A GUESS.

DATA_FILE = Path(os.getenv("CHENORA_DATA", Path(__file__).parent / "pipeline.csv"))
SAMPLE_FILE = Path(__file__).parent / "sample_pipeline.csv"

st.set_page_config(page_title="Chenora pipeline tracker", layout="wide")


# ----------------------------------------------------------------------------- password
def password_gate():
    expected = os.getenv("APP_PASSWORD", "")
    if not expected:
        try:
            expected = str(st.secrets.get("APP_PASSWORD", ""))
        except Exception:
            expected = ""
    if not expected or st.session_state.get("authed"):
        return
    st.title("Chenora pipeline tracker")
    pw = st.text_input("Password", type="password")
    if pw:
        if hmac.compare_digest(pw.encode(), expected.encode()):
            st.session_state["authed"] = True
            st.rerun()
        st.error("Wrong password.")
    st.stop()


password_gate()


# ----------------------------------------------------------------------------- data helpers
def clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in COLUMNS:
        if c not in out.columns:
            out[c] = None
    out = out[COLUMNS]
    for c in ("accounts_managed", "annual_revenue_usd"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    for c in ("date_added", "last_stage_change"):
        out[c] = pd.to_datetime(out[c], errors="coerce").dt.date
    for c in ("prospect_code", "segment", "has_digital_records", "decision_maker_access", "lead_source", "stage"):
        out[c] = out[c].astype(object).where(out[c].notna(), None)
    for c in ("owner", "why_won_or_lost"):
        out[c] = out[c].astype(object).where(out[c].notna(), "")
    return out.reset_index(drop=True)


def load() -> pd.DataFrame:
    if DATA_FILE.exists():
        try:
            return clean(pd.read_csv(DATA_FILE))
        except Exception:
            st.warning("The saved file could not be read, starting empty.")
    return clean(pd.DataFrame(columns=COLUMNS))


def save(df: pd.DataFrame) -> bool:
    try:
        df.to_csv(DATA_FILE, index=False)
        return True
    except OSError:
        return False


def add_checks(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    acc = pd.to_numeric(out["accounts_managed"], errors="coerce")
    rev = pd.to_numeric(out["annual_revenue_usd"], errors="coerce").fillna(0)
    yes = lambda s: s.astype(str).str.lower().eq("yes")
    out["passes_gates"] = (acc >= MIN_ACCOUNTS) & yes(out["has_digital_records"]) & yes(out["decision_maker_access"])

    def why(i):
        r = []
        if not acc.iloc[i] >= MIN_ACCOUNTS:
            r.append("under 1,000 accounts" if pd.notna(acc.iloc[i]) else "accounts unknown")
        if not yes(out["has_digital_records"]).iloc[i]:
            r.append("no digital records")
        if not yes(out["decision_maker_access"]).iloc[i]:
            r.append("no decision-maker access")
        return "; ".join(r)

    out["fails_because"] = [why(i) for i in range(len(out))]
    platform = np.maximum(acc.fillna(0) * PER_ACCOUNT_MONTH * 12, MIN_ANNUAL_FEE)
    out["est_year_one_usd"] = (platform + rev * REVENUE_WON_BACK * REVENUE_SHARE).round(0)
    return out


# ----------------------------------------------------------------------------- simulation
def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def stage_probs(scn, days, mult=1.0):
    """Chance a prospect at each active stage signs before the deadline."""
    if days <= 0:
        return [0.0] * 5
    return [min(1.0, w * mult) * norm_cdf((math.log(days) - math.log(d)) / SIGMA)
            for w, d in zip(scn["win"], scn["days"])]


def simulate(counts, scn, days, target, already_won=0, mult=1.0, n=20000, seed=42):
    rng = np.random.default_rng(seed)
    wins = np.zeros(n, dtype=int)
    for c, p in zip(counts, stage_probs(scn, days, mult)):
        if c > 0:
            wins += rng.binomial(int(c), p, n)
    wins = wins + already_won
    return {"p": float((wins >= target).mean()), "mean": float(wins.mean()),
            "p10": float(np.percentile(wins, 10)), "p90": float(np.percentile(wins, 90)), "draws": wins}


# ----------------------------------------------------------------------------- state
if "df" not in st.session_state:
    st.session_state["df"] = load()
    st.session_state["sample"] = False
df: pd.DataFrame = st.session_state["df"]

st.title("Chenora pipeline tracker")
st.caption("Log prospects, check the ICP gates, and see whether five paid Kenya contracts by 31 January is realistic. "
           "Use prospect codes, never people's names.")
if st.session_state["sample"]:
    st.warning("SAMPLE data: 100 fictional prospects. Nothing here is real. Clear it and add your own.")

with st.sidebar:
    st.header("Your data")
    st.write(f"Prospects: **{len(df)}**")
    up = st.file_uploader("Upload a pipeline CSV", type=["csv"])
    if up is not None and st.button("Use the uploaded file"):
        st.session_state["df"] = clean(pd.read_csv(up))
        st.session_state["sample"] = False
        save(st.session_state["df"])
        st.rerun()
    st.download_button("Download pipeline CSV", df.to_csv(index=False).encode(), "pipeline.csv", "text/csv")
    if SAMPLE_FILE.exists() and st.button("Load sample data"):
        st.session_state["df"] = clean(pd.read_csv(SAMPLE_FILE))
        st.session_state["sample"] = True
        st.rerun()
    if st.button("Clear everything"):
        st.session_state["df"] = clean(pd.DataFrame(columns=COLUMNS))
        st.session_state["sample"] = False
        st.rerun()
    st.info("On a free cloud host, saved data can disappear when the app restarts. Download the CSV after each session.")

tab_add, tab_view, tab_target = st.tabs(["1. Add and edit", "2. Pipeline view", "3. Can we hit five?"])

# ----------------------------------------------------------------------------- tab 1
with tab_add:
    st.subheader("Add a prospect")
    with st.form("add", clear_on_submit=True):
        a, b, c = st.columns(3)
        code = a.text_input("Prospect code", placeholder="KE-014", help="A code, not a person's name.")
        seg = b.selectbox("Segment", list(SEGMENTS), format_func=SEGMENTS.get)
        stage = c.selectbox("Stage", STAGES)
        d, e, f = st.columns(3)
        accounts = d.number_input("Business accounts they manage", min_value=0, step=100, help="The gate is 1,000+.")
        revenue = e.number_input("Annual revenue, USD (0 = unknown)", min_value=0, step=100000)
        source = f.selectbox("Lead source", SOURCES)
        g, h, i = st.columns(3)
        digital = g.radio("Digital records (CRM or billing)?", ["Yes", "No"], horizontal=True)
        access = h.radio("Can we reach the decision maker?", ["Yes", "No"], horizontal=True)
        owner = i.text_input("Owner", value="Founder")
        go = st.form_submit_button("Add prospect")
    if go:
        code = code.strip()
        if not code:
            st.error("Please enter a prospect code.")
        elif code in set(df["prospect_code"].astype(str)):
            st.error(f"{code} already exists. Edit it in the table below.")
        else:
            row = pd.DataFrame([{"prospect_code": code, "segment": seg,
                                 "accounts_managed": float(accounts) if accounts else np.nan,
                                 "annual_revenue_usd": float(revenue) if revenue else np.nan,
                                 "has_digital_records": digital, "decision_maker_access": access,
                                 "lead_source": source, "stage": stage, "date_added": date.today(),
                                 "last_stage_change": date.today(), "owner": owner, "why_won_or_lost": ""}])
            st.session_state["df"] = clean(pd.concat([df, row], ignore_index=True))
            st.session_state["sample"] = False
            ok = save(st.session_state["df"])
            st.success(f"Added {code}." + ("" if ok else " Could not save to disk: download the CSV."))
            st.rerun()

    st.subheader("Edit the table")
    st.caption("Change a stage, fix a number, or delete a row (select it, press Delete). Then press Save changes.")
    edited = st.data_editor(df, num_rows="dynamic", width="stretch", key="editor", column_config={
        "segment": st.column_config.SelectboxColumn("Segment", options=list(SEGMENTS), required=True),
        "stage": st.column_config.SelectboxColumn("Stage", options=STAGES, required=True),
        "has_digital_records": st.column_config.SelectboxColumn("Digital records", options=["Yes", "No"]),
        "decision_maker_access": st.column_config.SelectboxColumn("Decision-maker access", options=["Yes", "No"]),
        "lead_source": st.column_config.SelectboxColumn("Lead source", options=SOURCES),
        "accounts_managed": st.column_config.NumberColumn("Accounts", min_value=0, step=100),
        "annual_revenue_usd": st.column_config.NumberColumn("Revenue USD", min_value=0, step=100000),
        "date_added": st.column_config.DateColumn("Added"),
        "last_stage_change": st.column_config.DateColumn("Last stage change"),
        "why_won_or_lost": st.column_config.TextColumn("Why won or lost")})
    if st.button("Save changes", type="primary"):
        new = clean(pd.DataFrame(edited))
        codes = new["prospect_code"].dropna().astype(str)
        if new["prospect_code"].isna().any() or (codes.str.strip() == "").any():
            st.error("Every row needs a prospect code.")
        elif codes.duplicated().any():
            st.error("Duplicate prospect codes: " + ", ".join(codes[codes.duplicated()].unique()[:5]))
        else:
            old = df.set_index("prospect_code")["stage"].to_dict()
            moved = new["prospect_code"].isin(old) & (new["prospect_code"].map(old) != new["stage"])
            new.loc[moved, "last_stage_change"] = date.today()
            st.session_state["df"] = new
            st.session_state["sample"] = False
            ok = save(new)
            st.success("Saved." if ok else "Could not save to disk here. Download the CSV.")
            st.rerun()

# ----------------------------------------------------------------------------- tab 2
with tab_view:
    if df.empty:
        st.info("No prospects yet. Add one in tab 1, upload a CSV, or load the sample from the sidebar.")
    else:
        view = add_checks(df)
        active = view[view["stage"].isin(ACTIVE)]
        k = st.columns(5)
        k[0].metric("Prospects", len(view))
        k[1].metric("Active", len(active))
        k[2].metric("Pass the ICP gates", f"{int(view['passes_gates'].sum())} of {len(view)}")
        k[3].metric("Won (paid)", int((view["stage"] == "Won").sum()))
        k[4].metric("Est. year-one value (active, passing)",
                    f"${active.loc[active['passes_gates'], 'est_year_one_usd'].sum():,.0f}")
        left, right = st.columns(2)
        left.markdown("**Prospects by stage**")
        left.bar_chart(view["stage"].value_counts().reindex(STAGES, fill_value=0))
        right.markdown("**Prospects by segment**")
        right.bar_chart(view["segment"].map(SEGMENTS).value_counts())

        st.markdown("**Active prospects that fail an ICP gate**")
        fails = view[~view["passes_gates"] & view["stage"].isin(ACTIVE)]
        if fails.empty:
            st.success("All active prospects pass the gates.")
        else:
            st.dataframe(fails[["prospect_code", "segment", "stage", "accounts_managed", "fails_because"]],
                         width="stretch", hide_index=True)

        st.markdown("**Stuck prospects (no stage change for 14+ days)**")
        ref = pd.Timestamp("2026-11-22") if st.session_state["sample"] else pd.Timestamp(date.today())
        stuck = active[(ref - pd.to_datetime(active["last_stage_change"], errors="coerce")).dt.days >= 14]
        if len(stuck):
            st.dataframe(stuck[["prospect_code", "segment", "stage", "last_stage_change", "owner"]],
                         width="stretch", hide_index=True)
        else:
            st.write("None.")
        st.markdown("**All prospects with gate check and value**")
        st.dataframe(view[["prospect_code", "segment", "stage", "accounts_managed", "passes_gates", "est_year_one_usd"]],
                     width="stretch", hide_index=True)
        st.caption("Year-one value = $1 per account a month (minimum $12,000 a year) plus 15% of an assumed 2% of annual "
                   "revenue won back. An estimate, not a quote.")

# ----------------------------------------------------------------------------- tab 3
with tab_target:
    st.subheader("Can we reach the target by the deadline?")
    c1, c2, c3 = st.columns(3)
    today = c1.date_input("Today", value=date.today())
    deadline = c2.date_input("Deadline", value=TARGET_DATE)
    target = c3.number_input("Paid contracts needed", min_value=1, value=TARGET_CONTRACTS)
    days = max(0, (deadline - today).days)
    won = int((df["stage"] == "Won").sum()) if not df.empty else 0
    st.write(f"**{days} days** left. Already won: **{won}**.")

    vc = df["stage"].value_counts() if not df.empty else pd.Series(dtype=int)
    real = [int(vc.get(s, 0)) for s in ACTIVE]
    options = ["My pipeline (tab 1)", "Assumed split of 100 prospects", "Type the counts"]
    pick = st.radio("Where do the stage counts come from?", options, horizontal=True,
                    index=0 if sum(real) > 0 and not st.session_state["sample"] else 1)
    if pick == options[0]:
        counts = real if sum(real) > 0 else ASSUMED_MIX
        if sum(real) == 0:
            st.warning("No active prospects yet, using the assumed split.")
    elif pick == options[1]:
        counts = ASSUMED_MIX
        st.caption("Darren reported 100 prospects but not their stages. This split is a GUESS.")
    else:
        cols = st.columns(5)
        counts = [int(cols[i].number_input(s, min_value=0, value=ASSUMED_MIX[i], key=f"c_{s}")) for i, s in enumerate(ACTIVE)]
    st.write("Counts used:", dict(zip(ACTIVE, counts)))

    name = st.radio("Scenario", list(SCENARIOS), index=1, horizontal=True)
    mult = st.slider("Stress the win rates (1.0 = as assumed)", 0.5, 1.5, 1.0, 0.05)
    res = simulate(counts, SCENARIOS[name], days, int(target), won, mult)
    m = st.columns(3)
    m[0].metric(f"Chance of {int(target)}+ paid contracts", f"{res['p']:.0%}")
    m[1].metric("Expected contracts", f"{res['mean']:.1f}")
    m[2].metric("Likely range (10th to 90th pct)", f"{res['p10']:.0f} to {res['p90']:.0f}")
    st.bar_chart(pd.Series(res["draws"]).value_counts(normalize=True).sort_index().mul(100))
    st.caption("Share of 20,000 simulated pipelines (%) by number of paid contracts.")

    st.markdown("**All three scenarios**")
    st.dataframe(pd.DataFrame([{"Scenario": n, f"Chance of {int(target)}+": f"{simulate(counts, s, days, int(target), won, mult)['p']:.0%}",
                                "Expected": round(simulate(counts, s, days, int(target), won, mult)["mean"], 1)}
                               for n, s in SCENARIOS.items()]), hide_index=True, width="stretch")

    st.markdown("**What moves the answer most**")
    base = res["p"]
    def p_of(c=counts, d=days, mu=mult):
        return simulate(c, SCENARIOS[name], d, int(target), won, mu)["p"]
    rows = [("Win rates 30% lower", p_of(mu=mult * 0.7)), ("Win rates 30% higher", p_of(mu=mult * 1.3)),
            ("15 fewer days", p_of(d=max(0, days - 15))), ("15 more days", p_of(d=days + 15)),
            ("+5 prospects at Quote sent", p_of(c=[counts[0], counts[1], counts[2], counts[3] + 5, counts[4]])),
            ("+10 prospects at Scoping call", p_of(c=[counts[0], counts[1], counts[2] + 10, counts[3], counts[4]]))]
    tbl = pd.DataFrame([{"Change": a, "Chance": f"{b:.0%}", "Shift (points)": round((b - base) * 100)} for a, b in rows])
    st.dataframe(tbl.sort_values("Shift (points)", key=abs, ascending=False), hide_index=True, width="stretch")
    st.caption("Win rates and signing times are ASSUMPTIONS (see the top of app.py). Replace them with real outcomes as they "
               "arrive. This is a planning aid, not a forecast.")

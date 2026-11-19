"""Campus Complaint Portal Dashboard  (Streamlit + Plotly + pandas)
Run:  pip install streamlit plotly pandas numpy wordcloud matplotlib
      streamlit run app.py
"""
import numpy as np, pandas as pd, plotly.express as px, streamlit as st

st.set_page_config(page_title="Complaint Portal Dashboard", layout="wide")
SEC_COL = {"Hostel": "#3b82f6", "Classroom & Lab": "#10b981", "Other": "#f59e0b"}

# ---------- 1. DATA (synthetic; replace with your own CSV via the sidebar) ----------
# category: (section, weight, mean resolution days, keywords)
CATS = {
    "Internet": ("Hostel", 22, 1.5, ["wifi slow", "no internet", "router down", "LAN port"]),
    "Electric": ("Hostel", 16, 2, ["power cut", "switch broken", "tube light", "socket"]),
    "Carpentry": ("Hostel", 8, 4, ["door lock", "cupboard", "bed broken", "window"]),
    "Plumbing": ("Hostel", 12, 5, ["tap leak", "no water", "drain block", "flush"]),
    "Projector": ("Classroom & Lab", 6, 3, ["projector", "no display"]),
    "AC": ("Classroom & Lab", 5, 6, ["AC not cooling"]),
    "Fan": ("Classroom & Lab", 5, 2, ["fan noisy", "fan not working"]),
    "Lights": ("Classroom & Lab", 4, 1.5, ["lights off"]),
    "Bench": ("Classroom & Lab", 4, 4, ["bench broken"]),
    "Computer": ("Classroom & Lab", 5, 3, ["PC slow", "keyboard"]),
    "Mess": ("Other", 5, 2, ["food quality", "hygiene"]),
    "Library": ("Other", 2, 3, ["books", "seating"]),
    "Transport": ("Other", 2, 4, ["bus late"]),
    "Cleanliness": ("Other", 4, 1.5, ["dustbin", "washroom"]),
}
LOCS = {"Hostel": ["Block A", "Block B", "Block C", "Block C", "Block D"],
        "Classroom & Lab": ["Academic 1", "Academic 2", "Lab Complex"], "Other": ["Campus"]}


@st.cache_data
def make_data(n=600, seed=7):
    rng = np.random.default_rng(seed)
    names = list(CATS)
    cat = rng.choice(names, n, p=np.array([CATS[c][1] for c in names]) / sum(CATS[c][1] for c in names))
    month_w = np.array([1.6, 1.5, .8, .8, .9, 1.3, 1.5, .7, .6, .7, .9, 1.4])  # exam spikes
    m = rng.choice(12, n, p=month_w / month_w.sum())
    start = pd.Timestamp("2025-11-01")
    sub = [start + pd.DateOffset(months=int(mm)) + pd.Timedelta(days=int(rng.integers(0, 28)),
           hours=int(rng.choice(range(18, 24)) if CATS[c][0] == "Hostel" else rng.integers(9, 18)))
           for mm, c in zip(m, cat)]
    df = pd.DataFrame({"complaint_id": range(1, n + 1), "submitted": sub, "category": cat})
    df["section"] = df.category.map(lambda c: CATS[c][0])
    df["location"] = df.section.map(lambda s: rng.choice(LOCS[s]))
    df["keyword"] = df.category.map(lambda c: rng.choice(CATS[c][3]))
    df["has_photo"] = np.where(df.section == "Classroom & Lab", rng.random(n) < .6, False)
    st_ = rng.random(n)
    df["status"] = np.where(st_ < .15, "Open", np.where(st_ < .30, "In progress", "Resolved"))
    days = 0.5 + rng.exponential(df.category.map(lambda c: CATS[c][2]) * .8)
    df["resolved"] = np.where(df.status == "Resolved", df.submitted + pd.to_timedelta(days, unit="D"), pd.NaT)
    # messy values on purpose, so the cleaning step has work to do
    df.loc[rng.choice(n, 15, replace=False), "category"] = df.category.str.lower()
    df = pd.concat([df, df.sample(10, random_state=1)])  # duplicates
    return df


def clean(df):
    """Unit 2: consistency checking, duplicates, missing data."""
    log = {"rows before": len(df)}
    df = df.drop_duplicates(subset="complaint_id").copy()
    df["category"] = df.category.str.strip().str.title().replace({"Ac": "AC"})
    df["resolved"] = pd.to_datetime(df.resolved)
    df["submitted"] = pd.to_datetime(df.submitted)
    log["missing resolve dates (open/in-progress)"] = int(df.resolved.isna().sum())
    df["res_days"] = (df.resolved - df.submitted).dt.total_seconds() / 86400
    df["month"] = df.submitted.dt.to_period("M").astype(str)
    df["weekday"] = df.submitted.dt.day_name()
    df["band"] = pd.cut(df.submitted.dt.hour, [-1, 3, 7, 11, 15, 19, 23],
                        labels=["00-04", "04-08", "08-12", "12-16", "16-20", "20-24"])
    log["rows after"] = len(df)
    return df, log


# ---------- 2. SIDEBAR ----------
st.sidebar.header("Filters")
up = st.sidebar.file_uploader("Use your own CSV (optional)", type="csv")
raw = pd.read_csv(up) if up else make_data()
df, log = clean(raw)
sec = st.sidebar.multiselect("Section", list(SEC_COL), default=list(SEC_COL))
stat = st.sidebar.multiselect("Status", ["Open", "In progress", "Resolved"],
                              default=["Open", "In progress", "Resolved"])
lo, hi = df.submitted.min().date(), df.submitted.max().date()
dr = st.sidebar.slider("Date range", lo, hi, (lo, hi))
d = df[df.section.isin(sec) & df.status.isin(stat) &
       df.submitted.dt.date.between(*dr)]
with st.sidebar.expander("Data cleaning log (Unit 2)"):
    st.write(log)

# ---------- 3. HEADER + KPIs ----------
st.title("Campus Complaint Portal Dashboard")
st.caption("For the warden and administration: what is broken, where, and how fast it is fixed. "
           "Data is anonymised and shown at block or building level only.")
if d.empty:
    st.warning("No data for this filter."); st.stop()

top = d.category.value_counts().idxmax()
c = st.columns(4)
c[0].metric("Total complaints", len(d))
c[1].metric("Open", int((d.status == "Open").sum()))
c[2].metric("% resolved", f"{(d.status == 'Resolved').mean() * 100:.0f}%")
c[3].metric("Most frequent issue", top)
slow = d.groupby("category").res_days.median().idxmax()
st.info(f"**Insight:** {top} is the most frequent issue and {slow} takes the longest to fix. "
        "Volume peaks around exam months. Click **Enlarge** under any chart to view it bigger.")


# ---------- 4. CHART HELPERS ----------
def tidy(fig, h):
    """Tufte: no gridlines, no chartjunk, plain background."""
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      showlegend=False, title_font_size=16)
    fig.update_xaxes(showgrid=False); fig.update_yaxes(showgrid=False)
    return fig


def render(fig, key):
    if hasattr(fig, "savefig"):
        st.pyplot(fig)
    else:
        st.plotly_chart(fig, width="stretch", key=key)


@st.dialog("Enlarged chart", width="large")
def enlarge(build, key):
    render(build(650), key + "_big")


def card(col, key, build):
    """Draw a chart with an Enlarge button that opens it in a big pop-up."""
    with col:
        render(build(330), key)
        if st.button("🔍 Enlarge", key="btn_" + key):
            enlarge(build, key)


# ---------- 5. CHART BUILDERS ----------
mc = d.groupby("month").size().reset_index(name="complaints")
cc = d.category.value_counts().reset_index()
cc.columns = ["category", "count"]
cc["section"] = cc.category.map(lambda x: CATS.get(x, ("Other",))[0])
h1 = d.pivot_table(index="location", columns="category", values="complaint_id", aggfunc="count", fill_value=0)
m2 = d.groupby("month").agg(volume=("complaint_id", "size"), mean_days=("res_days", "mean")).dropna().reset_index()
kw = d.keyword.value_counts()


def b_month(h):
    return tidy(px.area(mc, x="month", y="complaints", title="Complaints per month"), h)


def b_pie(h):
    return tidy(px.pie(d, names="section", color="section", color_discrete_map=SEC_COL, hole=.5,
                       title="Section share"), h).update_layout(showlegend=True)


def b_cat(h):
    return tidy(px.bar(cc.sort_values("count"), x="count", y="category", orientation="h", color="section",
                       color_discrete_map=SEC_COL, title="Complaints by category"), h)


def b_loc(h):
    return tidy(px.imshow(h1, text_auto=True, color_continuous_scale="Blues", aspect="auto",
                          title="Location vs. category"), h).update_coloraxes(showscale=False)


def b_wc(h):
    try:
        import matplotlib.pyplot as plt
        from wordcloud import WordCloud
        wc = WordCloud(width=900, height=int(h * 1.6), background_color="white").generate_from_frequencies(kw.to_dict())
        fig, ax = plt.subplots(figsize=(8, h / 55)); ax.imshow(wc); ax.axis("off"); ax.set_title("Common issues")
        return fig
    except ImportError:  # fallback if wordcloud is not installed
        return tidy(px.bar(kw.head(12)[::-1], orientation="h", title="Common issues"), h)


def b_scatter(h):
    fig = tidy(px.scatter(m2, x="volume", y="mean_days", hover_name="month",
                          title="Monthly volume vs. mean resolution time"), h)
    if len(m2) > 2:
        k, i0 = np.polyfit(m2.volume, m2.mean_days, 1)
        xs = np.array([m2.volume.min(), m2.volume.max()])
        fig.add_scatter(x=xs, y=k * xs + i0, mode="lines", line=dict(color="red", dash="dash"))
    return fig


# ---------- 6. LAYOUT ----------
a, b = st.columns([2, 1]); card(a, "month", b_month); card(b, "pie", b_pie)
a, b = st.columns(2); card(a, "cat", b_cat); card(b, "loc", b_loc)
a, b = st.columns(2); card(a, "wc", b_wc); card(b, "scatter", b_scatter)

st.subheader("Hotspots: top 5 repeat problem areas")
hot = (d.groupby(["location", "category"]).size().reset_index(name="complaints")
       .sort_values("complaints", ascending=False).head(5))
st.dataframe(hot, hide_index=True, width="stretch")

st.download_button("⬇ Download filtered data (CSV)", d.to_csv(index=False), "complaints_filtered.csv", "text/csv")
with st.expander("Descriptive statistics of resolution time in days (Unit 3)"):
    st.dataframe(d.groupby("category").res_days.describe(percentiles=[.25, .5, .75]).round(2))

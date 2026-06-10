# app.py — Olist Fulfilment & Revenue Dashboard (Streamlit)
# Run locally:  pip install streamlit plotly pandas
#               streamlit run app.py
# Needs: master.csv in the same folder (export from your notebook — see note at bottom)

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Olist Ops & Revenue Dashboard", layout="wide")

@st.cache_data
def load():
    df = pd.read_csv("master.csv", parse_dates=["order_purchase_timestamp"])
    df = df[df.order_purchase_timestamp >= "2017-01-01"]          # drop sparse 2016
    bins = [0, 3, 7, 14, 21, 100]
    labels = ["0-3d", "4-7d", "8-14d", "15-21d", "22d+"]
    df["speed_bucket"] = pd.cut(df.delivery_days, bins=bins, labels=labels)
    return df

df = load()

# ---------------- Sidebar filters (this is what makes it "interactive") ----------
st.sidebar.header("Filters")
states = st.sidebar.multiselect("Customer state", sorted(df.customer_state.dropna().unique()))
cats   = st.sidebar.multiselect("Category", sorted(df.product_category_name_english.dropna().unique()))

f = df.copy()
if states: f = f[f.customer_state.isin(states)]
if cats:   f = f[f.product_category_name_english.isin(cats)]

st.title("E-commerce Fulfilment & Revenue Dashboard")
st.caption(f"Olist Brazilian e-commerce · {len(f):,} delivered orders · 2017–2018 · by Amish Dildeep")

# ---------------- KPI strip ----------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Median delivery", f"{f.delivery_days.median():.0f} days",
          f"p90: {f.delivery_days.quantile(0.9):.0f} days", delta_color="off")
k2.metric("Late deliveries", f"{f.late.mean():.1%}")
k3.metric("Avg order value", f"R$ {f.revenue.mean():.0f}")
k4.metric("Repeat customers",
          f"{(f.groupby('customer_unique_id').order_id.nunique() > 1).mean():.1%}")

st.divider()

# ---------------- Row 1: speed + revenue ----------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("How fast do orders arrive?")
    fig = px.histogram(f[f.delivery_days <= 40], x="delivery_days", nbins=40,
                       labels={"delivery_days": "days to deliver"})
    fig.add_vline(x=f.delivery_days.median(), line_dash="dash",
                  annotation_text=f"median {f.delivery_days.median():.0f}d")
    fig.update_layout(showlegend=False, height=380, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Where does revenue concentrate?")
    top = (f.groupby("product_category_name_english").revenue.sum()
             .sort_values(ascending=False).head(10).reset_index())
    fig = px.bar(top, x="revenue", y="product_category_name_english",
                 orientation="h", labels={"product_category_name_english": ""})
    fig.update_layout(yaxis=dict(autorange="reversed"), height=380, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Row 2: trend + the headline finding ----------------
c3, c4 = st.columns(2)

with c3:
    st.subheader("Monthly revenue trend")
    monthly = (f.set_index("order_purchase_timestamp").resample("ME").revenue.sum()
                 .reset_index())
    fig = px.line(monthly, x="order_purchase_timestamp", y="revenue", markers=True,
                  labels={"order_purchase_timestamp": "", "revenue": "R$"})
    fig.update_layout(height=380, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Does speed drive satisfaction?")
    sb = f.groupby("speed_bucket", observed=True).review_score.mean().reset_index()
    fig = px.bar(sb, x="speed_bucket", y="review_score", text_auto=".2f",
                 labels={"speed_bucket": "delivery speed", "review_score": "avg review"})
    fig.update_layout(yaxis_range=[2.4, 5], height=340, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
    on_lt = f.groupby("late").review_score.mean()
    if True in on_lt.index and False in on_lt.index:
        st.error(f"Broken delivery promises crater ratings: "
                 f"**{on_lt[True]:.2f}** stars when late vs **{on_lt[False]:.2f}** on time")

st.divider()
st.caption("Limitation: Olist is marketplace e-commerce (days-long delivery), used here as a proxy "
           "for fulfilment economics. The relationships — density→speed, reliability→satisfaction, "
           "category concentration — generalise to quick commerce.")

# ---------------------------------------------------------------------------
# Exporting master.csv from your notebook (keep it small for free hosting):
#   cols = ["order_id", "order_purchase_timestamp", "customer_unique_id",
#           "customer_state", "product_category_name_english",
#           "revenue", "delivery_days", "late", "review_score"]
#   master[cols].to_csv("master.csv", index=False)
# ---------------------------------------------------------------------------

import os
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

st.set_page_config(page_title="Cart2Insights", layout="wide")


@st.cache_resource
def get_engine():
    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url)


@st.cache_data
def run_query(sql):
    return pd.read_sql(sql, get_engine())


st.title("Cart2Insights: E-Commerce Dashboard")

# ---------- 1. Business Overview ----------
overview = run_query("""
    SELECT COUNT(DISTINCT o.order_id) AS total_orders,
           COUNT(DISTINCT c.customer_unique_id) AS total_customers,
           ROUND(SUM(oi.price), 2) AS total_revenue,
           ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
""").iloc[0]

sellers = run_query("SELECT COUNT(*) AS n FROM sellers").iloc[0]["n"]
avg_review = run_query("SELECT ROUND(AVG(review_score), 2) AS r FROM order_reviews").iloc[0]["r"]

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Revenue", f"{overview['total_revenue']:,.0f}")
c2.metric("Total Orders", f"{int(overview['total_orders']):,}")
c3.metric("Total Customers", f"{int(overview['total_customers']):,}")
c4.metric("Total Sellers", f"{int(sellers):,}")
c5.metric("Avg Order Value", f"{overview['avg_order_value']:,.2f}")
c6.metric("Avg Review Score", f"{float(avg_review):.2f}")

# ---------- 2. Sales Analysis ----------
st.header("Sales Analysis")
monthly = run_query("""
    SELECT CONCAT(YEAR(o.order_purchase_timestamp), '-',
                  LPAD(MONTH(o.order_purchase_timestamp), 2, '0')) AS month,
           ROUND(SUM(oi.price), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY month
    ORDER BY month
""")
st.plotly_chart(
    px.line(monthly, x="month", y="revenue", markers=True,
            title="Monthly revenue (Jan 2017 to Aug 2018)"),
    use_container_width=True, key="monthly_revenue")

cat_rev = run_query("""
    SELECT COALESCE(t.product_category_name_english, p.product_category_name) AS category,
           ROUND(SUM(oi.price), 2) AS revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN product_category_translation t
           ON p.product_category_name = t.product_category_name
    GROUP BY category
    ORDER BY revenue DESC
    LIMIT 10
""")
st.plotly_chart(
    px.bar(cat_rev, x="revenue", y="category", orientation="h",
           title="Top 10 categories by revenue")
    .update_layout(yaxis={"categoryorder": "total ascending"}),
    use_container_width=True, key="category_revenue")

# ---------- 3. Customer Analysis ----------
st.header("Customer Analysis")
repeat = run_query("""
    SELECT CASE WHEN n > 1 THEN 'Repeat' ELSE 'New (one order)' END AS customer_type,
           COUNT(*) AS customers
    FROM (
        SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS n
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        WHERE o.order_status NOT IN ('canceled', 'unavailable')
        GROUP BY c.customer_unique_id
    ) t
    GROUP BY customer_type
""")
top_states = run_query("""
    SELECT c.customer_state, COUNT(DISTINCT o.order_id) AS orders
    FROM orders o JOIN customers c ON o.customer_id = c.customer_id
    GROUP BY c.customer_state
    ORDER BY orders DESC
    LIMIT 10
""")
left, right = st.columns(2)
left.plotly_chart(
    px.pie(repeat, names="customer_type", values="customers",
           title="Repeat vs new customers"),
    use_container_width=True, key="repeat_pie")
right.plotly_chart(
    px.bar(top_states, x="customer_state", y="orders",
           title="Top 10 states by orders"),
    use_container_width=True, key="top_states")

# ---------- 4. Seller & Product Analysis ----------
st.header("Seller & Product Analysis")
top_sellers = run_query("""
    SELECT LEFT(seller_id, 8) AS seller, ROUND(SUM(price), 2) AS revenue
    FROM order_items
    GROUP BY seller_id
    ORDER BY revenue DESC
    LIMIT 10
""")
st.plotly_chart(
    px.bar(top_sellers, x="seller", y="revenue",
           title="Top 10 sellers by revenue"),
    use_container_width=True, key="top_sellers")

# ---------- 5. Delivery Analysis ----------
st.header("Delivery Analysis")
delivery = run_query("""
    SELECT c.customer_state AS state,
           ROUND(AVG(DATEDIFF(o.order_delivered_customer_date,
                              o.order_purchase_timestamp)), 1) AS avg_delivery_days
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
    GROUP BY c.customer_state
    ORDER BY avg_delivery_days
""")
ontime = run_query("""
    SELECT CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
                THEN 'Delayed' ELSE 'On time' END AS delivery_status,
           COUNT(*) AS orders,
           ROUND(AVG(r.review_score), 2) AS avg_review
    FROM orders o
    JOIN order_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
    GROUP BY delivery_status
""")
d1, d2 = st.columns(2)
d1.plotly_chart(
    px.bar(delivery, x="state", y="avg_delivery_days",
           title="Average delivery days by state"),
    use_container_width=True, key="delivery_by_state")
d2.plotly_chart(
    px.pie(ontime, names="delivery_status", values="orders",
           title="On-time vs delayed orders"),
    use_container_width=True, key="ontime_pie")

# ---------- 6. Customer Experience ----------
st.header("Customer Experience")
scores = run_query("""
    SELECT review_score, COUNT(*) AS reviews
    FROM order_reviews
    GROUP BY review_score
    ORDER BY review_score
""")
e1, e2 = st.columns(2)
e1.plotly_chart(
    px.bar(scores, x="review_score", y="reviews",
           title="Review score distribution"),
    use_container_width=True, key="review_dist")
e2.plotly_chart(
    px.bar(ontime, x="delivery_status", y="avg_review",
           title="Average review: delayed vs on-time"),
    use_container_width=True, key="review_by_delivery")
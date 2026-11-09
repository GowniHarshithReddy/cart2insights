# Cart2Insights: Decoding E-Commerce Performance

An end-to-end e-commerce analytics project built with **Python, Pandas, MySQL, SQLAlchemy, statistics and Streamlit**. It takes 9 raw CSV tables (orders, customers, products, sellers, payments, reviews, geolocation) and turns them into a cleaned SQL database, statistical findings, an interactive dashboard and business recommendations.

**Author:** Gowni Harshith Reddy
**Domain:** E-Commerce & Retail Analytics

---

## 1. Project Objective

An e-commerce platform stores its data across many related tables, which makes overall performance hard to see. This project analyses that data to answer questions about:

- Sales and revenue trends
- Customer behaviour (including repeat buying)
- Product and seller performance
- Payments and order outcomes
- Delivery performance
- Customer satisfaction (review scores)

---

## 2. Tech Stack

| Area | Tools |
|---|---|
| Language | Python 3.13 |
| Data work | Pandas, NumPy |
| Visualisation | Matplotlib, Seaborn, Plotly |
| Statistics | SciPy |
| Database | MySQL 8, SQLAlchemy, PyMySQL |
| Dashboard | Streamlit |
| Version control | Git / GitHub |

---

## 3. Project Structure

```
cart2insights/
├── app/
│   └── app.py                      # Streamlit dashboard (reads from MySQL)
├── data/                           # NOT uploaded to GitHub (see .gitignore)
│   ├── raw/                        # 9 original CSV files
│   └── cleaned/                    # cleaned tables and engineered features
├── notebooks/
│   ├── 01_data_loading.ipynb       # load, quality checks, cleaning, load into MySQL
│   ├── 02_feature_engineering.ipynb
│   ├── 03_eda.ipynb
│   └── 04_statistics.ipynb
├── sql/
│   └── analysis_queries.sql        # SQL analysis queries
├── .env                            # database credentials (NOT uploaded)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 4. Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/GowniHarshithReddy/cart2insights.git
   cd cart2insights
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Add the dataset.** Place the 9 raw CSV files in `data/raw/`. The data is not included in this repository.
4. **Install MySQL 8** and create the database:
   ```sql
   CREATE DATABASE cart2insights_db;
   ```
5. **Create a `.env` file** in the project root (never commit this file):
   ```
   DB_USER=root
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=cart2insights_db
   ```
6. **Run the notebooks in order** (`01` to `04`). Notebook 01 cleans the data, creates the tables with keys, and loads them into MySQL.
7. **Start the dashboard**
   ```bash
   python -m streamlit run app/app.py
   ```
   Then open http://localhost:8501.

---

## 5. Dataset and ER Diagram

The dataset has **9 related tables**:

| Table | Rows (raw) | Primary key | Description |
|---|---|---|---|
| customers | 99,441 | customer_id | Customer record per order; `customer_unique_id` identifies the real person |
| orders | 99,441 | order_id | Order status and key timestamps |
| order_items | 112,650 | order_id + order_item_id | Products in each order, price, freight |
| order_payments | 103,886 | order_id + payment_sequential | Payment type, installments, value |
| order_reviews | 99,224 | review_id | Review score and comments |
| products | 32,951 | product_id | Product category and size |
| sellers | 3,095 | seller_id | Seller location |
| geolocation | 1,000,163 | zip code prefix (after cleaning) | Zip code to latitude and longitude |
| product_category_translation | 71 | product_category_name | Portuguese to English category names |

**Key relationships:** a customer places orders; an order has items, payments and reviews; an item links a product and a seller; products link to category translation.

> Add your ER diagram image here: `![ER Diagram](images/er_diagram.png)`

---

## 6. Methodology

### Step 1: Data quality analysis
- Checked shape, data types, missing values, duplicates and primary-key uniqueness for all 9 tables.
- Missing delivery dates in `orders` correspond to orders that were never delivered, so they were **kept as missing** (not filled with invented dates).
- Review comment title and message are mostly empty because many customers only give a star rating.

### Step 2: Data cleaning
| Issue found | Action |
|---|---|
| Date columns stored as text | Converted to datetime |
| `product_name_lenght`, `product_description_lenght` misspelled | Renamed to `length` |
| 610 products with no category and listing info | Category set to `unknown`; numeric fields filled with the median |
| 2 products with missing size/weight | Filled with the median |
| 814 repeated `review_id` values | Kept one row per `review_id` |
| Geolocation: 261,831 duplicate rows, repeated zip codes | Dropped duplicates, then one row per zip prefix (mean latitude/longitude) |
| 3 payments with type `not_defined` (all on canceled orders) | Removed |
| 6 voucher payments with value 0 | Kept (valid leftover entries on split payments) |
| City and state text | Standardised (lowercase cities, uppercase states) |

Validation checks passed: no item price <= 0, all review scores between 1 and 5, no order delivered before it was purchased, and all foreign keys resolve to existing parent rows.

**Data-quality decision:** 278 customer zip codes and 7 seller zip codes do not exist in geolocation. These are real customers and sellers, so they were **not deleted**. No foreign key was created from `customers`/`sellers` to `geolocation`; use a `LEFT JOIN` when coordinates are needed.

### Step 3: Store in MySQL
Tables were created from the ER diagram with primary and foreign key constraints, then loaded with SQLAlchemy and verified with row counts. Credentials are read from `.env`.

### Step 4: Feature engineering
| Feature | Definition |
|---|---|
| total_order_value | items price + freight per order |
| delivery_days | delivered date minus purchase date (whole days) |
| delivery_delay_days | delivered date minus estimated date (positive = late) |
| is_delayed | delivery_delay_days > 0 |
| customer_order_count, customer_total_spending, avg_order_value | per `customer_unique_id`, excluding canceled/unavailable orders |
| is_repeat_customer | customer_order_count > 1 |
| seller_revenue, seller_order_count, seller_items_sold | per seller |

### Step 5: Exploratory data analysis
Univariate (status, delivery days, review scores, order value), bivariate (delay vs review score), multivariate (correlation heatmap), trend (orders per month), and distribution analysis.

### Step 6: Statistical analysis
See Section 7.

### Step 7: SQL analysis and dashboard
SQL covers SELECT/WHERE/ORDER BY, GROUP BY, HAVING, joins, subqueries, CTEs, window functions and aggregations (`sql/analysis_queries.sql`). The Streamlit dashboard runs these queries live against MySQL.

---

## 7. Statistical Tests

### Test 1: Independent two-sample t-test (Welch): delivery and satisfaction
- **H0:** mean review score is the same for delayed and on-time orders. **H1:** delayed orders score lower.
- **Assumptions:** independent observations; large samples (CLT); Levene's test showed unequal variances, so Welch's version was used.
- **Result:** delayed mean **2.27** (n = 6,361) vs on-time mean **4.29** (n = 89,248); t = -100.78, p < 0.001. **Reject H0.**
- **Insight:** late orders score about 2 stars lower. The size of the gap, not just the p-value, is what makes this meaningful.

### Test 2: One-way ANOVA: product category and order value
- **H0:** mean order value is equal across categories. **H1:** at least one differs.
- **Data:** 52 categories with at least 100 orders (97,814 orders); category taken from the first item of each order.
- **Assumptions:** Levene's test failed (unequal variances) and order values are right-skewed, so **Kruskal-Wallis** was run as a robustness check.
- **Result:** F = 201.44, p < 0.001; Kruskal-Wallis p < 0.001. **Reject H0.**
- **Insight:** highest mean order value is `computers` (about 1,286) and lowest is `food` (about 82), roughly 16 times lower.

### Test 3: Chi-square test of independence: payment method and order status
- **H0:** payment method and order status are independent. **H1:** they are associated.
- **Data:** one main payment type per order (largest payment); rare statuses merged into "other". Smallest expected count was 9.35 (at least 5, so the test is valid).
- **Result:** chi-square = 267.02, dof = 12, p = 3.8e-50. **Reject H0.** But **Cramér's V = 0.03**, a very weak association.
- **Insight:** voucher orders have a higher cancellation rate (about 2.8%) than other payment types (about 0.5% to 0.6%), but payment method is not a major driver of order outcome.

---

## 8. Key Results

| Metric | Value |
|---|---|
| Total revenue | 13,494,401 |
| Total orders | 98,199 |
| Total customers | 94,983 |
| Total sellers | 3,095 |
| Average order value | 137.42 |
| Average review score | 4.09 |
| Median delivery time | 10 days (mean 12.1) |
| Repeat customers | about 3% |

---

## 9. Dashboard

The Streamlit app (`app/app.py`) connects to MySQL and has six sections:

1. **Business Overview:** revenue, orders, customers, sellers, average order value, average review score
2. **Sales Analysis:** monthly revenue (Jan 2017 to Aug 2018), top 10 categories by revenue
3. **Customer Analysis:** repeat vs new customers, top 10 states by orders
4. **Seller and Product Analysis:** top 10 sellers by revenue
5. **Delivery Analysis:** average delivery days by state, on-time vs delayed orders
6. **Customer Experience:** review score distribution, average review for delayed vs on-time orders

> Add dashboard screenshots here: `![Dashboard](images/dashboard.png)`

---

## 10. Business Insights and Recommendations

Format: **Observation → Interpretation → Business Impact**

| # | Observation | Interpretation | Business impact and recommendation |
|---|---|---|---|
| 1 | Only about 3% of customers place a second order | The platform relies on one-time purchases | Retention is the biggest growth opportunity: post-delivery offers, loyalty rewards |
| 2 | Delayed orders average 2.27 stars vs 4.29 for on-time (significant) | Delivery reliability strongly drives satisfaction | Set realistic delivery estimates and monitor late orders by seller and region |
| 3 | Delivery takes about 8.7 days in SP but about 26 to 29 days in far northern states | Distance from sellers drives delivery time | Regional warehouses and seller onboarding in distant regions |
| 4 | Revenue peaks in Nov 2017, then plateaus through Aug 2018 | Seasonal peak (likely Black Friday), then slower growth | Prepare stock and delivery capacity before November; look for new growth sources |
| 5 | Order value differs significantly by category (computers about 16x food) | Product type shapes spending | Premium promotion for high-ticket categories, bundles for low-ticket ones |
| 6 | Voucher orders are cancelled more often (about 2.8% vs about 0.5%), but the association is weak | Vouchers add small but avoidable cancellation risk | Validate voucher use earlier in checkout |
| 7 | Revenue is concentrated in a few top sellers (top seller about 230k) | Dependence on a small group | Support top sellers and help mid-tier sellers grow |
| 8 | Review score correlates most with delivery days (-0.33) and barely with order value (-0.04) | Customers judge speed and reliability more than price | Invest in logistics before discounts |

---

## 11. Definitions and Limitations

- **Revenue** = sum of item price (freight excluded), canceled and unavailable orders excluded.
- **Delayed order (SQL and dashboard):** delivered after the estimated date, compared by full timestamp (about 8% of delivered orders with reviews).
- **Delayed order (Python `is_delayed`):** whole days late greater than 0 (about 6.8% of delivered orders). The two definitions give slightly different counts, so they are not interchangeable.
- **Time range:** the dataset has very few orders in late 2016 and after Aug 2018, so trend charts and the dashboard use **Jan 2017 to Aug 2018**.
- Statistical results show **association, not proof of cause**. With about 99,000 orders, even tiny differences are statistically significant, so effect sizes (mean gap, Cramér's V) are reported alongside p-values.
- The ANOVA assigns each order to the category of its first item.

---

## 12. Requirements

Create `requirements.txt` with:

```
pandas
numpy
matplotlib
seaborn
scipy
sqlalchemy
pymysql
python-dotenv
streamlit
plotly
jupyter
ipykernel
```

---

## 13. Security Note

Database credentials live in `.env` and are never committed. The `data/` folder is also excluded to keep large datasets out of the repository.

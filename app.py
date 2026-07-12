import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="Retail Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("🛒 Online Retail Sales Dashboard")
st.markdown("Analyzing customer purchasing behavior and revenue trends")

# ---------- Database Connection ----------
@st.cache_resource
def get_db_connection():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'dataset', 'myapp.db')
    return sqlite3.connect(db_path)

# ---------- Load Data with Caching ----------
@st.cache_data
def load_data(query):
    """Run a SQL query and return a DataFrame."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df

# ---------- SIDEBAR FILTERS ----------
st.sidebar.header("🔍 Filters")

# Get unique countries for filter
countries_df = load_data("SELECT DISTINCT Country FROM sales ORDER BY Country")
countries = countries_df['Country'].tolist()
selected_country = st.sidebar.selectbox("Select Country", options=['All'] + countries)

# Build dynamic WHERE clause
where_clause = ""
if selected_country != 'All':
    where_clause = f"WHERE Country = '{selected_country}'"

# ---------- KPI CARDS ----------
st.subheader("📈 Key Performance Indicators")

kpi_query = f"""
SELECT 
    SUM(TotalPrice) as Total_Revenue,
    COUNT(DISTINCT "Customer ID") as Unique_Customers,
    COUNT(DISTINCT Invoice) as Total_Orders,
    AVG(TotalPrice) as Avg_Order_Value
FROM sales
{where_clause}
"""
kpi_df = load_data(kpi_query)

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Revenue", f"${kpi_df['Total_Revenue'].iloc[0]:,.0f}")
col2.metric("👤 Unique Customers", f"{kpi_df['Unique_Customers'].iloc[0]:,}")
col3.metric("📦 Total Orders", f"{kpi_df['Total_Orders'].iloc[0]:,}")
col4.metric("📊 Avg Order Value", f"${kpi_df['Avg_Order_Value'].iloc[0]:,.2f}")

# ---------- CHARTS ----------

# 1. Monthly Revenue Trend
monthly_query = f"""
SELECT 
    Monthname as Month,
    SUM(TotalPrice) as Revenue
FROM sales
{where_clause}
GROUP BY Month
ORDER BY MIN(Month)
"""
monthly_df = load_data(monthly_query)

if not monthly_df.empty:
    fig1 = px.line(
        monthly_df,
        x='Month',
        y='Revenue',
        title='📆 Monthly Revenue Trend',
        markers=True
    )
    st.plotly_chart(fig1, width='stretch')

# 2. Top 10 Products by Revenue
products_query = f"""
SELECT 
    Description,
    SUM(TotalPrice) as Revenue
FROM sales
{where_clause}
GROUP BY Description
ORDER BY Revenue DESC
LIMIT 10
"""
products_df = load_data(products_query)

if not products_df.empty:
    fig2 = px.bar(
        products_df,
        x='Revenue',
        y='Description',
        orientation='h',
        title='🏆 Top 10 Products by Revenue',
        color='Revenue',
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig2, width='stretch')

# 3. Revenue by Country
country_query = f"""
SELECT 
    Country,
    SUM(TotalPrice) as Revenue
FROM sales
{where_clause}
GROUP BY Country
ORDER BY Revenue DESC
LIMIT 10
"""
country_df = load_data(country_query)

if not country_df.empty:
    fig3 = px.pie(
        country_df,
        values='Revenue',
        names='Country',
        title='🌍 Revenue Distribution by Country (Top 10)'
    )
    st.plotly_chart(fig3, width='stretch')

# 4. Top 5 Customers
customers_query = f"""
SELECT 
    "Customer ID",
    SUM(TotalPrice) as Total_Spent,
    COUNT(DISTINCT Invoice) as Order_Count
FROM sales
{where_clause}
GROUP BY "Customer ID"
ORDER BY Total_Spent DESC
LIMIT 5
"""
customers_df = load_data(customers_query)

if not customers_df.empty:
    st.subheader("👑 Top 5 VIP Customers")
    st.dataframe(customers_df, width='stretch')

# ---------- KEY BUSINESS INSIGHTS ----------
st.subheader("💡 Key Business Insights")

peak_query = f"""
    SELECT Monthname as Month, SUM(TotalPrice) as Revenue
    FROM sales
    {where_clause}
    GROUP BY Monthname
    ORDER BY Revenue DESC
    LIMIT 1
"""
peak_df = load_data(peak_query)

uk_query = f"""
    SELECT 
        SUM(TotalPrice) as Total_Revenue,
        SUM(CASE WHEN Country = 'United Kingdom' THEN TotalPrice ELSE 0 END) as UK_Revenue
    FROM sales
    {where_clause}
"""
uk_df = load_data(uk_query)

seller_query = f"""
    SELECT Description, SUM(Quantity) as Total_Quantity
    FROM sales
    {where_clause}
    GROUP BY Description
    ORDER BY Total_Quantity DESC
    LIMIT 1
"""
seller_df = load_data(seller_query)

peak_month = peak_df['Month'].iloc[0] if not peak_df.empty else "N/A"
peak_revenue = peak_df['Revenue'].iloc[0] if not peak_df.empty else 0
total_rev = uk_df['Total_Revenue'].iloc[0]
uk_rev = uk_df['UK_Revenue'].iloc[0]
uk_pct = (uk_rev / total_rev * 100) if total_rev > 0 else 0

best_seller = seller_df['Description'].iloc[0] if not seller_df.empty else "N/A"
best_qty = seller_df['Total_Quantity'].iloc[0] if not seller_df.empty else 0

col1, col2, col3 = st.columns(3)
col1.metric("📈 Peak Month", peak_month, f"${peak_revenue:,.0f} in sales")
col2.metric("🇬🇧 UK Share", f"{uk_pct:.1f}%", f"of filtered revenue")
col3.metric("🏆 Best Seller", best_seller[:25] + "..." if len(best_seller) > 50 else best_seller, f"{best_qty:,} units sold")

st.caption("💡 Insights automatically update when you apply filters")

# ---------- RAW DATA PREVIEW ----------
with st.expander("📋 View Raw Data"):
    raw_query = f"SELECT * FROM sales {where_clause} LIMIT 100"
    raw_df = load_data(raw_query)
    st.dataframe(raw_df)
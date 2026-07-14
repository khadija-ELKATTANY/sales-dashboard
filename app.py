import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os
import urllib.request
from io import BytesIO

# ---------- Download and build database if missing ----------
def ensure_database():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'dataset', 'myapp.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if not os.path.exists(db_path):
        st.warning("🔄 Database not found. Building from scratch... This may take a few minutes.")
        
        # Download the Excel file directly from UCI
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00502/online_retail_II.xlsx"
        
        try:
            # Download the file
            with urllib.request.urlopen(url) as response:
                excel_data = response.read()
            
            # Read both sheets and combine them
            xls = pd.ExcelFile(BytesIO(excel_data))
            df1 = pd.read_excel(xls, sheet_name="Year 2009-2010")
            df2 = pd.read_excel(xls, sheet_name="Year 2010-2011")
            df = pd.concat([df1, df2], ignore_index=True)
            
            st.info(f"✅ Downloaded and combined {len(df)} rows from Excel.")
            
        except Exception as e:
            st.error(f"❌ Failed to download dataset: {str(e)}")
            st.stop()

        # Clean and engineer features
        df.dropna(subset=['Customer ID'], inplace=True)
        df = df[df['Quantity'] > 0]
        df['TotalPrice'] = df['Quantity'] * df['Price']
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
        df['Year'] = df['InvoiceDate'].dt.year
        df['Month'] = df['InvoiceDate'].dt.month
        df['Monthname'] = df['InvoiceDate'].dt.month_name()
        df['Weekday'] = df['InvoiceDate'].dt.day_name()
        df['Hour'] = df['InvoiceDate'].dt.hour
        df.drop_duplicates(inplace=True)

        # Save to SQLite
        conn = sqlite3.connect(db_path)
        df.to_sql('sales', conn, if_exists='replace', index=False)
        conn.close()
        st.success(f"✅ Database created with {len(df)} rows.")
    else:
        # Check if the table exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales'")
        if not cursor.fetchone():
            conn.close()
            os.remove(db_path)
            return ensure_database()
        conn.close()
    return db_path

# ---------- Page Configuration ----------
st.set_page_config(page_title="Retail Sales Dashboard", page_icon="📊", layout="wide")
st.title("🛒 Online Retail Sales Dashboard")
st.markdown("Analyzing customer purchasing behavior and revenue trends")

# ---------- Ensure Database ----------
db_path = ensure_database()

# ---------- Load Data (no caching of connection) ----------
@st.cache_data
def load_data(query):
    """Run a SQL query and return a DataFrame."""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df

# ---------- SIDEBAR FILTERS ----------
st.sidebar.header("🔍 Filters")
countries_df = load_data("SELECT DISTINCT Country FROM sales ORDER BY Country")
countries = countries_df['Country'].tolist()
selected_country = st.sidebar.selectbox("Select Country", options=['All'] + countries)

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
monthly_query = f"""
SELECT Monthname as Month, SUM(TotalPrice) as Revenue
FROM sales {where_clause}
GROUP BY Month
ORDER BY MIN(Month)
"""
monthly_df = load_data(monthly_query)
if not monthly_df.empty:
    fig1 = px.line(monthly_df, x='Month', y='Revenue', title='📆 Monthly Revenue Trend', markers=True)
    st.plotly_chart(fig1, width='stretch')

products_query = f"""
SELECT Description, SUM(TotalPrice) as Revenue
FROM sales {where_clause}
GROUP BY Description
ORDER BY Revenue DESC
LIMIT 10
"""
products_df = load_data(products_query)
if not products_df.empty:
    fig2 = px.bar(products_df, x='Revenue', y='Description', orientation='h',
                  title='🏆 Top 10 Products by Revenue', color='Revenue', color_continuous_scale='Viridis')
    st.plotly_chart(fig2, width='stretch')

country_query = f"""
SELECT Country, SUM(TotalPrice) as Revenue
FROM sales {where_clause}
GROUP BY Country
ORDER BY Revenue DESC
LIMIT 10
"""
country_df = load_data(country_query)
if not country_df.empty:
    fig3 = px.pie(country_df, values='Revenue', names='Country', title='🌍 Revenue Distribution by Country (Top 10)')
    st.plotly_chart(fig3, width='stretch')

# ---------- TOP CUSTOMERS ----------
customers_query = f"""
SELECT "Customer ID", SUM(TotalPrice) as Total_Spent, COUNT(DISTINCT Invoice) as Order_Count
FROM sales {where_clause}
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
FROM sales {where_clause}
GROUP BY Monthname
ORDER BY Revenue DESC
LIMIT 1
"""
peak_df = load_data(peak_query)

uk_query = f"""
SELECT 
    SUM(TotalPrice) as Total_Revenue,
    SUM(CASE WHEN Country = 'United Kingdom' THEN TotalPrice ELSE 0 END) as UK_Revenue
FROM sales {where_clause}
"""
uk_df = load_data(uk_query)

seller_query = f"""
SELECT Description, SUM(Quantity) as Total_Quantity
FROM sales {where_clause}
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

# ---------- RAW DATA ----------
with st.expander("📋 View Raw Data"):
    raw_query = f"SELECT * FROM sales {where_clause} LIMIT 100"
    raw_df = load_data(raw_query)
    st.dataframe(raw_df)


# ---------- RFM CUSTOMER SEGMENTATION ----------
st.divider()
st.header("🧑‍🤝‍🧑 Customer Segmentation (RFM Analysis)")

@st.cache_data
def load_rfm():
    # Use the CSV we just created (or query the database again)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rfm_path = os.path.join(script_dir, 'rfm_results.csv')
    
    if os.path.exists(rfm_path):
        return pd.read_csv(rfm_path)
    else:
        # Fallback: query the database and calculate RFM on the fly
        conn = sqlite3.connect(db_path)
        query = """
        SELECT 
            "Customer ID" as Customer_ID,
            MAX(InvoiceDate) AS LastPurchaseDate,
            COUNT(DISTINCT Invoice) AS Frequency,
            SUM(TotalPrice) AS Monetary
        FROM sales
        GROUP BY "Customer ID"
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        df['LastPurchaseDate'] = pd.to_datetime(df['LastPurchaseDate'])
        latest_date = df['LastPurchaseDate'].max()
        df['Recency'] = (latest_date - df['LastPurchaseDate']).dt.days
        
        df['R_Score'] = pd.qcut(df['Recency'], 5, labels=[5, 4, 3, 2, 1])
        df['F_Score'] = pd.qcut(df['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
        df['M_Score'] = pd.qcut(df['Monetary'], 5, labels=[1, 2, 3, 4, 5])
        
        def seg(row):
            if row['R_Score'] >= 4 and row['F_Score'] >= 4 and row['M_Score'] >= 4:
                return '👑 Champions'
            elif row['R_Score'] >= 3 and row['F_Score'] >= 3 and row['M_Score'] >= 3:
                return '💎 Loyal Customers'
            elif row['R_Score'] >= 2 and row['F_Score'] >= 2 and row['M_Score'] >= 2:
                return '📈 Potential Loyalists'
            elif row['R_Score'] <= 2 and row['F_Score'] >= 3 and row['M_Score'] >= 3:
                return '⚠️ At Risk'
            else:
                return '💤 Lost / Need Attention'
        
        df['Segment'] = df.apply(seg, axis=1)
        return df

rfm_df = load_rfm()

# Show segment counts
seg_counts = rfm_df['Segment'].value_counts().reset_index()
seg_counts.columns = ['Segment', 'Count']

fig_rfm = px.bar(
    seg_counts,
    x='Segment',
    y='Count',
    title='👥 Customer Segment Distribution',
    color='Segment',
    color_discrete_sequence=px.colors.qualitative.Set2
)
st.plotly_chart(fig_rfm, width='stretch')

# Show top 10 customers by segment
st.subheader("🏆 Top 10 Customers by Monetary Value")
top_customers = rfm_df.nlargest(10, 'Monetary')[['Customer_ID', 'Segment', 'Monetary', 'Frequency', 'Recency']]
st.dataframe(top_customers, width='stretch')




#------------SALES FORECAST (Prophet)------------
st.divider()
st.header("🔮 Sales Forecasting (Next 30 Days)")

@st.cache_data
def run_forecast():
    """Run Prophet forecast and return data"""
    conn = sqlite3.connect(db_path)
    query = """
 SELECT 
        DATE(InvoiceDate) as ds,
        SUM(TotalPrice) as y
    FROM sales
    GROUP BY DATE(InvoiceDate)
    ORDER BY ds
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['ds'] = pd.to_datetime(df['ds'])
    
    try:
        from prophet import Prophet
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        model.fit(df)
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)
        return forecast, model, df
    except ImportError:
        st.warning("⚠️ Prophet not installed. Forecast disabled.")
        return None, None, None

forecast, model, history = run_forecast()

if forecast is not None:
    # Extract last 30 days of forecast
    forecast_30 = forecast.tail(30)
    
    # Show total predicted revenue
    total_forecast = forecast_30['yhat'].sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Predicted (30 Days)", f"${total_forecast:,.0f}")
    col2.metric("📊 Avg Daily", f"${forecast_30['yhat'].mean():,.0f}")
    col3.metric("📅 Forecast Period", f"{forecast_30['ds'].min().date()} to {forecast_30['ds'].max().date()}")
    
    # Create plot
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Historical data (last 90 days)
    hist_90 = history.tail(90)
    fig.add_trace(go.Scatter(
        x=hist_90['ds'], 
        y=hist_90['y'],
        mode='lines',
        name='Actual Sales',
        line=dict(color='#1f77b4')
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_30['ds'], 
        y=forecast_30['yhat'],
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#ff7f0e', dash='dash')
    ))
    
    # Confidence interval (shaded area)
    fig.add_trace(go.Scatter(
        x=forecast_30['ds'].tolist() + forecast_30['ds'].tolist()[::-1],
        y=forecast_30['yhat_upper'].tolist() + forecast_30['yhat_lower'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(255, 127, 14, 0.2)',
        line=dict(color='rgba(255, 127, 14, 0)'),
        name='Confidence Interval'
    ))
    
    fig.update_layout(
        title='📊 30-Day Sales Forecast',
        xaxis_title='Date',
        yaxis_title='Sales ($)',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # Show forecast table (optional)
    with st.expander("📋 View Forecast Table"):
        display = forecast_30.copy()
        display['ds'] = display['ds'].dt.strftime('%Y-%m-%d')
        display['yhat'] = display['yhat'].round(2)
        display['yhat_lower'] = display['yhat_lower'].round(2)
        display['yhat_upper'] = display['yhat_upper'].round(2)
        display.columns = ['Date', 'Predicted', 'Lower Bound', 'Upper Bound']
        st.dataframe(display, width='stretch')


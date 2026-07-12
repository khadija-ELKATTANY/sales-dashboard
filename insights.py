import sqlite3
import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'dataset', 'myapp.db')
conn = sqlite3.connect(db_path)

print("📊 === KEY BUSINESS INSIGHTS === \n")

# Insight 1: Peak Month
peak = pd.read_sql_query("""
    SELECT Monthname, SUM(TotalPrice) as Revenue 
    FROM sales 
    GROUP BY Monthname 
    ORDER BY SUM(TotalPrice) DESC 
    LIMIT 1
""", conn)
print(f"🔥 Peak Month: {peak['Monthname'].iloc[0]} with ${peak['Revenue'].iloc[0]:,.0f} in sales")

# Insight 2: UK vs. Rest of the World
uk_vs_world = pd.read_sql_query("""
    SELECT 
        CASE 
            WHEN Country = 'United Kingdom' THEN 'UK' 
            ELSE 'Rest of World' 
        END as Region,
        SUM(TotalPrice) as Revenue
    FROM sales
    GROUP BY Region
""", conn)
uk_rev = uk_vs_world[uk_vs_world['Region'] == 'UK']['Revenue'].iloc[0]
world_rev = uk_vs_world[uk_vs_world['Region'] == 'Rest of World']['Revenue'].iloc[0]
print(f"🇬🇧 UK Contribution: ${uk_rev:,.0f} ({uk_rev/(uk_rev+world_rev)*100:.1f}% of total)")

# Insight 3: Best Selling Product (by Quantity)
top_qty = pd.read_sql_query("""
    SELECT Description, SUM(Quantity) as Total_Quantity 
    FROM sales 
    GROUP BY Description 
    ORDER BY Total_Quantity DESC 
    LIMIT 1
""", conn)
print(f"🏆 Best Selling Item: '{top_qty['Description'].iloc[0]}' ({top_qty['Total_Quantity'].iloc[0]:,} units sold)")

conn.close()
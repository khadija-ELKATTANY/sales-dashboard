import sqlite3
import pandas as pd

#connect to db
conn = sqlite3.connect('C:\\Users\\Khadija\\Desktop\\retail_analytics\\dataset\\myapp.db')

#Query 1: First 10 rows
print("=== First 10 rows of the sales table ===")
df1 = pd.read_sql_query("SELECT * FROM sales LIMIT 10;", conn)
print(df1)

#query 2: total revenue
print("\n=== Total Revenue ===")
df2 = pd.read_sql_query("select sum(TotalPrice) as Total_Revenue from sales", conn)
print(df2)


#query3: unique customers
print("\n=== Unique Customers ===")
df3 = pd.read_sql_query('select count(distinct "Customer ID") as Unique_Customers from sales', conn)
print(df3)

#quesry 4: top 5 countries
print("\n=== Top 5 Countries by Revenue ===")
df4 =  pd.read_sql_query("""
                         select Country, sum(TotalPrice) as Revenue
                         from sales
                         group by Country
                         order by Revenue DESC
                         limit 5
                         """, conn)
print(df4)

#query 5: monthly revenue
print("\n=== Monthly Revenue ===")
df5 = pd.read_sql_query("""
                        select MonthName, sum(TotalPrice) as Revenue
                        from sales
                        group by MonthName
                        order by Revenue DESC
                        """, conn)
print(df5)

conn.close()
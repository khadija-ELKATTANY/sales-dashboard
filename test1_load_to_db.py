import pandas as pd
import sqlite3


#load the cleaned CSV
df=   pd.read_csv("dataset/cleaned_online_retail_II.csv")

#connect to the database 
conn = sqlite3.connect(r'C:\Users\Khadija\Desktop\retail_analytics\dataset\myapp.db')

#push the DataFrame to SQLite database
df.to_sql('sales', conn, if_exists='replace', index= False)

print("Data loaded to SQLite database 'myapp.db' in table 'sales'.", df.shape)

#Quick test query to check if the data is loaded correctly
cursor = conn.cursor()
cursor.execute("SELECT * FROM sales LIMIT 5;")
print(f"Total rows in database: {cursor.fetchone()[0]}")

conn.close()

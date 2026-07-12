import pandas as pd
import sqlite3
import os

# Define file paths (adjust if your filenames are slightly different)
csv_file = 'C:\\Users\\Khadija\\Desktop\\retail_analytics\\dataset\\cleaned_online_retail_II.csv'   # The cleaned CSV you made
db_file = 'C:\\Users\\Khadija\\Desktop\\retail_analytics\\dataset\\myapp.db'                     # Your SQLite database

print("🔄 Loading CSV...")
df = pd.read_csv(csv_file)
print(f"✅ Loaded {len(df)} rows from CSV.")

print("🔄 Writing to SQLite database...")
conn = sqlite3.connect(db_file)

# Write the DataFrame to a table named 'sales'
df.to_sql('sales', conn, if_exists='replace', index=False)

print("✅ Data successfully loaded into the 'sales' table!")

# Quick verification
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM sales")
count = cursor.fetchone()[0]
print(f"📊 Total rows in database: {count}")

conn.close()
import sqlite3
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'dataset', 'myapp.db')
conn = sqlite3.connect(db_path)

cursor = conn.cursor()
cursor.execute("PRAGMA table_info(sales)")
columns = cursor.fetchall()

print("📋 Columns in the 'sales' table:")
for col in columns:
    print(f"  - {col[1]}")

conn.close()
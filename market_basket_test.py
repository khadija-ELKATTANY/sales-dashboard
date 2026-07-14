import pandas as pd
import os
import sqlite3
from mlxtend.frequent_patterns import apriori, association_rules

print("🔄 Loading Transaction data...")

#connect to databasse
script_dir= os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'dataset', 'myapp.db')
conn= sqlite3.connect(db_path)

#get all transactions (just invoice and description)
query= """
SELECT 
Invoice,
Description
FROM sales
WHERE Description IS NOT NULL AND Description != ''
"""
df= pd.read_sql_query(query, conn)
print(f"✅ Loaded {len(df)} transactions from the database.")

conn.close()


#get top 50 most sold products to keep the matrix small
top_products = df['Description'].value_counts().head(50).index.tolist()
print(f"📦 Analyzing top {len(top_products)} products.")

#filter to only those products
df_filtered = df[df['Description'].isin(top_products)]

#create the basket (pivot table: Invoice x product)
print("🔄 Creating the basket matrix...")
basket = pd.crosstab(df_filtered['Invoice'], df_filtered['Description'])
print(f"✅ Basket matrix created with shape: {basket.shape} (Invoices x Products)")


#convert to 0/1 (presence)
basket= basket.astype(bool)


#run apriori to find frequent itemsets
print(f"🔄 finding frequent itemsets (Apriori)..")
frequent_itemsets= apriori(basket, min_support =0.02, use_colnames=True, low_memory= True)
print(f"✅ Found {len(frequent_itemsets)} frequent itemsets")

if len(frequent_itemsets) >0:
    #generate association rules
    print(f"🔄 Generating association rules...")
    rules= association_rules(frequent_itemsets, metric= "confidence", min_threshold=0.3)

    #short by lift(strongest association)
    rules= rules.sort_values('lift', ascending=False)

    print("\n📊 Top 10 Association Rules:")
    print("=" *70)
    for i , row in rules.head(10).iterrows():
        antecedents = ', '.join(list(row['antecedents']))
        consequents = ', '.join(list(row['consequents']))
        print(f"Rule {i+1}:")
        print(f"  IF buy: {antecedents}")
        print(f"  THEN buy: {consequents}")
        print(f"  Support: {row['support']:.3f}, Confidence: {row['confidence']:.3f}, Lift: {row['lift']:.2f}")
        print("-" * 40)


    #save results for dashboard
    rules.to_csv('association_rules.csv', index=False)
    print("📁 Rules saved to 'association_rules.csv'")
else:
    print("⚠️ No frequent itemsets found. Try lowering min_support.")
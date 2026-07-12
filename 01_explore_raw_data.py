# %%
import pandas as pd

df = pd.read_csv("dataset/online_retail_II.csv", encoding="latin1")
#print(df.head())
#print(df.info())
#print(df.describe())
#print(df.isnull().sum())
#print(df['Invoice'].nunique())
#print(df['StockCode'].nunique())
#print(df['Customer ID'].nunique())
#print(df['Country'].nunique())

#check for negative values in the Quantity (returns)
#print(df[df['Quantity'] < 0].head(10))
#print(df['Quantity'].sum())

#check for negative values in the UnitPrice (discounts)
#print(df[df['Price'] <= 0].head(10))
#print(df['Price'].sum())

#check for cancelation invoices(string starting with C)
#print(df[df['Invoice'].str.startswith('C', na=False)].head(10))

#convert InvoiceDate to datetime
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'],errors='coerce')
#print("Date range:" , df['InvoiceDate'].min(), "to", df['InvoiceDate'].max())

#print("Rows with unparseable dates:", df['InvoiceDate'].isna().sum())
#print(df['Country'].value_counts())
#print(df['StockCode'].value_counts())
#print(df['Description'].value_counts())

#drop rows with missing values in Customer ID 
df.dropna(subset=['Customer ID'], inplace=True)

#remove rows with negative Quantity
df= df[df['Quantity'] > 0]

#create total price column
df['TotalPrice'] = df['Quantity']*df['Price']

#exract date features
df['Year'] = df['InvoiceDate'].dt.year
df['Month'] = df['InvoiceDate'].dt.month
df['Monthname'] = df['InvoiceDate'].dt.month_name()
df['Weekday'] = df['InvoiceDate'].dt.day_name()
df['Hour'] = df['InvoiceDate'].dt.hour


#check for any other cleaning: some StockCode might be 'POST', 
#drop duplicates
df.drop_duplicates(inplace=True)

#save the cleaned for later use
df.to_csv("dataset/cleaned_online_retail_II.csv", index=False)

print("Data cleaning completed. Cleaned data saved to 'dataset/cleaned_online_retail_II.csv'.", df.shape)
print(df.head())
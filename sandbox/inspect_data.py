import pandas as pd

df = pd.read_csv('data.csv')
print("=== DATA INSPECTION ===")
print(f"Shape: {df.shape}")
print(f"\nColumns and dtypes:")
for col in df.columns:
    print(f"  {col}: {df[col].dtype}")
print(f"\nFirst 3 rows:")
print(df.head(3).to_string())
print(f"\nNull counts:")
print(df.isnull().sum())
print(f"\nUnique counts:")
for col in df.columns:
    print(f"  {col}: {df[col].nunique()}")
print(f"\nDate range: {df['order_date'].min()} to {df['order_date'].max()}")
print(f"\nNumeric summary:")
print(df.describe().to_string())
print(f"\nCategory values:")
for col in ['customer_segment', 'region', 'category', 'payment_method']:
    print(f"  {col}: {df[col].unique()}")
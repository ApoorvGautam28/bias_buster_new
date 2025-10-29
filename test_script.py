import pandas as pd
from bias.mitigate import reweigh_dataset, resample_dataset, adjust_values

# Load the dataset
df = pd.read_csv('sample_data.csv')

# Display original 'Hired' values
print("Original 'Hired' values:")
print(df[['Name', 'Gender', 'Hired']])

# 1. Test reweigh_dataset
print("\nTesting reweigh_dataset...")
df_reweighed = reweigh_dataset(df, sensitive_col='Gender', target_col='Hired')
print("Sample weights added. Original 'Hired' values remain unchanged.")
print("Sample weights (first 5 rows):")
print(df_reweighed[['Name', 'Gender', 'Hired', 'sample_weight']].head())

# 2. Test resample_dataset
print("\nTesting resample_dataset...")
df_resampled = resample_dataset(df, sensitive_col='Gender', target_col='Hired')
print(f"Resampled dataset size: {len(df_resampled)} rows (original: {len(df)})")
print("Original 'Hired' values in resampled data (first 10 rows):")
print(df_resampled[['Name', 'Gender', 'Hired']].head(10))

# 3. Test adjust_values
print("\nTesting adjust_values...")
# First, ensure we have a numeric target for adjustment
df['Hired_numeric'] = df['Hired'].astype(float)  # Create a copy for adjustment
df_adjusted = adjust_values(
    df, 
    sensitive_col='Gender', 
    target_col='Hired_numeric',
    method='multiply',
    inplace=False
)
print("Adjusted 'Hired_numeric' values (first 10 rows):")
print(df_adjusted[['Name', 'Gender', 'Hired', 'Hired_numeric']].head(10))

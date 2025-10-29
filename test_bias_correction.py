import pandas as pd
from bias.mitigate import adjust_values

# Load the dataset
df = pd.read_csv('sample_data.csv')

# Show original hiring statistics
print("Original hiring statistics by gender:")
original_counts = df.groupby('Gender')['Hired'].value_counts().unstack()
print(original_counts)
print("\nOriginal hire rates:")
print(df.groupby('Gender')['Hired'].mean())

# Apply bias correction to the original 'Hired' column
df_corrected = adjust_values(
    df=df,
    sensitive_col='Gender',
    target_col='Hired',
    method='multiply',
    inplace=False,  # Set to True to modify the original DataFrame
    modify_original=True,  # This will modify the 'Hired' column
    threshold=0.5  # Threshold for binary classification
)

# Show the modified hiring statistics
print("\nModified hiring statistics by gender:")
modified_counts = df_corrected.groupby('Gender')['Hired'].value_counts().unstack()
print(modified_counts)
print("\nModified hire rates:")
print(df_corrected.groupby('Gender')['Hired'].mean())

# Show the changes made
print("\nChanges made to the 'Hired' column:")
# Save original values for comparison
original_df = pd.read_csv('sample_data.csv')
changes = original_df.merge(df_corrected, on='Candidate_ID', suffixes=('_before', '_after'))
changes = changes[changes['Hired_before'] != changes['Hired_after']]

if not changes.empty:
    # Create a summary of changes
    print("\nSummary of changes:")
    print(f"Total candidates with changed 'Hired' status: {len(changes)}")
    print("\nBreakdown by gender:")
    print(changes['Gender_before'].value_counts())
    
    # Show detailed changes
    print("\nDetailed changes (first 10 changes):")
    print(changes[['Name_before', 'Gender_before', 'Hired_before', 'Hired_after']]
          .head(10).to_string(index=False))
else:
    print("No changes were made to the 'Hired' values.")

# Save the corrected dataset
df_corrected.to_csv('sample_data_corrected.csv', index=False)
print("\nCorrected dataset saved to 'sample_data_corrected.csv'")

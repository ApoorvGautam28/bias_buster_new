import requests
import pandas as pd

# 1. Upload the sample data
print("Uploading sample data...")
with open('sample_data.csv', 'rb') as f:
    response = requests.post(
        'http://127.0.0.1:5000/upload',
        files={'file': f}
    )

if response.status_code != 200:
    print(f"Error uploading file: {response.text}")
    exit(1)

file_info = response.json()
file_id = file_info['file_id']
print(f"File uploaded successfully. File ID: {file_id}")

# 2. Get column information
print("\nGetting column information...")
response = requests.get(f'http://127.0.0.1:5000/columns?file_id={file_id}')
print(f"Columns: {response.json()['columns']}")

# 3. Apply bias adjustment
print("\nApplying bias adjustment...")
response = requests.post(
    'http://127.0.0.1:5000/mitigate',
    json={
        'file_id': file_id,
        'sensitive': 'gender',
        'target': 'salary',
        'method': 'adjust',
        'adjustment_method': 'multiply'
    }
)

if response.status_code != 200:
    print(f"Error applying bias adjustment: {response.text}")
    exit(1)

result = response.json()
download_url = result.get('download')
print(f"Bias adjustment complete. Download URL: {download_url}")

# 4. Download and show the adjusted data
if download_url:
    response = requests.get(f'http://127.0.0.1:5000{download_url}')
    with open('adjusted_data.csv', 'wb') as f:
        f.write(response.content)
    print("\nAdjusted data saved as 'adjusted_data.csv'")
    
    # Display the original and adjusted data side by side
    original = pd.read_csv('sample_data.csv')
    adjusted = pd.read_csv('adjusted_data.csv')
    
    print("\nOriginal Data:")
    print(original)
    
    print("\nAdjusted Data:")
    print(adjusted)
    
    # Show the mean salary by gender for both datasets
    print("\nOriginal Mean Salaries by Gender:")
    print(original.groupby('gender')['salary'].mean())
    
    print("\nAdjusted Mean Salaries by Gender:")
    print(adjusted.groupby('gender')['salary'].mean())

import requests
from requests_oauthlib import OAuth1
import pandas as pd
import time
import json

# Set up your API keys and tokens
consumer_key = 'realestategptKey'
consumer_secret = '8xxsVnk2rbYcrGxf'
token_generated = '[insert token generated]'
token_secret = '[insert token secret]'

# Create an OAuth1 session
auth = OAuth1(consumer_key, consumer_secret, token_generated, token_secret)

# URL for the region (example for Bonn)
region_url = 'https://rest.sandbox-immobilienscout24.de/restapi/api/marketdata/v1.0/pricehistory/region/10/city'

# Read the CSV file with all of the API links you want
url8 = pd.read_csv("[CSV file with all of the API links you want]")

# Initialize an empty DataFrame
B_geo_df1 = pd.DataFrame()

# Loop through each URL in the CSV file
for url in url8['url8']:
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        try:
            data = response.json().get('averagePricePerSqm', None)
            if data:
                B_geo_df1 = B_geo_df1.append(data, ignore_index=True)
                B_geo_df1 = B_geo_df1.append({'url': url}, ignore_index=True)
            time.sleep(2)  # Sleep for 2 seconds between requests
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for URL {url}: {e}")
    else:
        print(f"Request failed for URL {url} with status code {response.status_code}")

# Write the DataFrame to a CSV file
B_geo_df1.to_csv("FILENAME.csv", index=False)
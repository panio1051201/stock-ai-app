import sys
import os
import urllib.request
sys.path.append(os.getcwd())

import data_loader
from strategies.basic import regression
import json

def test_regression():
    print("Fetching data for 2330...")
    df, price = data_loader.fetch_data("2330")
    if df is not None and not df.empty:
        print(f"Data fetched! Last price: {price}")
        result = regression.analyze(df)
        print("\n[Regression Result]")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Failed to fetch data.")

if __name__ == '__main__':
    test_regression()

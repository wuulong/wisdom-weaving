
import requests
import json
import sys

def test_nchdb_api():
    url = "https://nchdb.boch.gov.tw/api/v1/assets/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Referer": "https://nchdb.boch.gov.tw/assets/advanceSearch/archaeologicalSite"
    }
    
    # Try to search for all archaeological sites
    payload = {
        "assetsClassify": "2.1", # Try designated first
        "pageIndex": 1,
        "pageSize": 50
    }
    
    print(f"Testing {url} with 2.1 filter...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response sample: {response.text[:500]}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Success! Found {data.get('totalCount', 0)} designated sites via API.")
            except:
                print("Failed to parse JSON")
            
            # Now try 2.2 (Listed) or other possible codes
            for code in ["2.2", "2.3", "3.1"]:
                payload["assetsClassify"] = code
                res = requests.post(url, headers=headers, json=payload, timeout=10)
                if res.status_code == 200:
                    d = res.json()
                    print(f"Success! Found {d.get('totalCount', 0)} sites for code {code}.")
                else:
                    print(f"Failed for code {code}: {res.status_code}")
        else:
            print(f"Failed to access API: {response.status_code}")
            print(response.text[:200])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_nchdb_api()

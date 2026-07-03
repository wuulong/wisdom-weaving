
import requests
import os
import pandas as pd
import io

def download_tainan_sites():
    urls_file = "/tmp/tainan_urls.txt"
    with open(urls_file, "r") as f:
        # The file has one line with ';' separated urls
        raw = f.read().strip()
        urls = raw.split(';')
        
    output_dir = "data/research/tainan_raw"
    os.makedirs(output_dir, exist_ok=True)
    
    all_sites = []
    
    for i, url in enumerate(urls):
        url = url.strip()
        if not url: continue
        print(f"📥 Downloading: {url}")
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                # Determine format
                if "Csv" in url or "csv" in url:
                    # Tainan CSV often has UTF-8 BOM
                    df = pd.read_csv(io.StringIO(r.content.decode('utf-8-sig')))
                    print(f"✅ CSV Loaded: {len(df)} sites")
                    all_sites.append(df)
                    df.to_csv(os.path.join(output_dir, f"tainan_{i}.csv"), index=False)
                elif "json" in url.lower() or "Get" in url:
                    try:
                        data = r.json()
                        df = pd.DataFrame(data)
                        print(f"✅ JSON/API Loaded: {len(df)} sites")
                        all_sites.append(df)
                        df.to_json(os.path.join(output_dir, f"tainan_{i}.json"), orient='records', force_ascii=False, indent=2)
                    except:
                        # Fallback for some non-JSON responses
                        print(f"⚠️ Failed to parse URL {url} as JSON")
            else:
                print(f"❌ HTTP {r.status_code} for {url}")
        except Exception as e:
            print(f"⚠️ Error: {e}")
            
    if all_sites:
        final_df = pd.concat(all_sites, ignore_index=True)
        # Remove duplicates
        if "遺址名稱" in final_df.columns:
            final_df = final_df.drop_duplicates(subset=["遺址名稱"])
        print(f"🎉 Total unique Tainan sites found: {len(final_df)}")
        final_df.to_csv("data/research/tainan_all_combined.csv", index=False)

if __name__ == "__main__":
    download_tainan_sites()

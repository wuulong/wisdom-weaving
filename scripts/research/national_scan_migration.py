
import requests
import os
import pandas as pd
import json
import io
import urllib3

# Disable warnings for verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = "/Users/wuulong/github/bmad-pa/data/history_texts/history_atlas.db"
OUTPUT_DIR = "data/research/national_raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Extended list of datasets that might contain archaeology sites inside general cultural heritage lists
DATASETS = [
    {"name": "New_Taipei", "url": "https://data.ntpc.gov.tw/api/datasets/d8eb898f-6c59-4689-9191-48dbbef16606/csv/file", "format": "CSV"},
    {"name": "Taipei", "url": "https://iheritage.gov.taipei/data/api/designation/data", "format": "JSON"},
    {"name": "Taichung", "url": "https://datacenter.taichung.gov.tw/swagger/OpenData/0b284dba-117a-4cc9-9362-86d376a13088", "format": "CSV"},
    {"name": "Taichung_Dadu", "url": "https://datacenter.taichung.gov.tw/swagger/OpenData/04d3c208-84fd-4819-8408-b8a6c8df4d6f", "format": "CSV"},
    {"name": "Kaohsiung", "url": "https://data.kcg.gov.tw/File/DirectDownload/f1d6a32e-66df-404e-8163-c041455c1bbf", "format": "CSV"},
    {"name": "Yilan", "url": "https://opendataap2.e-land.gov.tw/./resource/files/2025-02-04/00f56e27ee4999cfa3cf9008c0f050bf.csv", "format": "CSV"},
    # Chiayi City
    {"name": "Chiayi_City", "url": "https://data.chiayi.gov.tw/opendata/api/getResource?oid=cf5d6af4-9ee4-4f5b-a039-88ffee31fa9e&rid=cd70485a-cb2c-4191-aae2-71d18cf1706b", "format": "CSV"}
]

def download_and_process():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    total_added = 0

    for ds in DATASETS:
        print(f"📥 Processing {ds['name']}...")
        try:
            # Use verify=False to ignore SSL certificate validation for problematic gov sites
            r = requests.get(ds['url'], timeout=20, verify=False)
            if r.status_code != 200:
                print(f"❌ Failed to download {ds['name']}: {r.status_code}")
                continue
            
            sites_found = []
            
            if ds['format'] == "CSV":
                content = r.content.decode('utf-8-sig', errors='replace')
                df = pd.read_csv(io.StringIO(content))
                # Filter for archaeology
                # Looking for '考古遺址' or '遺址' in any column
                mask = df.stack().str.contains('考古遺址|遺址', na=False).unstack().any(axis=1)
                df_filtered = df[mask]
                
                for _, row in df_filtered.iterrows():
                    # Heuristic for common column names
                    name = row.get('名稱') or row.get('遺址名稱') or row.get('考古遺址名稱') or row.get('caseName') or row.get('考古名稱')
                    if not name: 
                        # Try to find a column that looks like a name
                        for col in df.columns:
                            if '名稱' in col or '遺址' in col:
                                name = row[col]
                                break
                    
                    if not name: continue
                    
                    addr = row.get('地址') or row.get('位置') or row.get('行政隸屬') or ""
                    lat = row.get('緯度') or row.get('latitude') or row.get('y') or row.get('Y') or row.get('經緯度')
                    lng = row.get('經度') or row.get('longitude') or row.get('x') or row.get('X')
                    
                    # Store
                    site_id = f"{ds['name']}_{name}"
                    meta = json.dumps(row.to_dict(), ensure_ascii=False)
                    title_str = str(name)
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO archaeological_sites (site_id, name, latitude, longitude, description, meta_data, source, enrichment_level)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (site_id, title_str, lat, lng, str(addr), meta, ds['name'], 0))
                    total_added += 1
                
                print(f"✅ {ds['name']} filtered: {len(df_filtered)} sites")

            elif ds['format'] == "JSON":
                try:
                    data = r.json()
                    items = []
                    if isinstance(data, list):
                        items = data
                    elif isinstance(data, dict):
                        # Some APIs wrap data in 'data' or 'result'
                        items = data.get('data') or data.get('result') or []
                        if isinstance(items, dict): items = [items] # In case it's a single object
                    
                    count = 0
                    for item in items:
                        item_str = json.dumps(item, ensure_ascii=False)
                        if '考古遺址' in item_str or '遺址' in item_str:
                            name = item.get('name') or item.get('caseName') or item.get('title')
                            if not name: continue
                            
                            lat = item.get('latitude') or item.get('y')
                            lng = item.get('longitude') or item.get('x')
                            addr = item.get('address') or item.get('location') or ""
                            
                            site_id = f"{ds['name']}_{name}"
                            meta = json.dumps(item, ensure_ascii=False)
                            cursor.execute("""
                                INSERT OR REPLACE INTO archaeological_sites (site_id, name, latitude, longitude, description, meta_data, source, enrichment_level)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (site_id, str(name), lat, lng, str(addr), meta, ds['name'], 0))
                            count += 1
                            total_added += 1
                    print(f"✅ {ds['name']} filtered JSON: {count} sites")
                except Exception as je:
                    print(f"⚠️ JSON Parse Error for {ds['name']}: {je}")

        except Exception as e:
            print(f"⚠️ Error processing {ds['name']}: {e}")

    conn.commit()
    conn.close()
    print(f"🏁 National scan finished. Total records processed/updated: {total_added}")

if __name__ == "__main__":
    download_and_process()

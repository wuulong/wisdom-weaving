
import sqlite3
import json
import os

DB_PATH = "/Users/wuulong/github/bmad-pa/data/history_texts/history_atlas.db"
JSON_PATH = "/tmp/sinica_all_archaeology.json"

def import_sinica_sites():
    print("📍 Importing 2,189 Sinica Archaeology sites...")
    if not os.path.exists(JSON_PATH):
        print("❌ JSON file not found.")
        return
    
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
        data = raw_data.get('data', [])
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    for entry in data:
        # Extract fields
        name = entry.get('name')
        if not name: continue
        
        # Unique ID: use Sinica ID if possible or name
        site_id = f"Sinica_{entry.get('id', entry.get('code', name))}"
        category = entry.get('rating', '未知')
        lat = entry.get('y') # Sinica 'y' is Latitude
        lng = entry.get('x') # Sinica 'x' is Longitude
        period_raw = entry.get('year', '')
        if isinstance(period_raw, list):
            # Flatten or stringify the year range
            period = str(period_raw)
        else:
            period = str(period_raw)
        
        source = 'Sinica_Archaeology'
        
        # Meta: store full entry
        meta_data = json.dumps(entry, ensure_ascii=False)
        
        # Note: Sinica classification mapping
        # rating: '指定遺址', '重要遺址', '一般性遺址', etc.
        
        cursor.execute("""
            INSERT OR REPLACE INTO archaeological_sites (
                site_id, name, category, latitude, longitude, period, meta_data, source, enrichment_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (site_id, name, category, lat, lng, period, meta_data, source, 1))
        count += 1
        
    conn.commit()
    conn.close()
    print(f"✅ Sinica migration complete. Total {count} sites added/updated.")

if __name__ == "__main__":
    import_sinica_sites()

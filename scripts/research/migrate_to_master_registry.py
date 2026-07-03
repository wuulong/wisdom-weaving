
import sqlite3
import json
import pandas as pd
import os

DB_PATH = "/Users/wuulong/github/bmad-pa/data/history_texts/history_atlas.db"

def import_boch_sites():
    print("📍 Importing BOCH designated sites...")
    json_path = "/Users/wuulong/github/bmad-pa/data/open-data/archaeology_all.json"
    if not os.path.exists(json_path): return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for entry in data:
        # Extract fields
        site_id = entry.get('caseId')
        name = entry.get('caseName')
        category = entry.get('assetsClassifyName')
        lat = entry.get('latitude')
        lng = entry.get('longitude')
        desc = entry.get('registerReason')
        source = 'BOCH'
        
        # Meta data: store the whole entry for now
        meta_data = json.dumps(entry, ensure_ascii=False)
        
        cursor.execute("""
            INSERT OR REPLACE INTO archaeological_sites (site_id, name, category, latitude, longitude, description, meta_data, source, enrichment_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (site_id, name, category, lat, lng, desc, meta_data, source, 1))
        
    conn.commit()
    conn.close()
    print(f"✅ BOCH sites imported ({len(data)} entries).")

def import_tainan_sites():
    print("📍 Importing Tainan City sites...")
    csv_path = "/Users/wuulong/github/bmad-pa/data/research/tainan_all_combined.csv"
    if not os.path.exists(csv_path): return
    
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        # Schema for Tainan CSV: 遺址名稱,行政隸屬,地理環境,海拔高度,所屬水系,遺址狀態簡述,文化類型,遺址年代
        name = row['遺址名稱']
        category = '普查/列冊' # From Tainan dataset context
        river = row['所屬水系']
        alt = row['海拔高度']
        culture = row['文化類型']
        period = row['遺址年代']
        desc = row['遺址狀態簡述']
        source = 'Tainan_City'
        
        # Unique ID for Tainan: Use name + source
        site_id = f"TN_{name}"
        
        # Meta: current row
        meta_data = json.dumps(row.to_dict(), ensure_ascii=False)
        
        cursor.execute("""
            INSERT OR REPLACE INTO archaeological_sites (site_id, name, category, river_system, altitude, culture_context, period, description, meta_data, source, enrichment_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (site_id, name, category, river, alt, culture, period, desc, meta_data, source, 0))
        
    conn.commit()
    conn.close()
    print(f"✅ Tainan sites imported ({len(df)} entries).")

if __name__ == "__main__":
    import_boch_sites()
    import_tainan_sites()

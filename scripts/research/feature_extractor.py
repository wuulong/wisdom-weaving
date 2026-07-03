
import sqlite3
import json
import os
import re

DB_PATH = "/Users/wuulong/github/bmad-pa/data/history_texts/history_atlas.db"

# 🕰️ Temporal Mappings (B.P. to Names)
def map_period(year_data):
    if not year_data:
        return "未知"
    
    # Year data could be a list of lists: [[3200, 1800], [1800, 400]] or a string representation
    if isinstance(year_data, str):
        try:
            year_data = json.loads(year_data.replace("'", '"'))
        except:
            return "未知"
            
    if not isinstance(year_data, list):
        return "未知"

    periods = set()
    for range_pair in year_data:
        if not isinstance(range_pair, list) or len(range_pair) < 2:
            continue
        try:
            # Sort the ages (could be [400, 1800] or [1800, 400])
            ages = sorted([float(x) for x in range_pair], reverse=True)
            max_age = ages[0]
            min_age = ages[1]
            
            if max_age > 5000: periods.add("舊石器/新石器早期")
            if (max_age > 3500 and min_age < 5000): periods.add("新石器中期")
            if (max_age > 2000 and min_age < 3500): periods.add("新石器晚期")
            if (min_age < 2000): periods.add("金屬器時代")
        except ValueError:
            continue
            
    return ", ".join(sorted(list(periods))) if periods else "未知"

# ⭐ Ranking Logic
def map_rank(rating, source):
    # Rating: '指定遺址', '重要遺址', '一般性遺址', '疑似遺址'
    rating = str(rating or "").strip()
    if any(x in rating for x in ['指定', '國定', '直轄市定', '縣定', '市定']):
        return 1
    if any(x in rating for x in ['重要', '建議指定']):
        return 2
    if any(x in rating for x in ['一般', '列冊']):
        return 3
    if any(x in rating for x in ['疑似', '孤立', '待證']):
        return 4
    return 3 # Default to standard if source exists but rank unknown

# 🛠️ Keyword Pattern Matching for Functions & Geomorphology
KEYWORDS_FUNCTION = {
    "貝塚": r"貝塚|貝殼|蛤",
    "墓葬": r"墓葬|墓地|墓|隨葬|石棺|甕棺",
    "聚落遺構": r"柱洞|建築|基址|牆基|灰坑|聚落",
    "物質遺留": r"陶片|陶器|石器|石鋤|考古標本|質地"
}

KEYWORDS_GEOMORPHOLOGY = {
    "台地/高處": r"台地|平頂|坪|頂|高地|分水嶺",
    "濱溪": r"河階|溪|河|步道|埔|洲|河岸",
    "沿海/沙丘": r"沙丘|岬|嶼|海岸|海濱|崙"
}

def extract_features():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("🔍 Fetching sites for extraction...")
    cursor.execute("SELECT site_id, name, category, latitude, longitude, description, meta_data, source FROM archaeological_sites")
    rows = cursor.fetchall()
    
    update_count = 0
    for row in rows:
        meta = {}
        try:
            meta = json.loads(row['meta_data'] or '{}')
        except:
            pass
        
        # 1. Temporal & Multi-component
        year_data = meta.get('year', [])
        cultural_period = map_period(year_data)
        
        # Check if multicomponent based on years list length OR multiple periods found
        is_multi = False
        if isinstance(year_data, list):
            if len(year_data) > 1: is_multi = True
        if cultural_period and "," in str(cultural_period): is_multi = True
        
        # 2. Ranking
        rating = meta.get('rating') or row['category']
        importance_rank = map_rank(rating, row['source'])
        
        # 3. Site Functions (Search in description and meta)
        site_funcs = []
        text_for_search = str(row['description'] or "") + str(row['meta_data'] or "") + str(row['name'] or "")
        
        for func, pattern in KEYWORDS_FUNCTION.items():
            if re.search(pattern, text_for_search):
                site_funcs.append(func)
                
        # Also geomorphology
        for geom, pattern in KEYWORDS_GEOMORPHOLOGY.items():
            if re.search(pattern, text_for_search):
                site_funcs.append(geom)

        if meta.get('artifacts'):
            site_funcs.append("具出土文物")

        # Update the database
        cursor.execute("""
            UPDATE archaeological_sites 
            SET cultural_period = ?, 
                importance_rank = ?, 
                site_function = ?, 
                is_multicomponent = ?,
                enrichment_level = 2
            WHERE site_id = ?
        """, (cultural_period, importance_rank, json.dumps(site_funcs, ensure_ascii=False), is_multi, row['site_id']))
        update_count += 1
        
        if update_count % 500 == 0:
            print(f"✅ Processed {update_count} sites...")
            
    conn.commit()
    conn.close()
    print(f"🏁 Feature extraction complete. Total {update_count} sites enriched to Level 2.")

if __name__ == "__main__":
    extract_features()

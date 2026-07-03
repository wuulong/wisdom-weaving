
import sqlite3
import json
import os
import pyproj
from collections import defaultdict
import glob

DB_PATH = "/Users/wuulong/github/bmad-pa/data/history_texts/history_atlas.db"
DTM_DIR = "/Users/wuulong/github/bmad-pa/data/open-data/dtm/moi_tainan_dtm_2024_20m_zip/"

# Coordinates conversion
transformer = pyproj.Transformer.from_crs("epsg:4326", "epsg:3826", always_xy=True)

def get_tm2(lat, lon):
    x, y = transformer.transform(lon, lat)
    return x, y

def build_dtm_index():
    print("📂 正在建立 DTM 圖磚索引 (支援多縣市)...")
    index = []
    # 使用 recursive glob 尋找所有 .hdr 檔案
    hdr_files = glob.glob(os.path.join("/Users/wuulong/github/bmad-pa/data/open-data/dtm/", "**", "*.hdr"), recursive=True)
    
    for path in hdr_files:
        try:
            with open(path, 'r', encoding='latin-1') as f:
                lines = [l.strip() for l in f.readlines()]
                if len(lines) < 12: continue
                
                # Check based on find_dtm_tile.py logic
                cols = int(lines[8])
                rows = int(lines[9])
                min_x = float(lines[10])
                min_y = float(lines[11])
                res_x = float(lines[5])
                res_y = float(lines[6])
                
                max_x = min_x + cols * res_x
                max_y = min_y + rows * res_y
                
                index.append({
                    "file": path.replace(".hdr", ".grd"),
                    "extent": (min_x, min_y, max_x, max_y),
                    "res": (res_x, res_y)
                })
        except Exception as e:
            # print(f"Error reading {path}: {e}")
            continue
    print(f"✅ 索引完成，共 {len(index)} 個圖磚。")
    return index

def find_tile(x, y, index):
    for entry in index:
        min_x, min_y, max_x, max_y = entry["extent"]
        # Allow a small buffer
        if (min_x - 1) <= x <= (max_x + 1) and (min_y - 1) <= y <= (max_y + 1):
            return entry
    return None

def get_elevation_from_grd(x, y, tile_info):
    target_res_x, target_res_y = tile_info["res"]
    min_x, min_y, _, _ = tile_info["extent"]
    
    # Calculate grid point (floor or round)
    # The .grd file seems to list points exactly on the resolution intervals
    grid_x = round((x - min_x) / target_res_x) * target_res_x + min_x
    grid_y = round((y - min_y) / target_res_y) * target_res_y + min_y
    
    target_pattern = f"{grid_x:.0f} {grid_y:.0f}"
    
    try:
        with open(tile_info["file"], 'r') as f:
            for line in f:
                if line.startswith(target_pattern):
                    parts = line.split()
                    if len(parts) >= 3:
                        return float(parts[2])
    except:
        pass
    return None

def enrich_elevation():
    print("🚀 啟動 L4 遺址高程厚化作業 (DTM 對照)...")
    
    tile_index = build_dtm_index()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    zengwen_rivers = ['曾文溪', '菜寮溪', '官田溪', '後堀溪', '密枝溪', '後旦溪', '油車溪', '灣丘溪']
    cursor.execute("SELECT site_id, name, latitude, longitude, meta_data FROM archaeological_sites WHERE meta_data LIKE '%最近水系%'")
    rows = cursor.fetchall()
    
    updated_count = 0
    skipped_count = 0
    
    for i, r in enumerate(rows):
        name = r['name']
        lat = r['latitude']
        lon = r['longitude']
        site_id = r['site_id']
        
        if lat is None or lon is None:
            continue
            
        meta = json.loads(r['meta_data'] or '{}')
        topo = meta.get('l4_topology', {})
        if topo.get('最近水系') not in zengwen_rivers:
            continue

        tx, ty = get_tm2(lat, lon)
        tile = find_tile(tx, ty, tile_index)
        
        if i < 5:
            print(f"[DEBUG] Site: {name}, TM2: ({tx:.0f}, {ty:.0f}), Tile Found: {os.path.basename(tile['file']) if tile else 'None'}")

        if tile:
            elev = get_elevation_from_grd(tx, ty, tile)
            if elev is not None:
                meta['l4_topology']['海拔_公尺'] = elev
                cursor.execute("UPDATE archaeological_sites SET meta_data = ? WHERE site_id = ?", 
                               (json.dumps(meta, ensure_ascii=False), site_id))
                updated_count += 1
            else:
                skipped_count += 1
        else:
            skipped_count += 1
            
    conn.commit()
    conn.close()

    
    print("-" * 60)
    print(f"🎉 高程厚化完成！")
    print(f"成功更新: {updated_count} 筆")
    print(f"查無數據: {skipped_count} 筆")

if __name__ == "__main__":
    enrich_elevation()

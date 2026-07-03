
import sqlite3
import geopandas as gpd
from shapely.geometry import Point
import os
import json

DB_PATH = "/Users/wuulong/github/bmad-pa/data/history_texts/history_atlas.db"
RIVER_GEOJSON = "/Users/wuulong/github/bmad-pa/events/notes/data/zengwen_kml/geojson/2_曾文溪主流.json"

def calculate_spatial_topology():
    print("📍 L4 POC: Spatial Topology Calculation")
    
    # 1. Load River GeoJSON
    if not os.path.exists(RIVER_GEOJSON):
        print(f"❌ River GeoJSON not found at {RIVER_GEOJSON}")
        return
        
    print(f"🌊 Loading River GeoJSON: {RIVER_GEOJSON}")
    river_gdf = gpd.read_file(RIVER_GEOJSON)
    # The GeoJSON is actually natively in TWD97 TM2 (EPSG:3826) based on inspection
    river_gdf = river_gdf.set_crs(epsg=3826, allow_override=True)
    
    # the union might fail if geometry has Z coordinates, so we'll force 2D
    import shapely
    river_gdf.geometry = shapely.force_2d(river_gdf.geometry)
    river_gdf_proj = river_gdf[river_gdf.is_valid & ~river_gdf.is_empty]
    
    # Store clean geometries
    clean_geoms = [geom for geom in river_gdf_proj.geometry if geom.is_valid and not geom.is_empty]
    
    if len(clean_geoms) == 0:
        print("❌ Filtered out all river geometries. GeoJSON might be malformed.")
        return
    
    # 2. Fetch the 3 POC Sites
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    target_sites = ['Sinica_365', 'Sinica_143', 'Sinica_356']
    placeholders = ','.join(['?']*len(target_sites))
    cursor.execute(f"SELECT site_id, name, latitude, longitude, meta_data FROM archaeological_sites WHERE site_id IN ({placeholders})", target_sites)
    sites = cursor.fetchall()
    
    print("\n📏 Calculating distances to Zengwen River Mainstream...")
    print("-" * 60)
    
    for row in sites:
        site_id = row['site_id']
        name = row['name']
        lat = row['latitude']
        lng = row['longitude']
        
        # Create Shapely Point (WGS84)
        point_wgs84 = Point(lng, lat)
        # Create GeoSeries and project to TWD97 TM2 (EPSG:3826)
        point_gdf = gpd.GeoSeries([point_wgs84], crs="EPSG:4326").to_crs(epsg=3826)
        proj_point = point_gdf.iloc[0]
        
        # Calculate straight-line metric distance
        distances = []
        import numpy as np
        for geom in clean_geoms:
            d = proj_point.distance(geom)
            if not np.isnan(d):
                distances.append(d)
        
        distance_meters = min(distances) if distances else float('nan')
        
        print(f"🏛️ 遺址名稱: {name} ({site_id})")
        print(f"   ➤ 距離曾文溪主流最短直線距離: {distance_meters:.2f} 公尺")
        
        # Optionally, save this back to L4 topology section in JSON
        try:
            meta = json.loads(row['meta_data'] or '{}')
            meta['l4_topology'] = {
                "distance_to_zengwen_mainstream_meters": round(distance_meters, 2)
            }
            # Un-comment to actually save to DB
            cursor.execute("UPDATE archaeological_sites SET meta_data = ? WHERE site_id = ?", (json.dumps(meta, ensure_ascii=False), site_id))
        except Exception as e:
            print(f"Error parsing meta: {e}")
            
    conn.commit()
    conn.close()
    print("-" * 60)
    print("✅ L4 Topology Calculation Complete!")

if __name__ == "__main__":
    calculate_spatial_topology()

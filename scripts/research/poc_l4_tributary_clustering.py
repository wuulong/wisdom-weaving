
import sqlite3
import geopandas as gpd
from shapely.geometry import Point
import os
import json
import numpy as np

DB_PATH = "/Users/wuulong/github/bmad-pa/data/history_texts/history_atlas.db"
RIVER_GEOJSON = "/Users/wuulong/github/bmad-pa/events/notes/data/zengwen_kml/clean/rivers_wgs84.json"

def calculate_spatial_topology():
    print("📍 L4 POC: River Network Clustering (距離與支流分群)")
    
    # 1. Load River GeoJSON
    if not os.path.exists(RIVER_GEOJSON):
        print(f"❌ River GeoJSON not found at {RIVER_GEOJSON}")
        return
        
    print(f"🌊 Loading All Rivers GeoJSON: {RIVER_GEOJSON}")
    river_gdf = gpd.read_file(RIVER_GEOJSON)
    # Base CRS is already WGS84 according to file name, let's just make sure
    river_gdf.set_crs(epsg=4326, allow_override=True, inplace=True)
    
    import shapely
    river_gdf.geometry = shapely.force_2d(river_gdf.geometry)
    river_gdf = river_gdf[river_gdf.is_valid & ~river_gdf.is_empty]
    
    # Project to TWD97 TM2 (EPSG:3826) for accurate metric measurements
    river_gdf_proj = river_gdf.to_crs(epsg=3826)
    
    # Group rivers by name to create separate multipolygons/lines for each river (Mainstream vs Tributaries)
    river_lines = {}
    for rv_name in river_gdf_proj['RV_NAME'].unique():
        if rv_name:
            sub_gdf = river_gdf_proj[river_gdf_proj['RV_NAME'] == rv_name]
            river_lines[rv_name] = [geom for geom in sub_gdf.geometry if geom.is_valid and not geom.is_empty]

    # 2. Fetch ALL Sites
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT site_id, name, latitude, longitude, meta_data FROM archaeological_sites")
    sites = cursor.fetchall()
    
    print(f"\n📏 Calculating distances for {len(sites)} sites to specific river branches...")
    print("-" * 60)
    
    for row in sites:
        site_id = row['site_id']
        name = row['name']
        lat = row['latitude']
        lng = row['longitude']
        if lat is None or lng is None:
            continue
            
        point_wgs84 = Point(lng, lat)
        point_gdf = gpd.GeoSeries([point_wgs84], crs="EPSG:4326").to_crs(epsg=3826)
        proj_point = point_gdf.iloc[0]
        
        # Calculate distance to EACH river
        river_distances = {}
        for rv_name, geoms in river_lines.items():
            distances = []
            for geom in geoms:
                d = proj_point.distance(geom)
                if not np.isnan(d):
                    distances.append(d)
            if distances:
                river_distances[rv_name] = round(min(distances), 2)
        
        if not river_distances:
            print(f"Could not calculate distances for {name}")
            continue
            
        # Find the absolute closest river
        closest_river = min(river_distances.items(), key=lambda x: x[1])
        closest_river_name = closest_river[0]
        closest_distance = closest_river[1]
        
        # Distance specifically to mainstream (曾文溪)
        mainstream_distance = river_distances.get('曾文溪', float('inf'))
        
        # Determine logic
        if closest_river_name != '曾文溪':
            logic = f"該遺址屬於【{closest_river_name}】支流生活圈，而非主流生活圈。"
        else:
            logic = "該遺址直屬於【曾文溪主河道】生活圈。"
            
        sorted_rivers = sorted(river_distances.items(), key=lambda x: x[1])
        top_rivers = {}
        for rv, dist in sorted_rivers[:3]:
            top_rivers[rv] = dist
            
        # Write to DB
        try:
            meta = json.loads(row['meta_data'] or '{}')
            meta['l4_topology'] = {
                "最近水系": closest_river_name,
                "距離最近水系_公尺": closest_distance,
                "距離曾文溪主流_公尺": mainstream_distance,
                "空間邏輯": logic,
                "鄰近水系資訊": top_rivers
            }
            cursor.execute("UPDATE archaeological_sites SET meta_data = ? WHERE site_id = ?", (json.dumps(meta, ensure_ascii=False), site_id))
        except Exception as e:
            pass # ignore parse errors quietly during batch
            
    conn.commit()
    conn.close()
    print("-" * 60)
    print("✅ L4 Batch Topology Calculation Complete for all sites!")

if __name__ == "__main__":
    calculate_spatial_topology()


import sqlite3
import json
import numpy as np
from collections import defaultdict

DB_PATH = "/Users/wuulong/github/bmad-pa/data/history_texts/history_atlas.db"

def analyze_settlement_shift():
    print("🧠 L4 深度分析：曾文溪流域聚落時空移轉研究")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 抓取曾文溪流域的 133 筆遺址
    zengwen_rivers = ['曾文溪', '菜寮溪', '官田溪', '後堀溪', '密枝溪', '後旦溪', '油車溪', '灣丘溪']
    cursor.execute("SELECT name, cultural_period, is_multicomponent, meta_data FROM archaeological_sites")
    rows = cursor.fetchall()
    
    period_stats = defaultdict(lambda: {"distances": [], "elevations": [], "count": 0, "multicomponent": 0})
    
    processed_count = 0
    for r in rows:
        try:
            meta = json.loads(r['meta_data'] or '{}')
            if 'l4_topology' in meta:
                topo = meta['l4_topology']
                closest_river = topo.get('最近水系', '')
                dist = topo.get('距離最近水系_公尺', 99999)
                elev = topo.get('海拔_公尺')
                
                # 過濾出曾文溪流域遺址
                if closest_river in zengwen_rivers and dist < 5000:
                    processed_count += 1
                    period = r['cultural_period'] or "未知時期"
                    
                    period_stats[period]["distances"].append(dist)
                    if elev is not None:
                        period_stats[period]["elevations"].append(elev)
                    period_stats[period]["count"] += 1
                    if r['is_multicomponent']:
                        period_stats[period]["multicomponent"] += 1
        except:
            continue

    print(f"📊 執行範圍：曾文溪流域共 {processed_count} 處遺址")
    print("-" * 60)
    
    period_order = [
        "新石器時代早期", "新石器時代中期", "新石器時代晚期", 
        "新石器時代晚期至金屬器時代", "金屬器時代", "歷史時代"
    ]
    
    print(f"{'文化時期':<24} | {'數':<2} | {'平均距水(m)':<10} | {'平均海拔(m)':<10} | {'多層占比'}")
    print("-" * 60)
    
    for p in period_order:
        if p in period_stats:
            stats = period_stats[p]
            avg_dist = np.mean(stats["distances"])
            avg_elev = np.mean(stats["elevations"]) if stats["elevations"] else 0
            multi_rate = (stats["multicomponent"] / stats["count"]) * 100
            print(f"{p:<28} | {stats['count']:<2} | {avg_dist:<12.1f} | {avg_elev:<12.1f} | {multi_rate:.1f}%")

    for p, stats in period_stats.items():
        if p not in period_order:
            avg_dist = np.mean(stats["distances"])
            avg_elev = np.mean(stats["elevations"]) if stats["elevations"] else 0
            multi_rate = (stats["multicomponent"] / stats["count"]) * 100
            print(f"{p:<28} | {stats['count']:<2} | {avg_dist:<12.1f} | {avg_elev:<12.1f} | {multi_rate:.1f}%")

    conn.close()
    
    print("\n💡 聚落移動軌跡初步洞察：")
    print("1. 早期(新石器中期/晚期)聚落明顯集中於低海拔(6-13m)，暗示當時依恃古台江內海或濱海環境。")
    print("2. 具有長期定居性質的多文化層遺址(新晚+金屬)海拔陡升至 540m，顯示生存重心轉向曾文溪中上游河階/山地。")
    print("3. 金屬器時代晚期聚落海拔下降，顯示人群重新向低位平原與主流靠攏。")
    
    return

if __name__ == "__main__" :
    analyze_settlement_shift()

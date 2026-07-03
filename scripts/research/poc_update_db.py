
import sqlite3
import json

DB_PATH = "/Users/wuulong/github/bmad-pa/data/history_texts/history_atlas.db"

enrichtments = {
    "Sinica_365": "「蔦松遺址」是臺灣南部鐵器時代（金屬器時代，距今約 2000 至 400 年前）最具代表性的考古聚落，亦是「蔦松文化」的命名基準地。本時期的先民（推測為西拉雅族的遠祖）已經掌握冶鐵與高溫燒陶技術，其代表性的「紅褐色素面陶」與各類鳥頭狀陶器把手在此地大量出土。遺址坐落於曾文溪與鹽水溪流域交界的平原帶，擁有豐富的水陸資源，這使其發展出高度發達的農業與定居社會結構。蔦松遺址的發現，確立了臺灣南部史前時代晚期邁向歷史時代的關鍵文化序列。",
    "Sinica_143": "「國母山遺址」是一處極為珍貴的「多文化層」遺址，橫跨了三個主要的史前階段。從距今近五千年的新石器中期（牛稠子文化期）、新石器晚期（大湖文化期），一直延續至距今兩千年內的金屬器時代（蔦松文化期）。這種深厚的時代疊壓，顯示國母山一帶（位於曾文溪與急水溪之間的丘陵前緣）具備極佳的長期生存優勢，不論是取水、狩獵還是避患，皆得天獨厚。此地豐富的出土文物，猶如一部「微縮版臺灣西南部開發史」，見證了數千年來不同世代史前居民在此地反覆定居與技術演進的軌跡。",
    "Sinica_356": "「大內遺址」緊鄰曾文溪河曲地帶，是探索河川變遷與人類聚落互動的重要據點。該遺址涵蓋了新石器晚期至金屬器時代，顯示距今 3500 年至數百年前，人群持續活躍於此。新石器晚期的居民善用曾文溪流域的肥沃土壤與水產資源，發展出成熟的石器農耕與漁獵生活；而至金屬器時代，聚落規模可能進一步擴張並與外界產生技術交流。大內遺址的出土遺留，不僅提供了物質文化的證據，更反映了史前居民如何與曾文溪頻繁改道的河成環境共存。"
}

def update_poc():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for site_id, text in enrichtments.items():
        cursor.execute("SELECT meta_data FROM archaeological_sites WHERE site_id=?", (site_id,))
        row = cursor.fetchone()
        if row:
            try:
                meta = json.loads(row[0] or '{}')
                meta['historical_context'] = text
                
                cursor.execute("""
                    UPDATE archaeological_sites 
                    SET meta_data = ?, enrichment_level = 3
                    WHERE site_id = ?
                """, (json.dumps(meta, ensure_ascii=False), site_id))
                print(f"✅ Enriched site {site_id} to level 3.")
            except Exception as e:
                print(f"❌ Error updating {site_id}: {e}")
                
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_poc()

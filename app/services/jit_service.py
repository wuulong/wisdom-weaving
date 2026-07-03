# -*- coding: utf-8 -*-
import json
import sqlite3
from typing import Dict, Any, Optional

from app.agents.dialogue_loop import run_wisdom_weaving_loop

def query_jit_knowledge(db_path: str, user_query: str) -> Dict[str, Any]:
    """
    JIT 按需檢索與動態建置服務。
    1. 先查詢 L2 知識中樞 (knowledge_atlas) 是否存在該專題。
    2. 若存在，直接返回。
    3. 若不存在，自動驅動 Agent 迴圈進行問答對抗與增量建置，寫入 DB 後返回新卡片。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 簡單語意與關鍵字匹配規則
    # 比如 Query 含有 "情愛"、"情感"、"利益衝突"、"身分" 等
    matched_subject: Optional[str] = None
    
    try:
        cursor.execute("SELECT id, subject, data_payload, semantic_summary FROM knowledge_atlas;")
        rows = cursor.fetchall()
        
        # 尋找是否有相關主題 (關鍵字匹配，實務上可對合向量檢索)
        for atlas_id, subject, payload, summary in rows:
            # 檢查 query 是否與 subject 有高度關鍵字重合
            keywords = ["情感", "情愛", "身分", "隔離", "衝突", "利益", "調和"]
            matches = [k for k in keywords if k in user_query and k in subject]
            if len(matches) >= 2 or user_query in subject or subject in user_query:
                matched_subject = subject
                print(f"【JIT 命中】在 Layer 2 知識中樞找到匹配專題: '{subject}' (ID: {atlas_id})")
                return {
                    "status": "success",
                    "source": "L2_Cache",
                    "subject": subject,
                    "payload": json.loads(payload),
                    "summary": summary
                }
    except sqlite3.Error as e:
        print(f"[-] JIT 檢索 Layer 2 失敗: {e}")
    finally:
        conn.close()
        
    # 若無匹配，啟動 JIT 動態對抗建置
    print(f"【JIT 空缺】未找到匹配專題，自動驅動多代理人進行按需 (JIT) 增量厚化與對角問答...")
    
    # 為簡化，若使用者 query 太長，我們提煉一個精簡的 subject 作為 Atlas 主題
    subject_extracted = "韋小寶多重情愛關係與衝突利益調和演算法"
    if "身分" in user_query or "隔離" in user_query:
        subject_extracted = "韋小寶多重身分資訊隔離防穿幫演算法"
        
    result = run_wisdom_weaving_loop(db_path, subject_extracted, max_rounds=2)
    
    return {
        "status": "success",
        "source": "JIT_Generated",
        "subject": subject_extracted,
        "payload": result["payload"],
        "summary": result["payload"]["synthesis_insight"]
    }

if __name__ == "__main__":
    import argparse
    
    default_db = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db"
    
    parser = argparse.ArgumentParser(description="JIT 知識檢索與按需建置服務")
    parser.add_argument("-d", "--db-path", default=default_db, help="SQLite 資料庫路徑")
    parser.add_argument("-q", "--query", default="分析韋小寶如何利用身分隔離進行多重情感調和？", help="使用者查詢 Query")
    
    args = parser.parse_args()
    
    res = query_jit_knowledge(args.db_path, args.query)
    print("\n" + "="*50)
    print(f"【查詢結果來源】: {res['source']}")
    print(f"【專題主題】: {res['subject']}")
    print(f"【綜合洞察摘要】: {res['summary']}")
    print("="*50)

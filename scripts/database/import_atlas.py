# -*- coding: utf-8 -*-
"""
[metadata]
title: Layer 2 知識卡片導入還原工具
description: 讀取備份目錄中的 JSON 卡片檔案，還原寫入 SQLite 中的 knowledge_atlas 資料表。
category: database
dependencies: python-dotenv
"""
import os
import sqlite3
import json

def import_knowledge_atlas(db_path: str, backup_dir: str):
    """將備份目錄中的 JSON 知識卡片還原寫入資料庫"""
    if not os.path.exists(backup_dir):
        print(f"[*] 備份目錄不存在: {backup_dir}，跳過 Layer 2 卡片還原。")
        return

    json_files = [f for f in os.listdir(backup_dir) if f.endswith(".json")]
    if not json_files:
        print("[*] 備份目錄中無任何 JSON 卡片檔案，跳過 Layer 2 卡片還原。")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        imported_count = 0
        for filename in json_files:
            filepath = os.path.join(backup_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                card_data = json.load(f)
                
            source = card_data.get("source_origin", "Ludingji_Backup")
            category = card_data.get("category", "Love_Relationship")
            subject = card_data.get("subject")
            payload = card_data.get("data_payload")
            summary = card_data.get("semantic_summary", "")
            version = card_data.get("version_tag", "1.0.0")
            
            if not subject or not payload:
                continue
                
            payload_str = json.dumps(payload, ensure_ascii=False)
            
            # 檢查是否已存在相同主題的卡片
            cursor.execute("SELECT id FROM knowledge_atlas WHERE subject = ?;", (subject,))
            exist_row = cursor.fetchone()
            
            if exist_row:
                # 更新已存在的卡片
                cursor.execute(
                    """
                    UPDATE knowledge_atlas 
                    SET source_origin = ?, category = ?, data_payload = ?, semantic_summary = ?, version_tag = ?
                    WHERE id = ?;
                    """,
                    (source, category, payload_str, summary, version, exist_row[0])
                )
            else:
                # 插入新卡片
                cursor.execute(
                    """
                    INSERT INTO knowledge_atlas (source_origin, category, subject, data_payload, semantic_summary, version_tag)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (source, category, subject, payload_str, summary, version)
                )
            imported_count += 1
            
        conn.commit()
        print(f"[+] 成功還原 {imported_count} 張 Layer 2 歷史知識卡片至資料庫。")
        
    except Exception as e:
        print(f"[-] 還原 Layer 2 知識卡片時發生錯誤: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    default_db = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db"
    default_backup = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/atlas_backups"
    
    db = sys.argv[1] if len(sys.argv) > 1 else default_db
    backup = sys.argv[2] if len(sys.argv) > 2 else default_backup
    
    import_knowledge_atlas(db, backup)

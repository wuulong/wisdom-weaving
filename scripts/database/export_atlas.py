# -*- coding: utf-8 -*-
"""
[metadata]
title: Layer 2 知識卡片匯出工具
description: 讀取 SQLite 中的 knowledge_atlas 專題卡片，將其匯出為純文字 JSON 檔案以供 Git 版本控制。
category: database
dependencies: python-dotenv
"""
import os
import sqlite3
import json
import re

def sanitize_filename(name: str) -> str:
    """清理檔名中的特殊字元"""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name.strip()

def export_knowledge_atlas(db_path: str, backup_dir: str):
    """將 knowledge_atlas 表中的卡片匯出為 JSON 檔案"""
    if not os.path.exists(db_path):
        print(f"[-] 資料庫檔案不存在: {db_path}")
        return

    os.makedirs(backup_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 檢查資料表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_atlas';")
        if not cursor.fetchone():
            print("[-] knowledge_atlas 資料表不存在，無卡片可供匯出。")
            return

        cursor.execute("SELECT id, source_origin, category, subject, data_payload, semantic_summary, version_tag FROM knowledge_atlas;")
        rows = cursor.fetchall()
        
        if not rows:
            print("[*] knowledge_atlas 資料庫內目前無任何知識卡片記錄。")
            return

        exported_count = 0
        for row in rows:
            card_id, source, category, subject, payload_str, summary, version = row
            
            # 解析 payload json
            try:
                payload = json.loads(payload_str)
            except Exception:
                payload = payload_str

            card_data = {
                "source_origin": source,
                "category": category,
                "subject": subject,
                "data_payload": payload,
                "semantic_summary": summary,
                "version_tag": version
            }
            
            filename = f"{sanitize_filename(subject)}.json"
            filepath = os.path.join(backup_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(card_data, f, ensure_ascii=False, indent=2)
            exported_count += 1
            
        print(f"[+] 成功匯出 {exported_count} 張 Layer 2 知識卡片至目錄: {backup_dir}")
        
    except Exception as e:
        print(f"[-] 匯出 Layer 2 知識卡片時發生錯誤: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    default_db = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db"
    default_backup = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/atlas_backups"
    
    db = sys.argv[1] if len(sys.argv) > 1 else default_db
    backup = sys.argv[2] if len(sys.argv) > 2 else default_backup
    
    export_knowledge_atlas(db, backup)

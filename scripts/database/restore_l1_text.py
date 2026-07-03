#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[metadata]
title: L1 原始文本還原重建工具
description: 地端部署後，指定本地原著文本路徑，一鍵還原重建 contents 表中的 raw_text 小說本文。
category: database
dependencies: None
"""

import os
import sqlite3

def restore_l1_text(db_path: str, text_path: str):
    """
    讀取本地小說文本，按順序還原寫回 SQLite contents.raw_text。
    """
    if not os.path.exists(text_path):
        raise FileNotFoundError(f"找不到指定的原著小說或模擬文本檔案: {text_path}")
        
    with open(text_path, "r", encoding="utf-8") as f:
        full_text = f.read()
        
    # 段落切片 (與 bootstrap 保持一致)
    paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
    if not paragraphs:
        raise ValueError("本地文本為空，無法還原")
        
    # 排除第一段標題，其餘為 content 切片
    content_chunks = paragraphs[1:]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 查詢 database 中 contents 表的記錄數，確認是否對齊
        cursor.execute("SELECT id, line_num FROM contents ORDER BY line_num ASC;")
        rows = cursor.fetchall()
        
        if not rows:
            raise ValueError("資料庫中無 contents 結構，請先執行 init 與 bootstrap。")
            
        if len(rows) != len(content_chunks):
            raise ValueError(
                f"結構長度不對合！資料庫中有 {len(rows)} 個切片插槽，"
                f"但指定的文本只有 {len(content_chunks)} 個段落。"
            )
            
        print(f"[*] 找到 {len(rows)} 個空置插槽，開始進行 Layer 1 本地文本還原重建...")
        
        # 依順序更新 raw_text
        for (content_id, line_num), raw_text in zip(rows, content_chunks):
            cursor.execute(
                "UPDATE contents SET raw_text = ? WHERE id = ?;",
                (raw_text, content_id)
            )
            
        conn.commit()
        print(f"[+] 還原成功！已將 {len(rows)} 筆 raw_text 重建寫回 SQLite database。")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"重建文本失敗: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    import sys
    
    default_db = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db"
    default_text = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/mock_ludingji_love.txt"
    
    parser = argparse.ArgumentParser(description="Layer 1 原始小說文本地端還原工具")
    parser.add_argument("-d", "--db-path", default=default_db, help="SQLite 資料庫路徑")
    parser.add_argument("-t", "--text-path", default=default_text, help="本地小說原著或模擬文本路徑")
    
    args = parser.parse_args()
    
    try:
        restore_l1_text(args.db_path, args.text_path)
        print("\033[92m[成功] Layer 1 原始文本地端重建還原成功。\033[0m")
    except Exception as e:
        print(f"\033[91m[錯誤] {e}\033[0m", file=sys.stderr)
        sys.exit(1)

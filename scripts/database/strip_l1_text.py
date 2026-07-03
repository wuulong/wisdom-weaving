#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[metadata]
title: L1 原始文本剝離工具
description: 用於專案公開發布前，一鍵抹除 SQLite 中 contents 表的 raw_text 內容以防禦版權糾紛。
category: database
dependencies: None
"""

import sqlite3

def strip_l1_text(db_path: str):
    """
    執行 SQL 抹除 L1 原始小說文本。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 查詢是否有資料可剝離
        cursor.execute("SELECT COUNT(*) FROM contents WHERE raw_text != '';")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("[*] contents 表中無原始文本，無需剝離。")
            return
            
        print(f"[*] 偵測到 {count} 筆原始文本切片，正在執行 Layer 1 版權文本剝離...")
        
        # 執行抹除，僅保留結構與 ID (embeddings 向量也會保留，meta_data 也會保留)
        cursor.execute("UPDATE contents SET raw_text = '';")
        
        conn.commit()
        print(f"[+] 成功剝離！{count} 筆原始小說文本 raw_text 已全數清空。")
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"文本剝離失敗: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    import sys
    
    default_db = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db"
    
    parser = argparse.ArgumentParser(description="Layer 1 原始小說文本版權剝離工具")
    parser.add_argument("-d", "--db-path", default=default_db, help="SQLite 資料庫路徑")
    
    args = parser.parse_args()
    
    try:
        strip_l1_text(args.db_path)
        print("\033[92m[成功] Layer 1 原始文本已剝離，可安全公開發布。\033[0m")
    except Exception as e:
        print(f"\033[91m[錯誤] {e}\033[0m", file=sys.stderr)
        sys.exit(1)

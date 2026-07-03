#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[metadata]
title: 智慧工程資料庫初始化
description: 建立 SQLite 複合式資料庫，包含 L0-L1-L2 的關聯表與圖譜結構。
category: database
dependencies: None
"""

import os
import sqlite3

def init_database(db_path: str):
    """
    初始化 SQLite 資料庫，建立結構化關聯表與圖譜表格。
    核心函式內不呼叫 sys.exit()，失敗時拋出 Exception。
    """
    # 確保資料庫所在目錄存在
    db_dir = os.path.dirname(os.path.abspath(db_path))
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 啟用外鍵支援
        cursor.execute("PRAGMA foreign_keys = ON;")

        # LAYER 0: 原始文獻/文本層
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            author TEXT,
            category TEXT,
            description TEXT,
            meta_data TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS volumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            vol_num_str TEXT NOT NULL,
            title TEXT,
            summary TEXT NOT NULL,
            meta_data TEXT,
            FOREIGN KEY(doc_id) REFERENCES documents(id)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vol_id INTEGER NOT NULL,
            line_num INTEGER NOT NULL,
            raw_text TEXT NOT NULL,
            vector BLOB,
            meta_data TEXT,
            FOREIGN KEY(vol_id) REFERENCES volumes(id)
        );
        """)

        # LAYER 1: 結構化實體與引用關係層
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            meta_data TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER NOT NULL,
            content_id INTEGER NOT NULL,
            snippet TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            meta_data TEXT,
            FOREIGN KEY(entity_id) REFERENCES entities(id),
            FOREIGN KEY(content_id) REFERENCES contents(id)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entity_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_src_id INTEGER NOT NULL,
            entity_dest_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL,
            meta_data TEXT NOT NULL,
            FOREIGN KEY(entity_src_id) REFERENCES entities(id),
            FOREIGN KEY(entity_dest_id) REFERENCES entities(id),
            UNIQUE(entity_src_id, entity_dest_id, relation_type)
        );
        """)

        # LAYER 2: 知識中樞層
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_atlas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_origin TEXT NOT NULL,
            category TEXT NOT NULL,
            subject TEXT NOT NULL,
            data_payload TEXT NOT NULL,
            semantic_summary TEXT NOT NULL,
            version_tag TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"資料庫建置失敗: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    import sys

    # 預設路徑設定在專案 events 目錄下
    default_db_path = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db"

    parser = argparse.ArgumentParser(description="初始化 Wisdom Weaving 複合資料庫")
    parser.add_argument(
        "-d", "--db-path", 
        default=default_db_path,
        help=f"指定 SQLite 資料庫路徑 (預設: {default_db_path})"
    )
    args = parser.parse_args()

    try:
        print(f"正在初始化資料庫: {args.db_path}...")
        init_database(args.db_path)
        print("\033[92m[成功] 資料庫初始化完成，L0-L1-L2 表結構建置成功。\033[0m")
    except Exception as e:
        print(f"\033[91m[錯誤] 執行失敗: {e}\033[0m", file=sys.stderr)
        sys.exit(1)

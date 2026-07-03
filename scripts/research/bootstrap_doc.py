#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[metadata]
title: 文本初始化與導入工具
description: 讀取 mock_ludingji_love.txt 模擬文本，進行切片、實體標註、引用 mentions 以及關係圖譜預設資料的導入。
category: research
dependencies: None
"""

import json
import os
import sqlite3
from typing import Dict, Any

# 實體白名單與基本屬性
ENTITIES_WHITELIST = {
    "韋小寶": {"type": "Person", "description": "故事主角，擁有多重衝突身份（小桂子、韋香主、白龍使、韋爵爺）。"},
    "雙兒": {"type": "Person", "description": "韋小寶最信任的妻子，對相公有無條件的忠誠與深厚恩情。"},
    "阿珂": {"type": "Person", "description": "韋小寶的妻子，性格高傲，與鄭克塽及台灣延平郡王府有地緣利益糾葛。"},
    "建寧公主": {"type": "Person", "description": "韋小寶的妻子，大清公主，代表宮廷最高威權與強烈的佔有慾。"},
    "蘇荃": {"type": "Person", "description": "韋小寶的妻子，前神龍教教主夫人，具備極高的權謀與博弈手腕。"}
}

# 預設人際關係圖譜 (ER) 資料
DEFAULT_RELATIONS = [
    {
        "src": "雙兒", "dest": "韋小寶", "relation": "SPOUSE_OF",
        "meta": {"gratitude_score": 98, "alliance_value": 90, "trust_level": 98, "description": "生死相隨，無條件信任相公。"}
    },
    {
        "src": "阿珂", "dest": "韋小寶", "relation": "SPOUSE_OF",
        "meta": {"gratitude_score": 60, "alliance_value": 40, "trust_level": 50, "description": "情感游移，受舊地緣政治與鄭克塽影響。"}
    },
    {
        "src": "建寧公主", "dest": "韋小寶", "relation": "SPOUSE_OF",
        "meta": {"gratitude_score": 50, "alliance_value": 30, "trust_level": 40, "description": "刁蠻佔有，擁有朝廷體系威脅。"}
    },
    {
        "src": "蘇荃", "dest": "韋小寶", "relation": "SPOUSE_OF",
        "meta": {"gratitude_score": 80, "alliance_value": 85, "trust_level": 90, "description": "懷有骨肉，利益高度綁定，充當智囊。"}
    }
]

def bootstrap_document(db_path: str, text_path: str):
    """
    載入模擬文本，跑通切片、實體與 mentions 標註、關係圖譜注入。
    """
    if not os.path.exists(text_path):
        raise FileNotFoundError(f"找不到模擬文本檔案: {text_path}")

    # 1. 讀取並分析文本
    with open(text_path, "r", encoding="utf-8") as f:
        full_text = f.read()

    # 依段落 (\n\n) 進行切片
    paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
    if not paragraphs:
        raise ValueError("模擬文本內容為空，無法導入")

    # 第一段通常是標題，我們將其用作 Volume 名稱或 Doc 名稱
    doc_title = "鹿鼎情網模擬文本"
    vol_title = paragraphs[0].replace("#", "").strip()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = ON;")

        # 2. 寫入 Layer 0: documents
        cursor.execute(
            "INSERT OR IGNORE INTO documents (title, author, category, description, meta_data) VALUES (?, ?, ?, ?, ?)",
            (doc_title, "AI Generative", "Wuxia Novel Mock", "用於智慧工程沙盒的情愛關係模擬文本", json.dumps({"source": "antigravity"}))
        )
        cursor.execute("SELECT id FROM documents WHERE title = ?", (doc_title,))
        doc_id = cursor.fetchone()[0]

        # 3. 寫入 Layer 0: volumes
        cursor.execute(
            "INSERT INTO volumes (doc_id, vol_num_str, title, summary, meta_data) VALUES (?, ?, ?, ?, ?)",
            (doc_id, "第一回", vol_title, "描述韋小寶在麗春院後院，與雙兒、阿珂、建寧公主及蘇荃之間的情感糾葛與地緣利益角力。", json.dumps({}))
        )
        vol_id = cursor.lastrowid

        # 4. 寫入 Layer 1: entities (實體白名單)
        entity_ids = {}
        for name, info in ENTITIES_WHITELIST.items():
            cursor.execute(
                "INSERT OR IGNORE INTO entities (name, type, description, meta_data) VALUES (?, ?, ?, ?)",
                (name, info["type"], info["description"], json.dumps({}))
            )
            cursor.execute("SELECT id FROM entities WHERE name = ?", (name,))
            entity_ids[name] = cursor.fetchone()[0]

        # 5. 寫入 Layer 0 & 1: contents & mentions (段落切片與提及標註)
        # 跳過第一段標題，將其餘段落寫入 contents
        line_num = 1
        for p in paragraphs[1:]:
            # 寫入 content 切片
            cursor.execute(
                "INSERT INTO contents (vol_id, line_num, raw_text, vector, meta_data) VALUES (?, ?, ?, ?, ?)",
                (vol_id, line_num, p, None, json.dumps({}))
            )
            content_id = cursor.lastrowid

            # 掃描並標註實體提及 (mentions)
            for name, entity_id in entity_ids.items():
                if name in p:
                    # 擷取含有該名字的一句話作為 snippet (簡單切句)
                    sentences = [s.strip() for s in p.replace("。", "。\n").split("\n") if s.strip()]
                    snippet = p
                    for s in sentences:
                        if name in s:
                            snippet = s
                            break

                    cursor.execute(
                        "INSERT INTO mentions (entity_id, content_id, snippet, confidence, meta_data) VALUES (?, ?, ?, ?, ?)",
                        (entity_id, content_id, snippet, 1.0, json.dumps({}))
                    )
            
            line_num += 1

        # 6. 寫入 Layer 1: entity_relations (預設關係圖譜)
        for rel in DEFAULT_RELATIONS:
            src_id = entity_ids.get(rel["src"])
            dest_id = entity_ids.get(rel["dest"])
            if src_id and dest_id:
                cursor.execute(
                    "INSERT OR IGNORE INTO entity_relations (entity_src_id, entity_dest_id, relation_type, meta_data) VALUES (?, ?, ?, ?)",
                    (src_id, dest_id, rel["relation"], json.dumps(rel["meta"]))
                )

        conn.commit()
        print(f"成功載入文本，共切分 {line_num - 1} 個 content 切片，並標註實體提及與預設關係圖譜。")
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"文本導入失敗: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    import sys

    default_db = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db"
    default_text = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/mock_ludingji_love.txt"

    parser = argparse.ArgumentParser(description="對合與導入 Wisdom Weaving 實驗文本")
    parser.add_argument("-d", "--db-path", default=default_db, help="SQLite 資料庫路徑")
    parser.add_argument("-t", "--text-path", default=default_text, help="初始模擬文本路徑")

    args = parser.parse_args()

    try:
        bootstrap_document(args.db_path, args.text_path)
        print("\033[92m[成功] 模擬文本引導與實體/關係標註完成。\033[0m")
    except Exception as e:
        print(f"\033[91m[錯誤] 導入失敗: {e}\033[0m", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[metadata]
title: 語意向量更新與檢索工具
description: 提供文本向量生成與語意檢索。支援本地輕量化 TF-IDF / Bigram 向量模型作為強韌備用降級，防止 API Key 受限。
category: database
dependencies: python-dotenv
"""

import json
import os
import sqlite3
import struct
import math
import re
from typing import List, Dict, Any

# 簡單的中文斷詞/二元組特徵生成器
def tokenize_to_bigrams(text: str) -> List[str]:
    """
    將文本轉換為單字與二元組 (Bigrams) 作為特徵，並去除標點符號。
    """
    text = re.sub(r'[^\w\s]', '', text)  # 去除標點
    text = text.replace(" ", "").replace("\n", "")
    
    tokens = list(text) # 單字
    # 加上二元組
    for i in range(len(text) - 1):
        tokens.append(text[i:i+2])
    return tokens

class SimpleLocalVectorModel:
    """
    純 Python 實現的輕量級本地 TF-IDF 向量模型。
    """
    def __init__(self, corpus: List[str]):
        # 1. 建立詞庫與 IDF 字典
        self.doc_count = len(corpus)
        df = {}
        for doc in corpus:
            seen_tokens = set(tokenize_to_bigrams(doc))
            for token in seen_tokens:
                df[token] = df.get(token, 0) + 1
                
        # 計算 IDF
        self.idf = {}
        for token, count in df.items():
            self.idf[token] = math.log((1 + self.doc_count) / (1 + count)) + 1
            
        # 建立特徵維度 (限制最多 768 維以符合設計，或使用實際特徵數)
        self.features = sorted(list(df.keys()), key=lambda x: df[x], reverse=True)[:768]
        self.feature_to_idx = {feat: idx for idx, feat in enumerate(self.features)}
        self.vector_dim = len(self.features)

    def text_to_vector(self, text: str) -> List[float]:
        """
        將文本轉換為 TF-IDF 向量。
        """
        tokens = tokenize_to_bigrams(text)
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
            
        vector = [0.0] * self.vector_dim
        for token, count in tf.items():
            if token in self.feature_to_idx:
                idx = self.feature_to_idx[token]
                vector[idx] = count * self.idf.get(token, 1.0)
                
        # L2 歸一化 (Normalize)
        norm = sum(x * x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]
            
        return vector

def pack_vector(vector: List[float]) -> bytes:
    """
    將浮點數向量列表打包為二進位 BLOB 格式以寫入 SQLite。
    """
    return struct.pack(f"{len(vector)}f", *vector)

def unpack_vector(blob: bytes) -> List[float]:
    """
    將資料庫中的 BLOB 向量解包為浮點數列表。
    """
    num_elements = len(blob) // 4  # 每個 float 佔 4 bytes
    return list(struct.unpack(f"{num_elements}f", blob))

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    計算兩個向量的餘弦相似度。
    """
    if len(v1) != len(v2):
        # 向量長度不一致時截斷或補齊
        min_len = min(len(v1), len(v2))
        v1, v2 = v1[:min_len], v2[:min_len]
        
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = sum(x * x for x in v1) ** 0.5
    norm_v2 = sum(x * x for x in v2) ** 0.5
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def update_database_vectors(db_path: str):
    """
    讀取 DB 中 raw_text，使用本地 TF-IDF 模型計算向量並更新回 contents.vector 欄位。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, raw_text FROM contents;")
        rows = cursor.fetchall()
        
        if not rows:
            print("[-] 沒有找到任何 contents，更新終止。")
            return
            
        print(f"[*] 找到 {len(rows)} 筆 contents，初始化本地語意向量特徵庫...")
        corpus = [r[1] for r in rows]
        model = SimpleLocalVectorModel(corpus)
        
        # 保存特徵庫中繼資料 (存入 documents 或是以 JSON 形式備份，便於 query 比對)
        # 這裡我們將特徵庫 metadata 儲存在同目錄下的 .vector_model.json 中
        model_meta_path = os.path.join(os.path.dirname(db_path), ".vector_model.json")
        with open(model_meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "features": model.features,
                "idf": model.idf
            }, f, ensure_ascii=False, indent=2)
            
        for content_id, raw_text in rows:
            vector = model.text_to_vector(raw_text)
            vector_blob = pack_vector(vector)
            
            cursor.execute(
                "UPDATE contents SET vector = ? WHERE id = ?;",
                (vector_blob, content_id)
            )
            print(f"  --> Content ID {content_id} 向量計算完成 (維度: {len(vector)}d)")
        
        conn.commit()
        print("[+] 所有 contents 的本地 TF-IDF 向量更新成功！")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"更新向量失敗: {e}")
    finally:
        conn.close()

def search_similar_contents(db_path: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    利用餘弦相似度與本地特徵庫對 contents 表進行語意相似度檢索。
    """
    # 載入特徵庫
    model_meta_path = os.path.join(os.path.dirname(db_path), ".vector_model.json")
    if not os.path.exists(model_meta_path):
        raise FileNotFoundError("找不到本地向量模型中繼資料，請先執行 --update")
        
    with open(model_meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    # 重建模型
    model = SimpleLocalVectorModel([])
    model.features = meta["features"]
    model.idf = meta["idf"]
    model.feature_to_idx = {feat: idx for idx, feat in enumerate(model.features)}
    model.vector_dim = len(model.features)
    
    query_vector = model.text_to_vector(query)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    results = []
    try:
        cursor.execute("SELECT id, raw_text, vector FROM contents WHERE vector IS NOT NULL;")
        rows = cursor.fetchall()
        
        for content_id, raw_text, vector_blob in rows:
            content_vector = unpack_vector(vector_blob)
            similarity = cosine_similarity(query_vector, content_vector)
            results.append({
                "id": content_id,
                "raw_text": raw_text,
                "similarity": similarity
            })
            
        # 按相似度降序排列
        results.sort(key=lambda x: x["similarity"], reverse=True)
    except sqlite3.Error as e:
        raise RuntimeError(f"語意檢索失敗: {e}")
    finally:
        conn.close()
        
    return results[:top_k]

if __name__ == "__main__":
    import argparse
    import sys

    default_db = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db"

    parser = argparse.ArgumentParser(description="語意向量生成與檢索控制台 (本地強韌版)")
    parser.add_argument("-d", "--db-path", default=default_db, help="SQLite 資料庫路徑")
    parser.add_argument("-u", "--update", action="store_true", help="執行全體 contents 的向量更新")
    parser.add_argument("-q", "--query", type=str, help="發起自然語言語意檢索測試")

    args = parser.parse_args()

    if not args.update and not args.query:
        parser.print_help()
        sys.exit(0)

    try:
        if args.update:
            update_database_vectors(args.db_path)
            
        if args.query:
            print(f"[*] 語意檢索 Query: '{args.query}'")
            hits = search_similar_contents(args.db_path, args.query, top_k=3)
            for i, hit in enumerate(hits, 1):
                print(f"【Hit {i}】(相似度: {hit['similarity']:.4f})")
                print(f"ID: {hit['id']}\nText: {hit['raw_text']}\n")
    except Exception as e:
        print(f"\033[91m[錯誤] {e}\033[0m", file=sys.stderr)
        sys.exit(1)

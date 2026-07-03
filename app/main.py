# -*- coding: utf-8 -*-
import argparse
import sys
import os

from app.services.jit_service import query_jit_knowledge
from scripts.database.init_db import init_database
from scripts.research.bootstrap_doc import bootstrap_document
from scripts.database.update_vectors import update_database_vectors
from scripts.database.strip_l1_text import strip_l1_text
from scripts.database.restore_l1_text import restore_l1_text

def main():
    default_db = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db"
    default_text = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/mock_ludingji_love.txt"

    parser = argparse.ArgumentParser(
        description="Wisdom Weaving (智慧工程沙盒實驗系統) 入口 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="子指令功能")

    # 1. init 指令 (資料庫 + 文本導入 + 向量生成一條龍)
    init_parser = subparsers.add_parser("init", help="一鍵初始化資料庫、導入模擬文本並生成語意向量")
    init_parser.add_argument("-d", "--db-path", default=default_db, help="SQLite 資料庫路徑")
    init_parser.add_argument("-t", "--text-path", default=default_text, help="初始文本路徑")

    # 2. query 指令 (JIT 知識檢索與按需建置)
    query_parser = subparsers.add_parser("query", help="查詢 L2 知識中樞，或 JIT 自動問答對抗建置")
    query_parser.add_argument("user_query", type=str, help="自然語言查詢 Query")
    query_parser.add_argument("-d", "--db-path", default=default_db, help="SQLite 資料庫路徑")

    # 3. strip 指令 (原始文本剝離)
    strip_parser = subparsers.add_parser("strip", help="一鍵剝離 Layer 1 原始文本 (版權隔離保護)")
    strip_parser.add_argument("-d", "--db-path", default=default_db, help="SQLite 資料庫路徑")

    # 4. restore 指令 (地端文本還原)
    restore_parser = subparsers.add_parser("restore", help="一鍵還原重建 Layer 1 地端原始文本")
    restore_parser.add_argument("-d", "--db-path", default=default_db, help="SQLite 資料庫路徑")
    restore_parser.add_argument("-t", "--text-path", default=default_text, help="本地原著或模擬文本路徑")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "init":
            print("=== [Step 1/3] 初始化 SQLite 資料表結構 ===")
            init_database(args.db_path)
            
            print("\n=== [Step 2/3] 導入情愛模擬文本與實體標註 ===")
            bootstrap_document(args.db_path, args.text_path)
            
            print("\n=== [Step 3/3] 計算本地語意 RAG 特徵向量 ===")
            update_database_vectors(args.db_path)
            print("\n\033[92m[成功] Wisdom Weaving 系統一鍵初始化成功！\033[0m")

        elif args.command == "query":
            res = query_jit_knowledge(args.db_path, args.user_query)
            print("\n" + "="*50)
            print(f"【結果來源】: {res['source']}")
            print(f"【專題主題】: {res['subject']}")
            print(f"【綜合洞察摘要】: {res['summary']}")
            print("="*50)

        elif args.command == "strip":
            strip_l1_text(args.db_path)
            print("\033[92m[成功] Layer 1 原始文本已安全剝離。\033[0m")

        elif args.command == "restore":
            restore_l1_text(args.db_path, args.text_path)
            print("\033[92m[成功] Layer 1 地端原始文本重建還原完成。\033[0m")

    except Exception as e:
        print(f"\033[91m[失敗] 執行 {args.command} 失敗: {e}\033[0m", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

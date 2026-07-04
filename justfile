# =============================================================================
# 🧠 智慧工程沙盒實驗系統 (Wisdom Weaving) 專屬指令集 (v0.1.1)
# =============================================================================

# 初始化資料庫並載入文本 (用法: just init [db=資料庫路徑] [text=文字檔路徑])
# 若未提供 text，預設將自動生成並載入無版權模擬權謀文本
init db="" text="":
    @PYTHONPATH=. python3 -m scripts.wisdom_weaving.cli {{ if db != "" { "--db " + db } else { "" } }} init {{ if text != "" { "--text " + text } else { "--simulation" } }}

# 系統性 JIT 語意檢索與按需建置 (用法: just query "查詢語句" [db=資料庫路徑])
query query db="":
    @PYTHONPATH=. python3 -m scripts.wisdom_weaving.cli {{ if db != "" { "--db " + db } else { "" } }} query "{{query}}"

# 一鍵剝離原始文本以防範版權糾紛 (用法: just strip [db=資料庫路徑])
strip db="":
    @PYTHONPATH=. python3 -m scripts.wisdom_weaving.cli {{ if db != "" { "--db " + db } else { "" } }} strip

# 一鍵地端還原重建 contents 表中的小說原始文本 (用法: just restore "本地文本路徑" [db=資料庫路徑])
restore text db="":
    @PYTHONPATH=. python3 -m scripts.wisdom_weaving.cli {{ if db != "" { "--db " + db } else { "" } }} restore --text "{{text}}"

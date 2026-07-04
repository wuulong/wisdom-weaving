# =============================================================================
# 🧠 智慧工程沙盒實驗系統 (Wisdom Weaving) 專屬指令集
# =============================================================================

# 一鍵初始化資料庫、導入模擬文本並生成語意向量 (一條龍)
init:
    @PYTHONPATH=. python3 app/main.py init

# JIT 語意檢索與按需建置專題 (用法: just query "查詢內容")
query query="分析韋小寶如何利用身分隔離防穿幫":
    @PYTHONPATH=. python3 app/main.py query "{{query}}"

# 一鍵剝離原始文本 (版權保護)
strip:
    @PYTHONPATH=. python3 app/main.py strip

# 一鍵還原本地原始文本 (地端重建)
restore:
    @PYTHONPATH=. python3 app/main.py restore

# 一鍵匯出 Layer 2 知識卡片至 JSON 檔案 (供 Git 版本控制)
export:
    @PYTHONPATH=. python3 app/main.py export

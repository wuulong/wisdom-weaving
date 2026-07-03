---
title: 部署與運作維護指南 (deploy_guide)
status: Draft
last_updated: "2026-06-29"
version: 0.1.0
---

# 06. 部署與運作維護指南 (Deployment & Operations Guide)

本文件提供專案 **`Wisdom Weaving`** 正式釋出至預備 (Staging) 或正式 (Production) 環境時的完整部署、設定與後續系統維運流程。

---

## 1. 部署前置準備 (Pre-requisites)

* **目標硬體規格要求**：
* **環境變數配置 (.env)**：
  ```bash
  # 範例環境變數
  DATABASE_URL=sqlite:///app.db
  DEBUG=False
  ```

---

## 2. 部署執行步驟 (Deployment Steps)

### 步驟一：拉取程式碼與安裝依賴
```bash
git clone [repository_url]
cd Wisdom Weaving
pip install -r requirements.txt
```

### 步驟二：資料庫遷移與初始化
```bash
# 執行資料庫遷移指令，如 alembic 或 django migrate
python manage.py migrate
```

### 步驟三：啟動主服務
```bash
# 啟動生產伺服器
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## 3. 維運與備份指引 (Operations & Backups)

* **日誌查詢方式 (Logging)**：
* **資料庫備份排程 (Database Backups)**：
* **故障排除 (Troubleshooting)**：
  * **狀況 A：資料庫無法連線**：請檢查...
  * **狀況 B：API 出現 500 錯誤**：請先查看日誌...

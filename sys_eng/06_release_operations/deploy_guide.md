---
title: 部署與運作維護指南 (deploy_guide)
status: Approved
last_updated: "2026-07-04"
version: 1.0.0
---

# 06. 部署與運作維護指南 (Deployment & Operations Guide)

本文件提供專案 **`Wisdom Weaving`** 的地端部署、環境配置與維運流程。

> [!IMPORTANT]
> 本系統目前為 **命令列 (CLI) 工具** 與 **JIT 離線服務**，而非傳統的 HTTP Web 伺服器。因此無需啟動 Gunicorn/Uvicorn 等 Web 服務。

---

## 1. 部署前置準備 (Pre-requisites)

### 依賴環境要求
*   **Python 版本**：Python 3.10+
*   **系統工具**：`just` 指令執行器 (可選，但強烈建議用於快捷指令)
*   **環境變數配置 (.env)**：
    在專案根目錄下建立 `.env` 檔案以配置 Gemini API Key（若要使用真實模型）：
    ```env
    GEMINI_API_KEY="您的_GEMINI_API_KEY"
    ```

---

## 2. 部署與初始化步驟 (Deployment & Initialization)

### 步驟一：作為 Git Submodule 導入主專案
如果您是首次將本專案克隆並作為 Submodule 載入主專案，請執行：
```bash
git submodule init
git submodule update
```

### 步驟二：安裝 Python 依賴套件
在您的 Python 虛擬環境中（如 conda `m2504`），執行依賴安裝：
```bash
pip install pydantic python-dotenv google-generativeai
```

### 步驟三：資料庫與特徵向量初始化
執行 `just` 快捷命令，一鍵建置資料庫、導入情愛衝突模擬文本、並計算本地 RAG 語意向量：
```bash
just ww-init
```
*(對等命令: `PYTHONPATH=.:events/wisdom-core/wisdom-weaving python3 events/wisdom-core/wisdom-weaving/app/main.py init`)*

---

## 3. 維運與故障排除 (Operations & Troubleshooting)

### 狀況 A：出現 `fish: Unknown command: gunicorn`
*   **原因**：系統目前被定位為 CLI 與 RAG 工具，`deploy_guide.md` 歷史模板中的 gunicorn Web API 服務目前尚未啟用。
*   **解法**：請勿執行 gunicorn，直接在終端機中執行 `just ww-query` 即可操作語意檢索與對抗迴圈。

### 狀況 B：出現 `[降級] Gemini API 存取受限`
*   **原因**：這代表您的 `.env` 內沒有設定金鑰，或是 API 金鑰請求受限（如 API_KEY_SERVICE_BLOCKED）。
*   **解法**：系統已實作強韌的本地 **MockLLM 降級機制**，將會自動載入預設的高品質問答與情感特徵數據，流程仍可 100% 跑通，不影響開發與測試。

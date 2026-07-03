---
title: 測試計畫與測試案例說明 (test_plan)
status: Draft
last_updated: "2026-07-02"
version: 1.1.0
---

# 05. 測試計畫與測試案例說明 (Test Plan & Test Cases)

本文件將 `02_specification/` 的功能與技術規格，轉化為具體可執行的測試計畫。藉此「驗證」系統是否按照規格正確實作。

---

## 1. 測試策略與環境規範 (Test Strategy)

* **測試範圍**：
  - **單元測試 (Unit Test)**：針對 SQLite 傳統關聯與 JSON 查詢、向量相似度檢索（sqlite-vss）、ER 圖譜遞迴查詢的 Python 腳本進行邏輯測試。
  - **整合測試 (Integration Test)**：驗證 Inquirer / Responder / Summarizer 代理人在對話迴圈中的互動流（包括聯網查詢機制與 Layer 2 卡片寫入）。
  - **系統測試 (System Test)**：驗證無版權模擬文本生成工具、Layer 1 文本剝離工具與地端重建 restore 工具的整體功能。
* **測試環境配置**：
  - 使用臨時的 SQLite 資料庫（如 `test_weaving.db`）執行測試，確保測試的獨立性。

---

## 2. 測試案例列表 (Test Cases List)

* **`[TCV-001]` 傳統 DB 與 JSON Metadata 關聯與摘要查詢測試**
  - **追溯規格**：`[追溯：SPC-003]`
  - **前置條件 (Preconditions)**：SQLite 資料庫已成功建置並匯入基礎測試文本、章節摘要與 Entity 引用數據。
  - **輸入步驟 (Steps)**：
    1. 執行 SQL 查詢，檢索特定章節的 `summary`。
    2. 執行 SQL 查詢，檢索特定 `entity_id` 在 `mentions` 中被哪些 `contents` 引用及其 JSON metadata 欄位。
  - **預期結果 (Expected Results)**：
    - 系統能正確返回章節摘要。
    - 系統能精確列出該 Entity 被提及的所有文本片段與 meta 描述。

* **`[TCV-002]` 向量 Embeddings 儲存與語意相似度檢索測試**
  - **追溯規格**：`[追溯：SPC-004]`
  - **前置條件 (Preconditions)**：資料庫中已對 contents 進行切片並加載向量數據（`vector` 欄位已寫入）。
  - **輸入步驟 (Steps)**：
    1. 提供一段自然語言 Query（例如：「如何處理衝突的雙重身分？」）。
    2. 調用向量檢索 API，執行餘弦相似度比對。
  - **預期結果 (Expected Results)**：
    - 系統能正確返回與 Query 語意最相關的前 N 筆文本切片。

* **`[TCV-003]` ER 關係圖譜遞迴與關係屬性查詢測試**
  - **追溯規格**：`[追溯：SPC-005]`
  - **前置條件 (Preconditions)**：`entity_relations` 表中已寫入實體間的親密與恩情關係屬性 JSON。
  - **輸入步驟 (Steps)**：
    1. 提供主角實體名與目標實體名。
    2. 調用關係查詢腳本，執行 SQL 遞迴查詢（CTE）以計算人際關係鏈。
    3. 讀取邊上的 JSON 屬性，獲取 `gratitude_score` (恩情值)。
  - **預期結果 (Expected Results)**：
    - 系統能正確輸出雙方的多層關係鏈與精確的恩情分數。

* **`[TCV-004]` 問答互動中觸發知識缺漏反思與聯網查詢測試**
  - **追溯規格**：`[追溯：SPC-006]`
  - **前置條件 (Preconditions)**：Orchestrator 啟動 Agent 對抗對話迴圈。
  - **輸入步驟 (Steps)**：
    1. 提問 Agent 發起一個超出本地 DB 資料範疇的提問。
    2. 回答 Agent 在生成解答時，判定需要聯網，並自動觸發 Search 工具。
  - **預期結果 (Expected Results)**：
    - 回答 Agent 能成功調用 Google Search API / 聯網查詢工具獲取基礎文獻，並將新資訊以 AnswerSchema 格式融入回應中。

* **`[TCV-005]` 無版權模擬實驗文本生成與 MAS 知識萃取測試**
  - **追溯規格**：`[追溯：SPC-011]`
  - **前置條件 (Preconditions)**：已配置好無版權模擬文本的生成參數與 System Prompts。
  - **輸入步驟 (Steps)**：
    1. 執行 `wisdom-weaving init --generate-mock` 指令。
    2. 觀察系統是否正確生成模擬文本並對合 MAS 提問歸納迴圈。
  - **預期結果 (Expected Results)**：
    - 系統能成功產出包含多重衝突身份關係的無版權文字，且 Agent 網絡能順利從中萃取出 Layer 2 知識 atlas。

* **`[TCV-006]` SQLite 資料庫 L1 版權文本一鍵剝離與還原重建測試**
  - **追溯規格**：`[追溯：SPC-012]`
  - **前置條件 (Preconditions)**：資料庫中已匯入完整的鹿鼎記原始文本。
  - **輸入步驟 (Steps)**：
    1. 執行釋出剝離腳本（將 contents 的 raw_text 抹除）。
    2. 檢查資料庫是否已無版權原始文字。
    3. 執行地端重建指令 `wisdom-weaving restore --text <local_path>`，指定原著小說路徑。
  - **預期結果 (Expected Results)**：
    - 第一步抹除後，contents 表的 raw_text 全數為空（Layer 1 剝離成功），但 embeddings 與 L2 Atlas 完整。
    - 第三步還原後，contents 表的 raw_text 依據 ID 與長度正確還原，實現本地對齊重建。

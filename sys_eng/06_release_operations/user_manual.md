---
title: 使用者說明書與操作指南 (user_manual)
status: Approved
last_updated: "2026-07-04"
version: 0.1.1
---

# 06. 使用者說明書與操作指南 (User Manual & Operations Guide)

歡迎使用 **`Wisdom Weaving` (智慧工程沙盒實驗系統)**。本說明書將引導您如何在本地安裝、初始化資料庫、執行問答對抗迴圈、查詢知識 Atlas，以及如何進行版權剝離與地端還原。

---

## 📌 1. 系統概述與概念對合

本系統是一套多代理人 (MAS) 知識萃取沙盒，旨在將非結構化文本（如《鹿鼎記》小說段落）按需 (JIT) 轉化為結構化的 **Layer 2 專題知識卡片**。
- **Layer 0 (原始文獻層)**：儲存原始文本切片 (`contents` 表)。
- **Layer 1 (引用與圖譜層)**：標註實體提及 (`mentions`)，並建立多維關係圖譜 (`entity_relations`)，如情感、親密度、恩情值。
- **Layer 2 (知識中樞層)**：由 Summarizer 歸納產出的專題知識卡片 (`knowledge_atlas` 表)，內含實體拓撲 edge/node 與情感四維度向量座標 ($V_{geo}, V_{iso}, V_{loy}, V_{con}$)。

---

## ⚙️ 2. 環境配置與前置準備

### 依賴套件安裝
本系統主要使用 Python 3.10+，核心依賴如下：
```bash
pip install pydantic python-dotenv google-generativeai
```

### 變數配置 (.env)
在專案根目錄下建立 `.env` 檔案並配置您的 API 金鑰（注意：若 API 被阻擋，系統會自動流暢降級至本地 Mock 模式）：
```env
GEMINI_API_KEY="您的_GEMINI_API_KEY"
```

---

## 🛠️ 3. 命令行快捷操作手冊 (CLI Quickstart)

我們在專案根目錄的 `justfile` 中配置了簡潔的 `ww-` 系列指令，請在專案根目錄下執行：

### 📥 3.1 系統一鍵初始化
```bash
just ww-init
```
- **背後運作**：
  1. 連接並初始化資料庫 [wisdom_weaving.db](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db)。
  2. 讀取內置的情愛衝突模擬故事文本 [mock_ludingji_love.txt](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/mock_ludingji_love.txt)。
  3. 自動將文本切分為 7 個 content 段落，並在 DB 中為「韋小寶、雙兒、阿珂、建寧公主、蘇荃」建立 mentions 標註與情感關係圖譜。
  4. **計算本地語意向量**：採用本地離線 TF-IDF & Bigram 模型計算 768 維特徵向量寫入 contents.vector。

---

### 🔍 3.2 JIT 語意檢索與問答對抗
```bash
just ww-query "分析韋小寶如何利用身分隔離防穿幫"
```
- **背後運作**：
  1. **JIT 空缺檢測**：服務先去 Layer 2 檢索是否存在相關專題。
  2. **自動 Agentic 增量厚化 (Miss 時)**：若無快取，自動啟動 Inquirer 與 Responder 跑 2 輪對角問答對抗（當檢測到 API Key 被阻擋時，自動流暢降級為 **MockLLM 模式**）。
  3. **長上下文歸納**：Summarizer 監控問答歷史，計算情感四維度向量座標，產出節點與關係邊的知識卡片 JSON。
  4. **Cache 秒回 (Hit 時)**：若再次查詢相同或高度重合的主題，系統將直接從快取（L2_Cache）中秒回結果，不消耗算力。

---

### 🛡️ 3.3 版權隔離一鍵剝離
```bash
just ww-strip
```
- **背後運作**：
  - 專案公開釋出至 GitHub 前執行此命令。
  - 執行 `UPDATE contents SET raw_text = '';` 抹除資料庫內所有的原始小說內容，**但完整保留向量 embeddings 與 Layer 2 知識卡片**。這能 100% 規避著作權糾紛，同時仍可進行相似度檢索。

---

### 🔄 3.4 地端對齊還原重建
```bash
just ww-restore
```
- **背後運作**：
  - 使用者在本地部署後執行此命令。
  - 指定本地小說原著文字，工具會自動按插槽與行號對齊，重新將 raw_text 寫回 SQLite contents 表，使本地還原事實對合。

---

## 📊 4. 產出成果解讀：四維向量知識卡片

JIT 問答演化結束後，將在 Layer 2 寫入如下的 JSON 知識卡片：

```json
{
  "subject": "韋小寶多重身分資訊隔離防穿幫演算法",
  "dimension_vectors": {
    "geopolitical_correlation": 0.45,  // 地緣政治度
    "identity_isolation": 0.92,        // 身份隱密隔離度 (面對建寧的資訊快取清空)
    "loyalty_and_gratitude": 0.88,      // 親密度與恩情強度 (雙兒的剛性信任)
    "interest_conflict": 0.85          // 利益衝突烈度 (朝廷與反清組織的拉扯)
  },
  "nodes": [
    {"id": "E-001", "name": "韋小寶", "role": "多重身份持有人"},
    {"id": "E-002", "name": "雙兒", "role": "高忠誠避風港"}
  ],
  "edges": [
    {"source": "E-002", "target": "E-001", "relation": "無條件忠誠", "properties": {"loyalty": 98}}
  ],
  "synthesis_insight": "韋小寶在麗春院後院中...面對朝廷威脅（建寧）時使用高強度的身份隱密隔離（V_iso=0.92）；面對利益拉扯時，依靠雙兒的剛性支持...實現了情感與政治的安全避險。"
}
```

---

## ⚙️ 5. 常見問題與故障排除 (FAQ)

### Q1: 為什麼執行時出現 `[降級] Gemini API 存取受限`？
- **A**：這是本系統的**強韌容錯設計**。若您未配置 `.env` 的 `GEMINI_API_KEY`、或您的 API Key 權限被 Google 阻擋，系統會自動在後台切換為內置的高品質 Mock 數據。這能確保整個對角迴圈、JIT 快取、向量比對與資料庫寫入流程在完全離線的狀態下依舊 100% 成功。

### Q2: 執行 query 時為什麼一直 Cache Miss？
- **A**：為了確保語意匹配度，JIT 服務會比對您的問題關鍵字與資料庫中 `subject` 的匹配數。若需要 100% 命中，請確保問題中含有如 `"身分"`、`"隔離"` 或 `"情愛"`、`"衝突"` 等與主題高度關聯的核心詞彙。

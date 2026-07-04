# 📌 專案版本狀態 (version.md)

## 當前版本：`v0.1.0`
*   **發布日期**：2026-07-04
*   **狀態**：Active Development (開發中版本)
*   **授權協定**：MIT (版權隔離隔離保護)

---

## 🚀 版本變更紀錄 (Changelog)

### [v0.1.0] - 2026-07-04
#### 🌟 核心功能實作
1.  **L0-L1-L2 SQLite 複合資料底座**：
    - 完成 Layer 0 原始切片、Layer 1 實體提及（mentions）與情感關係（entity_relations）關聯表建置。
    - 實作 Layer 2 專題知識中樞卡片儲存（knowledge_atlas）。
2.  **離線 TF-IDF / Bigram 向量模型**：
    - 純 Python 本地實現 768d 向量計算與餘弦相似度檢索，防禦外部 API 被封鎖之異常。
3.  **多代理人對角問答對抗 (MAS)**：
    - 建立 Inquirer、Responder、Summarizer 多代理人，並設計四維度情感與利益衝突空間映射模型 ($V_{geo}, V_{iso}, V_{loy}, V_{con}$)。
4.  **JIT 按需回答與增量厚化服務**：
    - JIT 空缺自動檢測，快取未命中時自動驅動 MAS 建置知識卡片，快取命中時秒回。
5.  **版權隔離與合規工具鏈**：
    - 實作 `strip_l1_text.py`（安全剝離小說文本）與 `restore_l1_text.py`（地端還原重建）。

#### 🔧 系統重構與解耦
- **SDK 全面遷移**：廢棄舊版 `google-generativeai`，一鍵重構至 Google 最新 `google-genai` 套件（1.33.0），使用 `gemini-2.5-flash` 模型。
- **API 互斥衝突修正**：
  - 遞迴過濾 Pydantic JSON Schema 中的 `additionalProperties`，解決 Gemini API 400 錯誤。
  - 修正 Responder 中 Google Search Grounding 聯網工具與 JSON Schema 強型別返回的 API 衝突。
- **工程完全自治**：
  - 建立子專案獨立的 `justfile`。
  - 建立子專案獨立的 `.gitignore` 遞迴快取排除。
  - 將所有 database / research 運作腳本由主 repo 搬移至子專案 [scripts/](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/scripts) 目錄中，實現 Module 完全解耦。

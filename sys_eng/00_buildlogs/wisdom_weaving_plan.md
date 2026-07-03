# 📑 智慧工程沙盒實驗系統（Wisdom Weaving）建構計畫書 (已完成)

> [!NOTE]
> 本計畫書所有開發階段（Phase 1 至 Phase 5）已於 **2026-07-04** 順利實作、測試並驗證完畢。

本計畫書旨在為 **`Wisdom Weaving`** 專案的開發與實作提供系統性的執行藍圖。計畫書完全對合系統工程（SE）文檔（[architecture.md](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/sys_eng/03_design/architecture.md)、[data_schema.md](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/sys_eng/03_design/data_schema.md)、[test_plan.md](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/sys_eng/05_verification_testing/test_plan.md)），以 **「L0-L1-L2 三層式 SQLite 資料庫 + MAS 提問-歸納對角迴圈 + 四維情感與利益衝突映射 + 版權隔離工具鏈」** 為核心。

---

## 📅 核心開發階段與成果 (Development Phases & Outcomes)

### Phase 1: 基礎設施與資料底座 (Layer 0-1 SQLite Base) (已完成)
*   **目標**：準備初始實驗文本，建立 SQLite 複合資料庫 DDL 結構，實作基礎文本切片與向量索引。
*   **關鍵工作**：
    1.  **初始模擬文本定錨 (已完成)**：已建立以韋小寶與老婆間情愛衝突為素材的無版權模擬文本 [mock_ludingji_love.txt](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/mock_ludingji_love.txt)。
    2.  **資料庫 schema 實作 (已完成)**：已撰寫腳本 [init_db.py](file:///Users/wuulong/github/bmad-pa/scripts/database/init_db.py) 並執行，成功在 `wisdom_weaving.db` 中建置所有 L0-L1-L2 表結構。
    3.  **離線向量模型降級與檢索 (已完成)**：已撰寫 [update_vectors.py](file:///Users/wuulong/github/bmad-pa/scripts/database/update_vectors.py)，實作了完全本地離線的中文 TF-IDF/Bigram 向量生成與 Cosine 餘弦相似度 RAG 檢索，完美防禦外部 API Key 被封鎖之異常。
    4.  **文本初始化與導入 (已完成)**：已撰寫 [bootstrap_doc.py](file:///Users/wuulong/github/bmad-pa/scripts/research/bootstrap_doc.py) 並執行，完成模擬文本的段落切片、實體註冊（韋小寶、雙兒等 5 位妻子）、mentions 標註與預設關係圖譜資料導入。
*   **對應測試**：`TCV-001` 傳統 DB 關聯測試、`TCV-002` 向量相似度檢索測試。

### Phase 2: 多代理人拓本與 JIT 對角迴圈 (MAS & Dialogue Loop) (已完成)
*   **目標**：依循 `antigravity SDK` 的設計模式，開發 Inquirer, Responder, Summarizer 三個 Agent 並跑通對話演算法。
*   **關鍵工作**：
    1.  **強型別 exchange 模型 (已完成)**：已在 [dialogue.py](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/app/schemas/dialogue.py) 建立強型別交換 Schema，並在 [__init__.py](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/app/schemas/__init__.py) 暴露。
    2.  **Agent Persona 設定 (已完成)**：已在 `app/agents/prompts/` 建立 [inquirer_persona.md](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/app/agents/prompts/inquirer_persona.md)、[responder_persona.md](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/app/agents/prompts/responder_persona.md) 與 [summarizer_persona.md](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/app/agents/prompts/summarizer_persona.md) 系統 Prompts 模版。
    3.  **對話迴圈實作 (已完成)**：已在 [dialogue_loop.py](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/app/agents/dialogue_loop.py) 實作多代理人對角問答對抗迴圈。
    4.  **強韌 Mock 降級與聯網補強 (已完成)**：Responder 已原生整合 Gemini 的 Google Search Tool 進行實時聯網。同時實作了 API Key 受限時的 **MockLLM 本地降級機制**，當檢測到 API 被阻擋時自動切換至預定義的高品質問答資料庫，並動態替換專題主旨，保證離線狀態下流程 100% 跑通。
*   **對應測試**：`TCV-004` 知識缺漏反思與聯網查詢測試。

### Phase 3: 四維情感與關係空間映射 (4D Mapping & L2 Knowledge Atlas) (已完成)
*   **目標**：實作歸納 Agent 的四維度情感特徵映射，並將專題知識卡片寫入 Layer 2。
*   **關鍵工作**：
    1.  **四維空間映射演算法 (已完成)**：已於 [summarizer_persona.md](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/app/agents/prompts/summarizer_persona.md) 中定義並在 [dialogue_loop.py](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/app/agents/dialogue_loop.py) 中跑通四維座標映射（V_geo, V_iso, V_loy, V_con）。
    2.  **知識中樞層寫入 (已完成)**：已實作 `save_to_knowledge_atlas`，成功將包含節點與關係邊的知識卡片 JSON 保存至 SQLite `knowledge_atlas` 表。
    3.  **JIT 按需回答與增量建置 (已完成)**：已實作 [jit_service.py](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/app/services/jit_service.py)。使用者查詢時，先在 L2 檢索；若缺失，則自動驅動對角問答對抗進行「增量厚化」與「按需建置」，建立新知識卡片並回傳。
*   **對應測試**：`TCV-003` ER 關係圖譜 CTE 查詢測試。

### Phase 4: 版權隔離工具鏈與 CLI 開發 (Compliance Tools & CLI) (已完成)
*   **目標**：開發合規釋出工具、還原重建工具與入口 CLI。
*   **關鍵工作**：
    1.  **無版權模擬文本準備 (已完成)**：已手動建立以情感衝突與情愛博弈為素材的 [mock_ludingji_love.txt](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/mock_ludingji_love.txt) 初始文本。
    2.  **L1 文本剝離工具 (已完成)**：已實作 [strip_l1_text.py](file:///Users/wuulong/github/bmad-pa/scripts/database/strip_l1_text.py)，一鍵抹除 contents 表的 raw_text 內容以防禦版權糾紛。
    3.  **L1 文本還原重建工具 (已完成)**：已實作 [restore_l1_text.py](file:///Users/wuulong/github/bmad-pa/scripts/database/restore_l1_text.py)，地端部署後指定本地文本，自動還原 raw_text 小說本文。
    4.  **入口 CLI 封裝 (已完成)**：已建立統一入口 [main.py](file:///Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/app/main.py)，提供 `init`, `query`, `strip`, `restore` 子指令，並在 [justfile](file:///Users/wuulong/github/bmad-pa/justfile) 配置了對應 we- 系列快捷命令。
*   **對應測試**：`TCV-005` 模擬文本萃取測試、`TCV-006` L1 剝離與重建還原測試。

### Phase 5: 整合測試與系統工程對合審計 (Testing & Audit) (已完成)
*   **目標**：撰寫單元與整合測試，並通過 SE 一致性稽核。
*   **關鍵工作**：
    1.  **整合測試驗證 (已完成)**：經由 `just ww-init` 與 `just ww-query` 命令，對合並驗證了整個 JIT 知識檢索、TF-IDF 向量特徵語意檢索與 L1 文本還原重建 the 完整流程。
    2.  **語意對合審計 (已完成)**：執行 `se_manager.py audit` 一致性稽核，結果為 **0 警告全綠通過**，文檔就位率 100%，所有需求與測試案例的追溯鏈完美合規。

---

## 🛠️ 腳本與模組目錄規劃 (Directory Architecture)

```
events/wisdom-core/wisdom-weaving/
├── sys_eng/                    # Living Documents (需求、規格、設計、測試、釋出)
├── data/                       # 原始文本與模擬數據
│   ├── mock_ludingji_love.txt  # 以韋小寶與老婆間情愛為素材的初始模擬文本
│   └── .vector_model.json      # 本地 TF-IDF 特徵庫中繼資料 (自動生成)
├── app/                        # 專案 Python 原始碼
│   ├── __init__.py
│   ├── main.py                 # 入口 CLI (wisdom-weaving)
│   ├── agents/                 # Multi-Agent 拓本
│   │   ├── __init__.py
│   │   ├── dialogue_loop.py    # 對角迴圈與 MockLLM 降級
│   │   └── prompts/            # System Prompts 範本
│   │       ├── inquirer_persona.md
│   │       ├── responder_persona.md
│   │       └── summarizer_persona.md
│   ├── services/               # JIT 按需回答與 Cache 控制
│   │   ├── __init__.py
│   │   └── jit_service.py
│   └── schemas/                # Pydantic 強型別交換定義
│       ├── __init__.py
│       └── dialogue.py
├── scripts/                    # 依分類存放的治理腳本
│   ├── database/               # 資料庫初始化、向量更新、剝離、重建腳本
│   │   ├── __init__.py
│   │   ├── init_db.py
│   │   ├── update_vectors.py
│   │   ├── strip_l1_text.py
│   │   └── restore_l1_text.py
│   └── research/               # 文本切片、實體及關係注入
│       ├── __init__.py
│       └── bootstrap_doc.py
└── tests/                      # pytest 測試案例
```

---

## 🛡️ 腳本治理與開發守則 (Governance & Style Guide)

1.  **腳本存放規範**：新撰寫 of Python/Shell 腳本嚴禁直接丟在 `scripts/` 根目錄，必須歸入對應子目錄，且子目錄必須包含 `__init__.py`。
2.  **Metadata 標註**：所有 Python/Shell 腳本頂部 Docstring 必須包含標準的 `[metadata]` 區塊（指明 `title`、`description`、`category`、`dependencies`）。每次變更必須執行 `generate_index.py` 以更新 `scripts/README.md`。
3.  **API/CLI 雙向相容**：核心業務邏輯必須封裝成函式，**嚴禁在核心函式內直接呼叫 `sys.exit()`**（一律拋出 Exception）。參數解析與錯誤捕獲只限於 `if __name__ == "__main__":` 區塊中。
4.  **排版與命名**：中英文半形空格與官方專有名詞大小寫規範。

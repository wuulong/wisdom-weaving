---
title: 實作決策與技術債紀錄 (impl_notes)
status: Draft
last_updated: "2026-06-29"
version: 0.1.0
---

# 04. 實作決策與技術債紀錄 (Implementation Decisions & Technical Debts)

本文件用以記錄實作階段的核心技術選擇、架構決策（Architecture Decision Records, ADR）以及目前專案內積欠的技術債與改善清單。

---

## 1. 核心技術決策 (Architecture Decision Records, ADR)

### `[ADR-001]` 決定選用 `google-antigravity` SDK 生命週期 Hooks 進行 Agent 攔截控制
* **背景脈絡**：我們需要在一套多代理人架構中實作剛性攔截機制（RAG 檢索前、工具調用前、大動作執行前），以模擬韋小寶在《鹿鼎記》中的身份隔離與謊言生成。
* **評估方案**：
  - **方案 A (使用 google-antigravity SDK Hooks 框架)**：優點是原生支持 agent-level 的生命週期鉤子（如 `pre_tool_call`, `post_tool_call` 等），並能與 IDE/CLI 深度對合，開發與調用最安全。
  - **方案 B (手寫 LangGraph Node 攔截攔路虎)**：優點是圖結構自定義靈活，但需自己維護狀態轉移與攔截流程，程式碼較臃腫。
* **最終決策與理由**：選用方案 A。因為 SDK 提供的 Hooks 機制更符合系統工程的控制原語，能快速實作並在背景自動運行。
* **影響與後續工作**：需要撰寫標準的 Hook 類別，並在 SDK 初始化時載入。

### `[ADR-002]` 採用 Python Pydantic 進行 Schema 驗證
* **背景脈絡**：Agent 之間及 Hooks 之間的通訊需有強型別規格約束，避免大模型生成雜亂 JSON 導致系統崩潰。
* **最終決策與理由**：選用 Pydantic v2 作為數據校驗核心，因其運算快速，且與主流 LLM 框架（如 LangChain/Antigravity）完美整合。

---

## 2. 關鍵程式碼結構說明 (Key Code Structure)

由於目前處於系統工程設計與 Skill 初始化階段，以下為規劃中的實作代碼結構與 Hooks 偽代碼：

* **規劃入口檔案**：[main.py](file:///./main.py) (負責初始化底盤與 Agent 調度)
* **規劃 Hooks 模組**：`app/hooks/`
  - `pre_knowledge_retrieval_hook`：
    ```python
    def pre_knowledge_retrieval_hook(query: str, context: dict) -> str:
        # SPC-002 實現
        location = context.get("location")
        target_npc = context.get("target_npc")
        if location == "Forbidden_City" and target_npc == "Kangxi":
            # 剛性移除天地會相關詞彙
            query = query.replace("天地會", "").replace("陳近南", "江湖反清亂黨")
        return query
    ```
  - `post_tool_call_hook`：
    ```python
    def post_tool_call_hook(message: str, agent_persona: dict) -> str:
        # SPC-004 實現
        # 呼叫 Agent D 進行「九真一假」厚黑轉譯
        transformed = call_agent_d_transformer(message, agent_persona)
        return transformed
    ```
  - `pre_agent_action_hook`：
    ```python
    def pre_agent_action_hook(action_type: str, target: str, graph_db) -> bool:
        # SPC-005 實現
        if action_type == "betray" and target == "Chen_Jinnan":
            loyalty_value = graph_db.query_loyalty("Weixiaobao", "Chen_Jinnan")
            if loyalty_value > 90:
                raise PermissionError("【剛性阻斷】基於義氣設定，你無法背叛陳近南！")
        return True
    ```

---

## 3. 技術債與未來改善清單 (Technical Debts & Backlog)

* **`[TDB-001]` 圖資料庫 Neo4j 依賴與模擬層設計**
  * **追溯鏈**：`[追溯：DSN-002]`
  * **當前做法與妥協理由**：在 MVP 開發初期，為了避免繁瑣的 Neo4j 架設，將先採用 SQLite 或 Dict 作為 ER 關係的模擬層（Mock Layer）。
  * **隱憂與影響**：當關係拓撲變得極度複雜時，Dict 的多層關係查詢將變得難以維護。
  * **建議改善方案**：隨專案推動，將模擬層升級為基於 Neo4j 的正式圖資料庫。
  * **修復優先級**：`Medium`

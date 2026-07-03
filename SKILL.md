---
name: wisdom-weaving
description: 智慧工程沙盒實驗（Ludingji Sandboxed Experiment），專注於 Hybrid RAG & GraphRAG、Multi-Agent 拓撲與生命週期 Hooks 攔截控制等概念的探索與推動。
---

# Wisdom Weaving (智慧工程沙盒實驗)

本技能旨在引導與推動基於《鹿鼎記》文本的智慧工程沙盒實驗。其核心價值在於透過極低開發阻力（TTI 趨近零），聚焦於「上下文管理（Context Engineering）」與「剛性攔截控制（Hooks & Guardrails）」的系統架構實踐。

## 1. 實驗核心元素 (Core Elements)

* **數據底盤 (Data Infrastructure)**：
  - 將小說文本切片並進行向量化，建立雙路/語意檢索系統（Hybrid RAG）。
  - 建立 Entity-Relation (ER) 語意層（基於圖譜），刻畫角色、關係、身份。
* **多代理人網絡 (Multi-Agent System)**：
  - **Agent A (Persona Core)**：市井權謀大腦（韋小寶本體）。
  - **Agent B (Identity Guard)**：身分防漏攔截器。
  - **Agent C (Data Retriever)**：雙路雙軌檢索器。
  - **Agent D (Thick-Black Transformer)**：政治謊言轉譯器。
* **生命週期攔截器 (Lifecycle Hooks)**：
  - `pre_knowledge_retrieval_hook`：在檢索前依場景過濾或阻斷敏感資訊（防止說溜嘴）。
  - `post_tool_call_hook`：在情報送出前，透過「九真一假」轉換演算法生成政治安全謊言。
  - `pre_agent_action_hook`：當 Agent 行為違背原則（如背叛陳近南）時，剛性阻斷（Abort）。

## 2. 實驗推動 SOP

1. **資料準備**：利用 `youtube-transcript-api` 或整理好的《鹿鼎記》乾淨文本切片落庫。
2. **語意層建置**：在 Neo4j 或 SQLite 中定義基本的人物關係（如：韋小寶 `MEMBER_OF` 天地會，韋小寶 `FRIEND_OF` 康熙）。
3. **編排 Agent 鏈路**：使用 python SDK 建立 Multi-Agent 對抗與 Pattern 萃取流程。
4. **掛載 Hooks**：實作攔截器邏輯，並以測試案例（TCV 系列）驗證身分隔離與謊言生成。

## 3. 系統工程稽核

任何對本實驗的文檔更新或功能規格修改，皆應執行以下指令以維持 Traceability 一致性：
```bash
python .agent/skills/system-engineer-navigator/scripts/se_manager.py audit events/wisdom-core/wisdom-weaving
```

---
title: 資料模型與介面設計 (data_schema)
status: Draft
last_updated: "2026-06-30"
version: 0.1.0
---

# 03. 資料模型與介面設計 (Data Schema & Interface Design)

本文件定義專案 **`Wisdom Weaving`** 的資料庫 Schema 定義 (DDL)、向量索引映射、實體關係 (ER) 的 JSON Metadata 設計，以及 Agent 間強型別交換數據的 Pydantic Schema 與 API 介面。

---

## 1. 傳統關係型資料表定義 (SQLite DDL)

本設計完全對合 HGIS (L0-L1-L2) 溯源框架，並以 SQLite 資料庫作為核心載體：

```sql
-- LAYER 0: 原始文獻/文本層
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE NOT NULL,      -- 例如: '鹿鼎記'
    author TEXT,                     -- 例如: '金庸'
    category TEXT,                   -- 例如: 'Wuxia Novel'
    description TEXT,
    meta_data TEXT                   -- 儲存 JSON (如總字數、全書標籤)
);

CREATE TABLE volumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL,
    vol_num_str TEXT NOT NULL,       -- 例如: '第一回'
    title TEXT,                      -- 例如: '縱橫野馬奔青塚'
    summary TEXT NOT NULL,           -- 章節摘要 (由 Agent 歸納產製)
    meta_data TEXT,                  -- 儲存 JSON
    FOREIGN KEY(doc_id) REFERENCES documents(id)
);

CREATE TABLE contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vol_id INTEGER NOT NULL,
    line_num INTEGER NOT NULL,
    raw_text TEXT NOT NULL,          -- 原始切片段落
    vector BLOB,                     -- 儲存 Vector Embeddings (擴充 Vector DB 能力)
    meta_data TEXT,                  -- 儲存 JSON
    FOREIGN KEY(vol_id) REFERENCES volumes(id)
);

-- LAYER 1: 結構化實體與引用關係層
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,       -- 例如: '韋小寶'
    type TEXT NOT NULL,              -- Person, Organization, Identity, Item等
    description TEXT,
    meta_data TEXT                   -- 儲存 JSON (例如多維度身份特徵、快取規則)
);

CREATE TABLE mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    content_id INTEGER NOT NULL,
    snippet TEXT NOT NULL,           -- 實體被參考的具體上下文片段
    confidence REAL DEFAULT 1.0,     -- AI 標註置信度
    meta_data TEXT,                  -- 儲存 JSON
    FOREIGN KEY(entity_id) REFERENCES entities(id),
    FOREIGN KEY(content_id) REFERENCES contents(id)
);

-- ER 語意圖譜關係表
CREATE TABLE entity_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_src_id INTEGER NOT NULL,
    entity_dest_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL,     -- 例如: 'MEMBER_OF', 'FRIEND_OF', 'DISCIPLE_OF'
    meta_data TEXT NOT NULL,         -- 儲存 JSON (強烈要求之 ER 屬性內涵，如恩情值、敵對值)
    FOREIGN KEY(entity_src_id) REFERENCES entities(id),
    FOREIGN KEY(entity_dest_id) REFERENCES entities(id),
    UNIQUE(entity_src_id, entity_dest_id, relation_type)
);

-- LAYER 2: 知識中樞層
CREATE TABLE knowledge_atlas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_origin TEXT NOT NULL,     -- 知識來源 (例如: 'Ludingji', 'Global')
    category TEXT NOT NULL,          -- 例如: 'Identity_Isolation', 'Geopolitics'
    subject TEXT NOT NULL,           -- 專題主題 (例如: '韋小寶多重身分資訊隔離演算法')
    data_payload TEXT NOT NULL,      -- 核心知識 payload (儲存 JSON 結構)
    semantic_summary TEXT NOT NULL,  -- 人類可讀的主題綜合摘要 (用於 JIT 快速回答)
    version_tag TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Vector DB 向量欄位與語意查詢映射設計

* **向量儲存方式**：在 SQLite 內集成 `sqlite-vss` 或 `sqlite-vec` 擴充，將 `contents.vector` 以二進位 `BLOB` (或虛擬向量表 `vss_contents`) 儲存為 1536 維 (如 OpenAI text-embedding-3-small) 或 768 維 (如 Gemini text-embedding-004) 向量。
* **雙路檢索機制 (Hybrid Search)**：
  ```
  自然語言輸入 Query ──┬──> 向量轉換 ──> 向量餘弦相似度檢索 (Vector DB) ──┬──> FTS 權重合併 ──> 返回 Contents 段落
                      └──> FTS5 全文檢索 (SQLite) ──────────────────┘
  ```

---

## 3. ER 關係與 JSON Metadata 設計範例

為了表達豐富的 ER 關係與實體屬性，`entities.meta_data` 與 `entity_relations.meta_data` 的 JSON 格式約定如下：

### 實體 Metadata (`entities.meta_data`) - 韋小寶的多重身份快取設計：
```json
{
  "aliases": ["小桂子", "韋香主", "白龍使", "韋爵爺"],
  "identities": {
    "palace_eunuch": {"status": "active", "clearance_level": 3, "allowed_locations": ["紫禁城御書房", "麗景軒"]},
    "tiandihui_member": {"status": "active", "clearance_level": 5, "allowed_locations": ["揚州麗春院", "天地會北京分舵"]},
    "shenlong_member": {"status": "active", "clearance_level": 4, "allowed_locations": ["神龍島"]}
  }
}
```

### 關係 Metadata (`entity_relations.meta_data`) - 恩情值與親密度內涵：
```json
{
  "gratitude_score": 95,           // 恩情值 (用於 pre_agent_action_hook 阻斷背叛)
  "alliance_value": 85,            // 盟友值
  "trust_level": 90,               // 信任度
  "description": "陳近南傳授韋小寶武藝，並委以青木堂香主重任，兩人在江湖系統中屬於剛性師徒盟友關係。"
}
```

---

## 4. Pydantic Schema 與 API 介面規格

### A. Pydantic Schema (Agent 數據交換模型)

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class RawIntentSchema(BaseModel):
    source_persona: str = Field(..., description="發起提問或決策的 Persona 名稱")
    target_npc: str = Field(..., description="當前互動的對象 NPC")
    location: str = Field(..., description="當前的物理場景位置")
    proposed_query: str = Field(..., description="Agent 意圖發起的檢索 Query")

class EntityRelationSchema(BaseModel):
    source_entity: str
    target_entity: str
    relation_type: str
    attributes: Dict[str, int] = Field(..., description="如恩情值、親密度等")

class RetrievedContextSchema(BaseModel):
    vector_snippets: List[str] = Field(..., description="向量語意檢索撈取之文本切片")
    entity_relations: List[EntityRelationSchema] = Field(..., description="從 ER 圖譜查詢到的人際/地緣脈絡")
    chapter_summaries: List[str] = Field(..., description="相關章節的歸納摘要")

class KnowledgePayloadSchema(BaseModel):
    topic: str
    dimension_vectors: Dict[str, float] = Field(..., description="知識體系的多維度向量空間坐標")
    nodes: List[Dict[str, str]]
    edges: List[Dict[str, str]]
```

### B. 核心 API 路由介面

* **`POST /api/v1/init`**
  - **功能**：當文本被提供後，起始建置資料庫、切片並初始化向量與圖譜。
  - **Request Body**：
    ```json
    {
      "document_title": "鹿鼎記",
      "source_text_path": "/data/history_texts/ludingji.txt",
      "chunk_size": 800
    }
    ```
  - **Response**：
    ```json
    {
      "status": "success",
      "message": "系統初始化成功",
      "doc_id": 1,
      "total_chunks": 1420
    }
    ```

* **`POST /api/v1/query` (JIT 按需回答與動態建置接口)**
  - **功能**：智慧運用者查詢知識體系。若發現體系缺漏，則按需動態觸發 Agent 對抗提問、聯網查詢並完成建置。
  - **Request Body**：
    ```json
    {
      "user_query": "分析韋小寶如何利用資訊隔離進行多重身份防穿幫？"
    }
    ```
  - **Response**：
    ```json
    {
      "status": "success",
      "answer": "韋小寶利用資訊延遲與隔離策略來應對衝突身分...",
      "knowledge_atlas_ref": {
        "id": 12,
        "subject": "韋小寶多重身分資訊隔離演算法",
        "semantic_summary": "韋小寶在紫禁城與天地會之間利用快取失效策略維持資訊不對稱..."
      }
    }
    ```

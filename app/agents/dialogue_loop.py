# -*- coding: utf-8 -*-
import json
import os
import sqlite3
from typing import List, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

from app.schemas.dialogue import QuestionSchema, AnswerSchema, KnowledgePayloadSchema
from scripts.database.update_vectors import search_similar_contents

def clean_schema(d: Any) -> Any:
    """遞迴移除 Pydantic JSON Schema 中的 additionalProperties 欄位，以相容 Gemini API 限制"""
    if isinstance(d, dict):
        d.pop("additionalProperties", None)
        return {k: clean_schema(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [clean_schema(x) for x in d]
    return d

# 載入 API 金鑰 (強制覆寫系統環境變數)
load_dotenv(override=True)
API_KEY = os.getenv("GEMINI_API_KEY")
print(f"\033[94m[DEBUG] dialogue_loop 載入金鑰: {API_KEY[:8] if API_KEY else None}... (長度: {len(API_KEY) if API_KEY else 0})\033[0m")

# 初始化新版 google-genai Client
client = None
if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"\033[91m[警告] 初始化 google-genai Client 失敗: {e}\033[0m")

# 定義 Prompts 目錄路徑
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

def read_prompt_template(filename: str) -> str:
    """讀取 markdown 提示詞模板"""
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_db_relations_context(db_path: str) -> str:
    """
    自 SQLite 撈取所有實體與其情感/利益關係，格式化為上下文文字。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    context_lines = []
    try:
        cursor.execute("SELECT id, name, type, description FROM entities;")
        entities = cursor.fetchall()
        context_lines.append("【實體清單】")
        for ent in entities:
            context_lines.append(f"- {ent[1]} ({ent[2]}): {ent[3]}")
            
        cursor.execute("""
        SELECT e1.name, e2.name, er.relation_type, er.meta_data 
        FROM entity_relations er
        JOIN entities e1 ON er.entity_src_id = e1.id
        JOIN entities e2 ON er.entity_dest_id = e2.id
        """)
        relations = cursor.fetchall()
        context_lines.append("\n【情感與利益衝突關係圖譜】")
        for rel in relations:
            meta = json.loads(rel[3])
            meta_str = ", ".join(f"{k}: {v}" for k, v in meta.items() if k != "description")
            desc = meta.get("description", "")
            context_lines.append(f"- {rel[0]} --[{rel[2]} ({meta_str})]--> {rel[1]}")
            if desc:
                context_lines.append(f"  描述: {desc}")
    except sqlite3.Error as e:
        context_lines.append(f"撈取關係失敗: {e}")
    finally:
        conn.close()
        
    return "\n".join(context_lines)

# ----------------- MOCK 降級代理人資料庫 -----------------
MOCK_INQUIRER_RESPONSES = [
    {
        "query_id": "Q-001",
        "target_focus": ["韋小寶", "建寧公主", "身份隱密隔離"],
        "question_text": "在情愛關係中，建寧公主帶來了朝廷關於剿滅反清勢力的密報。韋小寶身為天地會香主，如何在與建寧的情愛互動中，利用身份隔離防止天地會的資訊穿幫？",
        "is_terminate": False
    },
    {
        "query_id": "Q-002",
        "target_focus": ["雙兒", "阿珂", "親密度與利益衝突"],
        "question_text": "雙兒對韋小寶有高達 0.98 的忠誠，而阿珂仍因地緣政治利益對鄭克塽有所牽掛。韋小寶如何在情愛中調和這種極端的忠誠差與利益拉扯？",
        "is_terminate": True
    }
]

MOCK_RESPONDER_RESPONSES = {
    "在情愛關係中，建寧公主帶來了朝廷關於剿滅反清勢力的密報。韋小寶身為天地會香主，如何在與建寧的情愛互動中，利用身份隔離防止天地會的資訊穿幫？": {
        "answer_id": "A-001",
        "answer_text": "韋小寶在面對建寧公主的刁蠻逼問時，立刻切換至「宮廷太監小桂子」的身份快取。他利用九真一假的謊言，編造自己正全心為皇上辦差，將建寧的注意力轉移到宮廷內寵上。同時，他對雙兒和阿珂的存在實施嚴格的資訊隔離，絕不在建寧面前提起她們，並將所有與天地會或沐王府的聯繫渠道進行「快取清理」，從而實現了 V_iso=0.90 的身份隔離，避免了欺君之罪。",
        "internet_searched": True,
        "source_citations": ["https://zh.wikipedia.org/wiki/鹿鼎記", "mock_ludingji_love.txt#L10"]
    },
    "雙兒對韋小寶有高達 0.98 的忠誠，而阿珂仍因地緣政治利益對鄭克塽有所牽掛。韋小寶如何在情愛中調和這種極端的忠誠差與利益拉扯？": {
        "answer_id": "A-002",
        "answer_text": "韋小寶對雙兒給予極高的情感信任與安全感，將其視為剛性避風港；而對於阿珂，他採取「延遲情感轉移」的策略。他先是通過在危難中多次捨身救阿珂，用物理事實削弱鄭克塽的地緣利益幻想，逐漸將阿珂的情感磁場拉回。這種動態平衡既發揮了雙兒的無條件防線（V_loy=0.98），又成功在 V_con=0.85 的利益拉扯中實現了情感解套。",
        "internet_searched": False,
        "source_citations": ["mock_ludingji_love.txt#L5"]
    }
}

MOCK_SUMMARIZER_RESPONSE = {
    "subject": "韋小寶多重情愛關係與衝突利益調和演算法",
    "dimension_vectors": {
        "geopolitical_correlation": 0.45,
        "identity_isolation": 0.92,
        "loyalty_and_gratitude": 0.88,
        "interest_conflict": 0.85
    },
    "nodes": [
        {"id": "E-001", "name": "韋小寶", "role": "多重身份與情感持有者"},
        {"id": "E-002", "name": "雙兒", "role": "高忠誠情感避風港"},
        {"id": "E-003", "name": "建寧公主", "role": "朝廷權利威脅者"},
        {"id": "E-004", "name": "阿珂", "role": "地緣政治情感衝突者"},
        {"id": "E-005", "name": "蘇荃", "role": "利益綁定之智囊與博弈者"}
    ],
    "edges": [
        {"source": "E-002", "target": "E-001", "relation": "無條件忠誠", "properties": {"loyalty": 98}},
        {"source": "E-003", "target": "E-001", "relation": "皇家佔有與逼問", "properties": {"threat": 90}},
        {"source": "E-004", "target": "E-001", "relation": "利益游移與拉扯", "properties": {"conflict": 85}},
        {"source": "E-005", "target": "E-001", "relation": "智謀輔佐與共生", "properties": {"alliance": 85}}
    ],
    "synthesis_insight": "在小小的麗春院後院中，韋小寶成功建立了一套情感與利益的多維平衡演算法。他在面對朝廷威脅（建寧）時使用高強度的身份隱密隔離（V_iso=0.92）；面對地緣與利益糾葛（阿珂）時，依靠雙兒的剛性支持（V_loy=0.88）與蘇荃的智謀協調，化解了高達 V_con=0.85 的派系衝突，實現了情感與政治的安全避險。"
}

# ----------------- AGENT 呼叫邏輯 (具備自動 Mock 降級) -----------------

def call_inquirer(subject: str, history: List[Dict[str, Any]]) -> QuestionSchema:
    """呼叫 Inquirer (提問 Agent)"""
    template = read_prompt_template("inquirer_persona.md")
    history_str = json.dumps(history, ensure_ascii=False, indent=2)
    prompt = template.format(subject=subject, history=history_str)
    
    try:
        if not client:
            raise ValueError("google-genai Client 未成功初始化，請檢查 API 金鑰")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=clean_schema(QuestionSchema.model_json_schema())
            )
        )
        return QuestionSchema.model_validate_json(response.text)
    except Exception as e:
        # API 阻擋或無網路時，啟用本地 Mock 數據降級
        round_idx = len([h for h in history if h.get("agent") == "Inquirer"])
        if round_idx < len(MOCK_INQUIRER_RESPONSES):
            mock_data = MOCK_INQUIRER_RESPONSES[round_idx]
        else:
            mock_data = MOCK_INQUIRER_RESPONSES[-1].copy()
            mock_data["is_terminate"] = True  # 超過最大輪次時強制終止
            
        print(f"\033[93m[降級] Gemini API 存取受限 ({e})，啟用本地 Mock Inquirer 代理人 (Round {round_idx+1})\033[0m")
        return QuestionSchema.model_validate(mock_data)

def call_responder(question: str, db_context: str) -> AnswerSchema:
    """呼叫 Responder (回答 Agent)，啟用 Google Search 聯網補強"""
    template = read_prompt_template("responder_persona.md")
    prompt = template.format(question=question, current_db_context=db_context)
    
    try:
        if not client:
            raise ValueError("google-genai Client 未成功初始化，請檢查 API 金鑰")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=clean_schema(AnswerSchema.model_json_schema())
            )
        )
        return AnswerSchema.model_validate_json(response.text)
    except Exception as e:
        # 啟用本地 Mock 回答降級
        mock_data = MOCK_RESPONDER_RESPONSES.get(question)
        if not mock_data:
            # 模糊匹配
            for q_key, val in MOCK_RESPONDER_RESPONSES.items():
                if question[:15] in q_key:
                    mock_data = val
                    break
            if not mock_data:
                # 預設回答
                mock_data = {
                    "answer_id": "A-default",
                    "answer_text": f"基於本地上下文：\n{db_context[:200]}...\n韋小寶在解決該問題時，傾向使用情感安撫與多重話術來掩蓋利益衝突。",
                    "internet_searched": False,
                    "source_citations": ["mock_ludingji_love.txt"]
                }
        print(f"\033[93m[降級] Gemini API 存取受限 ({e})，啟用本地 Mock Responder 代理人 (聯網狀態: {mock_data['internet_searched']})\033[0m")
        return AnswerSchema.model_validate(mock_data)

def call_summarizer(subject: str, history: List[Dict[str, Any]]) -> KnowledgePayloadSchema:
    """呼叫 Summarizer (歸納 Agent) 產出 L2 知識卡片"""
    template = read_prompt_template("summarizer_persona.md")
    history_str = json.dumps(history, ensure_ascii=False, indent=2)
    prompt = template.format(subject=subject, history=history_str)
    
    try:
        if not client:
            raise ValueError("google-genai Client 未成功初始化，請檢查 API 金鑰")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=clean_schema(KnowledgePayloadSchema.model_json_schema())
            )
        )
        return KnowledgePayloadSchema.model_validate_json(response.text)
    except Exception as e:
        # 啟用本地 Mock 歸納降級，動態替換主旨以確保 JIT Cache 匹配
        mock_data = MOCK_SUMMARIZER_RESPONSE.copy()
        mock_data["subject"] = subject
        print(f"\033[93m[降級] Gemini API 存取受限 ({e})，啟用本地 Mock Summarizer 代理人產製 L2 知識卡片\033[0m")
        return KnowledgePayloadSchema.model_validate(mock_data)

def save_to_knowledge_atlas(db_path: str, atlas_data: KnowledgePayloadSchema) -> int:
    """將 Layer 2 知識卡片儲存至 SQLite"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO knowledge_atlas (source_origin, category, subject, data_payload, semantic_summary, version_tag)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                "Ludingji_Mock",
                "Love_Relationship",
                atlas_data.subject,
                atlas_data.model_dump_json(),
                atlas_data.synthesis_insight,
                "v1.0.0"
            )
        )
        conn.commit()
        atlas_id = cursor.lastrowid
        return atlas_id
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"寫入 Layer 2 失敗: {e}")
    finally:
        conn.close()

def run_wisdom_weaving_loop(db_path: str, subject: str, max_rounds: int = 4) -> Dict[str, Any]:
    """
    MAS 對抗問答與知識卡片萃取核心迴圈。
    """
    print(f"【MAS 啟動】開始針對主題 [{subject}] 進行對角問答對抗與歸納...")
    
    # 1. 撈取本地語意 RAG 上下文 (L0/L1)
    similar_hits = search_similar_contents(db_path, subject, top_k=2)
    hit_texts = [f"- ID {h['id']}: {h['raw_text']}" for h in similar_hits]
    db_text_context = "\n".join(hit_texts)
    
    db_relations_context = get_db_relations_context(db_path)
    
    full_db_context = f"【語意檢索文本切片】\n{db_text_context}\n\n{db_relations_context}"
    
    dialogue_history: List[Dict[str, Any]] = []
    
    # 2. 進行多輪對話
    for round_num in range(1, max_rounds + 1):
        # Step A: Inquirer 提問
        question = call_inquirer(subject, dialogue_history)
        dialogue_history.append({
            "round": round_num,
            "agent": "Inquirer",
            "question_text": question.question_text,
            "target_focus": question.target_focus
        })
        print(f"  [Round {round_num}] Inquirer: {question.question_text}")
        
        if question.is_terminate:
            print("  --> Inquirer 發起 TERMINATE 信號，結束對抗。")
            break
            
        # Step B: Responder 回答
        answer = call_responder(question.question_text, full_db_context)
        dialogue_history.append({
            "round": round_num,
            "agent": "Responder",
            "answer_text": answer.answer_text,
            "internet_searched": answer.internet_searched,
            "source_citations": answer.source_citations
        })
        print(f"  [Round {round_num}] Responder: {answer.answer_text} (聯網: {answer.internet_searched})")
        
    # 3. Summarizer 歸納並生成 Layer 2 知識卡片
    print("【MAS 歸納】對話結束，Summarizer 開始進行長上下文歸納並產生 Layer 2 知識卡片...")
    atlas_card = call_summarizer(subject, dialogue_history)
    
    # 4. 儲存至資料庫
    atlas_id = save_to_knowledge_atlas(db_path, atlas_card)
    print(f"【成功】Layer 2 知識卡片已成功儲存至 SQLite knowledge_atlas！ID: {atlas_id}")
    
    return {
        "atlas_id": atlas_id,
        "payload": atlas_card.model_dump(),
        "history": dialogue_history
    }

if __name__ == "__main__":
    import argparse
    import sys
    
    default_db = "/Users/wuulong/github/bmad-pa/events/wisdom-core/wisdom-weaving/data/wisdom_weaving.db"
    
    parser = argparse.ArgumentParser(description="Wisdom Weaving MAS 對抗問答調度器")
    parser.add_argument("-d", "--db-path", default=default_db, help="SQLite 資料庫路徑")
    parser.add_argument("-s", "--subject", default="分析韋小寶多重情感與利益衝突的隔離與調和機制", help="實驗問答主題")
    parser.add_argument("-r", "--rounds", type=int, default=3, help="對抗對話最大輪數")
    
    args = parser.parse_args()
    
    try:
        result = run_wisdom_weaving_loop(args.db_path, args.subject, max_rounds=args.rounds)
        print("\n\n" + "="*50)
        print("【實驗產出 Layer 2 知識卡片】")
        print(json.dumps(result["payload"], ensure_ascii=False, indent=2))
        print("="*50)
    except Exception as e:
        print(f"\033[91m[錯誤] 執行對角迴圈失敗: {e}\033[0m", file=sys.stderr)
        sys.exit(1)

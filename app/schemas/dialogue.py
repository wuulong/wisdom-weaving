# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class QuestionSchema(BaseModel):
    query_id: str = Field(description="提問唯一 ID")
    target_focus: List[str] = Field(description="本次提問關注的實體或概念點")
    question_text: str = Field(description="具體的批判性提問內容")
    is_terminate: bool = Field(description="若認為當前概念已挖掘完畢，設為 True 以終止對話")

class AnswerSchema(BaseModel):
    answer_id: str = Field(description="回答唯一 ID")
    answer_text: str = Field(description="結合本地 DB 與聯網查詢後的詳細解答")
    internet_searched: bool = Field(description="是否執行了聯網補強")
    source_citations: List[str] = Field(description="參考的原始文獻或聯網 URL")

class KnowledgePayloadSchema(BaseModel):
    subject: str = Field(..., description="專題知識主題名稱")
    dimension_vectors: Dict[str, float] = Field(..., description="知識體系在多維向量空間中的座標 (V_geo, V_iso, V_loy, V_con)")
    nodes: List[Dict[str, str]] = Field(..., description="提取出的關鍵實體節點")
    edges: List[Dict[str, Any]] = Field(..., description="實體間的關係邊及其屬性 (如親密值、恩情值)")
    synthesis_insight: str = Field(..., description="大歷史語義綜整分析與長文本摘要")

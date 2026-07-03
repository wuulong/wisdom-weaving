import sys
import json
import sqlite3
import os
import re

# Add local path to import paper_scout functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import paper_scout
except ImportError:
    # Fallback if import fails during standard path resolution
    import scripts.research.paper_scout as paper_scout

DB_PATH = "/Users/wuulong/github/bmad-pa/data/research/Research_Artifacts.db"

def list_tools():
    """Return list of available MCP tools according to spec."""
    return [
        {
            "name": "scout_online_papers",
            "description": "搜尋線上文獻庫（ArXiv 與 Semantic Scholar），獲取非結構化文獻元數據、摘要與連結，自動具備離線降級模擬。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "論文搜尋關鍵字，支援英文與布林邏輯，如 'QMEMS resonator 5G'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "每單一來源最大返回筆數，預設為 5，最大值為 10",
                        "default": 5
                    },
                    "source": {
                        "type": "string",
                        "enum": ["arxiv", "sem-scholar", "all"],
                        "description": "檢索來源，預設為 'all'",
                        "default": "all"
                    },
                    "force_mock": {
                        "type": "boolean",
                        "description": "強制啟用本地離線模擬模式（適合測試環境）",
                        "default": False
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "save_papers_to_local_db",
            "description": "將選出或檢索到的論文數據沉澱寫入實驗室本地 SQLite 資料庫 (Research_Artifacts.db) 中。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "papers": {
                        "type": "array",
                        "description": "包含一或多篇論文結構的列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "paper_id": { "type": "string", "description": "唯一識別鍵名，如 'arxiv_2401_1234'" },
                                "title": { "type": "string" },
                                "authors": { "type": "string" },
                                "year": { "type": "integer" },
                                "core_method": { "type": "string" },
                                "key_parameters": { "type": "object", "description": "動態 RF/物理/製程參數鍵值對" },
                                "simulation_result": { "type": "string" },
                                "critique_score": { "type": "object", "description": "紅軍自審評分與 vulnerabilities" }
                            },
                            "required": ["paper_id", "title", "authors", "year", "core_method"]
                        }
                    }
                },
                "required": ["papers"]
            }
        },
        {
            "name": "query_local_research_db",
            "description": "對本地 SQLite 資料庫 (Research_Artifacts.db) 的論文資料進行唯讀 SQL SELECT 語義查詢與分析。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "唯讀 SQLite SELECT 語句，如 'SELECT paper_id, title FROM papers WHERE year >= 2025'"
                    }
                },
                "required": ["sql_query"]
            }
        }
    ]

def handle_scout(arguments):
    query = arguments.get("query")
    limit = arguments.get("limit", 5)
    source = arguments.get("source", "all")
    force_mock = arguments.get("force_mock", False)
    
    papers = []
    warning = None
    
    if force_mock:
        papers = paper_scout.get_mock_results(query, limit)
        warning = "強制使用【離線模擬模式（Force Mock Mode）】"
    else:
        # Standard execution with auto-fallback on error
        # We manually intercept potential exceptions to pass warning back to LLM
        arxiv_failed = False
        sem_failed = False
        
        if source in ["arxiv", "all"]:
            try:
                arxiv_results = paper_scout.search_arxiv(query, limit, try_mock_on_fail=False)
                if not arxiv_results:
                    arxiv_failed = True
                papers.extend(arxiv_results)
            except Exception:
                arxiv_failed = True
                
        if source in ["sem-scholar", "all"]:
            try:
                sem_results = paper_scout.search_semantic_scholar(query, limit, try_mock_on_fail=False)
                if not sem_results:
                    sem_failed = True
                papers.extend(sem_results)
            except Exception:
                sem_failed = True
                
        # Trigger fallback if both failed or if sandbox restricted
        if (source == "all" and arxiv_failed and sem_failed) or (source == "arxiv" and arxiv_failed) or (source == "sem-scholar" and sem_failed):
            papers = paper_scout.get_mock_results(query, limit)
            warning = "網路連線異常或遭遇 API 頻率限制，已自動安全退避至【離線模擬模式 (Offline Mock Mode)】"
            
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"papers": papers, "warning": warning}, ensure_ascii=False, indent=2)
            }
        ]
    }

def handle_save_db(arguments):
    papers = arguments.get("papers", [])
    
    if not os.path.exists(DB_PATH):
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Error: SQLite database not found at {DB_PATH}. Please run setup_research_db.py first."}]
        }
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    success_count = 0
    
    for p in papers:
        try:
            cursor.execute("""
            INSERT OR REPLACE INTO papers (
                paper_id, title, authors, year, core_method, key_parameters, simulation_result, critique_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p['paper_id'],
                p['title'],
                p['authors'],
                p['year'],
                p['core_method'],
                json.dumps(p.get('key_parameters', {}), ensure_ascii=False),
                p.get('simulation_result', ''),
                json.dumps(p.get('critique_score', {}), ensure_ascii=False)
            ))
            success_count += 1
        except Exception as e:
            conn.rollback()
            conn.close()
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Error saving paper {p.get('title', '')}: {str(e)}"}]
            }
            
    conn.commit()
    conn.close()
    return {
        "content": [{"type": "text", "text": f"Successfully saved {success_count} papers to local research database."}]
    }

def handle_query_db(arguments):
    sql_query = arguments.get("sql_query", "").strip()
    
    # Security check: strictly read-only SELECT
    is_safe = re.match(r'^\s*SELECT\b', sql_query, re.IGNORECASE)
    has_unsafe = re.search(r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE)\b', sql_query, re.IGNORECASE)
    
    if not is_safe or has_unsafe:
        return {
            "isError": True,
            "content": [{"type": "text", "text": "Security Error: Only SELECT read-only statements are permitted for database querying."}]
        }
        
    if not os.path.exists(DB_PATH):
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Error: SQLite database not found at {DB_PATH}."}]
        }
        
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        
        results = []
        for r in rows:
            results.append(dict(r))
            
        conn.close()
        return {
            "content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False, indent=2)}]
        }
    except Exception as e:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Database Error: {str(e)}"}]
        }

def respond(response_id, result=None, error=None):
    """Write standard JSON-RPC response to stdout."""
    res = {"jsonrpc": "2.0", "id": response_id}
    if error:
        res["error"] = error
    else:
        res["result"] = result
        
    sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def main():
    # Clear sys.stderr buffer to avoid log contamination in some IDEs
    sys.stderr.write("Paper Scout MCP Server starting...\n")
    sys.stderr.flush()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            if method == "initialize":
                respond(req_id, {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "paper-scout-mcp",
                        "version": "1.0.0"
                    }
                })
            elif method == "tools/list":
                respond(req_id, {"tools": list_tools()})
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "scout_online_papers":
                    res = handle_scout(arguments)
                elif tool_name == "save_papers_to_local_db":
                    res = handle_save_db(arguments)
                elif tool_name == "query_local_research_db":
                    res = handle_query_db(arguments)
                else:
                    res = {
                        "isError": True,
                        "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
                    }
                respond(req_id, res)
            else:
                # Unsupported method
                if req_id is not None:
                    respond(req_id, error={"code": -32601, "message": f"Method not found: {method}"})
        except Exception as e:
            sys.stderr.write(f"Error handling request: {str(e)}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()

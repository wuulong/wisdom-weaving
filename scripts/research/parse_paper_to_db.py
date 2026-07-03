import os
import sqlite3
import json
import subprocess
import re

FAB_CMD = "/Users/wuulong/github/bmad-pa/fab"
DB_PATH = "/Users/wuulong/github/bmad-pa/data/research/Research_Artifacts.db"
PAPER_PATH = "/Users/wuulong/github/bmad-pa/data/research/sample_paper_marker_output.md"

def extract_json_from_text(text):
    """Robustly extract JSON string from LLM output."""
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_text = ansi_escape.sub('', text)
    
    # Strip potential headers/footers in fab output
    clean_lines = []
    for line in clean_text.split('\n'):
        l = line.strip()
        if not l: continue
        if "Gemini 回覆" in l: continue
        if "MCP issues" in l: continue
        if "Task" in l: continue
        if "Gemini 正在思考" in l: continue
        clean_lines.append(line)
    
    joined_text = "\n".join(clean_lines).strip()
    
    # Find JSON block
    json_match = re.search(r'\{.*\}', joined_text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return joined_text

def parse_paper():
    if not os.path.exists(PAPER_PATH):
        print(f"❌ Error: Sample paper not found at {PAPER_PATH}")
        return
        
    print(f"📖 Reading sample paper: {PAPER_PATH}")
    with open(PAPER_PATH, 'r', encoding='utf-8') as f:
        paper_content = f.read()
        
    prompt = f"""
你是一位頂尖的 RF-MEMS (射頻微機電系統) 與學術資料結構化專家。請將以下這篇學術論文（已轉為 Markdown，包含 LaTeX 公式）進行「硬核數據萃取」與「紅軍自審評估」。

論文內容：
\"\"\"
{paper_content}
\"\"\"

請將其結構化轉譯，並且**只輸出一個合法的 JSON 物件**，不要有任何前言後語（如「好的，為您生成...」），也不要用 ```json 或 ``` 標記包裝。

JSON 結構要求（鍵名必須精確對應）：
{{
  "paper_id": "請生成一個簡短且具識別度的鍵，如 QMEMS_HighQ_Resonator_2026",
  "title": "論文完整標題",
  "authors": "作者清單",
  "year": 論文年份 (整數),
  "core_method": "一句話總結其核心物理或結構方法",
  "key_parameters": {{
    "請提取論文中出現的所有關鍵 RF 參數": "以字串儲存，如 'f0': '28.5 GHz', 'Q': '12,000', 'IL': '-1.8 dB'"
  }},
  "simulation_result": "摘要其實驗或模擬結果",
  "critique_score": {{
    "vulnerabilities": ["列出論文中提到的關鍵缺點、脆弱點或物理瓶頸，如 TCF 溫度敏感性或功率上限"],
    "reviewer_score": 8.5,
    "critic_notes": "教授或審稿人視角的批判性備註"
  }}
}}
"""

    print("🤖 呼叫 Gemini 進行硬核數據萃取與紅軍自審...")
    try:
        result = subprocess.check_output(
            [FAB_CMD, "ask", f"--question={prompt.strip()}"], 
            text=True, 
            stderr=subprocess.STDOUT
        )
        
        json_str = extract_json_from_text(result)
        
        # Verify JSON validity
        parsed_data = json.loads(json_str)
        print("✅ 成功萃取結構化數據！")
        print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
        
        # Write to SQLite
        save_to_db(parsed_data)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Subprocess error calling fab CLI: {e.output}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error. Output was:\n{result}\nError: {e}")
    except Exception as e:
        print(f"❌ General error: {e}")

def save_to_db(data):
    print(f"💾 正在將數據沉澱至 SQLite 資料庫: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT OR REPLACE INTO papers (
        paper_id, title, authors, year, core_method, key_parameters, simulation_result, critique_score, meta_data
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['paper_id'],
        data['title'],
        data['authors'],
        data['year'],
        data['core_method'],
        json.dumps(data['key_parameters'], ensure_ascii=False),
        data['simulation_result'],
        json.dumps(data['critique_score'], ensure_ascii=False),
        json.dumps({"parsed_at": "2026-05-20", "parser_engine": "Gemini-CLI", "paper_format": "Markdown-with-LaTeX"}, ensure_ascii=False)
    ))
    
    conn.commit()
    conn.close()
    print("🎉 資料落庫成功！")
    print("-" * 60)
    verify_database()

def verify_database():
    print("🔍 驗證 SQLite 資料庫內容：")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM papers")
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"📌 [ID]: {row['paper_id']}")
        print(f"   [標題]: {row['title']}")
        print(f"   [作者]: {row['authors']} ({row['year']})")
        print(f"   [方法]: {row['core_method']}")
        print(f"   [關鍵參數]: {row['key_parameters']}")
        print(f"   [模擬結果]: {row['simulation_result']}")
        print(f"   [紅軍評估]: {row['critique_score']}")
        print("-" * 60)
        
    conn.close()

if __name__ == "__main__":
    parse_paper()

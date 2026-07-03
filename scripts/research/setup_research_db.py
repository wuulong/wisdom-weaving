import os
import sqlite3

def setup_db():
    db_path = "/Users/wuulong/github/bmad-pa/data/research/Research_Artifacts.db"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    print(f"Initializing SQLite database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the papers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        paper_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        authors TEXT,
        year INTEGER,
        core_method TEXT,
        key_parameters TEXT, -- JSON string storing dynamic key parameters
        simulation_result TEXT,
        critique_score TEXT, -- JSON string storing critique details & reviewer-like feedback
        meta_data TEXT       -- JSON string storing supplementary metadata (extensibility envelope)
    );
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    setup_db()

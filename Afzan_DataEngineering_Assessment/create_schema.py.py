import sqlite3

def create_drilling_schema(db_path='drilling_operations.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Force foreign key enforcement in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. PACs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pacs (
        pac_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pac_name TEXT NOT NULL UNIQUE
    );
    ''')
    
    # 2. Regions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS regions (
        region_id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_name TEXT NOT NULL UNIQUE
    );
    ''')
    
    # 3. Fields Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fields (
        field_id INTEGER PRIMARY KEY AUTOINCREMENT,
        field_name TEXT NOT NULL,
        pac_id INTEGER,
        region_id INTEGER,
        UNIQUE(field_name, pac_id, region_id),
        FOREIGN KEY (pac_id) REFERENCES pacs(pac_id) ON DELETE CASCADE,
        FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE
    );
    ''')
    
    # 4. Rigs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rigs (
        rig_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rig_name TEXT NOT NULL,
        rig_type TEXT,
        UNIQUE(rig_name, rig_type)
    );
    ''')
    
    # 5. Wells Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wells (
        well_id INTEGER PRIMARY KEY AUTOINCREMENT,
        well_name TEXT NOT NULL UNIQUE,
        well_type TEXT,
        field_id INTEGER,
        water_depth REAL,
        FOREIGN KEY (field_id) REFERENCES fields(field_id) ON DELETE CASCADE
    );
    ''')
    
    # 6. Well Operations (Campaign Dimension)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS well_operations (
        operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        well_id INTEGER NOT NULL,
        rig_id INTEGER NOT NULL,
        operation_year INTEGER,
        afe_cost REAL,
        afe_days REAL,
        spud_date TEXT,
        well_start_datetime TEXT,
        well_end_datetime TEXT,
        UNIQUE(well_id, rig_id, operation_year, spud_date),
        FOREIGN KEY (well_id) REFERENCES wells(well_id) ON DELETE CASCADE,
        FOREIGN KEY (rig_id) REFERENCES rigs(rig_id) ON DELETE CASCADE
    );
    ''')
    
    # 7. Operational Reports (Transactional Ledger)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS operational_reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_id INTEGER NOT NULL,
        report_type TEXT NOT NULL,
        document_name TEXT,
        document_date TEXT,
        submitted_at TEXT,
        submitted_by TEXT,
        final_cost REAL,
        final_days REAL,
        well_npt_percentage_wow REAL,
        well_npt_percentage REAL,
        completion_cost_plan REAL,
        completion_cost_actual REAL,
        drilling_plan_wcpf REAL,
        drilling_actual_wcpf REAL,
        FOREIGN KEY (operation_id) REFERENCES well_operations(operation_id) ON DELETE CASCADE
    );
    ''')
    
    conn.commit()
    print(f"Database initialized successfully at relative path: '{db_path}'")
    conn.close()

if __name__ == '__main__':
    create_drilling_schema()
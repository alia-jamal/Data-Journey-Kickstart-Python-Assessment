import sqlite3

def create_database():
    # Connect to the SQLite database (this creates the file automatically if it doesn't exist)
    conn = sqlite3.connect('drilling_operations.db')
    cursor = conn.cursor()
    
    # Enforce foreign key constraints to maintain data integrity
    cursor.execute("PRAGMA foreign_keys = ON;")

    print("Building database tables based on your updated 3NF model...")

    # 1. Companies Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            company_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL UNIQUE
        );
    ''')

    # 2. Regions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS regions (
            region_id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_name TEXT NOT NULL UNIQUE
        );
    ''')

    # 3. Fields Table (With water_depth included)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fields (
            field_id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_id INTEGER,
            field_name TEXT NOT NULL,
            water_depth REAL,
            FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE SET NULL
        );
    ''')

    # 4. Rigs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rigs (
            rig_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rig_name TEXT NOT NULL UNIQUE,
            rig_type TEXT
        );
    ''')

    # 5. Wells Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wells (
            well_id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER,
            company_id INTEGER,
            well_name TEXT NOT NULL,
            well_type TEXT,
            FOREIGN KEY (field_id) REFERENCES fields(field_id) ON DELETE SET NULL,
            FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE SET NULL
        );
    ''')

    # 6. Reports Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_id INTEGER,
            report_type TEXT,
            document_name TEXT,
            document_date TEXT,
            submitted_at TEXT,
            submitted_by TEXT,
            FOREIGN KEY (well_id) REFERENCES wells(well_id) ON DELETE CASCADE
        );
    ''')

    # 7. Well Operations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS well_operations (
            operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_id INTEGER,
            rig_id INTEGER,
            year INTEGER,
            afe_cost REAL,
            afe_days INTEGER,
            spud_date TEXT,
            well_start_datetime TEXT,
            well_end_datetime TEXT,
            final_cost REAL,
            final_days INTEGER,
            well_npt_percentage_wow REAL,
            well_npt_percentage REAL,
            completion_cost_plan REAL,
            completion_cost_actual REAL,
            drilling_plan_wcpf REAL,
            drilling_actual_wcpf REAL,
            FOREIGN KEY (well_id) REFERENCES wells(well_id) ON DELETE CASCADE,
            FOREIGN KEY (rig_id) REFERENCES rigs(rig_id) ON DELETE SET NULL
        );
    ''')

    conn.commit()
    conn.close()
    print("Success! 'drilling_operations.db' is ready with empty tables.")

if __name__ == "__main__":
    create_database()
import sqlite3

# Design Notes:
# 1. PAC and Region are master tables.
# 2. Field belongs to a PAC and Region.
# 3. Well belongs to a Field.
# 4. WellOperation stores drilling/completion metrics. WellOperation is separated from Well because operational metrics such as costs, days, and NPT percentages can vary across different operations for the same well. This design allows for multiple operations per well without data redundancy.
# 5. A WellOperation uses a Rig. Rig is linked to WellOperation instead of Well because rigs can be shared across wells and operations.
# 6. Reports are generated for WellOperations. A single WellOperation may generate multiple reports, therefore Report is designed as a separate table with a foreign key to WellOperation in order to prevent duplicate operational data.
# 7. Design follows Third Normal Form (3NF).

DB_NAME = "drilling_operations.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")

# PAC
cursor.execute("""
CREATE TABLE IF NOT EXISTS PAC (
    pac_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pac_name TEXT NOT NULL UNIQUE
);
""")

# Region
cursor.execute("""
CREATE TABLE IF NOT EXISTS Region (
    region_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_name TEXT NOT NULL UNIQUE
);
""")

# Field
cursor.execute("""
CREATE TABLE IF NOT EXISTS Field (
    field_id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name TEXT NOT NULL,
    pac_id INTEGER NOT NULL,
    region_id INTEGER NOT NULL,
    FOREIGN KEY (pac_id) REFERENCES PAC(pac_id),
    FOREIGN KEY (region_id) REFERENCES Region(region_id)
);
""")

# Well
cursor.execute("""
CREATE TABLE IF NOT EXISTS Well (
    well_id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER NOT NULL,
    well_name TEXT NOT NULL,
    well_type TEXT,
    spud_date DATETIME,
    water_depth DECIMAL(10,2),
    FOREIGN KEY (field_id) REFERENCES Field(field_id)
);
""")

# Rig
cursor.execute("""
CREATE TABLE IF NOT EXISTS Rig (
    rig_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rig_name TEXT NOT NULL,
    rig_type TEXT
);
""")

# WellOperation
cursor.execute("""
CREATE TABLE IF NOT EXISTS WellOperation (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    well_id INTEGER NOT NULL,
    rig_id INTEGER NOT NULL,
    operation_year INTEGER,
    well_start_datetime DATETIME,
    well_end_datetime DATETIME,
    afe_cost DECIMAL(18,2),
    afe_days DECIMAL(10,2),
    final_cost DECIMAL(18,2),
    final_days DECIMAL(10,2),
    npt_percentage DECIMAL(5,2),
    npt_percentage_wow DECIMAL(5,2),
    completion_cost_plan DECIMAL(18,2),
    completion_cost_actual DECIMAL(18,2),
    drilling_plan_wcpf DECIMAL(18,2),
    drilling_actual_wcpf DECIMAL(18,2),
    FOREIGN KEY (well_id) REFERENCES Well(well_id),
    FOREIGN KEY (rig_id) REFERENCES Rig(rig_id)
);
""")

# Report
cursor.execute("""
CREATE TABLE IF NOT EXISTS Report (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id INTEGER NOT NULL,
    report_type TEXT,
    document_name TEXT,
    document_date DATETIME,
    submitted_at DATETIME,
    submitted_by TEXT,
    FOREIGN KEY (operation_id)
        REFERENCES WellOperation(operation_id)
);
""")

conn.commit()
conn.close()

print(f"Database '{DB_NAME}' created successfully.")
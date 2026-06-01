import sqlite3

conn = sqlite3.connect("drilling_operations.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")

# -----------------------------
# REGIONS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS regions (
    region_id INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL
);
""")

# -----------------------------
# PAC
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS pac (
    pac_id INTEGER PRIMARY KEY,
    pac_name TEXT NOT NULL,
    region_id INTEGER NOT NULL,
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);
""")

# -----------------------------
# FIELDS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS fields (
    field_id INTEGER PRIMARY KEY,
    field_name TEXT NOT NULL,
    pac_id INTEGER NOT NULL,
    FOREIGN KEY (pac_id) REFERENCES pac(pac_id)
);
""")

# -----------------------------
# WELLS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS wells (
    well_id INTEGER PRIMARY KEY,
    well_name TEXT NOT NULL,
    well_type TEXT,
    field_id INTEGER NOT NULL,
    well_start_date DATETIME,
    well_end_date DATETIME,
    FOREIGN KEY (field_id) REFERENCES fields(field_id)
);
""")

# -----------------------------
# RIGS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS rigs (
    rig_id INTEGER PRIMARY KEY,
    rig_name TEXT NOT NULL,
    rig_type TEXT
);
""")

# -----------------------------
# WELL RIG ASSIGNMENT
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS well_rig_assignment (
    assignment_id INTEGER PRIMARY KEY,
    well_id INTEGER NOT NULL,
    rig_id INTEGER NOT NULL,
    start_date DATETIME,
    end_date DATETIME,
    FOREIGN KEY (well_id) REFERENCES wells(well_id),
    FOREIGN KEY (rig_id) REFERENCES rigs(rig_id)
);
""")

# -----------------------------
# REPORTS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    report_id INTEGER PRIMARY KEY,
    well_id INTEGER NOT NULL,
    report_type TEXT NOT NULL,
    year INTEGER,
    document_name TEXT,
    document_date DATETIME NOT NULL,
    submitted_at DATETIME,
    submitted_by TEXT,
    FOREIGN KEY (well_id) REFERENCES wells(well_id)
);
""")

# -----------------------------
# WELL OPERATIONS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS well_operations (
    operation_id INTEGER PRIMARY KEY,
    well_id INTEGER NOT NULL,
    assignment_id INTEGER,

    afe_cost REAL,
    afe_days INTEGER,
    final_cost REAL,
    final_days INTEGER,
    well_npt_percentage REAL,
    well_npt_percentage_wow REAL,

    FOREIGN KEY (well_id) REFERENCES wells(well_id),
    FOREIGN KEY (assignment_id) REFERENCES well_rig_assignment(assignment_id)
);
""")

# -----------------------------
# DRILLING OPERATIONS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS drilling (
    drilling_id INTEGER PRIMARY KEY,
    operation_id INTEGER NOT NULL UNIQUE,
    drilling_plan_wcpf REAL,
    drilling_actual_wcpf REAL,
    spud_date DATETIME,

    FOREIGN KEY (operation_id) REFERENCES well_operations(operation_id)
);
""")

# -----------------------------
# COMPLETION OPERATIONS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS completion (
    completion_id INTEGER PRIMARY KEY,
    operation_id INTEGER NOT NULL UNIQUE,
    completion_cost_plan REAL,
    completion_cost_actual REAL,

    FOREIGN KEY (operation_id) REFERENCES well_operations(operation_id)
);
""")

conn.commit()
conn.close()

print("Schema created successfully.")
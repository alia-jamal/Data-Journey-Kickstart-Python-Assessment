import pandas as pd
import sqlite3
import os

def run_etl():
    # Define relative file paths according to the assignment requirements
    csv_path = os.path.join('data', 'DataForAssessment.csv')
    db_path = 'drilling_operations.db'
    
    # Check if the CSV file exists before proceeding
    if not os.path.exists(csv_path):
        print(f"Error: Could not find dataset at {csv_path}. Please check your folder structure.")
        return

    print("--- 1. EXTRACT STAGE ---")
    df = pd.read_csv(csv_path)
    print(f"Successfully extracted {len(df)} rows from CSV data source.")

    print("\n--- 2. TRANSFORM & LOAD STAGE ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enforce foreign key constraints inside SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Helper clean functions to handle missing values (NaN) safely
    def clean_num(val): return float(val) if pd.notna(val) else None
    def clean_int(val): return int(val) if pd.notna(val) else None
    def clean_str(val): return str(val).strip() if pd.notna(val) else None

    # --- Table 1: Populate Companies (PAC) ---
    print("Loading companies table...")
    companies = df[['PacName']].dropna().drop_duplicates().rename(columns={'PacName': 'company_name'})
    for _, row in companies.iterrows():
        cursor.execute("INSERT OR IGNORE INTO companies (company_name) VALUES (?);", (clean_str(row['company_name']),))
    
    # --- Table 2: Populate Regions ---
    print("Loading regions table...")
    regions = df[['RegionName']].dropna().drop_duplicates().rename(columns={'RegionName': 'region_name'})
    for _, row in regions.iterrows():
        cursor.execute("INSERT OR IGNORE INTO regions (region_name) VALUES (?);", (clean_str(row['region_name']),))

    # --- Table 3: Populate Fields (With water_depth) ---
    print("Loading fields table...")
    fields_df = df[['FieldName', 'RegionName', 'WaterDepth']].drop_duplicates(subset=['FieldName'])
    for _, row in fields_df.iterrows():
        region_id = None
        if pd.notna(row['RegionName']):
            cursor.execute("SELECT region_id FROM regions WHERE region_name = ?;", (clean_str(row['RegionName']),))
            res = cursor.fetchone()
            if res: region_id = res[0]
            
        water_depth = clean_num(row['WaterDepth'])
        cursor.execute("INSERT INTO fields (region_id, field_name, water_depth) VALUES (?, ?, ?);", 
                       (region_id, clean_str(row['FieldName']), water_depth))

    # --- Table 4: Populate Rigs ---
    print("Loading rigs table...")
    rigs = df[['RigName', 'RigType']].dropna(subset=['RigName']).drop_duplicates(subset=['RigName'])
    for _, row in rigs.iterrows():
        rig_type = clean_str(row['RigType'])
        cursor.execute("INSERT OR IGNORE INTO rigs (rig_name, rig_type) VALUES (?, ?);", (clean_str(row['RigName']), rig_type))

    # --- Table 5: Populate Wells ---
    print("Loading wells table...")
    wells_df = df[['WellName', 'FieldName', 'PacName', 'WellType']].drop_duplicates(subset=['WellName'])
    for _, row in wells_df.iterrows():
        cursor.execute("SELECT field_id FROM fields WHERE field_name = ?;", (clean_str(row['FieldName']),))
        field_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT company_id FROM companies WHERE company_name = ?;", (clean_str(row['PacName']),))
        company_id = cursor.fetchone()[0]
        
        well_type = clean_str(row['WellType'])
        cursor.execute("INSERT INTO wells (field_id, company_id, well_name, well_type) VALUES (?, ?, ?, ?);",
                       (field_id, company_id, clean_str(row['WellName']), well_type))

    # --- Table 6: Populate Reports ---
    print("Loading reports table...")
    reports_df = df[['WellName', 'ReportType', 'DocumentName', 'DocumentDate', 'SubmittedAt', 'SubmittedBy']].dropna(subset=['ReportType'])
    for _, row in reports_df.iterrows():
        cursor.execute("SELECT well_id FROM wells WHERE well_name = ?;", (clean_str(row['WellName']),))
        well_id = cursor.fetchone()[0]
        
        doc_name = clean_str(row['DocumentName'])
        doc_date = clean_str(row['DocumentDate'])
        sub_at = clean_str(row['SubmittedAt'])
        sub_by = clean_str(row['SubmittedBy'])
        
        cursor.execute('''
            INSERT INTO reports (well_id, report_type, document_name, document_date, submitted_at, submitted_by)
            VALUES (?, ?, ?, ?, ?, ?);
        ''', (well_id, clean_str(row['ReportType']), doc_name, doc_date, sub_at, sub_by))

    # --- Table 7: Populate Well Operations ---
    print("Loading well_operations table...")
    ops_df = df.drop_duplicates(subset=['WellName'])
    for _, row in ops_df.iterrows():
        cursor.execute("SELECT well_id FROM wells WHERE well_name = ?;", (clean_str(row['WellName']),))
        well_id = cursor.fetchone()[0]
        
        rig_id = None
        if pd.notna(row['RigName']):
            cursor.execute("SELECT rig_id FROM rigs WHERE rig_name = ?;", (clean_str(row['RigName']),))
            res = cursor.fetchone()
            if res: rig_id = res[0]

        cursor.execute('''
            INSERT INTO well_operations (
                well_id, rig_id, year, afe_cost, afe_days, spud_date, 
                well_start_datetime, well_end_datetime, final_cost, final_days,
                well_npt_percentage_wow, well_npt_percentage, completion_cost_plan,
                completion_cost_actual, drilling_plan_wcpf, drilling_actual_wcpf
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
        ''', (
            well_id, rig_id, clean_int(row['Year']), clean_num(row['AfeCost']), clean_int(row['AfeDays']),
            clean_str(row['SpudDate']), clean_str(row['WellStartDateTime']), clean_str(row['WellEndDateTime']), 
            clean_num(row['FinalCost']), clean_num(row['FinalDays']), clean_num(row['WellNptPercentageWow']), 
            clean_num(row['WellNptPercentage']), clean_num(row['CompletionCostPlan']), clean_num(row['CompletionCostActual']),
            clean_num(row['DrillingPlanWcpf']), clean_num(row['DrillingActualWcpf'])
        ))

    # Save changes permanently
    conn.commit()

    print("\n--- 3. DATA LOAD VALIDATION SUMMARY ---")
    tables = ['companies', 'regions', 'fields', 'rigs', 'wells', 'reports', 'well_operations']
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        print(f"Table '{t}': {cursor.fetchone()[0]} records successfully verified.")

    conn.close()
    print("\nETL Pipeline Execution Completed Successfully!")

if __name__ == "__main__":
    run_etl()
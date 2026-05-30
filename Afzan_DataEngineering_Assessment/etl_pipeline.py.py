import os
import pandas as pd
import sqlite3

def clean_str(val):
    if pd.isna(val) or str(val).strip() == '':
        return None
    return str(val).strip()

def clean_num(val):
    if pd.isna(val):
        return None
    try:
        return float(val)
    except ValueError:
        return None

# Set your exact Windows path here as a raw string (r"...")
def run_etl(csv_path=r'DataForAssessment.csv', db_path='drilling_operations.db'):
    print("Beginning Extraction Stage...")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing input criteria file at designated path: {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"Successfully staged {len(df)} lines for processing transformations.")
    
    # Clean textual layers uniformly
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(clean_str)

    # Edge-case fallback management for unassigned tracking paths
    df['RegionName'] = df['RegionName'].fillna('OFFSHORE_MALAYSIA')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    try:
        # 1. Transform & Load PACs
        unique_pacs = df['PacName'].dropna().unique()
        for pac in unique_pacs:
            cursor.execute("INSERT OR IGNORE INTO pacs (pac_name) VALUES (?)", (pac,))
            
        # 2. Transform & Load Regions
        unique_regs = df['RegionName'].unique()
        for reg in unique_regs:
            cursor.execute("INSERT OR IGNORE INTO regions (region_name) VALUES (?)", (reg,))
            
        # 3. Transform & Load Fields
        fields_chunk = df[['FieldName', 'PacName', 'RegionName']].drop_duplicates().dropna(subset=['FieldName'])
        for _, row in fields_chunk.iterrows():
            cursor.execute("SELECT pac_id FROM pacs WHERE pac_name = ?", (row['PacName'],))
            p_res = cursor.fetchone()
            p_id = p_res[0] if p_res else None
            
            cursor.execute("SELECT region_id FROM regions WHERE region_name = ?", (row['RegionName'],))
            r_res = cursor.fetchone()
            r_id = r_res[0] if r_res else None
            
            cursor.execute("INSERT OR IGNORE INTO fields (field_name, pac_id, region_id) VALUES (?, ?, ?)", 
                           (row['FieldName'], p_id, r_id))

        # 4. Transform & Load Rigs
        rigs_chunk = df[['RigName', 'RigType']].drop_duplicates().dropna(subset=['RigName'])
        for _, row in rigs_chunk.iterrows():
            cursor.execute("INSERT OR IGNORE INTO rigs (rig_name, rig_type) VALUES (?, ?)", 
                           (row['RigName'], row['RigType']))

        # 5. Transform & Load Wells
        wells_chunk = df[['WellName', 'WellType', 'FieldName', 'PacName', 'RegionName', 'WaterDepth']].drop_duplicates().dropna(subset=['WellName'])
        for _, row in wells_chunk.iterrows():
            cursor.execute("SELECT pac_id FROM pacs WHERE pac_name = ?", (row['PacName'],))
            p_res = cursor.fetchone()
            p_id = p_res[0] if p_res else None
            
            cursor.execute("SELECT region_id FROM regions WHERE region_name = ?", (row['RegionName'],))
            r_res = cursor.fetchone()
            r_id = r_res[0] if r_res else None
            
            cursor.execute("SELECT field_id FROM fields WHERE field_name = ? AND pac_id = ? AND region_id = ?", 
                           (row['FieldName'], p_id, r_id))
            f_res = cursor.fetchone()
            f_id = f_res[0] if f_res else None
            
            cursor.execute("INSERT OR IGNORE INTO wells (well_name, well_type, field_id, water_depth) VALUES (?, ?, ?, ?)",
                           (row['WellName'], row['WellType'], f_id, clean_num(row['WaterDepth'])))

        # 6 & 7. Transform & Load Campaign Operations and Individual Reports
        print("Parsing structural campaigns and mapping individual ledger sheets...")
        for _, row in df.iterrows():
            cursor.execute("SELECT well_id FROM wells WHERE well_name = ?", (row['WellName'],))
            w_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT rig_id FROM rigs WHERE rig_name = ? AND (rig_type = ? OR (? IS NULL AND rig_type IS NULL))", 
                           (row['RigName'], row['RigType'], row['RigType']))
            rg_res = cursor.fetchone()
            rg_id = rg_res[0] if rg_res else None
            
            yr = int(row['Year']) if not pd.isna(row['Year']) else None
            spud = clean_str(row['SpudDate'])
            
            # Upsert structural project wrapper
            cursor.execute("""
                SELECT operation_id FROM well_operations 
                WHERE well_id = ? AND rig_id = ? AND (operation_year = ? OR (? IS NULL AND operation_year IS NULL))
                AND (spud_date = ? OR (? IS NULL AND spud_date IS NULL))
            """, (w_id, rg_id, yr, yr, spud, spud))
            
            op_res = cursor.fetchone()
            if op_res:
                op_id = op_res[0]
            else:
                cursor.execute("""
                    INSERT INTO well_operations (well_id, rig_id, operation_year, afe_cost, afe_days, spud_date, well_start_datetime, well_end_datetime)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (w_id, rg_id, yr, clean_num(row['AfeCost']), clean_num(row['AfeDays']), spud, clean_str(row['WellStartDateTime']), clean_str(row['WellEndDateTime'])))
                op_id = cursor.lastrowid
                
            # Direct insert operational report line
            cursor.execute("""
                INSERT INTO operational_reports (
                    operation_id, report_type, document_name, document_date, submitted_at, submitted_by,
                    final_cost, final_days, well_npt_percentage_wow, well_npt_percentage,
                    completion_cost_plan, completion_cost_actual, drilling_plan_wcpf, drilling_actual_wcpf
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                op_id, row['ReportType'], clean_str(row['DocumentName']), clean_str(row['DocumentDate']),
                clean_str(row['SubmittedAt']), clean_str(row['SubmittedBy']),
                clean_num(row['FinalCost']), clean_num(row['FinalDays']),
                clean_num(row['WellNptPercentageWow']), clean_num(row['WellNptPercentage']),
                clean_num(row['CompletionCostPlan']), clean_num(row['CompletionCostActual']),
                clean_num(row['DrillingPlanWcpf']), clean_num(row['DrillingActualWcpf'])
            ))
            
        conn.commit()
        print("\n=== ETL Processing Completed Successfully ===")
        
        # Summary verification output printout
        for t in ['pacs', 'regions', 'fields', 'rigs', 'wells', 'well_operations', 'operational_reports']:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"Total Rows Loaded inside '{t}': {cursor.fetchone()[0]}")
            
    except Exception as err:
        conn.rollback()
        print(f"Aborting execution transaction. Pipeline error caught: {err}")
        raise err
    finally:
        conn.close()

if __name__ == '__main__':
    run_etl()
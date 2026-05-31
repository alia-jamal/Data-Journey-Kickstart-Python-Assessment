"""
ETL Pipeline: DataForAssessment.csv → drilling_operations.db (SQLite)
======================================================================
Sections:
  0. Setup & Configuration
  1. EXTRACT  – read CSV, surface data quality issues
  2. TRANSFORM – normalise flat CSV into relational tables
  3. LOAD      – insert into SQLite with referential integrity
  4. VALIDATE  – post-load row counts & sample queries
"""

import pandas as pd
import sqlite3
import logging
import sys
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# 0.  SETUP & CONFIGURATION
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("etl")

CSV_PATH = Path("../data/DataForAssessment.csv")
DB_PATH  = Path("drilling_operations.db")

# Remove any stale DB so the run is idempotent
if DB_PATH.exists():
    DB_PATH.unlink()
    log.info("Removed existing database")

# ─────────────────────────────────────────────
# 1.  EXTRACT
# ─────────────────────────────────────────────
log.info("=" * 55)
log.info("STAGE 1 – EXTRACT")
log.info("=" * 55)

raw = pd.read_csv(CSV_PATH)
log.info("Loaded %d rows × %d columns from %s", *raw.shape, CSV_PATH.name)

# ── Data quality report ──────────────────────
dq_issues = []

null_counts = raw.isnull().sum()
for col, n in null_counts[null_counts > 0].items():
    pct = n / len(raw) * 100
    msg = f"NULL values in '{col}': {n} / {len(raw)} ({pct:.1f}%)"
    log.warning("  DQ: %s", msg)
    dq_issues.append(msg)

# Columns that are entirely NULL
all_null_cols = [c for c in raw.columns if raw[c].isnull().all()]
if all_null_cols:
    msg = f"Entirely NULL columns (will be skipped): {all_null_cols}"
    log.warning("  DQ: %s", msg)
    dq_issues.append(msg)

log.info("Extract complete – %d data-quality issues noted", len(dq_issues))

# ─────────────────────────────────────────────
# 2.  TRANSFORM
# ─────────────────────────────────────────────
log.info("=" * 55)
log.info("STAGE 2 – TRANSFORM")
log.info("=" * 55)

# ── Helper: parse datetime strings ──────────
def parse_dt(series: pd.Series) -> pd.Series:
    """Strip timezone offset and parse to 'YYYY-MM-DD HH:MM:SS' strings."""
    def _parse(v):
        if pd.isna(v):
            return None
        s = str(v).strip()
        # e.g. "2019-02-10 00:00:00.000 +0000"
        s = s.split("+")[0].strip().split(".")[0].strip()
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    return series.apply(_parse)

# ── 2a. PAC ──────────────────────────────────
pac_df = (
    raw[["PacName"]]
    .drop_duplicates()
    .dropna()
    .rename(columns={"PacName": "pac_name"})
    .reset_index(drop=True)
)
pac_df.insert(0, "pac_id", pac_df.index + 1)
log.info("PAC        → %d rows", len(pac_df))

# ── 2b. Region ───────────────────────────────
region_df = (
    raw[["RegionName"]]
    .drop_duplicates()
    .dropna()                                   # 2 NULLs: skip
    .rename(columns={"RegionName": "region_name"})
    .reset_index(drop=True)
)
region_df.insert(0, "region_id", region_df.index + 1)
log.info("Region     → %d rows", len(region_df))

# ── 2c. Field ────────────────────────────────
field_src = (
    raw[["FieldName", "PacName", "RegionName"]]
    .drop_duplicates()
    .dropna(subset=["FieldName"])
)
field_src = field_src.merge(pac_df,    left_on="PacName",    right_on="pac_name",    how="left")
field_src = field_src.merge(region_df, left_on="RegionName", right_on="region_name", how="left")

# If RegionName was NULL, region_id will be NaN; cast to nullable int
field_src["region_id"] = pd.to_numeric(field_src["region_id"], errors="coerce")

field_df = (
    field_src[["FieldName", "pac_id", "region_id"]]
    .drop_duplicates()
    .rename(columns={"FieldName": "field_name"})
    .reset_index(drop=True)
)
field_df.insert(0, "field_id", field_df.index + 1)
log.info("Field      → %d rows", len(field_df))

# ── 2d. Rig ──────────────────────────────────
rig_src = (
    raw[["RigName", "RigType"]]
    .drop_duplicates()
    .dropna(subset=["RigName"])
)
# Fill the 2 NULL RigType values
rig_src["RigType"] = rig_src["RigType"].fillna("UNKNOWN")
rig_df = rig_src.rename(columns={"RigName": "rig_name", "RigType": "rig_type"}).reset_index(drop=True)
rig_df.insert(0, "rig_id", rig_df.index + 1)
log.info("Rig        → %d rows", len(rig_df))
dq_issues.append("2 NULL RigType values filled with 'UNKNOWN'")

# ── 2e. Well ─────────────────────────────────
well_src = (
    raw[["WellName", "WellType", "SpudDate", "WaterDepth", "FieldName"]]
    .drop_duplicates(subset=["WellName"])
    .dropna(subset=["WellName"])
)
well_src = well_src.merge(
    field_df[["field_id", "field_name"]],
    left_on="FieldName", right_on="field_name", how="left"
)
well_src["SpudDate"] = parse_dt(well_src["SpudDate"])
well_df = (
    well_src[["WellName", "WellType", "SpudDate", "WaterDepth", "field_id"]]
    .rename(columns={
        "WellName":   "well_name",
        "WellType":   "well_type",
        "SpudDate":   "spud_date",
        "WaterDepth": "water_depth",
    })
    .reset_index(drop=True)
)
well_df.insert(0, "well_id", well_df.index + 1)
log.info("Well       → %d rows", len(well_df))

# ── 2f. WellOperation ────────────────────────
op_src = raw.copy()

# Merge FKs
op_src = op_src.merge(well_df[["well_id", "well_name"]], left_on="WellName",  right_on="well_name",  how="left")
op_src = op_src.merge(rig_df[["rig_id",   "rig_name"]],  left_on="RigName",   right_on="rig_name",   how="left")

# Parse datetimes
for col in ["WellStartDateTime", "WellEndDateTime"]:
    op_src[col] = parse_dt(op_src[col])

# One operation per (well, year, rig) – take first occurrence for financial cols
agg_cols = {
    "well_id":             "first",
    "rig_id":              "first",
    "WellStartDateTime":   "first",
    "WellEndDateTime":     "first",
    "AfeCost":             "first",
    "AfeDays":             "first",
    "FinalCost":           "first",
    "FinalDays":           "first",
    "WellNptPercentage":   "first",
    "WellNptPercentageWow":"first",
    "CompletionCostPlan":  "first",
    "CompletionCostActual":"first",
    "DrillingPlanWcpf":    "first",
    "DrillingActualWcpf":  "first",
}
op_grouped = (
    op_src.groupby(["WellName", "Year"])
    .agg(agg_cols)
    .reset_index()
)

op_df = op_grouped.rename(columns={
    "Year":                "operation_year",
    "WellStartDateTime":   "well_start_datetime",
    "WellEndDateTime":     "well_end_datetime",
    "AfeCost":             "afe_cost",
    "AfeDays":             "afe_days",
    "FinalCost":           "final_cost",
    "FinalDays":           "final_days",
    "WellNptPercentage":   "npt_percentage",
    "WellNptPercentageWow":"npt_percentage_wow",
    "CompletionCostPlan":  "completion_cost_plan",
    "CompletionCostActual":"completion_cost_actual",
    "DrillingPlanWcpf":    "drilling_plan_wcpf",
    "DrillingActualWcpf":  "drilling_actual_wcpf",
})[["well_id","rig_id","operation_year","well_start_datetime","well_end_datetime",
    "afe_cost","afe_days","final_cost","final_days","npt_percentage","npt_percentage_wow",
    "completion_cost_plan","completion_cost_actual","drilling_plan_wcpf","drilling_actual_wcpf"]]

op_df = op_df.reset_index(drop=True)
op_df.insert(0, "operation_id", op_df.index + 1)
log.info("WellOperation → %d rows", len(op_df))

# ── 2g. Report ───────────────────────────────
# Build operation lookup: (WellName, Year) → operation_id
op_lookup = op_grouped[["WellName", "Year", "well_id", "rig_id"]].copy()
op_lookup["operation_id"] = op_df["operation_id"].values

rep_src = raw[["WellName", "Year", "ReportType", "DocumentName",
               "DocumentDate", "SubmittedAt", "SubmittedBy"]].copy()
rep_src = rep_src.merge(op_lookup[["WellName", "Year", "operation_id"]],
                        on=["WellName", "Year"], how="left")

rep_src["DocumentDate"] = parse_dt(rep_src["DocumentDate"])
rep_src["SubmittedAt"]  = parse_dt(rep_src["SubmittedAt"])

# DocumentName is almost entirely NULL (134/138); keep as-is (NULL stored as None)
rep_df = rep_src.rename(columns={
    "ReportType":   "report_type",
    "DocumentName": "document_name",
    "DocumentDate": "document_date",
    "SubmittedAt":  "submitted_at",
    "SubmittedBy":  "submitted_by",
})[["operation_id","report_type","document_name","document_date","submitted_at","submitted_by"]]

rep_df = rep_df.reset_index(drop=True)
rep_df.insert(0, "report_id", rep_df.index + 1)
log.info("Report     → %d rows", len(rep_df))

log.info("Transform complete")

# ─────────────────────────────────────────────
# 3.  LOAD
# ─────────────────────────────────────────────
log.info("=" * 55)
log.info("STAGE 3 – LOAD")
log.info("=" * 55)

DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE PAC (
    pac_id   INTEGER PRIMARY KEY,
    pac_name TEXT    UNIQUE NOT NULL
);

CREATE TABLE Region (
    region_id   INTEGER PRIMARY KEY,
    region_name TEXT    UNIQUE NOT NULL
);

CREATE TABLE Field (
    field_id   INTEGER PRIMARY KEY,
    field_name TEXT NOT NULL,
    pac_id     INTEGER REFERENCES PAC(pac_id),
    region_id  INTEGER REFERENCES Region(region_id)
);

CREATE TABLE Rig (
    rig_id   INTEGER PRIMARY KEY,
    rig_name TEXT NOT NULL,
    rig_type TEXT
);

CREATE TABLE Well (
    well_id    INTEGER PRIMARY KEY,
    field_id   INTEGER REFERENCES Field(field_id),
    well_name  TEXT NOT NULL,
    well_type  TEXT,
    spud_date  TEXT,
    water_depth REAL
);

CREATE TABLE WellOperation (
    operation_id           INTEGER PRIMARY KEY,
    well_id                INTEGER REFERENCES Well(well_id),
    rig_id                 INTEGER REFERENCES Rig(rig_id),
    operation_year         INTEGER,
    well_start_datetime    TEXT,
    well_end_datetime      TEXT,
    afe_cost               REAL,
    afe_days               REAL,
    final_cost             REAL,
    final_days             REAL,
    npt_percentage         REAL,
    npt_percentage_wow     REAL,
    completion_cost_plan   REAL,
    completion_cost_actual REAL,
    drilling_plan_wcpf     REAL,
    drilling_actual_wcpf   REAL
);

CREATE TABLE Report (
    report_id     INTEGER PRIMARY KEY,
    operation_id  INTEGER REFERENCES WellOperation(operation_id),
    report_type   TEXT,
    document_name TEXT,
    document_date TEXT,
    submitted_at  TEXT,
    submitted_by  TEXT
);
"""

def load_table(conn, df: pd.DataFrame, table: str) -> int:
    """Insert a DataFrame into a SQLite table; return row count."""
    # Replace NaN with None so SQLite stores NULL
    records = [
        {k: (None if pd.isna(v) else v) for k, v in row.items()}
        for row in df.to_dict("records")
    ]
    if records:
        cols    = ", ".join(records[0].keys())
        placeholders = ", ".join(f":{k}" for k in records[0].keys())
        conn.executemany(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", records)
    conn.commit()
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    log.info("  Loaded %-20s → %3d rows", table, n)
    return n

conn = sqlite3.connect(DB_PATH)
conn.executescript(DDL)
log.info("Schema created")

load_order = [
    (pac_df,    "PAC"),
    (region_df, "Region"),
    (field_df,  "Field"),
    (rig_df,    "Rig"),
    (well_df,   "Well"),
    (op_df,     "WellOperation"),
    (rep_df,    "Report"),
]

record_counts = {}
for df, tbl in load_order:
    record_counts[tbl] = load_table(conn, df, tbl)

log.info("Load complete")

# ─────────────────────────────────────────────
# 4.  VALIDATE
# ─────────────────────────────────────────────
log.info("=" * 55)
log.info("STAGE 4 – VALIDATE")
log.info("=" * 55)

checks = [
    ("FK integrity – Field→PAC",
     "SELECT COUNT(*) FROM Field f LEFT JOIN PAC p ON f.pac_id=p.pac_id WHERE p.pac_id IS NULL"),
    ("FK integrity – Well→Field",
     "SELECT COUNT(*) FROM Well w LEFT JOIN Field f ON w.field_id=f.field_id WHERE f.field_id IS NULL"),
    ("FK integrity – Report→WellOperation",
     "SELECT COUNT(*) FROM Report r LEFT JOIN WellOperation o ON r.operation_id=o.operation_id WHERE o.operation_id IS NULL"),
    ("Orphan operations (no well)",
     "SELECT COUNT(*) FROM WellOperation WHERE well_id IS NULL"),
]
all_ok = True
for label, sql in checks:
    n = conn.execute(sql).fetchone()[0]
    status = "OK" if n == 0 else f"FAIL ({n} violations)"
    log.info("  %-42s %s", label, status)
    if n != 0:
        all_ok = False

# ── Summary report ───────────────────────────
print()
print("=" * 55)
print("  SUMMARY REPORT")
print("=" * 55)
print()
print("Records loaded per table:")
for tbl, n in record_counts.items():
    print(f"  {tbl:<22} {n:>4} rows")

print()
print("Data quality issues encountered:")
for i, issue in enumerate(dq_issues, 1):
    print(f"  {i}. {issue}")

print()
print("Sample queries:")

q1 = """
SELECT p.pac_name, COUNT(DISTINCT w.well_id) AS wells
FROM PAC p
JOIN Field f  ON f.pac_id  = p.pac_id
JOIN Well  w  ON w.field_id = f.field_id
GROUP BY p.pac_name
ORDER BY wells DESC
LIMIT 5;
"""
print("\n  Q1 – Top 5 PACs by well count:")
rows = conn.execute(q1).fetchall()
for r in rows:
    print(f"       {r[0]:<25} {r[1]} wells")

q2 = """
SELECT w.well_name,
       ROUND(o.afe_cost,0) AS afe_cost,
       ROUND(o.final_cost,0) AS final_cost,
       ROUND((o.final_cost - o.afe_cost)/o.afe_cost*100, 1) AS overrun_pct
FROM WellOperation o
JOIN Well w ON w.well_id = o.well_id
WHERE o.afe_cost > 0
ORDER BY overrun_pct DESC
LIMIT 5;
"""
print("\n  Q2 – Top 5 wells by cost overrun (%):")
rows = conn.execute(q2).fetchall()
for r in rows:
    print(f"       {r[0]:<22} AFE={r[1]:>12,.0f}  Final={r[2]:>12,.0f}  Overrun={r[3]}%")

q3 = """
SELECT rg.rig_name, COUNT(DISTINCT o.well_id) AS wells_drilled,
       ROUND(AVG(o.npt_percentage),2) AS avg_npt_pct
FROM Rig rg
JOIN WellOperation o ON o.rig_id = rg.rig_id
GROUP BY rg.rig_name
ORDER BY wells_drilled DESC
LIMIT 5;
"""
print("\n  Q3 – Top 5 rigs by wells drilled + avg NPT%:")
rows = conn.execute(q3).fetchall()
for r in rows:
    print(f"       {r[0]:<25} {r[1]} wells  avg NPT={r[2]}%")

print()
print("Validation:", "PASSED ✓" if all_ok else "FAILED – see log above")
print(f"Database written to: {DB_PATH}")
print("=" * 55)

conn.close()

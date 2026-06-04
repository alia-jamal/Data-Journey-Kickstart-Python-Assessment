# Drilling Operations – Python Training Task Assessment

**Candidate:** Daniel
**Date:** May 2026

---

## Overview

This submission covers all three tasks of the assessment:

1. **Task 1 – ERD Design** — Entity-Relationship Diagram for a drilling operations database
2. **Task 2 – Schema Creation** — SQLite database built from DDL scripts
3. **Task 3 – ETL Pipeline** — Python pipeline to extract, transform, and load `DataForAssessment.csv` into the database

---

## Repository Structure

The submission is a single flat folder so it can be unzipped and run as-is. All files live next to each other; the ETL script auto-discovers the CSV.

```
Training Python Task Assessment/
    README.md                              ← This file
    DataForAssessment.csv                  ← Source data (138 rows × 27 columns)
    create_schema.py                       ← Task 2: DDL script, builds all 16 tables
    etl_pipeline.py                        ← Task 3: ETL pipeline
    drilling_operations.db                 ← Populated SQLite database
    validation_queries.sql                 ← SQL integrity and business queries
    etl_summary_report.md                  ← Auto-generated ETL run report

    ERD Assessment (Compact).pdf           ← Task 1: ERD diagram (compact view)
    ERD Assessment (SS).pdf                ← Task 1: ERD diagram (full screenshot)
    ERD Design Documentation.docx          ← Task 1: detailed design write-up
    design_explanation.md                  ← Task 1: design rationale (Markdown)

    Drilling_Operations_Audit_and_Walkthrough.pdf    ← Self-audit + teaching guide
    Drilling_Operations_Audit_and_Walkthrough.docx
```

---

## How to Run

From inside this folder:

```bash
# 1. Create the empty schema (idempotent - safe to re-run)
python create_schema.py

# 2. Load the CSV into the database
python etl_pipeline.py

# 3. (Optional) Verify with the supplied SQL queries
sqlite3 drilling_operations.db < validation_queries.sql
```

**Dependencies:** `pandas >= 1.3`, `rapidfuzz >= 3.0`, `sqlite3` (Python standard library), Python `>= 3.10`.
Install with `pip install pandas rapidfuzz`.

---

## Task 1 – ERD Design

The ERD organises the domain into five business areas:

- **Asset / Business Hierarchy** — `ProductionAssetCompany`, `Region`, `Field`, `WellType`, `Well`, `Wellbore`
- **Rig / Equipment** — `RigType`, `Rig`, `WellOperationRigAssignment`
- **Well Operations** — `WellOperation`, `OperationPhaseType`, `WellOperationPhase`
- **Performance / Cost Metrics** — `OperationPerformance`
- **Reports / Documents** — `ReportType`, `Report`, `ReportWellOperation`

**Key design decisions:**

- All tables use `INTEGER PRIMARY KEY AUTOINCREMENT` surrogate keys — business names are not used as PKs because they can change and are not guaranteed unique.
- Many-to-many relationships (Rig ↔ WellOperation, Report ↔ WellOperation) are resolved through explicit bridge tables rather than composite keys.
- Lookup tables (WellType, RigType, ReportType, OperationPhaseType) prevent free-text repetition and support standardisation.
- The schema follows Third Normal Form (3NF) — no transitive dependencies.

---

## Task 2 – Schema Creation

`create_schema.py` connects to `drilling_operations.db` (creating it if absent) and executes 16 `CREATE TABLE IF NOT EXISTS` statements in foreign-key dependency order.

**Run:**

```bash
python create_schema.py
```

**Result:** An empty database with all 16 tables and FK constraints enabled via `PRAGMA foreign_keys = ON`.

---

## Task 3 – ETL Pipeline

`etl_pipeline.py` implements a three-stage pipeline with logging, data-quality tracking, and post-load validation.

### Extract

- Reads `DataForAssessment.csv` using pandas
- Audits all columns for nulls and logs every issue to the console
- Flags duplicate operation rows and RigType spelling variants

### Transform

Key transformations applied before insertion:

- **138 raw rows → 64 unique well operations**
  Deduplicated on composite key: PAC + Region + Field + Well + Rig + Start/End datetime.

- **RigType spelling variants** (`JACK UP`, `Semi-Submersible`, etc.)
  Normalised to canonical forms via a fuzzy-matching dictionary before loading into the `RigType` lookup table.

- **Missing `RegionName`** (2 rows)
  Assigned sentinel value `'UNKNOWN'`; loaded as a real Region row to preserve referential integrity.

- **Missing `DocumentName`** (134 of 138 rows)
  Synthetic name generated in the format `AUTO_{ReportType}_{well_operation_id}` to satisfy the NOT NULL constraint.

- **Four entirely-null columns** (`CompletionCostPlan`, `CompletionCostActual`, `DrillingPlanWcpf`, `DrillingActualWcpf`)
  Loaded as SQL NULL — the schema permits nullable REAL columns.

- **Dates with timezone offsets** (e.g. `+0800`)
  Parsed with `pandas.to_datetime(utc=True)` and stored as ISO 8601 UTC strings.

### Load

- Inserts in FK-safe order: lookup tables first, then master tables, then fact/bridge tables.
- Uses in-memory caches (Python dicts) to resolve surrogate keys without repeated `SELECT` round-trips.
- Single atomic `conn.commit()` — rolls back entirely on any error.
- FK enforcement enabled: `PRAGMA foreign_keys = ON`.

### Validate

Five post-load integrity checks run automatically. All return **0 violations**:

- WellOperations without a Rig assignment — **PASS**
- WellOperations without OperationPerformance — **PASS**
- Reports not linked to any WellOperation — **PASS**
- WellOperations with invalid `well_id` — **PASS**
- Fields with invalid `region_id` — **PASS**

**Run:**

```bash
python etl_pipeline.py
```

The pipeline logs progress to the console and writes `etl_summary_report.md` on completion.

---

## Data Loaded

Row counts after a full pipeline run:

- `ProductionAssetCompany` — 14
- `Region` — 19
- `Field` — 34
- `WellType` — 2
- `Well` — 64
- `RigType` — 8
- `Rig` — 29
- `WellOperation` — 64
- `WellOperationRigAssignment` — 64
- `OperationPerformance` — 64
- `ReportType` — 2
- `Report` — 132
- `ReportWellOperation` — 132
- `Wellbore`, `WellOperationPhase`, `OperationPhaseType` — 0 (no source data; schema retained for future use)

**Total:** 628 rows across 16 tables.

---

## Assumptions

1. **One CSV row = one (WellOperation, Report) pair.** The source data repeats each operation twice — once for a NOOP report and once for a FWR report. The pipeline deduplicates at the operation level while preserving both report records.
2. **WellOperation identity** is defined by the combination of PAC + Region + Field + WellName + RigName + WellStartDateTime + WellEndDateTime. Rows sharing all seven fields are treated as the same operation.
3. **Water depth** is treated as a property of the Well (not the operation), since it did not vary across multiple operations on the same well in the source data.
4. **Wellbore** records are not populated — the source CSV does not contain wellbore-level data. The table is present in the schema for future use.
5. **OperationPhaseType / WellOperationPhase** are empty for the same reason — the source data does not break operations into phases.
6. **RigType normalisation** maps visually equivalent variants to a single canonical label. `JACK-UP` and `JACK UP` become `JACK-UP`; `Semi-Submersible` and `SEMI-SUB` become `SEMI-SUBMERSIBLE`, and so on.
7. **Missing RegionName** for the `TEST PAC2 EDIT` / `BULOH DEV` / `AAZ 1` records is assumed to be a data entry omission. A sentinel region `'UNKNOWN'` is used to keep the row loadable without dropping it.

---

## Known Issues and Limitations

- **CompletionCostPlan, CompletionCostActual, DrillingPlanWcpf, DrillingActualWcpf** are entirely null in the source CSV and therefore null in the database. These columns exist in the schema for forward compatibility.
- **DocumentName** is null for 134 of 138 rows. Synthetic names are used; any downstream reporting on document names will show `AUTO_*` values for most records.
- **Wellbore and phase data** cannot be populated without additional source data.
- The ETL is designed for a **single-run load** against an empty database. Re-running against an already-populated database will produce duplicate rows (the script does not implement upsert logic). To re-run cleanly, restore the schema-only database using `create_schema.py` first.

---

## Dependencies

- Python `>= 3.10`
- `pandas >= 1.3`
- `rapidfuzz >= 3.0`
- `sqlite3` (Python standard library)

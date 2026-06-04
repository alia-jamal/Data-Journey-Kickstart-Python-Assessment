"""
create_schema.py
================
Task 2 - Database Schema Creation
Assessment: Python Training Task Assessment (Data Engineering)

Purpose
-------
Build an empty SQLite database (`drilling_operations.db`) with all 16 tables,
primary/foreign keys, NOT NULL/UNIQUE/CHECK constraints, and ON DELETE /
ON UPDATE referential rules required by the Drilling Operations data model.

Design choices (reflected in the DDL below)
-------------------------------------------
- Every table uses an INTEGER PRIMARY KEY AUTOINCREMENT surrogate key.
  Business names can change and are not guaranteed unique, so we never
  use them as primary keys.
- Lookup tables (WellType, RigType, ReportType, OperationPhaseType) have a
  UNIQUE constraint on their name column to prevent duplicate categories.
- NOT NULL is applied to every attribute that must exist for the row to make
  sense (e.g. `Region.pac_id`, `Field.region_id`, `Well.field_id`).
- Optional foreign keys (e.g. `Rig.rig_type_id`) are nullable because the
  source data sometimes omits the parent classification.
- Many-to-many relationships are resolved with explicit bridge tables
  (`WellOperationRigAssignment`, `ReportWellOperation`) rather than
  composite keys on either side.
- Boolean flags are stored as INTEGER + CHECK(... IN (0, 1)) - the standard
  SQLite idiom because SQLite has no native BOOLEAN type.
- ON DELETE RESTRICT protects mandatory parents from accidental deletion;
  ON DELETE SET NULL is used where the relationship is optional so the
  child can survive the parent going away.
- ON UPDATE CASCADE propagates surrogate-key changes through children
  (rarely needed in practice, but defensive).

Usage
-----
    python create_schema.py

Result
------
    drilling_operations.db in the same directory as this script, containing
    16 empty tables with foreign key enforcement enabled.
"""

import os
import sqlite3

# Resolve DB path relative to this script so the same command works regardless
# of where the user is when they invoke it.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "drilling_operations.db")


# DDL is split into one CREATE per list element so:
#   - sqlite3 sees individual statements (cursor.execute accepts one at a time)
#   - statement order respects FK dependencies (parents before children)
DDL_STATEMENTS = [

    # ============================================================
    # ASSET / BUSINESS HIERARCHY DOMAIN
    # ============================================================

    """CREATE TABLE IF NOT EXISTS ProductionAssetCompany (
        pac_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        pac_name  TEXT    NOT NULL UNIQUE  -- business name of the PAC
    )""",

    """CREATE TABLE IF NOT EXISTS Region (
        region_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        pac_id       INTEGER NOT NULL,          -- a region must belong to a PAC
        region_name  TEXT    NOT NULL,
        FOREIGN KEY (pac_id)
            REFERENCES ProductionAssetCompany (pac_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS Field (
        field_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        region_id   INTEGER NOT NULL,           -- a field must belong to a region
        field_name  TEXT    NOT NULL,
        FOREIGN KEY (region_id)
            REFERENCES Region (region_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS WellType (
        well_type_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        well_type_name  TEXT    NOT NULL UNIQUE  -- standardised classification
    )""",

    """CREATE TABLE IF NOT EXISTS Well (
        well_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        field_id      INTEGER NOT NULL,         -- a well must belong to a field
        well_type_id  INTEGER,                  -- optional - source may omit
        well_name     TEXT    NOT NULL,
        water_depth   REAL,                     -- metres; NULL for onshore
        FOREIGN KEY (field_id)
            REFERENCES Field (field_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE,
        FOREIGN KEY (well_type_id)
            REFERENCES WellType (well_type_id)
            ON DELETE SET NULL
            ON UPDATE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS Wellbore (
        wellbore_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        well_id         INTEGER NOT NULL,       -- a wellbore must belong to a well
        wellbore_name   TEXT    NOT NULL,
        wellbore_label  TEXT,                   -- short label e.g. "ST1", "L2"
        FOREIGN KEY (well_id)
            REFERENCES Well (well_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE
    )""",

    # ============================================================
    # RIG / EQUIPMENT DOMAIN
    # ============================================================

    """CREATE TABLE IF NOT EXISTS RigType (
        rig_type_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        rig_type_name  TEXT    NOT NULL UNIQUE  -- standardised rig classification
    )""",

    """CREATE TABLE IF NOT EXISTS Rig (
        rig_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        rig_type_id  INTEGER,                   -- optional - source may omit
        rig_name     TEXT    NOT NULL,
        FOREIGN KEY (rig_type_id)
            REFERENCES RigType (rig_type_id)
            ON DELETE SET NULL
            ON UPDATE CASCADE
    )""",

    # ============================================================
    # WELL OPERATIONS DOMAIN
    # ============================================================

    """CREATE TABLE IF NOT EXISTS OperationPhaseType (
        operation_phase_type_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_phase_type_name  TEXT    NOT NULL UNIQUE
    )""",

    """CREATE TABLE IF NOT EXISTS WellOperation (
        well_operation_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        well_id              INTEGER NOT NULL,  -- an operation must reference a well
        wellbore_id          INTEGER,           -- optional - operation may be tracked at well level
        operation_year       INTEGER,
        spud_date            TEXT,              -- ISO 8601 date string
        well_start_datetime  TEXT,              -- ISO 8601 datetime string
        well_end_datetime    TEXT,              -- ISO 8601 datetime string
        FOREIGN KEY (well_id)
            REFERENCES Well (well_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE,
        FOREIGN KEY (wellbore_id)
            REFERENCES Wellbore (wellbore_id)
            ON DELETE SET NULL
            ON UPDATE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS WellOperationPhase (
        well_operation_phase_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        well_operation_id        INTEGER NOT NULL,
        operation_phase_type_id  INTEGER NOT NULL,
        phase_start_datetime     TEXT,
        phase_end_datetime       TEXT,
        FOREIGN KEY (well_operation_id)
            REFERENCES WellOperation (well_operation_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE,
        FOREIGN KEY (operation_phase_type_id)
            REFERENCES OperationPhaseType (operation_phase_type_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS WellOperationRigAssignment (
        well_operation_rig_assignment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        well_operation_id                 INTEGER NOT NULL,
        rig_id                            INTEGER NOT NULL,
        assignment_start_datetime         TEXT,
        assignment_end_datetime           TEXT,
        rig_role                          TEXT,              -- e.g. "Primary Drilling Rig"
        is_primary_rig                    INTEGER NOT NULL DEFAULT 0
            CHECK (is_primary_rig IN (0, 1)),
        assignment_reason                 TEXT,
        FOREIGN KEY (well_operation_id)
            REFERENCES WellOperation (well_operation_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE,
        FOREIGN KEY (rig_id)
            REFERENCES Rig (rig_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE
    )""",

    # ============================================================
    # PERFORMANCE / COST DOMAIN
    # ============================================================

    """CREATE TABLE IF NOT EXISTS OperationPerformance (
        operation_performance_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        well_operation_id         INTEGER NOT NULL,
        well_operation_phase_id   INTEGER,                  -- NULL = operation-level metric
        performance_scope         TEXT,                     -- e.g. "Operation", "Drilling"
        performance_version       INTEGER NOT NULL DEFAULT 1,
        is_final                  INTEGER NOT NULL DEFAULT 0
            CHECK (is_final IN (0, 1)),

        -- planned values (source: AfeCost, AfeDays)
        afe_cost                  REAL,
        afe_days                  REAL,

        -- actual values (source: FinalCost, FinalDays)
        final_cost                REAL,
        final_days                REAL,

        -- NPT (source: WellNptPercentageWow, WellNptPercentage)
        well_npt_percentage_wow   REAL,
        well_npt_percentage       REAL,

        -- Completion costs (source: CompletionCostPlan / Actual)
        completion_cost_plan      REAL,
        completion_cost_actual    REAL,

        -- WCPF drilling metrics (source: DrillingPlanWcpf / ActualWcpf)
        drilling_plan_wcpf        REAL,
        drilling_actual_wcpf      REAL,

        created_at                TEXT NOT NULL DEFAULT (datetime('now')),

        FOREIGN KEY (well_operation_id)
            REFERENCES WellOperation (well_operation_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE,
        FOREIGN KEY (well_operation_phase_id)
            REFERENCES WellOperationPhase (well_operation_phase_id)
            ON DELETE SET NULL
            ON UPDATE CASCADE
    )""",

    # ============================================================
    # REPORTS / DOCUMENTS DOMAIN
    # ============================================================

    """CREATE TABLE IF NOT EXISTS ReportType (
        report_type_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        report_type_name  TEXT    NOT NULL UNIQUE
    )""",

    """CREATE TABLE IF NOT EXISTS Report (
        report_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        report_type_id  INTEGER,                  -- optional - classification may be unknown
        document_name   TEXT    NOT NULL,         -- source: DocumentName
        document_date   TEXT,                     -- ISO 8601 (source: DocumentDate)
        submitted_at    TEXT,                     -- ISO 8601 (source: SubmittedAt)
        submitted_by    TEXT,                     -- source: SubmittedBy
        FOREIGN KEY (report_type_id)
            REFERENCES ReportType (report_type_id)
            ON DELETE SET NULL
            ON UPDATE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS ReportWellOperation (
        report_well_operation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id                 INTEGER NOT NULL,
        well_operation_id         INTEGER NOT NULL,
        relationship_type         TEXT,                     -- e.g. "Primary Subject"
        FOREIGN KEY (report_id)
            REFERENCES Report (report_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE,
        FOREIGN KEY (well_operation_id)
            REFERENCES WellOperation (well_operation_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE
    )""",
]


def create_schema(db_path: str = DB_PATH) -> None:
    """Create (or re-create) the empty drilling operations schema."""
    print(f"Creating schema at: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        # Enforce FK constraints for this connection (off by default in SQLite).
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        for stmt in DDL_STATEMENTS:
            cursor.execute(stmt)

        conn.commit()

        # Confirm tables were created.
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name != 'sqlite_sequence' "
            "ORDER BY name;"
        )
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Created {len(tables)} tables:")
        for t in tables:
            print(f"  - {t}")
    finally:
        conn.close()
    print("Schema creation complete.")


if __name__ == "__main__":
    create_schema()

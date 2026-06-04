-- =============================================================================
-- validation_queries.sql
-- =============================================================================
-- Assessment: Python Training Task Assessment
-- Purpose   : Demonstrate successful data loading and verify referential
--             integrity across all tables in drilling_operations.db.
--
-- How to run:
--   Option A (SQLite CLI):
--     sqlite3 drilling_operations.db < validation_queries.sql
--   Option B (Python):
--     python -c "import sqlite3; conn=sqlite3.connect('drilling_operations.db'); [print(conn.execute(open('validation_queries.sql').read()).fetchall())]"
--
-- Sections:
--   1. Record counts per table
--   2. Referential integrity checks
--   3. Data quality spot-checks
--   4. Business-level sample queries
-- =============================================================================


-- ---------------------------------------------------------------------------
-- SECTION 1: Record counts per table
-- Confirms that all tables received data and none are unexpectedly empty.
-- ---------------------------------------------------------------------------

SELECT '=== SECTION 1: Row counts per table ===' AS section;

SELECT 'ProductionAssetCompany' AS table_name, COUNT(*) AS row_count FROM ProductionAssetCompany
UNION ALL
SELECT 'Region',                  COUNT(*) FROM Region
UNION ALL
SELECT 'Field',                   COUNT(*) FROM Field
UNION ALL
SELECT 'WellType',                COUNT(*) FROM WellType
UNION ALL
SELECT 'Well',                    COUNT(*) FROM Well
UNION ALL
SELECT 'Wellbore',                COUNT(*) FROM Wellbore
UNION ALL
SELECT 'RigType',                 COUNT(*) FROM RigType
UNION ALL
SELECT 'Rig',                     COUNT(*) FROM Rig
UNION ALL
SELECT 'WellOperation',           COUNT(*) FROM WellOperation
UNION ALL
SELECT 'OperationPhaseType',      COUNT(*) FROM OperationPhaseType
UNION ALL
SELECT 'WellOperationPhase',      COUNT(*) FROM WellOperationPhase
UNION ALL
SELECT 'WellOperationRigAssignment', COUNT(*) FROM WellOperationRigAssignment
UNION ALL
SELECT 'OperationPerformance',    COUNT(*) FROM OperationPerformance
UNION ALL
SELECT 'ReportType',              COUNT(*) FROM ReportType
UNION ALL
SELECT 'Report',                  COUNT(*) FROM Report
UNION ALL
SELECT 'ReportWellOperation',     COUNT(*) FROM ReportWellOperation;


-- ---------------------------------------------------------------------------
-- SECTION 2: Referential integrity checks
-- Each query should return 0 rows. Any non-zero result indicates an orphan.
-- ---------------------------------------------------------------------------

SELECT '=== SECTION 2: Referential integrity checks ===' AS section;

-- 2a. Regions without a parent PAC
SELECT 'Regions with invalid pac_id' AS check_name,
       COUNT(*) AS violations
FROM Region r
WHERE r.pac_id NOT IN (SELECT pac_id FROM ProductionAssetCompany);

-- 2b. Fields without a parent Region
SELECT 'Fields with invalid region_id' AS check_name,
       COUNT(*) AS violations
FROM Field f
WHERE f.region_id NOT IN (SELECT region_id FROM Region);

-- 2c. Wells without a parent Field
SELECT 'Wells with invalid field_id' AS check_name,
       COUNT(*) AS violations
FROM Well w
WHERE w.field_id NOT IN (SELECT field_id FROM Field);

-- 2d. WellOperations without a parent Well
SELECT 'WellOperations with invalid well_id' AS check_name,
       COUNT(*) AS violations
FROM WellOperation wo
WHERE wo.well_id NOT IN (SELECT well_id FROM Well);

-- 2e. Every WellOperation must have at least one Rig assignment
SELECT 'WellOperations missing a Rig assignment' AS check_name,
       COUNT(*) AS violations
FROM WellOperation wo
WHERE NOT EXISTS (
    SELECT 1 FROM WellOperationRigAssignment a
    WHERE a.well_operation_id = wo.well_operation_id
);

-- 2f. Every WellOperation must have an OperationPerformance record
SELECT 'WellOperations missing OperationPerformance' AS check_name,
       COUNT(*) AS violations
FROM WellOperation wo
WHERE NOT EXISTS (
    SELECT 1 FROM OperationPerformance p
    WHERE p.well_operation_id = wo.well_operation_id
);

-- 2g. Every Report must be linked to a WellOperation
SELECT 'Reports not linked to any WellOperation' AS check_name,
       COUNT(*) AS violations
FROM Report r
WHERE NOT EXISTS (
    SELECT 1 FROM ReportWellOperation rwo
    WHERE rwo.report_id = r.report_id
);

-- 2h. Rigs with an invalid RigType FK
SELECT 'Rigs with invalid rig_type_id' AS check_name,
       COUNT(*) AS violations
FROM Rig rig
WHERE rig.rig_type_id IS NOT NULL
  AND rig.rig_type_id NOT IN (SELECT rig_type_id FROM RigType);

-- 2i. ReportWellOperation bridge rows with invalid FKs
SELECT 'ReportWellOperation rows with invalid report_id' AS check_name,
       COUNT(*) AS violations
FROM ReportWellOperation rwo
WHERE rwo.report_id NOT IN (SELECT report_id FROM Report);

SELECT 'ReportWellOperation rows with invalid well_operation_id' AS check_name,
       COUNT(*) AS violations
FROM ReportWellOperation rwo
WHERE rwo.well_operation_id NOT IN (SELECT well_operation_id FROM WellOperation);


-- ---------------------------------------------------------------------------
-- SECTION 3: Data quality spot-checks
-- Informational queries that surface potential data issues.
-- ---------------------------------------------------------------------------

SELECT '=== SECTION 3: Data quality spot-checks ===' AS section;

-- 3a. Lookup values loaded (WellType, RigType, ReportType)
SELECT 'WellType values' AS check_name, well_type_name AS value FROM WellType
UNION ALL
SELECT 'RigType values',  rig_type_name  FROM RigType
UNION ALL
SELECT 'ReportType values', report_type_name FROM ReportType
ORDER BY check_name, value;

-- 3b. Wells assigned to the UNKNOWN region (data quality flag from source)
SELECT 'Wells in UNKNOWN region' AS note,
       w.well_name,
       f.field_name,
       pac.pac_name
FROM Well w
JOIN Field f    ON f.field_id    = w.field_id
JOIN Region r   ON r.region_id   = f.region_id
JOIN ProductionAssetCompany pac ON pac.pac_id = r.pac_id
WHERE r.region_name = 'UNKNOWN';

-- 3c. Operations with zero AFE cost (may indicate missing / test data)
SELECT 'Operations with zero AFE cost' AS note,
       w.well_name,
       wo.operation_year,
       p.afe_cost
FROM OperationPerformance p
JOIN WellOperation wo ON wo.well_operation_id = p.well_operation_id
JOIN Well w           ON w.well_id            = wo.well_id
WHERE p.afe_cost = 0 OR p.afe_cost IS NULL;

-- 3d. Operations where actual cost exceeded AFE (cost overruns)
SELECT 'Cost overruns (FinalCost > AfeCost)' AS note,
       w.well_name,
       wo.operation_year,
       ROUND(p.afe_cost, 2)   AS afe_cost,
       ROUND(p.final_cost, 2) AS final_cost,
       ROUND(((p.final_cost - p.afe_cost) / p.afe_cost) * 100, 1) AS overrun_pct
FROM OperationPerformance p
JOIN WellOperation wo ON wo.well_operation_id = p.well_operation_id
JOIN Well w           ON w.well_id            = wo.well_id
WHERE p.final_cost > p.afe_cost
  AND p.afe_cost > 0
ORDER BY overrun_pct DESC
LIMIT 10;

-- 3e. Reports with auto-generated document names (DocumentName was null in source)
SELECT 'Reports with auto-generated names' AS note,
       COUNT(*) AS count
FROM Report
WHERE document_name LIKE 'AUTO_%';


-- ---------------------------------------------------------------------------
-- SECTION 4: Business-level sample queries
-- Demonstrate that the relational structure supports meaningful analysis.
-- ---------------------------------------------------------------------------

SELECT '=== SECTION 4: Business-level sample queries ===' AS section;

-- 4a. Full hierarchy: PAC → Region → Field → Well → Operation count
SELECT pac.pac_name,
       r.region_name,
       f.field_name,
       COUNT(DISTINCT w.well_id)        AS well_count,
       COUNT(DISTINCT wo.well_operation_id) AS operation_count
FROM ProductionAssetCompany pac
JOIN Region         r   ON r.pac_id     = pac.pac_id
JOIN Field          f   ON f.region_id  = r.region_id
JOIN Well           w   ON w.field_id   = f.field_id
JOIN WellOperation  wo  ON wo.well_id   = w.well_id
GROUP BY pac.pac_name, r.region_name, f.field_name
ORDER BY pac.pac_name, r.region_name, f.field_name;

-- 4b. Top 5 most expensive wells by AFE cost
SELECT w.well_name,
       f.field_name,
       pac.pac_name,
       wo.operation_year,
       ROUND(p.afe_cost / 1e6, 2)   AS afe_cost_mUSD,
       ROUND(p.final_cost / 1e6, 2) AS final_cost_mUSD
FROM OperationPerformance p
JOIN WellOperation          wo  ON wo.well_operation_id = p.well_operation_id
JOIN Well                   w   ON w.well_id            = wo.well_id
JOIN Field                  f   ON f.field_id           = w.field_id
JOIN Region                 r   ON r.region_id          = f.region_id
JOIN ProductionAssetCompany pac ON pac.pac_id           = r.pac_id
ORDER BY p.afe_cost DESC
LIMIT 5;

-- 4c. Average NPT percentage by RigType (higher = more non-productive time)
SELECT rt.rig_type_name,
       COUNT(DISTINCT wo.well_operation_id) AS operations,
       ROUND(AVG(p.well_npt_percentage), 2) AS avg_npt_pct,
       ROUND(MIN(p.well_npt_percentage), 2) AS min_npt_pct,
       ROUND(MAX(p.well_npt_percentage), 2) AS max_npt_pct
FROM OperationPerformance p
JOIN WellOperation              wo  ON wo.well_operation_id = p.well_operation_id
JOIN WellOperationRigAssignment a   ON a.well_operation_id  = wo.well_operation_id
JOIN Rig                        rig ON rig.rig_id           = a.rig_id
JOIN RigType                    rt  ON rt.rig_type_id       = rig.rig_type_id
GROUP BY rt.rig_type_name
ORDER BY avg_npt_pct DESC;

-- 4d. Drilling activity by year
SELECT wo.operation_year                        AS year,
       COUNT(DISTINCT wo.well_operation_id)     AS operations,
       COUNT(DISTINCT w.well_id)                AS unique_wells,
       ROUND(AVG(p.final_days), 1)              AS avg_duration_days,
       ROUND(SUM(p.final_cost) / 1e6, 2)        AS total_cost_mUSD
FROM WellOperation       wo
JOIN Well                w   ON w.well_id            = wo.well_id
JOIN OperationPerformance p  ON p.well_operation_id  = wo.well_operation_id
GROUP BY wo.operation_year
ORDER BY wo.operation_year;

-- 4e. Report coverage: how many reports per well operation
SELECT wo.well_operation_id,
       w.well_name,
       wo.operation_year,
       COUNT(rwo.report_id) AS report_count,
       GROUP_CONCAT(rt.report_type_name, ' | ') AS report_types
FROM WellOperation       wo
JOIN Well                w   ON w.well_id           = wo.well_id
JOIN ReportWellOperation rwo ON rwo.well_operation_id = wo.well_operation_id
JOIN Report              rep ON rep.report_id        = rwo.report_id
JOIN ReportType          rt  ON rt.report_type_id    = rep.report_type_id
GROUP BY wo.well_operation_id
ORDER BY report_count DESC, w.well_name
LIMIT 15;

-- 4f. Cost efficiency: planned vs actual days (schedule performance)
SELECT w.well_name,
       wo.operation_year,
       rt.rig_type_name,
       ROUND(p.afe_days, 1)    AS planned_days,
       ROUND(p.final_days, 1)  AS actual_days,
       ROUND(p.final_days - p.afe_days, 1) AS day_variance,
       CASE
           WHEN p.final_days <= p.afe_days THEN 'On/Under Schedule'
           ELSE 'Over Schedule'
       END AS schedule_status
FROM OperationPerformance       p
JOIN WellOperation              wo  ON wo.well_operation_id = p.well_operation_id
JOIN Well                       w   ON w.well_id            = wo.well_id
JOIN WellOperationRigAssignment a   ON a.well_operation_id  = wo.well_operation_id
JOIN Rig                        rig ON rig.rig_id           = a.rig_id
JOIN RigType                    rt  ON rt.rig_type_id       = rig.rig_type_id
WHERE p.afe_days > 0
ORDER BY day_variance DESC
LIMIT 15;

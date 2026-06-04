-- =========================================
-- 1. ROW COUNT CHECK (sanity check)
-- =========================================
SELECT 'REGIONS' AS TableName, COUNT(*) AS TotalRows FROM REGIONS
UNION ALL
SELECT 'PAC', COUNT(*) FROM PAC
UNION ALL
SELECT 'FIELDS', COUNT(*) FROM FIELDS
UNION ALL
SELECT 'WELLS', COUNT(*) FROM WELLS
UNION ALL
SELECT 'RIGS', COUNT(*) FROM RIGS
UNION ALL
SELECT 'WELL_OPERATIONS', COUNT(*) FROM WELL_OPERATIONS
UNION ALL
SELECT 'REPORTS', COUNT(*) FROM REPORTS;


-- =========================================
-- 2. NULL CHECKS (critical columns)
-- =========================================

-- WELLS missing FK
SELECT *
FROM WELLS
WHERE WellId IS NULL OR WellName IS NULL;

-- OPERATIONS missing FK references
SELECT *
FROM WELL_OPERATIONS
WHERE WellId IS NULL
   OR RigId IS NULL;

-- REPORTS missing OperationId
SELECT *
FROM REPORTS
WHERE OperationId IS NULL;


-- =========================================
-- 3. FOREIGN KEY INTEGRITY CHECKS
-- =========================================

-- Operations with invalid WellId
SELECT *
FROM WELL_OPERATIONS wo
LEFT JOIN WELLS w ON wo.WellId = w.WellId
WHERE w.WellId IS NULL;

-- Operations with invalid RigId
SELECT *
FROM WELL_OPERATIONS wo
LEFT JOIN RIGS r ON wo.RigId = r.RigId
WHERE r.RigId IS NULL;

-- Reports with invalid OperationId
SELECT *
FROM REPORTS rp
LEFT JOIN WELL_OPERATIONS wo ON rp.OperationId = wo.OperationId
WHERE wo.OperationId IS NULL;


-- =========================================
-- 4. DUPLICATE CHECKS
-- =========================================

-- Duplicate Wells
SELECT WellName, Year, COUNT(*) AS cnt
FROM WELLS
GROUP BY WellName, Year
HAVING COUNT(*) > 1;

-- Duplicate Fields
SELECT FieldName, COUNT(*) AS cnt
FROM FIELDS
GROUP BY FieldName
HAVING COUNT(*) > 1;

-- Duplicate Operations (business logic check)
SELECT WellId, RigId, COUNT(*) AS cnt
FROM WELL_OPERATIONS
GROUP BY WellId, RigId
HAVING COUNT(*) > 1;


-- =========================================
-- 5. DATA COMPLETENESS CHECK
-- =========================================

-- Wells without operations
SELECT w.*
FROM WELLS w
LEFT JOIN WELL_OPERATIONS wo ON w.WellId = wo.WellId
WHERE wo.WellId IS NULL;

-- Operations without reports
SELECT wo.*
FROM WELL_OPERATIONS wo
LEFT JOIN REPORTS r ON wo.OperationId = r.OperationId
WHERE r.OperationId IS NULL;


-- =========================================
-- 6. RANGE / OUTLIER CHECKS
-- =========================================

-- Negative or zero cost
SELECT *
FROM WELL_OPERATIONS
WHERE AfeCost < 0
   OR FinalCost < 0;

-- Invalid dates (end before start)
SELECT *
FROM WELL_OPERATIONS
WHERE WellEndDateTime < WellStartDateTime;
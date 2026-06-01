SELECT name FROM sqlite_master WHERE type='table';

-- Checking all the table with the value
SELECT * FROM PAC;
SELECT * FROM REGIONS;
SELECT * from RIGS;
SELECT * from FIELDS;
SELECT * from WELLS;
SELECT * from REPORTS;
SELECT * from DRILLING_OPERATIONS;

--Row Count Validation
SELECT 'PAC' AS TableName, COUNT(*) FROM PAC
UNION ALL
SELECT 'REGIONS', COUNT(*) FROM REGIONS
UNION ALL
SELECT 'FIELDS', COUNT(*) FROM FIELDS
UNION ALL
SELECT 'WELLS', COUNT(*) FROM WELLS
UNION ALL
SELECT 'RIGS', COUNT(*) FROM RIGS
UNION ALL
SELECT 'REPORTS', COUNT(*) FROM REPORTS
UNION ALL
SELECT 'DRILLING_OPERATIONS', COUNT(*) FROM DRILLING_OPERATIONS;

--Check for WellName duplication

SELECT WellName, COUNT(*)
FROM WELLS
GROUP BY WellName
HAVING COUNT(*) > 1

--Check for invalid date

SELECT *
FROM WELLS
WHERE WellEndDateTime < WellStartDateTime;


-- Verify referential integrity
SELECT F.FieldId, F.FieldName,W.WellName, W.FieldId
FROM WELLS W
LEFT JOIN FIELDS F ON W.FieldId = F.FieldId
WHERE F.FieldId IS NULL;


SELECT
    w.WellName,
    f.FieldName,
    p.PACName
FROM WELLS w
JOIN FIELDS f ON w.FieldId = f.FieldId
JOIN PAC p ON f.PACId = p.PACId
LIMIT 10;


-- Check for data quality
SELECT 
    p.PACName,
    COUNT(DISTINCT w.WellId) AS Total_Wells,
    COUNT(DISTINCT r.RigId) AS Total_Rigs,
    COUNT(DISTINCT d.DrillingId) AS Total_Operations
FROM PAC p
LEFT JOIN FIELDS f ON p.PACId = f.PACId
LEFT JOIN WELLS w ON f.FieldId = w.FieldId
LEFT JOIN DRILLING_OPERATIONS d ON w.WellId = d.WellId
LEFT JOIN RIGS r ON d.RigId = r.RigId
GROUP BY p.PACName

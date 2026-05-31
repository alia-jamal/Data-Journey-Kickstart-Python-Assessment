-- 1. Check total records from each table --
SELECT 'Production Asset Company (PAC)' AS table_name, COUNT(*) AS record_count FROM PAC
UNION ALL
SELECT 'Region', COUNT(*) FROM Region
UNION ALL
SELECT 'Field', COUNT(*) FROM Field
UNION ALL
SELECT 'Rig', COUNT(*) FROM Rig
UNION ALL
SELECT 'Well', COUNT(*) FROM Well
UNION ALL
SELECT 'Well Operation', COUNT(*) FROM WellOperation
UNION ALL
SELECT 'Report', COUNT(*) FROM Report;

-- 2. Verify referential integrity between parent and child tables --
--Field -> PAC (Should return 0 rows if foreign keys are working perfectly)
SELECT COUNT(*) FROM Field f LEFT JOIN PAC p ON f.pac_id = p.pac_id WHERE p.pac_id IS NULL

--Well -> Field
SELECT COUNT(*) FROM Well w LEFT JOIN Field f ON w.field_id = f.field_id WHERE f.field_id IS NULL
    
--Report -> WellOperation
SELECT COUNT(*) FROM Report r LEFT JOIN WellOperation o ON r.operation_id = o.operation_id WHERE o.operation_id IS NULL


-- 3. Check for data quality --
SELECT p.pac_name, COUNT(DISTINCT w.well_id) AS wells
FROM PAC p
INNER JOIN Field f  ON f.pac_id  = p.pac_id
INNER JOIN Well  w  ON w.field_id = f.field_id
GROUP BY p.pac_name
ORDER BY wells DESC
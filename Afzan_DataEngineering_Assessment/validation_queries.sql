-- 1. Check total records in each table (Updated to include PACs and all 3NF tables)
SELECT 'PACs' as table_name, COUNT(*) as record_count FROM pacs
UNION ALL
SELECT 'Regions', COUNT(*) FROM regions
UNION ALL
SELECT 'Fields', COUNT(*) FROM fields
UNION ALL
SELECT 'Rigs', COUNT(*) FROM rigs
UNION ALL
SELECT 'Wells', COUNT(*) FROM wells
UNION ALL
SELECT 'Well Operations', COUNT(*) FROM well_operations
UNION ALL
SELECT 'Operational Reports', COUNT(*) FROM operational_reports;

-- 2. Verify referential integrity (Ensures zero orphan wells exist)
SELECT w.well_name, w.field_id, f.field_name
FROM wells w
LEFT JOIN fields f ON w.field_id = f.field_id
WHERE f.field_id IS NULL;

-- 3. Check for data quality 
-- (Since metrics are separated in 3NF, we join the operational ledger to get accurate averages)
SELECT 
    COUNT(DISTINCT r.operation_id) as total_operations,
    COUNT(DISTINCT o.well_id) as unique_wells,
    COUNT(DISTINCT o.rig_id) as unique_rigs,
    ROUND(AVG(r.final_cost), 2) as avg_cost,
    ROUND(AVG(r.final_days), 2) as avg_days
FROM operational_reports r
JOIN well_operations o ON r.operation_id = o.operation_id;
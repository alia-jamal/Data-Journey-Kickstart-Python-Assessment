-- =====================================================================
-- ASSESSMENT DATA INTEGRITY & VALIDATION QUERIES
-- =====================================================================

-- 1. Check total records populated in each relational table
SELECT 'companies' AS table_name, COUNT(*) AS record_count FROM companies
UNION ALL
SELECT 'regions', COUNT(*) FROM regions
UNION ALL
SELECT 'fields', COUNT(*) FROM fields
UNION ALL
SELECT 'rigs', COUNT(*) FROM rigs
UNION ALL
SELECT 'wells', COUNT(*) FROM wells
UNION ALL
SELECT 'reports', COUNT(*) FROM reports
UNION ALL
SELECT 'well_operations', COUNT(*) FROM well_operations;


-- 2. Verify referential integrity between Wells, Companies, and Fields
-- (Should return 0 rows if foreign keys are working perfectly)
SELECT w.well_name, w.field_id, f.field_name, c.company_name
FROM wells w
LEFT JOIN fields f ON w.field_id = f.field_id
LEFT JOIN companies c ON w.company_id = c.company_id
WHERE f.field_id IS NULL OR c.company_id IS NULL;


-- 3. High-Level Operations Data Quality Review Aggregations
SELECT 
    COUNT(*) AS total_operational_records,
    COUNT(DISTINCT well_id) AS unique_wells_tracked,
    COUNT(DISTINCT rig_id) AS unique_rigs_utilized,
    ROUND(AVG(final_cost), 2) AS average_final_cost,
    ROUND(AVG(final_days), 2) AS average_final_days
FROM well_operations;
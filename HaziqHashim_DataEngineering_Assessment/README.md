# Data-Journey-Kickstart-Python-Assessment

# Data Engineering Assessment - Summary Report
**Candidate Name:** Haziq Hashim  
**Project Folder Name:** HaziqHashim_DataEngineering_Assessment  

---

## 1. Number of Records Loaded Into Each Table

The ETL Pipeline was executed successfully using the custom `etl_pipeline.py` script. The original flat dataset containing 138 rows was successfully cleaned, transformed, and mapped into our 3NF relational SQLite database (`drilling_operations.db`). 

The final verified record counts loaded into each table are detailed below:

| Table Name | Records Successfully Loaded | Description |
| :--- | :---: | :--- |
| `companies` | **14** | Unique Production Asset Companies (PAC) |
| `regions` | **3** | Unique geographic operational regions (PM, SK, SB) |
| `fields` | **32** | Distinct oil and gas field offshore blocks |
| `rigs` | **28** | Unique drilling rigs deployed |
| `wells` | **64** | Unique operating well systems tracked |
| `reports` | **138** | Total documentation submissions (NOOP, FWR) |
| `well_operations` | **64** | Primary operational drilling campaigns |

---

## 2. Data Quality Issues Encountered & Handling Strategy

During the **Extract** and **Transform** stages of the pipeline, several data anomalies were automatically intercepted and normalized:

* **Missing (NULL) Values:** The source CSV columns `RegionName` and `RigType` contained missing entries. The pipeline used a custom string cleanup mechanism (`clean_str`), mapping those empty items to an explicit database `NULL` (`None` in Python) to prevent empty space strings from breaking data integrity.
* **Duplicate Record Redundancy:** The original file repeated identical core well parameters across multiple reporting rows (e.g., `WellName` duplicated across multiple daily or final reports). To achieve clean 3NF compliance, subsets were dynamically subsetted using `.drop_duplicates(subset=['WellName'])` before being mapped to the parent `wells` and `well_operations` tables.
* **Unstructured Data Columns:** Future tracking columns like `CompletionCostPlan`, `CompletionCostActual`, `DrillingPlanWcpf`, and `DrillingActualWcpf` were completely empty in the source dataset. The data pipeline safely normalized them into float-compatible fields while preserving database constraints.

---

## 3. Sample Validation & Data Loading Queries

To manually run verification checks on your database, open your SQLite tool or review `validation_queries.sql`. Below are sample validation statements proving complete referential integrity:

### Query A: Verify Record Distributions
```sql
SELECT 'companies' AS table_name, COUNT(*) AS record_count FROM companies
UNION ALL
SELECT 'wells', COUNT(*) FROM wells
UNION ALL
SELECT 'well_operations', COUNT(*) FROM well_operations;
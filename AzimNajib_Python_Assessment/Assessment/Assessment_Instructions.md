# Data Engineering Assessment

## Overview
This assessment evaluates your ability to design a normalized database schema, create tables, and implement an ETL pipeline using real-world drilling operations data.

**Database:** SQLite  
**Dataset:** DataForAssessment.csv (located in `/data` folder)

---

## Assessment Tasks

### Task 1: Data Modeling & ERD Design (30 minutes)

**Objective:** Analyze the provided dataset and design a normalized database schema.

#### Requirements:
1. Review the `DataForAssessment.csv` file to understand the data structure
2. Identify entities and their relationships
3. Design an Entity-Relationship Diagram (ERD) that follows normalization principles (at least 3NF)
4. Consider the following entities in your design:
   - Production Asset Companies (PAC)
   - Regions
   - Fields
   - Wells
   - Rigs
   - Reports
   - Well Operations (Drilling & Completion)

#### Deliverables:
- ERD diagram (using tools like dbdiagram.io or draw.io)
- Brief explanation document describing:
  - Your entities and their attributes
  - Primary keys and foreign keys
  - Relationships and cardinality
  - Normalization decisions made

#### Evaluation Criteria:
- Proper identification of entities
- Correct normalization (elimination of redundancy)
- Appropriate primary and foreign key selection
- Clear relationship definitions
- Consideration of data integrity

---

### Task 2: Database Schema Creation (30 minutes)

**Objective:** Translate your ERD into SQL CREATE TABLE statements and build the database schema.

#### Requirements:
1. Create a Python script or Jupyter notebook named `create_schema.py` or `create_schema.ipynb`
- OR -
Create SQL script named `create_schema.sql`
2. Write SQL CREATE TABLE statements for all entities in your ERD
3. Define appropriate data types for each column
4. Implement primary keys, foreign keys, and constraints
5. Create the tables in a SQLite database named `drilling_operations.db`

#### Deliverables:
- Python script/notebook OR SQL script with CREATE TABLE statements
- SQLite database file (`drilling_operations.db`) with empty tables
- Comments explaining your design choices

#### Evaluation Criteria:
- Correct SQL syntax
- Appropriate data types
- Proper constraint definitions (PRIMARY KEY, FOREIGN KEY, NOT NULL, etc.)
- Referential integrity implementation
- Code organization and documentation

---

### Task 3: ETL Pipeline Implementation (60-90 minutes)

**Objective:** Build an ETL pipeline to extract data from the CSV file, transform it according to your schema, and load it into the SQLite database.

#### Requirements:
1. Create a Python script or Jupyter notebook named `etl_pipeline.py` or `etl_pipeline.ipynb`
2. Implement the following ETL stages:

   **Extract:**
   - Read data from `DataForAssessment.csv`
   - Handle data quality issues (missing values, data type mismatches)

   **Transform:**
   - Normalize the flat CSV structure into your relational schema
   - Handle duplicate records appropriately
   - Convert data types as needed (dates, numbers, strings)
   - Clean and standardize data values
   - Generate surrogate keys if needed

   **Load:**
   - Insert transformed data into appropriate tables
   - Maintain referential integrity
   - Handle errors gracefully
   - Provide logging/progress updates

3. Include data validation checks after loading

#### Deliverables:
- Python ETL script/notebook with clear sections for Extract, Transform, and Load
- Populated SQLite database (`drilling_operations.db`)
- Summary report showing:
  - Number of records loaded into each table
  - Any data quality issues encountered and how they were handled
  - Sample queries demonstrating successful data loading

#### Evaluation Criteria:
- Correct implementation of ETL logic
- Proper handling of data transformations
- Maintenance of referential integrity
- Error handling and data validation
- Code quality (readability, modularity, comments)
- Efficiency of the pipeline

---

## Technical Requirements

### Required Python Libraries:
```python
import pandas as pd
import sqlite3
from datetime import datetime
```

### Folder Structure:
```
Assessment/
├── drilling_operations.db          # Your SQLite database
├── ERD_Design/                     # Your ERD and documentation
│   ├── ERD_diagram.png (or .pdf)
│   └── design_explanation.md
├── create_schema.py (or .ipynb or .sql)    # Schema creation script
├── etl_pipeline.py (or .ipynb)     # ETL implementation
└── validation_queries.sql          # Sample queries to validate data
```

---

## Data Dictionary

The `DataForAssessment.csv` contains the following columns:

| Column Name | Description |
|-------------|-------------|
| PacName | Production Asset Company name |
| RegionName | Geographic region |
| FieldName | Oil/gas field name |
| WellName | Well identifier |
| WellType | Type of well (exploration, development, etc.) |
| RigName | Drilling rig name |
| RigType | Type of rig (jack-up, semi-sub, etc.) |
| WaterDepth | Water depth in meters |
| Year | Year of operation |
| ReportType | Type of report (NOOP, FWR) |
| DocumentName | Associated document filename |
| DocumentDate | Date of document |
| SubmittedAt | Submission timestamp |
| SubmittedBy | User who submitted |
| AfeCost | Authorization for Expenditure cost (planned) |
| AfeDays | AFE days (planned) |
| SpudDate | Well spud date |
| WellStartDateTime | Well start date and time |
| WellEndDateTime | Well end date and time |
| FinalCost | Actual final cost |
| FinalDays | Actual days taken |
| WellNptPercentageWow | NPT percentage (week-over-week) |
| WellNptPercentage | Overall NPT percentage |
| CompletionCostPlan | Planned completion cost |
| CompletionCostActual | Actual completion cost |
| DrillingPlanWcpf | Drilling plan WCPF |
| DrillingActualWcpf | Drilling actual WCPF |

---

## Submission Guidelines

### What to Submit:
1. **ERD_Design/** folder containing:
   - ERD diagram (image or PDF)
   - Design explanation document

2. **create_schema.py** or **create_schema.ipynb**
   - Schema creation code

3. **etl_pipeline.py** or **etl_pipeline.ipynb**
   - Complete ETL implementation

4. **drilling_operations.db**
   - Populated SQLite database

5. **validation_queries.sql** (optional but recommended)
   - SQL queries demonstrating data integrity

6. **README.md** (optional)
   - Summary of your approach
   - Any assumptions made
   - Known issues or limitations

### Submission Format:
- Compile all files into a folder file named: `YourName_DataEngineering_Assessment`
- Upload your assessment folder  to your own branch in the following GitHub repo : 
 `https://github.com/alia-jamal/Data-Journey-Kickstart-Python-Assessment.git`
- Ensure all file paths are relative (not absolute)
- Include a brief README if you made any special assumptions

---

## Evaluation Rubric

| Criteria | Weight | Description |
|----------|--------|-------------|
| **ERD Design** | 25% | Quality of data modeling, normalization, and documentation |
| **Schema Implementation** | 25% | Correct SQL syntax, constraints, and data types |
| **ETL Pipeline** | 35% | Functionality, data transformation logic, error handling |
| **Code Quality** | 10% | Readability, documentation, organization |
| **Data Integrity** | 5% | Referential integrity, data validation |

---

## Tips for Success

1. **Start with the ERD:** A good design makes implementation much easier
2. **Think about normalization:** Avoid data redundancy
3. **Handle NULL values:** The dataset has many missing values
4. **Use transactions:** Ensure data consistency during loading
5. **Test incrementally:** Don't wait until the end to test your code
6. **Document your decisions:** Explain why you made certain design choices
7. **Validate your data:** Write queries to check that data loaded correctly

---

## Sample Validation Queries

After completing your ETL, run queries like these to validate:

```sql
-- Check total records in each table
SELECT 'Companies' as table_name, COUNT(*) as record_count FROM companies
UNION ALL
SELECT 'Wells', COUNT(*) FROM wells
UNION ALL
SELECT 'Rigs', COUNT(*) FROM rigs;

-- Verify referential integrity
SELECT w.well_name, w.field_id, f.field_name
FROM wells w
LEFT JOIN fields f ON w.field_id = f.field_id
WHERE f.field_id IS NULL;

-- Check for data quality
SELECT 
    COUNT(*) as total_operations,
    COUNT(DISTINCT well_name) as unique_wells,
    COUNT(DISTINCT rig_name) as unique_rigs,
    AVG(final_cost) as avg_cost,
    AVG(final_days) as avg_days
FROM well_operations;
```

---

## Important Notes

- Do NOT push directly to the main branch
- Make sure all files are inside the your assessment folder
- Ensure your ETL script runs successfully before submission
- Verify the SQLite database contains populated tables
---

## Questions?

If you have questions about the assessment requirements, please ask Faiz, Alia, Amran or Fatin before beginning.

**Good luck!**
-----------------------
# *Entity Explanations*
-----------------------

## 1. Production Asset Company 
Stores information about Production Asset Companies (PACs) responsible for managing oil and gas assets.

| Attribute   | Description                   |
| ----------- | ----------------------------- |
| pac_id (PK) | Unique PAC identifier         |
| pac_name    | Production Asset Company name |

Relationships
- One PAC can manage many Fields.
- A Field belongs to exactly one PAC.
- Cardinality: 1 → Many

## 2. Region
Stores geographical operating regions.

| Attribute      | Description              |
| -------------- | ------------------------ |
| region_id (PK) | Unique region identifier |
| region_name    | Geographic region        |

Relationships
- One Region can contain many Fields.
- A Field belongs to one Region.
- Cardinality: 1 → Many

## 3. Field
Represents an oil or gas field where drilling activities occur.

| Attribute      | Description                       |
| -------------- | --------------------------------- |
| field_id (PK)  | Unique field identifier           |
| field_name     | Oil/gas field name                |
| pac_id (FK)    | References ProductionAssetCompany |
| region_id (FK) | References Region                 |

Relationships
- Belongs to one PAC.
- Belongs to one Region.
- Can contain many Wells.
- Cardinality: 1 → Many

## 4. Rig
Stores rig master information used during well operations.

| Attribute   | Description                           |
| ----------- | ------------------------------------- |
| rig_id (PK) | Unique rig identifier                 |
| rig_name    | Drilling rig name                     |
| rig_type    | Type of rig (jack-up, semi-sub, etc.) |

Relationships
- One Rig can be used in multiple Well Operations.
- Each Well Operation uses one Rig.
- Cardinality: 1 → Many

## 5. Well
Represents individual wells drilled or completed within a field.

| Attribute     | Description                                   |
| ------------- | --------------------------------------------- |
| well_id (PK)  | Unique well identifier                        |
| field_id (FK) | References Field                              |
| well_name     | Name of the well                              |
| well_type     | Type of well (exploration, development, etc.) |
| spud_date     | Well spud date                                |
| water_depth   | Water depth in meters                         |

Relationships
- Belongs to one Field.
- Can have multiple Well Operations.
- Cardinality: 1 → Many

## 6. Well Operation
Stores operational, performance, schedule, and cost information for drilling and completion activities performed on a well.

| Attribute              | Description                                  |
| ---------------------- | -------------------------------------------- |
| operation_id (PK)      | Unique well operation identifier             |
| well_id (FK)           | References Well                              |
| rig_id (FK)            | References Rig                               |
| operation_year         | Year of operation                            |
| well_start_datetime    | Well start date and time                     |
| well_end_datetime      | Well end date and time                       |
| afe_cost               | Authorization for Expenditure cost (planned) |
| afe_days               | AFE days (planned)                           |
| final_cost             | Actual final cost                            |
| final_days             | Actual days taken                            |
| npt_percentage         | Overall NPT percentage                       |
| npt_percentage_wow     | NPT percentage (week-over-week)              |
| completion_cost_plan   | Planned completion cost                      |
| completion_cost_actual | Actual completion cost                       |
| drilling_plan_wcpf     | Drilling plan WCPF                           |
| drilling_actual_wcpf   | Actual plan WCPF                             |

Relationships
- Belongs to one Well.
- Uses one Rig.
- Can have multiple Reports.
- Cardinality: 1 → Many

## 7. Report
Stores operational reports submitted for a specific well operation.

| Attribute         | Description                  |
| ----------------- | ---------------------------- |
| report_id (PK)    | Unique report identifier     |
| operation_id (FK) | References Well Operation    |
| report_type       | Type of report (NOOP, FWR)   |
| document_name     | Associated document filename |  
| document_date     | Date of document             |
| submitted_at      | Submission timestamp         |
| submitted_by      | User who submitted           |

Relationships
- Each Report belongs to one Well Operation.
- A Well Operation can have multiple Reports.
- Cardinality: 1 → Many

------------------------
# *Normalization (3NF)*
------------------------

This ERD satisfies Third Normal Form (3NF) because:

1. 1NF
    - All attributes contain atomic values.
    - No repeating groups.
2. 2NF
    - Every non-key attribute is fully dependent on its table's primary key.
3. 3NF
    - PAC, Region, Field, Well, Rig, Well Operation, and Report data are separated into distinct entities.
    - No transitive dependencies exist.
    - Descriptive attributes are stored only in their respective master tables.
    - Operational metrics are isolated within Well Operation.
    - Report metadata is isolated within Report.
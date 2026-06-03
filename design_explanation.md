# Well Drilling and Completion Performance Database Design

# 1. Entities and Attributes

## REGIONS

Stores the geographical region where fields are located.

| Attribute     | Description                      |
| ------------- | -------------------------------- |
| RegionId (PK) | Unique identifier for the region |
| RegionName    | Region name (e.g., PM, SB, SK)   |

---

## FIELDS

Stores oil and gas fields within a region.

| Attribute     | Description                     |
| ------------- | ------------------------------- |
| FieldId (PK)  | Unique identifier for the field |
| RegionId (FK) | Reference to Region             |
| FieldName     | Name of the field               |

---

## PAC

Stores the production asset companies.

| Attribute  | Description                                           |
| ---------- | ----------------------------------------------------- |
| PacId (PK) | Unique identifier for PAC                             |
| PacName    | Production Asset Company name (e.g., PCSB, Shell)     |

---

## WELLS

Stores information about individual wells.

| Attribute    | Description                                                 |
| ------------ | ----------------------------------------------------------- |
| WellId (PK)  | Unique identifier for the well                              |
| FieldId (FK) | Reference to Field                                          |
| PacId (FK)   | Reference to PAC                                            |
| WellName     | Well name                                                   |
| WellType     | Well type (e.g., Exploration, Development, Appraisal, etc.) |
| WaterDepth   | Water depth of the well                                     |
| Year         | Year of well operation                                      |

---

## RIGS

Stores drilling rig information.

| Attribute  | Description                                                 |
| ---------- | ----------------------------------------------------------- |
| RigId (PK) | Unique identifier for the rig                               |
| RigName    | Rig name                                                    |
| RigType    | Rig type (e.g., Jack-Up, Semi-Submersible, Rigless, etc.)   |

---

## WELL_OPERATIONS

Stores drilling and completion operational metrics.

| Attribute            | Description                                      |
| -------------------- | ------------------------------------------------ |
| OperationId (PK)     | Unique identifier for the operation              |
| WellId (FK)          | Reference to Well                                |
| RigId (FK)           | Reference to Rig                                 |
| SpudDate             | Well spud date                                   |
| WellStartDateTime    | Operation start time                             |
| WellEndDateTime      | Operation end time                               |
| AfeCost              | Authorization for Expenditure cost               |
| AfeDays              | Authorization for Expenditure duration (in days) |
| FinalCost            | Actual final cost                                |
| FinalDays            | Actual days taken                                |
| WellNptPercentage    | Well Non-productive time percentage              |
| WellNptPercentageWow | Well Week-over-week NPT percentage               |
| CompletionCostPlan   | Planned completion cost                          |
| CompletionCostActual | Actual completion cost                           |
| DrillingPlanWcpf     | Planned drilling performance metric              |
| DrillingActualWcpf   | Actual drilling performance metric               |

---

## REPORTS

Stores report and document information related to well operations.

| Attribute        | Description                   |
| ---------------- | ----------------------------- |
| ReportId (PK)    | Unique identifier for report  |
| OperationId (FK) | Reference to Well Operation   |
| ReportType       | Report category               |
| DocumentName     | Report document name          |
| DocumentDate     | Report date                   |
| SubmittedAt      | Submission timestamp          |
| SubmittedBy      | User who submitted the report |

---

# 2. Primary Keys and Foreign Keys

## Primary Keys

| Table           | Primary Key |
| --------------- | ----------- |
| REGIONS         | RegionId    |
| FIELDS          | FieldId     |
| PAC             | PacId       |
| WELLS           | WellId      |
| RIGS            | RigId       |
| WELL_OPERATIONS | OperationId |
| REPORTS         | ReportId    |

## Foreign Keys

| Table           | Foreign Key | References                  |
| --------------- | ----------- | --------------------------- |
| FIELDS          | RegionId    | REGIONS.RegionId            |
| WELLS           | FieldId     | FIELDS.FieldId              |
| WELLS           | PacId       | PAC.PacId                   |
| WELL_OPERATIONS | WellId      | WELLS.WellId                |
| WELL_OPERATIONS | RigId       | RIGS.RigId                  |
| REPORTS         | OperationId | WELL_OPERATIONS.OperationId |

---

# 3. Relationships and Cardinality

| Parent Table    | Child Table     | Cardinality |
| --------------- | --------------- | ----------- |
| REGIONS         | FIELDS          | One to Many |
| FIELDS          | WELLS           | One to Many |
| PAC             | WELLS           | One to Many |
| WELLS           | WELL_OPERATIONS | One to Many |
| RIGS            | WELL_OPERATIONS | One to Many |
| WELL_OPERATIONS | REPORTS         | One to Many |

### Relationship Description

* One Region can contain multiple Fields.
* One Field can contain multiple Wells.
* One PAC can operate multiple Wells.
* Each Wells belongs to only one PAC.
* One Well can have multiple operations throughout its lifecycle.
* One Rig can be assigned to multiple operations.
* One Operation can have multiple reports and documents.

---

# 4. Normalization Decisions

The database design follows Third Normal Form (3NF).

## First Normal Form (1NF)

* All attributes contain atomic values.
* No repeating groups or multi-valued columns are stored.

## Second Normal Form (2NF)

* Every non-key attribute depends entirely on the primary key of its table.
* No partial dependencies exist.

## Third Normal Form (3NF)

* Non-key attributes depend only on the primary key.
* Geographic information is separated into Region and Field tables.
* PAC information is separated from Well information.
* Rig information is stored independently from operational records.
* Report information is separated from operational data.
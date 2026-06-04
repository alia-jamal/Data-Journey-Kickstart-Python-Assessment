# ERD Design Explanation

## Scalable Well Operations Data Model

**Prepared for:** Python Assessments  
**Submission folder:** `ERD_Design/`

---

## Purpose

This document explains the proposed Entity Relationship Diagram (ERD) for a scalable well operations data model.

The design is based on the following source attributes:

- `PacName`
- `RegionName`
- `FieldName`
- `WellName`
- `WellType`
- `RigName`
- `RigType`
- `WaterDepth`
- `Year`
- `ReportType`
- `DocumentName`
- `DocumentDate`
- `SubmittedAt`
- `SubmittedBy`
- `AfeCost`
- `AfeDays`
- `SpudDate`
- `WellStartDateTime`
- `WellEndDateTime`
- `FinalCost`
- `FinalDays`
- `WellNptPercentageWow`
- `WellNptPercentage`
- `CompletionCostPlan`
- `CompletionCostActual`
- `DrillingPlanWcpf`
- `DrillingActualWcpf`

The design separates the source data into clear business domains so that the model is normalized, scalable, and easier to maintain.

---

## 1. Scope and Deliverables

The submission package should contain:

- **ERD diagram**
  - Generated separately from the dbdiagram.io DBML script.
  - Can be submitted as an image or PDF.
- **Design explanation document**
  - Describes the entities and their attributes.
  - Explains primary keys and foreign keys.
  - Explains relationships and cardinality.
  - Describes normalization and data integrity decisions.

Recommended folder structure:

```text
ERD_Design/
├── ERD_Diagram.pdf or ERD_Diagram.png
├── ERD_Design_Documentation.md
```

---

## 2. Design Approach

The data model is designed using a scalable Third Normal Form (3NF) approach.

Instead of storing all attributes in one large flat table, the model separates data into domains:

- **Asset / Business Hierarchy Domain**
  - Stores PAC, region, field, well, well type, and wellbore data.
- **Rig / Equipment Domain**
  - Stores rig and rig type data.
  - Tracks historical rig assignment using a bridge table.
- **Well Operations Domain**
  - Stores well operation/campaign-level information.
  - Supports optional operation phases such as drilling and completion.
- **Performance / Cost Metrics Domain**
  - Stores cost, duration, NPT, and WCPF metrics.
  - Supports multiple records for revisions, final values, or phase-level metrics.
- **Reports / Documents Domain**
  - Stores report metadata.
  - Uses a bridge table so one report can relate to one or many well operations.

This structure improves:

- Data normalization
- Reduction of redundancy
- Referential integrity
- Historical tracking
- Future scalability for analytics, machine learning, deep learning, and GenAI/RAG use cases

---

## 3. Domain-Based Entity Design

### 3.1 Asset / Business Hierarchy Domain

Entities:

- `ProductionAssetCompany`
- `Region`
- `Field`
- `WellType`
- `Well`
- `Wellbore`

Purpose:

- Stores the business and physical asset hierarchy.
- Represents the structure from PAC down to Region, Field, Well, and Wellbore.
- Keeps asset names and classifications in master/reference tables instead of repeating them in operation or report records.

Hierarchy:

```text
ProductionAssetCompany
└── Region
    └── Field
        └── Well
            └── Wellbore
```

---

### 3.2 Rig / Equipment Domain

Entities:

- `RigType`
- `Rig`
- `WellOperationRigAssignment`

Purpose:

- Stores rig master data independently from well operations.
- Normalizes rig type values.
- Allows one well operation to involve multiple rigs.
- Allows one rig to be assigned to multiple well operations over time.

The bridge table `WellOperationRigAssignment` is used because the relationship between `WellOperation` and `Rig` can be many-to-many.

---

### 3.3 Well Operations Domain

Entities:

- `WellOperation`
- `OperationPhaseType`
- `WellOperationPhase`

Purpose:

- Stores the overall well operation or campaign.
- Supports optional phase-level breakdowns such as Drilling, Completion, Testing, Workover, or Intervention.
- Keeps operation identity separate from detailed cost/performance values.

---

### 3.4 Performance / Cost Metrics Domain

Entity:

- `OperationPerformance`

Purpose:

- Stores measurable operation outcomes.
- Includes cost, days, NPT percentage, and WCPF metrics.
- Supports multiple records per well operation for:
  - Revisions
  - Final values
  - Operation-level metrics
  - Phase-level metrics

---

### 3.5 Reports / Documents Domain

Entities:

- `ReportType`
- `Report`
- `ReportWellOperation`

Purpose:

- Stores report and document metadata.
- Normalizes report type values.
- Allows a report to be linked to one or many well operations.
- Allows one well operation to have many reports.

The bridge table `ReportWellOperation` supports both simple and complex reporting cases.

---

## 4. Entity and Attribute Explanation

### ProductionAssetCompany

- **Primary key:** `pac_id`
- **Main attributes:**
  - `pac_name`
- **Source attribute mapped:**
  - `PacName`
- **Description:**
  - Represents the Production Asset Company.
  - `PacName` is stored once here to avoid repeated PAC names across operation and report records.

---

### Region

- **Primary key:** `region_id`
- **Foreign key:**
  - `pac_id` references `ProductionAssetCompany.pac_id`
- **Main attributes:**
  - `region_name`
- **Source attribute mapped:**
  - `RegionName`
- **Description:**
  - Represents a region under a PAC.
  - Maintains the confirmed PAC-to-Region hierarchy.

---

### Field

- **Primary key:** `field_id`
- **Foreign key:**
  - `region_id` references `Region.region_id`
- **Main attributes:**
  - `field_name`
- **Source attribute mapped:**
  - `FieldName`
- **Description:**
  - Represents an oil or gas field under a region.

---

### WellType

- **Primary key:** `well_type_id`
- **Main attributes:**
  - `well_type_name`
- **Source attribute mapped:**
  - `WellType`
- **Description:**
  - Lookup table for well classifications.
  - Reduces repeated and inconsistent well type values.

---

### Well

- **Primary key:** `well_id`
- **Foreign keys:**
  - `field_id` references `Field.field_id`
  - `well_type_id` references `WellType.well_type_id`
- **Main attributes:**
  - `well_name`
  - `water_depth`
- **Source attributes mapped:**
  - `WellName`
  - `WaterDepth`
- **Description:**
  - Stores well-level master data.
  - `WaterDepth` is placed here because it is treated as a physical well/location attribute.
  - `well_type_id` is optional because some source data may not provide a well type.

---

### Wellbore

- **Primary key:** `wellbore_id`
- **Foreign key:**
  - `well_id` references `Well.well_id`
- **Main attributes:**
  - `wellbore_name`
  - `wellbore_label`
- **Description:**
  - Represents a bore within a well.
  - Supports scalable scenarios such as main bore, sidetrack, lateral, or re-entry.
  - Optional in the overall design because some source data may only provide well-level information.

---

### RigType

- **Primary key:** `rig_type_id`
- **Main attributes:**
  - `rig_type_name`
- **Source attribute mapped:**
  - `RigType`
- **Description:**
  - Lookup table for rig classifications.
  - Reduces inconsistent rig type values.

---

### Rig

- **Primary key:** `rig_id`
- **Foreign key:**
  - `rig_type_id` references `RigType.rig_type_id`
- **Main attributes:**
  - `rig_name`
- **Source attribute mapped:**
  - `RigName`
- **Description:**
  - Stores rig master data independently from well operations.
  - A rig may be assigned to many operations over time.
  - `rig_type_id` is optional because source data may not always include rig type.

---

### WellOperation

- **Primary key:** `well_operation_id`
- **Foreign keys:**
  - `well_id` references `Well.well_id`
  - `wellbore_id` references `Wellbore.wellbore_id`
- **Main attributes:**
  - `operation_year`
  - `spud_date`
  - `well_start_datetime`
  - `well_end_datetime`
- **Source attributes mapped:**
  - `Year`
  - `SpudDate`
  - `WellStartDateTime`
  - `WellEndDateTime`
- **Description:**
  - Represents the overall well operation or campaign.
  - Rig details are not stored directly here because `WellOperationRigAssignment` handles the rig relationship.
  - `wellbore_id` is optional because an operation may be tracked only at well level.

---

### OperationPhaseType

- **Primary key:** `operation_phase_type_id`
- **Main attributes:**
  - `operation_phase_type_name`
- **Examples:**
  - Drilling
  - Completion
  - Testing
  - Workover
  - Intervention
- **Description:**
  - Lookup table for operation phase categories.
  - Avoids repeated phase names in operation phase records.

---

### WellOperationPhase

- **Primary key:** `well_operation_phase_id`
- **Foreign keys:**
  - `well_operation_id` references `WellOperation.well_operation_id`
  - `operation_phase_type_id` references `OperationPhaseType.operation_phase_type_id`
- **Main attributes:**
  - `phase_start_datetime`
  - `phase_end_datetime`
- **Description:**
  - Optional child table under `WellOperation`.
  - Allows an operation to be broken into phases when source data provides phase-level details.
  - Supports flexible modelling where some operations are only available as summary-level records.

---

### OperationPerformance

- **Primary key:** `operation_performance_id`
- **Foreign keys:**
  - `well_operation_id` references `WellOperation.well_operation_id`
  - `well_operation_phase_id` references `WellOperationPhase.well_operation_phase_id`
- **Main attributes:**
  - `performance_scope`
  - `performance_version`
  - `is_final`
  - `afe_cost`
  - `afe_days`
  - `final_cost`
  - `final_days`
  - `well_npt_percentage_wow`
  - `well_npt_percentage`
  - `completion_cost_plan`
  - `completion_cost_actual`
  - `drilling_plan_wcpf`
  - `drilling_actual_wcpf`
  - `created_at`
- **Source attributes mapped:**
  - `AfeCost`
  - `AfeDays`
  - `FinalCost`
  - `FinalDays`
  - `WellNptPercentageWow`
  - `WellNptPercentage`
  - `CompletionCostPlan`
  - `CompletionCostActual`
  - `DrillingPlanWcpf`
  - `DrillingActualWcpf`
- **Description:**
  - Stores planned and actual performance metrics.
  - Supports multiple records for revisions, phase-level metrics, and final approved values.
  - `well_operation_phase_id` is optional because some metrics apply to the whole operation rather than a specific phase.

---

### ReportType

- **Primary key:** `report_type_id`
- **Main attributes:**
  - `report_type_name`
- **Source attribute mapped:**
  - `ReportType`
- **Description:**
  - Lookup table for report categories.
  - Examples include Daily Drilling Report, Completion Report, Final Well Report, and Monthly Summary Report.

---

### Report

- **Primary key:** `report_id`
- **Foreign key:**
  - `report_type_id` references `ReportType.report_type_id`
- **Main attributes:**
  - `document_name`
  - `document_date`
  - `submitted_at`
  - `submitted_by`
- **Source attributes mapped:**
  - `DocumentName`
  - `DocumentDate`
  - `SubmittedAt`
  - `SubmittedBy`
- **Description:**
  - Stores report and document metadata.
  - Linked to well operations through `ReportWellOperation`.
  - `report_type_id` is optional because source data may not always classify the report.

---

### WellOperationRigAssignment

- **Primary key:** `well_operation_rig_assignment_id`
- **Foreign keys:**
  - `well_operation_id` references `WellOperation.well_operation_id`
  - `rig_id` references `Rig.rig_id`
- **Main attributes:**
  - `assignment_start_datetime`
  - `assignment_end_datetime`
  - `rig_role`
  - `is_primary_rig`
  - `assignment_reason`
- **Description:**
  - Bridge table between `WellOperation` and `Rig`.
  - Supports multiple rigs per operation.
  - Preserves historical rig changes and rig roles.

---

### ReportWellOperation

- **Primary key:** `report_well_operation_id`
- **Foreign keys:**
  - `report_id` references `Report.report_id`
  - `well_operation_id` references `WellOperation.well_operation_id`
- **Main attributes:**
  - `relationship_type`
- **Description:**
  - Bridge table between `Report` and `WellOperation`.
  - Supports reports that cover one or many well operations.
  - `relationship_type` distinguishes whether the report is the primary subject, supporting reference, or summary coverage.

---

## 5. Source Attribute Mapping

### 5.1 Asset and Hierarchy Attributes

- `PacName`
  - Stored in `ProductionAssetCompany.pac_name`
- `RegionName`
  - Stored in `Region.region_name`
- `FieldName`
  - Stored in `Field.field_name`
- `WellName`
  - Stored in `Well.well_name`
- `WellType`
  - Stored in `WellType.well_type_name`
  - Referenced by `Well.well_type_id`
- `WaterDepth`
  - Stored in `Well.water_depth`

### 5.2 Rig Attributes

- `RigName`
  - Stored in `Rig.rig_name`
- `RigType`
  - Stored in `RigType.rig_type_name`
  - Referenced by `Rig.rig_type_id`

### 5.3 Well Operation Attributes

- `Year`
  - Stored in `WellOperation.operation_year`
- `SpudDate`
  - Stored in `WellOperation.spud_date`
- `WellStartDateTime`
  - Stored in `WellOperation.well_start_datetime`
- `WellEndDateTime`
  - Stored in `WellOperation.well_end_datetime`

### 5.4 Report Attributes

- `ReportType`
  - Stored in `ReportType.report_type_name`
  - Referenced by `Report.report_type_id`
- `DocumentName`
  - Stored in `Report.document_name`
- `DocumentDate`
  - Stored in `Report.document_date`
- `SubmittedAt`
  - Stored in `Report.submitted_at`
- `SubmittedBy`
  - Stored in `Report.submitted_by`

### 5.5 Performance and Cost Attributes

- `AfeCost`
  - Stored in `OperationPerformance.afe_cost`
- `AfeDays`
  - Stored in `OperationPerformance.afe_days`
- `FinalCost`
  - Stored in `OperationPerformance.final_cost`
- `FinalDays`
  - Stored in `OperationPerformance.final_days`
- `WellNptPercentageWow`
  - Stored in `OperationPerformance.well_npt_percentage_wow`
- `WellNptPercentage`
  - Stored in `OperationPerformance.well_npt_percentage`
- `CompletionCostPlan`
  - Stored in `OperationPerformance.completion_cost_plan`
- `CompletionCostActual`
  - Stored in `OperationPerformance.completion_cost_actual`
- `DrillingPlanWcpf`
  - Stored in `OperationPerformance.drilling_plan_wcpf`
- `DrillingActualWcpf`
  - Stored in `OperationPerformance.drilling_actual_wcpf`

---

## 6. Primary Key and Foreign Key Design

### 6.1 Primary Key Approach

The model uses surrogate/generated identifiers as primary keys.

Examples:

- `pac_id`
- `region_id`
- `field_id`
- `well_id`
- `wellbore_id`
- `rig_id`
- `well_operation_id`
- `report_id`

Reason:

- Business names such as `PacName`, `WellName`, and `RigName` may not be globally unique.
- Names can change over time.
- Generated IDs provide stable references across the model.

---

### 6.2 Required Foreign Keys

These foreign keys are required because the child record should not exist without the parent record:

- `Region.pac_id`
  - References `ProductionAssetCompany.pac_id`
- `Field.region_id`
  - References `Region.region_id`
- `Well.field_id`
  - References `Field.field_id`
- `Wellbore.well_id`
  - References `Well.well_id`
- `WellOperation.well_id`
  - References `Well.well_id`
- `WellOperationRigAssignment.well_operation_id`
  - References `WellOperation.well_operation_id`
- `WellOperationRigAssignment.rig_id`
  - References `Rig.rig_id`
- `WellOperationPhase.well_operation_id`
  - References `WellOperation.well_operation_id`
- `WellOperationPhase.operation_phase_type_id`
  - References `OperationPhaseType.operation_phase_type_id`
- `OperationPerformance.well_operation_id`
  - References `WellOperation.well_operation_id`
- `ReportWellOperation.report_id`
  - References `Report.report_id`
- `ReportWellOperation.well_operation_id`
  - References `WellOperation.well_operation_id`

---

### 6.3 Optional Foreign Keys

These foreign keys are optional because the source data may not always provide the information, or because the relationship may not apply in every case:

- `Well.well_type_id`
  - Optional reference to `WellType.well_type_id`
- `Rig.rig_type_id`
  - Optional reference to `RigType.rig_type_id`
- `WellOperation.wellbore_id`
  - Optional reference to `Wellbore.wellbore_id`
- `OperationPerformance.well_operation_phase_id`
  - Optional reference to `WellOperationPhase.well_operation_phase_id`
- `Report.report_type_id`
  - Optional reference to `ReportType.report_type_id`

---

## 7. Relationships and Cardinality

### ProductionAssetCompany to Region

- **Cardinality:** `1 to 0..*`
- **Implementation:** `Region.pac_id`
- **Meaning:**
  - One PAC can have zero or many Regions.
  - Each Region belongs to exactly one PAC.

---

### Region to Field

- **Cardinality:** `1 to 0..*`
- **Implementation:** `Field.region_id`
- **Meaning:**
  - One Region can have zero or many Fields.
  - Each Field belongs to exactly one Region.
  - This relationship is maintained as confirmed.

---

### Field to Well

- **Cardinality:** `1 to 0..*`
- **Implementation:** `Well.field_id`
- **Meaning:**
  - One Field can have zero or many Wells.
  - Each Well belongs to exactly one Field.

---

### WellType to Well

- **Cardinality:** `1 to 0..*`
- **Optionality:** A Well has `0..1` WellType.
- **Implementation:** `Well.well_type_id`
- **Meaning:**
  - One WellType can classify many Wells.
  - A Well may have one WellType or no WellType if the source data does not provide it.

---

### Well to Wellbore

- **Cardinality:** `1 to 0..*`
- **Implementation:** `Wellbore.well_id`
- **Meaning:**
  - One Well can have zero or many Wellbores.
  - Each Wellbore belongs to exactly one Well.

---

### Well to WellOperation

- **Cardinality:** `1 to 0..*`
- **Implementation:** `WellOperation.well_id`
- **Meaning:**
  - One Well can have zero or many operations or campaigns over time.
  - Each WellOperation belongs to exactly one Well.

---

### Wellbore to WellOperation

- **Cardinality:** `1 to 0..*`
- **Optionality:** A WellOperation has `0..1` Wellbore.
- **Implementation:** `WellOperation.wellbore_id`
- **Meaning:**
  - One Wellbore can be linked to zero or many WellOperations.
  - A WellOperation may be tracked at Well level or Wellbore level.

---

### RigType to Rig

- **Cardinality:** `1 to 0..*`
- **Optionality:** A Rig has `0..1` RigType.
- **Implementation:** `Rig.rig_type_id`
- **Meaning:**
  - One RigType can classify many Rigs.
  - A Rig may have one RigType or no RigType if the source data does not provide it.

---

### WellOperation to Rig

- **Cardinality:** `0..* to 0..*`
- **Implementation:** `WellOperationRigAssignment` bridge table
- **Meaning:**
  - One WellOperation can use multiple Rigs.
  - One Rig can support multiple WellOperations.
  - The bridge table records assignment dates, rig role, primary rig indicator, and assignment reason.

---

### WellOperation to WellOperationPhase

- **Cardinality:** `1 to 0..*`
- **Implementation:** `WellOperationPhase.well_operation_id`
- **Meaning:**
  - One WellOperation can have zero or many phases.
  - Phases are optional so summary-level operations can exist without phase records.

---

### OperationPhaseType to WellOperationPhase

- **Cardinality:** `1 to 0..*`
- **Implementation:** `WellOperationPhase.operation_phase_type_id`
- **Meaning:**
  - One OperationPhaseType can be used by many WellOperationPhase records.
  - Each WellOperationPhase must have exactly one phase type.

---

### WellOperation to OperationPerformance

- **Cardinality:** `1 to 0..*`
- **Implementation:** `OperationPerformance.well_operation_id`
- **Meaning:**
  - One WellOperation can have zero or many performance records.
  - Multiple records support revisions, final values, phase-specific values, and different performance scopes.

---

### WellOperationPhase to OperationPerformance

- **Cardinality:** `1 to 0..*`
- **Optionality:** OperationPerformance has `0..1` WellOperationPhase.
- **Implementation:** `OperationPerformance.well_operation_phase_id`
- **Meaning:**
  - One WellOperationPhase can have zero or many performance records.
  - A performance record may be linked to a phase or may apply to the overall operation.

---

### ReportType to Report

- **Cardinality:** `1 to 0..*`
- **Optionality:** A Report has `0..1` ReportType.
- **Implementation:** `Report.report_type_id`
- **Meaning:**
  - One ReportType can classify many Reports.
  - A Report may have no ReportType if the source data does not provide classification.

---

### Report to WellOperation

- **Cardinality:** `0..* to 0..*`
- **Implementation:** `ReportWellOperation` bridge table
- **Meaning:**
  - One Report can cover one or many WellOperations.
  - One WellOperation can have many Reports.
  - The bridge table supports both report-specific and summary-report scenarios.

---

## 8. Bridge Table Decisions

### 8.1 WellOperationRigAssignment

Decision:

- Use a bridge table between `WellOperation` and `Rig`.

Reason:

- A well operation may involve more than one rig.
- A rig may support many well operations over time.
- A rig may be replaced during an operation.
- Different rigs may support different phases or roles.

Benefits:

- Avoids forcing `rig_id` directly into `WellOperation`.
- Supports multiple rigs per operation.
- Preserves historical rig assignment dates.
- Allows classification of rig role, such as:
  - Primary Drilling Rig
  - Replacement Rig
  - Completion Rig
  - Support Rig

---

### 8.2 ReportWellOperation

Decision:

- Use a bridge table between `Report` and `WellOperation`.

Reason:

- Some reports are specific to one well operation.
- Some reports may summarize or reference multiple operations.
- A well operation can have multiple related reports.

Benefits:

- Supports one Report linked to one WellOperation.
- Supports one Report linked to many WellOperations.
- Supports one WellOperation linked to many Reports.
- Allows relationship context through `relationship_type`, such as:
  - Primary Subject
  - Supporting Reference
  - Summary Coverage

---

## 9. Normalization Decisions

The design follows Third Normal Form (3NF) principles.

### 9.1 Separation of Entity Responsibilities

Each table stores facts about one subject only:

- `ProductionAssetCompany` stores PAC information.
- `Region` stores region information.
- `Field` stores field information.
- `Well` stores well information.
- `Rig` stores rig information.
- `WellOperation` stores operation/campaign information.
- `OperationPerformance` stores performance metrics.
- `Report` stores report metadata.

This avoids mixing master data, operational data, performance data, and document data in one table.

---

### 9.2 Elimination of Repeating Text Values

Lookup tables are used for repeated categories:

- `WellType`
- `RigType`
- `ReportType`
- `OperationPhaseType`

This improves consistency and avoids repeated free-text values.

Example:

- Without lookup table:
  - `Jack Up`
  - `Jack-up`
  - `Jackup`
- With lookup table:
  - One standardized `RigType` value is stored and referenced.

---

### 9.3 Proper Placement of Attributes

Attributes are placed based on what they describe:

- PAC, Region, Field, Well, and Rig names are stored in master tables.
- Operation dates are stored in `WellOperation`.
- Cost, days, NPT, and WCPF metrics are stored in `OperationPerformance`.
- Document metadata is stored in `Report`.
- Many-to-many relationships are stored in bridge tables.

---

### 9.4 Controlled Optionality

Nullable foreign keys are used only when justified by source data or business reality.

Examples:

- `Well.well_type_id` is optional because WellType may be missing.
- `Rig.rig_type_id` is optional because RigType may be missing.
- `WellOperation.wellbore_id` is optional because operations may be tracked only at Well level.
- `OperationPerformance.well_operation_phase_id` is optional because some metrics apply to the full operation.
- `Report.report_type_id` is optional because ReportType may be missing.

---

## 10. Data Integrity Considerations

### Entity Integrity

- Every table has a primary key.
- Each record is uniquely identifiable.

### Referential Integrity

- Foreign keys connect child records to valid parent records.
- This prevents orphan records such as:
  - Region without PAC
  - Field without Region
  - Well without Field
  - Operation without Well
  - Rig assignment without Rig or WellOperation
  - Report relationship without Report or WellOperation

### Domain Consistency

- Lookup tables standardize repeated category values.
- This reduces spelling differences and duplicate classifications.

### Mandatory Relationships

Required relationships are marked as `not null` in the DBML.

Examples:

- `Region.pac_id`
- `Field.region_id`
- `Well.field_id`
- `WellOperation.well_id`

### Optional Relationships

Optional relationships remain nullable when data may be unavailable or not applicable.

Examples:

- `Well.well_type_id`
- `Rig.rig_type_id`
- `WellOperation.wellbore_id`
- `Report.report_type_id`

### Historical Tracking

The design supports history through:

- Rig assignment start and end dates.
- Performance version number.
- Final performance indicator.
- Operation and phase start/end dates.

### Scalability

Scalability is supported through:

- Domain separation.
- Lookup tables.
- Bridge tables.
- Optional phase-level breakdown.
- Multiple performance records per operation.

---

## 11. Analytics and AI Readiness

The submitted ERD is primarily a normalized operational model, but it is suitable as a trusted source for analytics and AI use cases.

### Analytics Readiness

The model can feed downstream analytics tables such as:

- `FactWellOperationPerformance`
- `DimAsset`
- `DimRig`
- `DimDate`
- `DimOperationPhase`

Potential analytics questions supported:

- Which PAC has the highest cost variance?
- Which Region has the highest NPT percentage?
- Which RigType performs best across operations?
- Which Fields have the largest difference between AFE cost and Final cost?
- How does planned WCPF compare against actual WCPF?

---

### ML / DL Readiness

The model provides clean structured inputs for machine learning and deep learning use cases.

Potential prediction use cases:

- Cost overrun prediction
- Schedule delay prediction
- NPT risk prediction
- Final cost estimation
- Final days estimation
- WCPF performance prediction

Useful features can be derived from:

- PAC, Region, Field, and Well hierarchy
- WellType
- WaterDepth
- RigType
- Operation year
- Spud date
- AFE cost and days
- Historical NPT values
- Final cost and days
- Drilling and completion performance values

---

### GenAI / RAG Readiness

The `Report` domain can be extended later for GenAI and document intelligence.

Possible future extension tables:

- `DocumentFile`
- `DocumentTextExtraction`
- `DocumentChunk`
- `DocumentEmbedding`
- `ExtractedEntity`
- `DocumentEntityMention`

This would allow the system to support questions such as:

- Summarize all drilling issues for a selected well.
- Compare planned versus actual performance from reports.
- Retrieve source-backed answers from historical well operation reports.
- Identify repeated NPT themes across documents.

---

## 12. Final Design Summary

The final ERD design meets the required evaluation criteria:

- Proper entities are identified from the source attributes.
- Redundant values are normalized into master and lookup tables.
- Primary keys are stable surrogate identifiers.
- Foreign keys are used to enforce valid relationships.
- Bridge tables are used where many-to-many relationships exist.
- Cardinality and optionality are documented clearly.
- Data integrity is considered through required FKs, optional FKs, lookup tables, and historical tracking fields.
- The model remains scalable for future analytics, ML, DL, and GenAI extensions.

In summary, the ERD is designed as a scalable 3NF operational model that can serve as a reliable foundation for reporting, analytics, and future AI-enabled use cases.

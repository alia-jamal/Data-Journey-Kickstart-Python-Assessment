# Design Explanation – Drilling & Well Operations Data Model

## Overview

This data model is designed to represent the full lifecycle of drilling and well operations, starting from regional structure down to operational activities like drilling and completion.

The main goal here is to:
- Keep the hierarchy clean and traceable
- Avoid duplicate data caused by report-level ingestion
- Make sure each table has a clearly defined scheme
- Support operational reporting (cost, duration, performance metrics)

---

## High-Level Structure

The model follows a clear hierarchical structure:

Each level represents a more detailed breakdown of the upstream entity.

---

## 1. Regions

This is the highest level in the hierarchy.

- Each region is uniquely identified by `region_name`
- A region can have multiple PACs

****1 row per region

---

## 2. PAC

PAC sits under Region.

PAC is not globally unique. A PAC is uniquely identified by the combination of:
(region_id + pac_name)

This ensures correct handling of historical and multi-region reporting inconsistencies.

---

## 3. Fields

A field is only unique **within a PAC**.

So the correct identity is:

> (pac_id, field_name)

This avoids duplication where the same field name exists under same PACs.

---

## 4. Wells

Wells originally had duplication issues because field_name alone was used for linking.

But since fields are PAC-dependent, wells must inherit that dependency properly.

So a well is uniquely identified by:

> (field_id, well_name)

This ensures:
- No duplication across PACs
- No incorrect merging of wells from different fields with the same name

---

## 5. Rigs

Rigs are independent resources used in operations.

- No dependency on geography hierarchy
- Simply stored as master data

---

## 6. Well-Rig Assignment (Bridge Table)

This table captures the relationship between wells and rigs over time.

A well can be assigned to different rigs, and rigs can move between wells.

Fields:
- well_id
- rig_id
- start_date (optional)
- end_date (optional)

### Design decision:
Start and end dates are kept optional because:
- Not all historical data has assignment timelines
- Some records only represent current state, not full history

---

## 7. Reports

Reports are transactional records tied to wells.

Each well can have multiple reports such as:
- NOOP
- FWR
- other operational reporting types

Fields include:
- report_type
- document metadata (name, date, submission info)

---

## 8. Well Operations (Fact Table)

This is the core operational fact table.

It stores:
- cost (AFE, final cost)
- duration (AFE days, final days)
- performance metrics (NPT, WoW)

Each operation is linked to:
- a well
- optionally a rig assignment

---

## 9. Drilling Operations

Stores drilling-specific metrics.

Linked 1-to-1 with well_operations.

Includes:
- spud_date
- drilling performance metrics (plan vs actual)

---

## 10. Completion Operations

Stores completion-specific metrics.

Also linked 1-to-1 with well_operations.

Includes:
- planned vs actual completion cost

---

## Key Design Decisions

### 1. Composite Keys Matter
A major correction in this model is that:
- Field uniqueness depends on PAC
- Well uniqueness depends on Field

This prevents duplication issues seen in earlier versions.

---

### 2. Separation of Master vs Transaction Data

- Master data: regions, pac, fields, wells, rigs
- Transaction data: reports, operations, drilling, completion

This separation ensures cleaner analytics and avoids duplication from repeated ingestion rows.

---

### 3. Optional Dates in Assignment Table

We intentionally keep start_date and end_date optional because:
- Not all datasets are time-aware
- Some records only represent snapshot assignments

---

### 4. 1-to-1 Operational Extension Tables

Drilling and Completion tables are separated from well_operations because:
- Not all wells have both drilling and completion
- They represent different phases of activity

---

## Final Thoughts

The main improvement in this design is fixing the grain definition across the hierarchy.

Once PAC → Field → Well relationships are correctly defined, most duplication issues disappear naturally without needing heavy dedup logic.

The model is now stable enough for:
- ETL ingestion
- reporting layer
- performance tracking
- operational analytics

---

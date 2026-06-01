# Well Operation Report – Data Design Overview

## 1. Overview

The Well Operation Report dataset is designed to support operational reporting across wells, fields, and production activities. At first glance, the structure may look simple, but the underlying relationships introduce complexity due to how operational data is modeled and grouped.

This document explains the key design considerations and why duplicates exist in certain tables.

---

## 2. Core Data Structure

The main entities involved are:

- **Field** – Represents a geographical or operational grouping
- **Well** – Individual wells under a field
- **PAC (Production Allocation Code)** – Represents different operational or allocation contexts under a well

---

## 3. Why the Data Looks Duplicated

### 3.1 Field-Level Duplication

A single **field name is not always unique** because:
- One field can have multiple PACs
- Each PAC represents a different operational segmentation (e.g., region, allocation logic)

So even if the field name looks the same, it may appear multiple times due to different PAC values.

---

### 3.2 Well-Level Duplication

Similarly, a **well can appear multiple times** because:
- A well can belong to the same field
- But be associated with different PACs

This means:
> One well ≠ one record  
> One well + multiple PACs = multiple records

---

## 4. Key Design Decision

Instead of forcing strict uniqueness at field or well level, the design intentionally keeps PAC as part of the grain of the dataset.
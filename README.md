# Drilling Operations ETL Pipeline

## 📌 Overview
This project implements an end-to-end ETL pipeline to transform flat drilling operations data into a normalized relational database using SQLite.

## 🛠️ Features
- Data cleaning and transformation
- RigName and RigType standardization
- FinalDays calculation
- Normalization (1NF → 3NF)
- Foreign key relationships
- Logging and validation

## 📊 Data Model
Entities:
- PAC
- Regions
- Fields
- Wells
- Rigs
- Reports
- Drilling Operations

## ⚙️ How to Run

```bash
python etl_pipeline.py
``
# Data Engineering Assessment - Drilling Operations

Submission by: **[Your Name Here]**

## Overview
This repository contains a normalized database schema and an automated ETL pipeline that extracts drilling operations records from a CSV file, processes fields/data constraints, and seeds a structured SQLite database.


## Project Structure
* `create_schema.py` - Generates the  SQLite database tables.
* `etl_pipeline.py` - Clean, transforms, and uploads data using relative path dependencies.
* `drilling_operations.db` - Output SQLite database file.
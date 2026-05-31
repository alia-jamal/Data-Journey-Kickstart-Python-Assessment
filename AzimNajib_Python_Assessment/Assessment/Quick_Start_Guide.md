# Quick Start Guide - Data Engineering Assessment

## Getting Started in 5 Minutes

### Step 1: Set Up Your Environment

Create your working folder structure:

```bash
cd Assessment
mkdir ERD_Design
```

### Step 2: Explore the Data

Open Python and take a quick look at the data:

```python
import pandas as pd

# Load the data
df = pd.read_csv('../data/DataForAssessment.csv')

# Basic exploration
print(df.shape)  # Number of rows and columns
print(df.columns.tolist())  # All column names
print(df.head())  # First few rows
print(df.info())  # Data types and null counts
print(df.describe())  # Statistical summary
```

### Step 3: Identify Entities

Look for repeating patterns in the data. Ask yourself:
- What are the main "things" (entities) in this dataset?
- Which columns describe the same entity?
- What relationships exist between entities?

**Hint:** Look for columns like:
- Company/Organization names
- Location information
- Equipment/Assets
- Events/Transactions
- Documents/Reports

### Step 4: Start Your ERD

Draw your ERD on paper or use a free tool:
- **Online:** [dbdiagram.io](https://dbdiagram.io), [draw.io](https://draw.io)
- **Desktop:** Microsoft Visio, Lucidchart, or even PowerPoint

Include:
- Entity boxes with attributes
- Primary keys (underlined or marked with PK)
- Foreign keys (marked with FK)
- Relationship lines with cardinality (1:1, 1:M, M:N)

### Step 5: Create Your First Table

Start simple with one entity:

```python
import sqlite3

# Connect to database
conn = sqlite3.connect('drilling_operations.db')
cursor = conn.cursor()

# Example: Create a companies table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS companies (
        company_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
```

### Step 6: Build Your ETL Pipeline

Structure your ETL code in three clear sections:

```python
import pandas as pd
import sqlite3

# EXTRACT
def extract_data(file_path):
    """Load data from CSV"""
    df = pd.read_csv(file_path)
    return df

# TRANSFORM
def transform_data(df):
    """Clean and normalize data"""
    # Your transformation logic here
    pass

# LOAD
def load_data(data, db_path):
    """Insert data into SQLite database"""
    conn = sqlite3.connect(db_path)
    # Your loading logic here
    conn.close()

# Run the pipeline
if __name__ == "__main__":
    raw_data = extract_data('../data/DataForAssessment.csv')
    transformed_data = transform_data(raw_data)
    load_data(transformed_data, 'drilling_operations.db')
```

---

## Common Pitfalls to Avoid

❌ **Don't:** Create one giant table with all columns  
✅ **Do:** Normalize into multiple related tables

❌ **Don't:** Ignore NULL values  
✅ **Do:** Handle missing data appropriately

❌ **Don't:** Use column names with spaces  
✅ **Do:** Use snake_case or camelCase

❌ **Don't:** Forget foreign key constraints  
✅ **Do:** Define relationships properly

❌ **Don't:** Load data without validation  
✅ **Do:** Check data integrity after loading

---

## Useful Code Snippets

### Check for Duplicates
```python
# Find duplicate wells
duplicates = df[df.duplicated(subset=['WellName'], keep=False)]
print(f"Found {len(duplicates)} duplicate well records")
```

### Handle Date Conversions
```python
# Convert string dates to datetime
df['SpudDate'] = pd.to_datetime(df['SpudDate'], errors='coerce')
```

### Extract Unique Values
```python
# Get unique companies
unique_companies = df['PacName'].dropna().unique()
print(f"Found {len(unique_companies)} unique companies")
```

### Insert with Foreign Keys
```python
# Insert a well with foreign key reference
cursor.execute('''
    INSERT INTO wells (well_name, field_id, rig_id)
    VALUES (?, ?, ?)
''', (well_name, field_id, rig_id))
```

### Bulk Insert with Pandas
```python
# Fast bulk insert
df.to_sql('table_name', conn, if_exists='append', index=False)
```

---

## Time Management Tips

| Task | Suggested Time | Priority |
|------|----------------|----------|
| Data exploration | 15 min | High |
| ERD design | 30 min | High |
| Schema creation | 30 min | High |
| ETL Extract | 15 min | High |
| ETL Transform | 45 min | High |
| ETL Load | 30 min | High |
| Validation | 15 min | Medium |
| Documentation | 20 min | Medium |

**Total:** ~3 hours

---

## Quick Reference: SQLite Data Types

| Python/Pandas Type | SQLite Type |
|-------------------|-------------|
| int, int64 | INTEGER |
| float, float64 | REAL |
| str, object | TEXT |
| datetime64 | TEXT or INTEGER |
| bool | INTEGER (0 or 1) |

---

## Need Help?

1. **SQLite Documentation:** https://www.sqlite.org/docs.html
2. **Pandas Documentation:** https://pandas.pydata.org/docs/
3. **Database Normalization:** Review Module 1 materials
4. **ERD Examples:** Check course resources

---

**Ready? Start with Task 1 - ERD Design!**

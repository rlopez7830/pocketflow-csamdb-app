# PyUber Migration Guide: UQE SQL Scripts to PyUber DBAPI-2

> **Audience:** AI coding agents and developers who need to convert Intel UQE SQL scripts into Python code using the PyUber library. This guide provides deterministic rules, patterns, and worked examples so that an agent can perform the conversion correctly on the first attempt.

---

## Table of Contents

1. [What Is UQE and What Is PyUber](#1-what-is-uqe-and-what-is-pyuber)
2. [Step-by-Step Conversion Procedure](#2-step-by-step-conversion-procedure)
3. [Rule Reference: UQE Syntax to PyUber Python](#3-rule-reference-uqe-syntax-to-pyuber-python)
4. [PyUber API Usage](#4-pyuber-api-usage)
5. [Worked Example: ARIES VID History Lookup](#5-worked-example-aries-vid-history-lookup)
6. [Worked Example: ARIES Image Path Lookup](#6-worked-example-aries-image-path-lookup)
7. [Worked Example: Local SQLite Join (Eliminated)](#7-worked-example-local-sqlite-join-eliminated)
8. [Known Datasource Mappings](#8-known-datasource-mappings)
9. [Known Schema Prefix Requirements](#9-known-schema-prefix-requirements)
10. [Common Pitfalls and How to Avoid Them](#10-common-pitfalls-and-how-to-avoid-them)

---

## 1. What Is UQE and What Is PyUber

### UQE (Universal Query Engine)
UQE is an Intel-internal query tool that runs SQL against manufacturing databases. UQE scripts contain:
- An `<OPTIONS>` block with connection and output settings (e.g., `/NODE=`, `/OLEDB=`, `/CSV=`)
- A `/*BEGIN SQL*/` ... `/*END SQL*/` block with the actual SQL
- Special macros like `SQL_Get_CSV_List()` and `@[]@` table prefixes
- Multi-query pipelines where one query writes CSV files and the next reads them

### PyUber
[PyUber](https://github.com/intel-innersource/applications.manufacturing.intel.yield.pyuber) is a Python library that provides **DBAPI-2 compliant** access to the same Intel manufacturing databases. It replaces UQE for programmatic use.

### Key Differences at a Glance

| Concept | UQE Syntax | PyUber Equivalent |
|---|---|---|
| Database connection | `/NODE=ATD.ARIES` | `PyUber.connect(datasource="ATD_PROD_ARIES")` |
| Parameter binding | Hardcoded literal values in SQL | Named bind variables using `:param_name` |
| Table schema resolution | `@[]@TableName` macro | Use table name directly, or add explicit schema prefix (e.g., `A43_PROD_0.TableName`) |
| Cross-query data piping | CSV files + `SQL_Get_CSV_List()` | In-memory Python data (lists/dicts) |
| Multi-query joins | Local SQLite (via `/OLEDB=SQLite`) | Python application logic (no intermediate database) |
| Result format | Tab-delimited `.tab` / `.csv` files | Python dicts (via `row_factory=PyUber.DictionaryRow`) |
| Oracle column names | Handled by UQE output headers | **UPPERCASE** from Oracle — must be lowercased in Python |

---

## 2. Step-by-Step Conversion Procedure

> **For AI Agents:** Follow these steps in order when given a UQE SQL script to convert to PyUber Python code.

### Step 1: Parse the OPTIONS block

Extract these fields from `<OPTIONS>`:
- `/NODE=` → This is the database target. Map it to a PyUber datasource name using the [Known Datasource Mappings](#8-known-datasource-mappings) table.
- `/OLEDB=` → If `SQLite`, this query is a local join step and may not need a PyUber query at all (see Step 6).
- `/CSV=` → The output filename. Not needed in PyUber — results stay in memory.
- `/HEADERS=` → The expected output columns. Use these as a reference for your SELECT aliases.

### Step 2: Extract the SQL

Copy the SQL between `/*BEGIN SQL*/` and `/*END SQL*/`. This is the raw Oracle SQL to convert.

### Step 3: Remove or replace UQE-only syntax

Apply these transformations to the SQL:

| UQE Pattern | Action | PyUber Replacement |
|---|---|---|
| `@[]@TableName` | Remove the `@[]@` prefix | Use `TableName` directly. If the query fails with `ORA-00942` (table not found), add the appropriate schema prefix from the [Known Schema Prefix Requirements](#9-known-schema-prefix-requirements) table. |
| `SQL_Get_CSV_List("file", column, "expr")` | Remove entirely | Replace with a parameterised IN clause built from the previous query's in-memory results. See [Rule 3.4](#34-replace-sql_get_csv_list-with-dynamic-in-clauses) for the pattern. |
| Hardcoded `IN ('value1', 'value2')` for user input | Replace with bind variables | Use `:param1, :param2` syntax. See [Rule 3.3](#33-parameterise-all-user-facing-input). |
| `'\\' \|\| col1 \|\| '\' \|\| col2` (path concatenation) | Move to Python | Build file paths in Python where you can validate them against the filesystem. |

### Step 4: Identify which columns are needed downstream

The original UQE query may SELECT many columns for reporting. Only SELECT the columns your Python application actually uses. Refer to the `/HEADERS=` list and your application's data model to decide.

### Step 5: Write the PyUber Python function

Use the standard pattern from [Section 4: PyUber API Usage](#4-pyuber-api-usage). Every query function should:
1. Accept application-level inputs (e.g., a VID string, or results from a previous query)
2. Build the SQL string with named bind parameter placeholders
3. Build the parameters dict
4. Call `execute_query(sql, datasource, params=params)`
5. Return the list of lowercase-keyed dicts

### Step 6: Handle local SQLite join steps

If the UQE script has a step with `/OLEDB=SQLite` and `/NODE=.\`, this is a **local join** between CSV outputs of earlier queries. In Python:
- You already have the results from earlier queries in memory
- The join is implicit — the second query uses values from the first query's results as filter criteria
- **You do not need a SQLite database or any intermediate files.** Skip this UQE step entirely.

### Step 7: Test the query

Run the Python function and verify:
1. The connection succeeds (no `BadDataSource` error)
2. The query executes (no `ORA-00942` table-not-found error)
3. The result columns are present with lowercase keys
4. The result data matches expectations

---

## 3. Rule Reference: UQE Syntax to PyUber Python

### 3.1 Map `/NODE=` to a PyUber datasource name

The UQE `/NODE=` value is **NOT** a valid PyUber datasource name. You must map it.

**Naming pattern observed:** Replace the dot (`.`) with `_PROD_`.

```
/NODE=ATD.ARIES   →  datasource="ATD_PROD_ARIES"
/NODE=ATD.MARS    →  datasource="ATD_PROD_MARS"
```

> **WARNING:** This pattern is not guaranteed for all datasources. Always verify by testing the connection. If the connection fails with a `BadDataSource` error, the name is wrong. See [Known Datasource Mappings](#8-known-datasource-mappings) for verified names.

### 3.2 Remove `@[]@` table prefix macro

UQE uses `@[]@` as a macro that auto-resolves the schema prefix at runtime. PyUber does not support this macro.

**Action:** Remove `@[]@` from all table references. If the query then fails with `ORA-00942` (table or view does not exist), add the explicit schema prefix.

```sql
-- UQE original
SELECT * FROM @[]@F_EntityLotHist

-- PyUber: first try without prefix
SELECT * FROM F_EntityLotHist
-- If ORA-00942: add schema prefix
SELECT * FROM A43_PROD_0.F_EntityLotHist
```

See [Known Schema Prefix Requirements](#9-known-schema-prefix-requirements) for tables we have verified.

### 3.3 Parameterise all user-facing input

UQE scripts hardcode filter values. In Python, **always** use named bind variables for any value that comes from user input or application state.

```sql
-- UQE original (hardcoded)
AND u0.visualid In ('D6858KH400011')
AND u0.ws_operation In ('3041', '3040')

-- PyUber (parameterised)
AND u0.visualid = :vid
AND u0.ws_operation IN (:op1, :op2)
```

```python
params = {"vid": user_vid, "op1": "3040", "op2": "3041"}
```

**Why:** Prevents SQL injection and makes the function reusable for any input value.

### 3.4 Replace `SQL_Get_CSV_List()` with dynamic IN clauses

UQE's `SQL_Get_CSV_List(".\file.tab", COLUMN, "expr")` reads a column from a previously-generated CSV file and expands it into an IN clause at runtime.

In Python, you already have the previous query's results in memory. Build the IN clause dynamically:

```python
def _build_in_clause(prefix, values):
    """Build a parameterised IN clause from a list of values.

    Args:
        prefix: A short string to name the bind params (e.g., "lot", "vid").
        values: A list of strings to include in the IN clause.

    Returns:
        (placeholder_sql, params_dict)

    Example:
        _build_in_clause("lot", ["LOT1", "LOT2"])
        → (":lot_0, :lot_1", {"lot_0": "LOT1", "lot_1": "LOT2"})
    """
    params = {f"{prefix}_{i}": v for i, v in enumerate(values)}
    placeholders = ", ".join(f":{k}" for k in params)
    return placeholders, params
```

**Usage in SQL construction:**
```python
lots = list({str(r["lot_1"]) for r in previous_query_results})
lot_ph, lot_params = _build_in_clause("lot", lots)

sql = f"SELECT ... WHERE a0.lot IN ({lot_ph})"
params = {**lot_params, **other_params}
```

> **Why not bind a list directly?** Oracle does not support binding a Python list as a single IN parameter. Each value must be a separate named bind variable.

### 3.5 Move path concatenation from SQL to Python

UQE scripts often build file paths in SQL using Oracle string concatenation (`||`). Move this to Python where you can:
- Validate the path exists on the filesystem (`os.path.isfile()`)
- Handle edge cases (trailing backslashes, empty values)
- Log warnings for missing files

```sql
-- UQE original (path built in SQL)
'\\' || a0.image_filer_address || '\' || a0.image_relative_path || coalesce(a9.string_val_3, a9.string_val_1) AS CSAM_Image_Path
```

```python
# Python replacement (path built + validated)
server = row["image_filer_address"]
rel_path = row["image_relative_path"]
filename = row["parameter_value"]

path = f"\\\\{server}\\{rel_path}"
if not rel_path.endswith("\\"):
    path += "\\"
path += filename

if os.path.isfile(path):
    # use the path
```

### 3.6 Normalise Oracle column names to lowercase

Oracle returns column names in **UPPERCASE**. PyUber with `DictionaryRow` preserves this convention. To avoid confusion, normalise to lowercase immediately after fetching:

```python
rows = [{k.lower(): v for k, v in row.items()} for row in rows]
```

**CRITICAL:** All downstream code must then reference columns in lowercase:
```python
# CORRECT
row["visual_id"]
row["lot_1"]
row["image_filer_address"]

# WRONG — will raise KeyError
row["VISUAL_ID"]
row["LOT_1"]
row["IMAGE_FILER_ADDRESS"]
```

### 3.7 Simplify SELECT columns

UQE scripts often SELECT many columns for reporting output. When converting to a Python application, only SELECT the columns your code actually uses downstream. This reduces query time and simplifies the data model.

---

## 4. PyUber API Usage

### Installation

```bash
pip install "PyUber @ git+https://github.com/intel-innersource/applications.manufacturing.intel.yield.pyuber"
```

> **Python version:** PyUber depends on `pythonnet`, which may not build on the latest Python. Python 3.10 is verified to work. Python 3.14 does NOT work (pythonnet build fails).

### Connection Pattern

```python
import PyUber

conn = PyUber.connect(
    datasource="ATD_PROD_ARIES",       # The datasource identifier (see Section 8)
    row_factory=PyUber.DictionaryRow    # Returns rows as dicts instead of tuples
)
cursor = conn.cursor()
```

### Execute with Parameters

```python
# Named bind parameters use :param_name syntax (Oracle convention)
cursor.execute(
    "SELECT u0.visualid FROM A_Ube_Unit_Hist2 u0 WHERE u0.visualid = :vid",
    parameters={"vid": "D6357XC800004"}
)
rows = cursor.fetchall()
```

### Centralised Wrapper (Recommended)

Create a single `execute_query()` function that handles connection, execution, and column normalisation:

```python
def execute_query(sql, datasource, params=None):
    """Execute a SQL query via PyUber and return normalised results.

    Args:
        sql: SQL string with :param_name placeholders for bind variables.
        datasource: PyUber datasource identifier (e.g., "ATD_PROD_ARIES").
        params: Optional dict of named parameters.

    Returns:
        List of dicts with lowercase column-name keys.
    """
    conn = PyUber.connect(datasource=datasource, row_factory=PyUber.DictionaryRow)
    cursor = conn.cursor()
    if params:
        cursor.execute(sql, parameters=params)
    else:
        cursor.execute(sql)
    rows = cursor.fetchall()
    # Normalise Oracle uppercase column names to lowercase
    rows = [{k.lower(): v for k, v in row.items()} for row in rows]
    return rows
```

---

## 5. Worked Example: ARIES VID History Lookup

### UQE Original (Step 1.1-a1)

```
<OPTIONS>
/NODE=ATD.ARIES
/OLEDB=SQLPlus
/CSV=rociopen_a1_13033.tab
/HEADERS=last_product_desc,last_product,...,CSAM_VID,...
</OPTIONS>

/*BEGIN SQL*/
SELECT
    ...10+ columns with DENSE_RANK, product joins...
FROM A_Ube_Unit_Hist2 u0
LEFT JOIN A_MARS_Lot ml ON ...
LEFT JOIN A_MARS_Product mp ON ...
LEFT JOIN (...subquery for loss codes...) ua0 ON ...
WHERE ...
    AND u0.ws_operation In ('3041', '3040')
    AND u0.visualid In ('D6858KH400011')
/*END SQL*/
```

### Conversion Steps Applied

1. **`/NODE=ATD.ARIES`** → `datasource="ATD_PROD_ARIES"` (Rule 3.1)
2. **Hardcoded VID and operations** → Bind variables `:vid`, `:op1`, `:op2` (Rule 3.3)
3. **10+ columns with JOINs** → Reduced to 3 columns needed downstream (Rule 3.7)
4. **Product/loss-code JOINs** → Removed — not needed for image lookup (Rule 3.7)

### PyUber Result

```python
def query_aries_vid(vid):
    sql = (
        "SELECT "
        "u0.visualid AS visual_id, "
        "u0.lotnum AS lot_1, "
        "u0.ws_operation AS operation_1 "
        "FROM A_Ube_Unit_Hist2 u0 "
        "WHERE u0.ws_operation IN (:op1, :op2) "
        "AND u0.visualid = :vid"
    )
    params = {"vid": vid, "op1": "3040", "op2": "3041"}
    return execute_query(sql, "ATD_PROD_ARIES", params=params)
```

**Output:** `[{"visual_id": "D6858KH400011", "lot_1": "D6858KH4", "operation_1": "3040"}, ...]`

---

## 6. Worked Example: ARIES Image Path Lookup

### UQE Original (Step 1.1-a2)

```
<OPTIONS>
/NODE=ATD.ARIES
/OLEDB=SQLPlus
/CSV=rociopen_a2_13033.tab
/HEADERS=lot,operation,visual_id,image_filer_address,image_relative_path,parameter_name_ud,parameter_value,CSAM_Image_Path
</OPTIONS>

/*BEGIN SQL*/
SELECT DISTINCT
    a0.lot, a0.operation, a6.visual_id,
    a0.image_filer_address, a0.image_relative_path,
    a9.parameter_name AS parameter_name_ud,
    coalesce(a9.string_val_3, a9.string_val_1) AS parameter_value,
    '\\' || a0.image_filer_address || '\' || a0.image_relative_path
        || coalesce(a9.string_val_3, a9.string_val_1) AS CSAM_Image_Path
FROM A_OBJ_SESSION a0
LEFT JOIN A_OBJ_MEDIA_TESTING a3 ON ...
LEFT JOIN A_OBJ_UNIT_TESTING a6 ON ...
LEFT JOIN A_OBJ_UNIT_DATA a9 ON ... AND a9.data_source = 'DEVICEDATA'
WHERE a0.module_name IN ('FCM')
    AND (a6.visual_id In SQL_Get_CSV_List(".\rociopen_a1_13033.tab", CSAM_VID, ...))
    AND a0.operation In ('3040', '3041')
    AND (a0.lot In SQL_Get_CSV_List(".\rociopen_a1_13033.tab", CSAM_Lot, ...))
    AND a9.parameter_name = 'IMAGE_NAME'
/*END SQL*/
```

### Conversion Steps Applied

1. **`/NODE=ATD.ARIES`** → `datasource="ATD_PROD_ARIES"` (Rule 3.1)
2. **`SQL_Get_CSV_List()` for VIDs and lots** → Dynamic IN clauses from previous query results (Rule 3.4)
3. **Path concatenation in SQL** → Moved to Python `path_builder.py` with `os.path.isfile()` validation (Rule 3.5)
4. **`parameter_name_ud` column** → Removed — always `IMAGE_NAME`, not needed downstream (Rule 3.7)
5. **`CSAM_Image_Path` column** → Removed — path built in Python instead (Rule 3.5)

### PyUber Result

```python
def query_aries_image_paths(aries_results):
    # Extract unique lots and VIDs from the previous query's results
    lots = list({str(r["lot_1"]) for r in aries_results})
    vids = list({str(r["visual_id"]) for r in aries_results})

    # Build dynamic IN clauses (replaces SQL_Get_CSV_List)
    lot_ph, lot_params = _build_in_clause("lot", lots)
    vid_ph, vid_params = _build_in_clause("vid", vids)

    sql = (
        "SELECT DISTINCT "
        "a0.lot AS lot, "
        "a0.operation AS operation, "
        "a6.visual_id AS visual_id, "
        "a0.image_filer_address AS image_filer_address, "
        "a0.image_relative_path AS image_relative_path, "
        "COALESCE(a9.string_val_3, a9.string_val_1) AS parameter_value "
        "FROM A_OBJ_SESSION a0 "
        "LEFT JOIN A_OBJ_MEDIA_TESTING a3 "
        "ON a3.lao_start_ww = a0.lao_start_ww AND a3.obj_s_id = a0.obj_s_id "
        "LEFT JOIN A_OBJ_UNIT_TESTING a6 "
        "ON a6.lao_start_ww = a3.lao_start_ww AND a6.obj_s_id = a3.obj_s_id "
        "AND a6.obj_mt_id = a3.obj_mt_id "
        "LEFT JOIN A_OBJ_UNIT_DATA a9 "
        "ON a9.lao_start_ww = a6.lao_start_ww AND a9.obj_s_id = a6.obj_s_id "
        "AND a9.obj_mt_id = a6.obj_mt_id AND a9.obj_ut_id = a6.obj_ut_id "
        "AND a9.data_source = 'DEVICEDATA' "
        "WHERE a0.module_name IN ('FCM') "
        f"AND a6.visual_id IN ({vid_ph}) "
        "AND a0.operation IN (:op1, :op2) "
        f"AND a0.lot IN ({lot_ph}) "
        "AND a9.parameter_name = 'IMAGE_NAME'"
    )
    params = {**lot_params, **vid_params, "op1": "3040", "op2": "3041"}
    return execute_query(sql, "ATD_PROD_ARIES", params=params)
```

### Path Construction in Python (replaces SQL concatenation)

```python
def build_image_paths(image_path_results):
    images = []
    for row in image_path_results:
        server = str(row.get("image_filer_address", "")).strip()
        rel_path = str(row.get("image_relative_path", "")).strip()
        filename = str(row.get("parameter_value", "")).strip()
        if not server or not filename:
            continue

        base = f"\\\\{server}\\{rel_path}"
        if rel_path and not rel_path.endswith("\\"):
            base += "\\"
        path = base + filename

        if not os.path.isfile(path):
            continue  # Skip non-existent files

        images.append({
            "file_name": filename,
            "absolute_path": path,
            "source_directory": os.path.dirname(path),
        })
    return images
```

---

## 7. Worked Example: Local SQLite Join (Eliminated)

### UQE Original (Step 3 — SQLite join)

```
<OPTIONS>
/NODE=.\
/OLEDB=SQLite
/TABLE=rociopen_a1_13033.tab,rociopen_a2_13033.tab
</OPTIONS>

SELECT DISTINCT
    a1.[CSAM_VID], a1.[CSAM_Lot], ...,
    a2.[CSAM_Image_Path]
FROM [rociopen_a1_13033] a1
LEFT OUTER JOIN [rociopen_a2_13033] a2
    ON a1.[CSAM_Lot] = a2.[lot]
    AND a1.[CSAM_VID] = a2.[visual_id]
```

### Why This Step Is Eliminated

In UQE, each query writes results to a CSV file. A third step loads those CSVs into a local SQLite database and JOINs them. In Python:

1. Query 1 results are stored in a Python list: `aries_results`
2. Query 2 receives `aries_results` as input and filters by those lots/VIDs
3. The join relationship is **implicit** — Query 2 already constrains its results to the lots and VIDs from Query 1

**No intermediate files, no SQLite, no third query needed.**

### Detection Rule for AI Agents

> If a UQE step has `/OLEDB=SQLite` and `/NODE=.\`, it is a local join step. Check whether the join can be replaced by passing data between Python functions. In almost all cases, it can.

---

## 8. Known Datasource Mappings

> **For AI Agents:** When you encounter a `/NODE=` value in a UQE script, look it up in this table. If it's not listed, try the pattern `replace(node, ".", "_PROD_")` and test the connection.

| UQE `/NODE=` | PyUber `datasource=` | Verified? | Notes |
|---|---|---|---|
| `ATD.ARIES` | `ATD_PROD_ARIES` | Yes | ARIES manufacturing history |
| `ATD.MARS` | `ATD_PROD_MARS` | Yes | MARS manufacturing data |
| `.\` (local) | N/A | N/A | Local SQLite — eliminate this step (see Section 7) |

### How to Discover New Datasource Names

If the mapping table above doesn't cover your `/NODE=` value:

1. Try the pattern: `/NODE=X.Y` → `datasource="X_PROD_Y"`
2. If that fails with `BadDataSource`, try variations:
   - `X_Y` (without PROD)
   - `X_PROD_Y` (with PROD)
   - `X_DEV_Y` (development environment)
3. You can write a diagnostic script to try multiple names:

```python
import PyUber

for ds in ["ATD_ARIES", "ATD_PROD_ARIES", "ARIES", "ATD_DEV_ARIES"]:
    try:
        conn = PyUber.connect(datasource=ds, row_factory=PyUber.DictionaryRow)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        print(f"SUCCESS: {ds}")
        break
    except Exception as e:
        print(f"FAILED:  {ds} → {e}")
```

---

## 9. Known Schema Prefix Requirements

> **For AI Agents:** When a PyUber query fails with `ORA-00942` (table or view does not exist), the table may require a schema prefix. Check this table first.

| Datasource | Table Name | Schema Prefix Required? | Full Qualified Name |
|---|---|---|---|
| `ATD_PROD_ARIES` | `A_Ube_Unit_Hist2` | No | `A_Ube_Unit_Hist2` |
| `ATD_PROD_ARIES` | `A_OBJ_SESSION` | No | `A_OBJ_SESSION` |
| `ATD_PROD_ARIES` | `A_OBJ_MEDIA_TESTING` | No | `A_OBJ_MEDIA_TESTING` |
| `ATD_PROD_ARIES` | `A_OBJ_UNIT_TESTING` | No | `A_OBJ_UNIT_TESTING` |
| `ATD_PROD_ARIES` | `A_OBJ_UNIT_DATA` | No | `A_OBJ_UNIT_DATA` |
| `ATD_PROD_ARIES` | `A_MARS_Lot` | No | `A_MARS_Lot` |
| `ATD_PROD_ARIES` | `A_MARS_Product` | No | `A_MARS_Product` |
| `ATD_PROD_MARS` | `F_Lot` | Optional | `F_Lot` or `A43_PROD_0.F_Lot` |
| `ATD_PROD_MARS` | `F_EntityLotHist` | **Yes** | `A43_PROD_0.F_EntityLotHist` |
| `ATD_PROD_MARS` | `F_Calendar` | **Yes** | `A43_PROD_0.F_Calendar` |

### How to Discover Schema Prefixes for New Tables

If a query fails with `ORA-00942` after removing `@[]@`:
1. Try adding `A43_PROD_0.` as a prefix (this is the most common MARS schema)
2. If that fails, query Oracle's metadata to find the schema:
```sql
SELECT owner, table_name FROM all_tables WHERE table_name = 'YOUR_TABLE_NAME'
```

---

## 10. Common Pitfalls and How to Avoid Them

### Pitfall 1: Using the UQE `/NODE=` value directly as a PyUber datasource
- **Symptom:** `BadDataSource` error
- **Cause:** UQE node aliases (e.g., `ATD.ARIES`) are not PyUber datasource names
- **Fix:** Map using [Section 8](#8-known-datasource-mappings)

### Pitfall 2: Leaving `@[]@` prefix in table names
- **Symptom:** Oracle syntax error or unexpected results
- **Cause:** `@[]@` is a UQE macro, not valid Oracle SQL
- **Fix:** Remove `@[]@` and add explicit schema prefix if needed ([Section 9](#9-known-schema-prefix-requirements))

### Pitfall 3: Referencing columns in UPPERCASE after lowercasing
- **Symptom:** `KeyError` when accessing row dict keys
- **Cause:** Oracle returns uppercase columns; our wrapper lowercases them
- **Fix:** Always use lowercase keys in Python: `row["visual_id"]` not `row["VISUAL_ID"]`

### Pitfall 4: Trying to bind a Python list to an IN clause
- **Symptom:** Oracle bind error or wrong results  
- **Cause:** Oracle doesn't support binding a list as a single parameter
- **Fix:** Use the `_build_in_clause()` helper to create individual bind params ([Rule 3.4](#34-replace-sql_get_csv_list-with-dynamic-in-clauses))

### Pitfall 5: PyUber failing to install on newer Python
- **Symptom:** `pythonnet` build failure during pip install
- **Cause:** `pythonnet` doesn't support Python 3.14+
- **Fix:** Use Python 3.10 (`py -3.10 -m pip install ...`)

### Pitfall 6: Missing schema prefix for MARS tables
- **Symptom:** `ORA-00942: table or view does not exist`
- **Cause:** Some MARS tables require explicit schema prefix
- **Fix:** Add `A43_PROD_0.` prefix. Check [Section 9](#9-known-schema-prefix-requirements)

### Pitfall 7: Building UNC file paths in SQL without validation
- **Symptom:** Application returns paths to files that don't exist
- **Cause:** SQL concatenation can't check the filesystem
- **Fix:** Build paths in Python and verify with `os.path.isfile()` ([Rule 3.5](#35-move-path-concatenation-from-sql-to-python))

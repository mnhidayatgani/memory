# Database Schema: SQLite Factual Storage

**Date**: 2025-11-14  
**Backend**: SQLiteFactualStore  
**File**: `{db_directory}/facts.db`

## Schema Definition

```sql
-- Facts table for key-value storage with JSON serialization
-- Used by SQLiteFactualStore backend implementation

CREATE TABLE IF NOT EXISTS facts (
    -- Primary key: unique string identifier
    -- Convention: use "__prefix_name__" for system/reserved keys
    -- Examples: "__persona_name__", "__persona_tone__", "__tech_stack__"
    key TEXT PRIMARY KEY,
    
    -- JSON-serialized value (supports str, int, float, bool, list, dict, None)
    -- Stored as TEXT for maximum compatibility and debuggability
    -- Serialized with json.dumps(), deserialized with json.loads()
    json_value TEXT NOT NULL,
    
    -- Automatic timestamp tracking for auditing and debugging
    -- Updated on every INSERT OR REPLACE operation
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Index Strategy

**No additional indexes needed** for MVP:
- Primary key on `key` provides automatic B-tree index for fast lookups
- Expected scale: <1000 facts per project
- Query pattern: Single-key lookups only (no range queries, no full-text search)

Future considerations:
- If query patterns change to include prefix matching: Add index on `key` with COLLATE
- If timestamp queries become common: Add index on `updated_at`

## Usage Examples

### Insert/Update (Upsert)

```sql
-- Insert new fact or update existing (upsert semantics)
INSERT OR REPLACE INTO facts (key, json_value, updated_at)
VALUES ('__persona_name__', '"J.A.R.V.I.S."', CURRENT_TIMESTAMP);

-- Store complex JSON structure
INSERT OR REPLACE INTO facts (key, json_value, updated_at)
VALUES (
    '__tech_stack__',
    '{"python_version": "3.10", "dependencies": ["chromadb>=0.4.0", "typer>=0.9.0"]}',
    CURRENT_TIMESTAMP
);
```

### Retrieve

```sql
-- Get single fact by key
SELECT json_value FROM facts WHERE key = '__persona_name__';
-- Returns: "J.A.R.V.I.S." (as TEXT, needs json.loads() in Python)

-- Get fact with metadata
SELECT key, json_value, updated_at 
FROM facts 
WHERE key = '__tech_stack__';
```

### List All Facts

```sql
-- Get all stored facts (useful for debugging/export)
SELECT key, json_value, updated_at 
FROM facts 
ORDER BY key;
```

### Delete

```sql
-- Delete specific fact
DELETE FROM facts WHERE key = '__persona_name__';

-- Clear all facts (dangerous!)
DELETE FROM facts;
```

### Check Existence

```sql
-- Check if key exists (returns 1 if exists, 0 otherwise)
SELECT EXISTS(SELECT 1 FROM facts WHERE key = '__persona_name__');
```

## Data Types Mapping

| Python Type     | JSON Representation | Example                              |
| --------------- | ------------------- | ------------------------------------ |
| str             | string              | `"hello"`                            |
| int             | number              | `42`                                 |
| float           | number              | `3.14`                               |
| bool            | boolean             | `true` / `false`                     |
| None            | null                | `null`                               |
| list            | array               | `["a", "b", "c"]`                    |
| dict            | object              | `{"key": "value"}`                   |
| nested          | nested              | `{"items": [1, 2, {"x": true}]}`     |

## Reserved Key Conventions

### Persona Keys (Prefix: `__persona_`)

- `__persona_name__`: Persona name (str)
- `__persona_role__`: Role description (str)
- `__persona_tone__`: Communication style (str)
- `__persona_user_title__`: How to address user (str)
- `__persona_core_directive__`: Primary mission (str)
- `__persona_language_rule__`: Language handling rules (str)

### Project Metadata Keys (Prefix: `__`)

- `__project_structure__`: Directory tree and files (dict)
- `__tech_stack__`: Dependencies and versions (dict)
- `__project_root__`: Absolute path to project root (str)
- `__seeded_at__`: Timestamp of last seeding (str, ISO format)
- `__hmc_version__`: Version of HMC that created this database (str)

### User-Defined Keys (No prefix restrictions)

Applications using HMC can use any keys without `__` prefix for custom data:
- `current_feature`: Track active feature (str)
- `task_counter`: Sequential task IDs (int)
- `user_preferences`: App-specific settings (dict)

## Concurrency & Transactions

**SQLite3 Default Behavior**:
- Isolation level: SERIALIZABLE (default in Python sqlite3 module)
- Lock mode: Entire database locked during write
- Safe for single-process, multi-threaded access

**HMC Usage Pattern**:
- Each `set_fact()` is auto-committed immediately (durability)
- No long-running transactions (each operation is atomic)
- Single-user/single-process assumption per Constitution

**No explicit transaction handling needed** for MVP:
```python
# Auto-commit after each operation
hmc.set_fact("key1", "value1")  # Committed
hmc.set_fact("key2", "value2")  # Committed
# If process crashes here, key1 and key2 are both persisted
```

## Migration Strategy

**Schema Version Tracking**:
```sql
-- Store schema version for future migrations
INSERT OR REPLACE INTO facts (key, json_value, updated_at)
VALUES ('__schema_version__', '"1.0.0"', CURRENT_TIMESTAMP);
```

**Future Migrations**:
1. Check `__schema_version__` on startup
2. If version < current, run migration scripts
3. Use `ALTER TABLE` for schema changes (SQLite supports limited ALTER)
4. For major changes, create new table, copy data, drop old, rename

**No migrations needed for v1.0.0** (initial release).

## Backup & Export

### Backup Database File

```bash
# Simple file copy (ensure no active connections)
cp {db_directory}/facts.db {db_directory}/facts.db.backup
```

### Export to JSON

```python
import sqlite3
import json

conn = sqlite3.connect("facts.db")
cursor = conn.execute("SELECT key, json_value FROM facts")
export = {row[0]: json.loads(row[1]) for row in cursor}

with open("facts_export.json", "w") as f:
    json.dump(export, f, indent=2)
```

### Import from JSON

```python
import sqlite3
import json

with open("facts_export.json") as f:
    data = json.load(f)

conn = sqlite3.connect("facts.db")
for key, value in data.items():
    conn.execute(
        "INSERT OR REPLACE INTO facts (key, json_value) VALUES (?, ?)",
        (key, json.dumps(value))
    )
conn.commit()
```

## Performance Characteristics

**Expected Performance** (on modern SSD):
- Single-key lookup: <1ms
- Insert/update: <2ms
- Bulk insert (100 facts): <50ms
- Database size: ~1KB per fact (average)

**Scale Limits**:
- Tested up to: 10,000 facts (acceptable for HMC use case)
- Theoretical limit: Millions of rows (SQLite supports up to 281 TB database)
- Practical limit: Keep under 100,000 facts for <100ms query latency

## Troubleshooting

### Database Locked

**Symptom**: `sqlite3.OperationalError: database is locked`

**Cause**: Another process has exclusive write lock

**Solution**: Ensure only one process writes at a time, or increase timeout:
```python
conn = sqlite3.connect("facts.db", timeout=10.0)  # Wait up to 10 seconds
```

### Corrupted Database

**Symptom**: `sqlite3.DatabaseError: database disk image is malformed`

**Solution**: Restore from backup or export/import to new database:
```bash
sqlite3 facts.db ".dump" | sqlite3 facts_new.db
```

### Invalid JSON

**Symptom**: `json.JSONDecodeError` when retrieving fact

**Cause**: Manual database edits or bug in serialization

**Solution**: Query raw value and fix:
```sql
SELECT key, json_value FROM facts WHERE key = 'problematic_key';
-- Manually fix JSON or delete row
```

## Summary

- ✅ Simple single-table schema optimized for key-value access
- ✅ JSON serialization for flexible value types
- ✅ Automatic timestamp tracking for auditing
- ✅ No additional indexes needed for MVP scale
- ✅ Reserved key conventions for system data
- ✅ Auto-commit for immediate durability
- ✅ Export/import support for backup and migration

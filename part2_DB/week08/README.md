# Week 8 Assignment — Field Specifications, Constraints & Relationships

**Course:** Computational Paleobiology  
**Section:** 2 — Databases & Ontologies  
**Week:** 8 of 15  
**Due:** Before Week 9 session  
**Submission:** Push all files to `part2_DB/week08/` in your GitHub repository

---

## Overview

In Week 7 you produced a mission statement, a set of objectives, an entity list, a preliminary ERD, and a `schema_draft.sql` that defines your tables. That schema probably has bare-bones structure — tables exist, primary keys are declared, but most fields lack data types beyond `TEXT` and most constraints are missing.

This week you sharpen that design into a schema you could hand to a colleague and have them build on. You will:

1. Complete a full **field specification table** for every field in every table
2. Justify every **primary key** choice
3. Add **field-level constraints** (`NOT NULL`, `UNIQUE`, `DEFAULT`, `CHECK`)
4. Define **referential integrity rules** for every foreign key (`ON DELETE`, `ON UPDATE`)
5. Update your `schema.sql` to incorporate all of the above
6. Write **INSERT tests** that verify your constraints fire correctly
7. Respond to your peer reviewer's Week 7 feedback
8. Write a design reflection connecting your decisions to DB Mortals Ch 8–10

Work continues on your own research database — not the OTB dataset.

**Readings:** DB Mortals Ch 8 (Keys), Ch 9 (Field Specifications), Ch 10 (Table Relationships)

---

## Part 1 — Complete Field Specification Table 

A field specification defines every attribute of every field in every table. This is the most detailed design document you will produce and the direct input to your `schema.sql`.

**Deliverable — `field_specs.xls`**

Create one table or sheet per database table in your design. Each table/sheet must include every field (including primary keys and foreign keys) with all columns filled in.

**Required columns:**

| Column | What to write |
|--------|---------------|
| **Field name** | Exact name as it will appear in SQL (snake_case) |
| **Data type** | `INTEGER`, `TEXT`, `REAL`, `NUMERIC`, `DATE` — be specific |
| **PK / FK** | Mark `PK` if primary key, `FK → table.field` if foreign key |
| **NOT NULL** | `YES` if the field must always have a value; `NO` if NULL is permitted |
| **UNIQUE** | `YES` if no two rows may share this value; `NO` otherwise |
| **DEFAULT** | The default value, or `—` if none |
| **CHECK constraint** | The expression (e.g., `age_ma > 0`), or `—` if none |
| **Rationale** | One sentence: why this type, why this constraint |

**Example — a specimen table from a hypothetical site excavation database:**

| Field name | Data type | PK/FK | NOT NULL | UNIQUE | DEFAULT | CHECK | Rationale |
|------------|-----------|-------|----------|--------|---------|-------|-----------|
| specimen_id | INTEGER | PK | YES | YES | — | — | Surrogate key; no stable natural identifier exists for excavation finds |
| catalog_number | TEXT | — | YES | YES | — | — | Field identifier assigned at excavation; unique within this database |
| taxon_id | INTEGER | FK → taxa.taxon_id | NO | NO | — | — | NULL permitted: many specimens are indeterminate at entry time |
| element_type | TEXT | — | YES | NO | — | element_type IN ('Tooth','Cranium','Mandible','Postcranium','Indet') | Controlled vocabulary; prevents free-text variation |
| length_mm | REAL | — | NO | NO | — | length_mm > 0 | NULL permitted for fragmentary specimens; positive value required if present |
| excavation_year | INTEGER | — | YES | NO | — | excavation_year BETWEEN 1900 AND 2100 | Sanity check; rules out data entry errors |
| notes | TEXT | — | NO | NO | — | — | Free text; optional |
| created_at | TEXT | — | YES | NO | CURRENT_TIMESTAMP | — | Insertion timestamp for audit trail |

Produce a table/sheet like this for every table in your database design. If you have linking tables, include them.

**Guidance on NOT NULL:**

Distinguish carefully between "this field has no value yet" and "this field will never have a value." A specimen's taxon assignment may be unknown at entry time but could be filled in later — that is a legitimate NULL. A specimen's catalog number must exist before the row is inserted — that is NOT NULL.

**Guidance on CHECK constraints:**

Write at least one CHECK constraint for each table. Strong candidates:
- Controlled vocabularies (preparation type, habitat category, analytical method)
- Numeric ranges that have a sensible minimum or maximum (age in Ma, depth in cm, count of specimens)
- Date or year fields with realistic bounds

```
part2_DB/week08/field_specs.md
```

---

## Part 2 — Primary Key Justifications 

**Deliverable — `pk_justifications.md`**

For each table in your database, write a short paragraph (3–5 sentences) that:

1. States whether you chose a **natural key** or a **surrogate key**
2. Explains why (stability, uniqueness, global recognisability, citability in the literature)
3. Notes any **composite key** situations and why the combination is unique
4. If you have a natural key that could theoretically change (a species name, a field-assigned number), explains how you would handle that change

**For each table, use this structure:**

```
### Table: <table_name>

Key field(s): <field_name(s)>
Key type: Natural / Surrogate / Composite

Justification:
<paragraph>
```

**Example:**

```
### Table: taxa

Key field(s): taxon_id
Key type: Surrogate (INTEGER, auto-increment)

Justification:
Taxon names change with taxonomic revision — Australopithecus aethiopicus has been
placed in Paranthropus and back again within a single decade. A surrogate integer key
insulates the rest of the database from these revisions: if a species is renamed, only
the scientific_name field changes, and all foreign key references in the specimens table
remain valid. The scientific_name field is kept as a separate UNIQUE TEXT field so it
can still be searched directly.
```

```
part2_DB/week08/pk_justifications.md
```

---

## Part 3 — Foreign Key Referential Integrity 

Every foreign key relationship requires a decision about what happens when a referenced row is deleted or updated. This is the `ON DELETE` and `ON UPDATE` clause.

**Deliverable — `fk_integrity.md`**

### 3a — Relationship inventory

List every foreign key in your database in a table:

| FK field | In table | References | Cardinality | ON DELETE | ON UPDATE |
|----------|----------|------------|-------------|-----------|-----------|
| taxon_id | specimens | taxa.taxon_id | ∞:1 | SET NULL | CASCADE |
| locality_id | specimens | localities.locality_id | ∞:1 | RESTRICT | CASCADE |
| specimen_id | specimen_publications | specimens.catalog_number | ∞:1 | CASCADE | CASCADE |
| pub_id | specimen_publications | publications.pub_id | ∞:1 | CASCADE | CASCADE |

*`specimen_publications` is a linking table resolving the many-to-many relationship between specimens and publications.*

### 3b — Justifications

For each foreign key, write **two to three sentences** justifying the `ON DELETE` behavior you chose:

**`RESTRICT` / `NO ACTION`** — Deletion is blocked if any dependent rows exist. Use when the referenced row is a prerequisite for the dependent rows (deleting a locality that has specimens assigned to it should be blocked, not silently orphaned).

**`CASCADE`** — Deletion of the parent row automatically deletes all dependent rows. Use for linking table rows and other "part-of" relationships where the dependent row has no independent meaning (deleting a specimen should delete its specimen_publication links).

**`SET NULL`** — The FK field is set to NULL when the parent row is deleted. Use when the dependent row can exist without its parent (a specimen can exist even if its taxon identification is withdrawn — the taxon_id becomes NULL, not deleted).

**`SET DEFAULT`** — The FK field reverts to its DEFAULT value. Rare; use only when a meaningful default reference exists.

### 3c — Recursive and self-referential relationships (if applicable)

If any of your tables have a self-referential relationship (a taxon that is a synonym of another taxon; a site that is a subsection of a parent site), document it here and explain how you handle it.

```
part2_DB/week08/fk_integrity.md
```

---

## Part 4 — Business Rules as Constraints  *(15 points)*

DB Mortals Ch 9 covers field specifications in detail, including data types, required vs optional fields, and default values. Building on that, this part asks you to also identify your domain's business rules — those that can be enforced in SQL as constraints, and those that cannot.

**Deliverable — `business_rules.md`**

### 4a — Rule inventory

List at least **eight business rules** that apply to your database domain. For each rule:

| # | Rule | Enforceable in SQL? | Constraint type | SQL expression or note |
|---|------|---------------------|-----------------|------------------------|
| 1 | A specimen must have a catalog number before it can be entered | Yes | NOT NULL | `catalog_number TEXT NOT NULL` |
| 2 | Age in Ma must be positive | Yes | CHECK | `CHECK (age_ma > 0)` |
| 3 | A specimen cannot be assigned to more than one taxon at a time | Yes | (FK to single row) | Natural consequence of the FK — no action needed |
| 4 | Earliest age must be ≥ latest age (deeper in time = higher Ma value) | Yes | CHECK | `CHECK (earliest_age_ma >= latest_age_ma)` |
| 5 | GPS coordinates must be within valid range | Yes | CHECK | `CHECK (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)` |
| 6 | A taxon name must be unique within the database | Yes | UNIQUE | `UNIQUE (scientific_name)` |
| 7 | Analytical methods must come from the approved lab list | Partial | CHECK (enum) | `CHECK (method IN ('AMS','OSL','ESR','U-Th','K-Ar'))` |
| 8 | No specimen may be entered with a future discovery year | Yes | CHECK | `CHECK (discovery_year <= strftime('%Y', 'now'))` |
| 9 | Field notes must be recorded in the session language (English) | No | Application | Cannot enforce character set constraints in SQLite |
| 10 | All GPS readings must be verified by a second observer before final entry | No | Workflow | Requires a separate `verified_by` field and application-level logic |

### 4b — Cross-field constraints

Identify at least **two rules that span multiple fields** within a single row and write the CHECK constraint for each. Cross-field rules are some of the most valuable constraints because they catch errors that individual-field checks cannot:

```sql
-- earliest chronometric age must be deeper in time than latest
CHECK (earliest_chronometric_age_ma >= latest_chronometric_age_ma)

-- a specimen cannot be recorded as both in situ and surface find
CHECK (NOT (recovery_context = 'in situ' AND depth_cm IS NULL))
```

```
part2_DB/week08/business_rules.md
```

---

## Part 5 — Updated Schema 

Incorporate all decisions from Parts 1–4 into a revised SQL schema file.

**Deliverable — `schema.sql`**

Requirements:

- [ ] `DROP TABLE IF EXISTS` statements in reverse dependency order at the top
- [ ] `PRAGMA foreign_keys = ON;` as the first executable statement (SQLite)
- [ ] Every table has an explicit `PRIMARY KEY`
- [ ] Every `NOT NULL` constraint from Part 1 is present
- [ ] Every `UNIQUE` constraint from Part 1 is present
- [ ] Every `DEFAULT` from Part 1 is present
- [ ] Every `CHECK` constraint from Parts 1 and 4 is present
- [ ] Every foreign key has an explicit `ON DELETE` and `ON UPDATE` clause from Part 3
- [ ] A comment block at the top of the file with your name, date, and database title
- [ ] A short inline comment (`-- rationale`) on any non-obvious constraint

**Template for each table:**

```sql
-- ── <table_name> ─────────────────────────────────────────────────────────────
-- <one sentence: what this table represents>
CREATE TABLE <table_name> (
    -- Primary key
    <pk_field>  <type>  PRIMARY KEY,

    -- Required fields
    <field>     <type>  NOT NULL,

    -- Optional fields
    <field>     <type>,                    -- NULL permitted: <reason>

    -- Controlled vocabulary
    <field>     TEXT    NOT NULL
                CHECK (<field> IN (...)),

    -- Foreign keys
    <fk_field>  INTEGER NOT NULL
                REFERENCES <parent>(<pk>)
                ON DELETE <action>
                ON UPDATE <action>,

    -- Cross-field business rule
    CHECK (<expression>)
);
```

The schema must run without errors in postgreSQL or SQLite.

If using postgreSQL you'll need to set the ON_ERROR_STOP variable or else the file will continue executing past the error and exit 0 because it completed the file successfully (even though there were errors)

```bash
psql --set ON_ERROR_STOP=1 -d myresearchdb -f schema.sql
echo "Exit code: $?"
```

Or if you prefer to run it from within the psql prompt
```sql
\i schema.sql
```

For SQLite
```bash
sqlite3 test.db < schema.sql
echo "Exit code: $?"   -- should be 0
```

Commit your final schema file
```
part2_DB/week08/schema.sql
```

---

## Part 6 — Constraint Tests

A constraint that has never been tested may not work as intended. Write INSERT statements that confirm your constraints fire.

**Deliverable — `constraint_tests.sql`**

For each of the following constraint types that appear in your schema, write one passing INSERT and one failing INSERT:

| Constraint type | Passing INSERT | Failing INSERT |
|-----------------|---------------|----------------|
| NOT NULL | Valid row with all required fields | Row with NULL in a NOT NULL field |
| UNIQUE | First row with a unique value | Second row with the same value |
| CHECK (enum) | Row with a valid vocabulary term | Row with an invalid term |
| CHECK (range) | Row with a value inside the valid range | Row with a value outside it |
| CHECK (cross-field) | Row where both fields satisfy the rule | Row where the combination violates it |
| FK RESTRICT | Delete a parent row with no children | Delete a parent row that has children |
| FK CASCADE | Delete a parent row; verify children are gone | — |
| FK SET NULL | Delete a parent row; verify FK field is NULL | — |

Format:

```sql
-- ── NOT NULL on catalog_number ─────────────────────────────────────────────

-- SHOULD SUCCEED
INSERT INTO specimens (catalog_number, element_type, excavation_year)
VALUES ('KAR-2024-001', 'Tooth', 2024);

-- SHOULD FAIL: catalog_number is NOT NULL
-- Expected error: NOT NULL constraint failed: specimens.catalog_number
INSERT INTO specimens (catalog_number, element_type, excavation_year)
VALUES (NULL, 'Tooth', 2024);

-- ── CHECK on element_type ──────────────────────────────────────────────────

-- SHOULD SUCCEED
INSERT INTO specimens (catalog_number, element_type, excavation_year)
VALUES ('KAR-2024-002', 'Postcranium', 2024);

-- SHOULD FAIL: 'Fragment' is not in the controlled vocabulary
-- Expected error: CHECK constraint failed: specimens
INSERT INTO specimens (catalog_number, element_type, excavation_year)
VALUES ('KAR-2024-003', 'Fragment', 2024);
```

Run your tests and paste the actual SQLite output (or a screenshot) into a file called `constraint_test_output.txt`.

```
part2_DB/week08/constraint_tests.sql
part2_DB/week08/constraint_test_output.txt
```

---

## Part 7 — Design Reflection

**Deliverable — `design_reflection_v2.md`**

Write 300–500 words addressing the following:

1. **What changed from your Week 7 draft?** Summarise the most significant revisions — to field types, to key choices, or to relationships — and what prompted them (peer review, constraint testing, further thought).

2. **Which constraint was hardest to specify?** Describe one constraint that you found difficult to get right and why. What alternatives did you consider?

3. **What cannot be enforced in SQL?** Identify at least two business rules from Part 4 that must be enforced outside the database (in application code, lab protocol, or workflow). Why does SQL fall short for these?

4. **Connection to readings:** Reference at least two specific concepts from DB Mortals Ch 8 (Keys), Ch 9 (Field Specifications), or Ch 10 (Table Relationships). Quote or paraphrase the relevant passage and explain how it shaped a decision in your schema.

```
part2_DB/week08/design_reflection_v2.md
```

---

## Submission Checklist

Push the following to `part2_DB/week08/` in your GitHub repository:

```
week08/
├── field_specs.md               ← Part 1
├── pk_justifications.md         ← Part 2
├── fk_integrity.md              ← Part 3
├── business_rules.md            ← Part 4
├── schema.sql                   ← Part 5
├── constraint_tests.sql         ← Part 6
├── constraint_test_output.txt   ← Part 6
└── design_reflection_v2.md      ← Part 7
```

Submit to Canvas:
- PDF export of `design_reflection_v2.md`
- A link to your GitHub repository

---


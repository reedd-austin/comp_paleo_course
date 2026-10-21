# OTB Database — Field Specification Table

**Database:** `otb` (Omo–Turkana Basin Fossil Collection)  
**Schema version:** Week 9 (revised)  
**Tables:** `taxa`, `localities`, `fossils`  
**View:** `otb_fossils_export`

A field specification documents every column in the schema: its data type, key role, nullability, default value, constraints, and the reasoning behind each decision. This is the written record that justifies the choices made in `schema.sql`.

---

## Table: `taxa`

Stores the taxonomic identities assigned to fossil specimens. The OTB dataset contains duplicate scientific names paired with different identification qualifiers (e.g., *Homo* cf. and *Homo* indet.), so a surrogate primary key is used rather than relying on the name itself.

| Field | Type | Key | Nullable | Default | Constraint | Justification |
|-------|------|-----|----------|---------|------------|---------------|
| `taxon_id` | `SERIAL` | PK | No | auto-increment | — | Surrogate key. Scientific names are not unique in this dataset (same name appears with different qualifiers); a surrogate key avoids a composite natural key and simplifies foreign key references from `fossils`. |
| `scientific_name` | `TEXT` | — | No | — | `NOT NULL` | Every taxon row must have a name. `TEXT` is preferred over `VARCHAR(n)` because no meaningful maximum length exists for taxonomic names, and PostgreSQL stores both identically. |
| `identification_qualifier` | `TEXT` | — | Yes | `NULL` | — | Records identification certainty: `cf.` (confer), `aff.` (affinis), `indet.` (indeterminate). Nullable because a confident identification carries no qualifier. A CHECK constraint was considered but omitted: qualifier vocabulary evolves and new values should not require a schema change. |

---

## Table: `localities`

Stores the named collection sites. This is a reference entity — not a thin lookup table — because each place carries its own descriptive attributes. The `place` field serves as the human-readable identifier used when matching fossils during data loading.

| Field | Type | Key | Nullable | Default | Constraint | Justification |
|-------|------|-----|----------|---------|------------|---------------|
| `locality_id` | `SERIAL` | PK | No | auto-increment | — | Surrogate key. Place names are not globally unique and may be revised; a surrogate key insulates `fossils` from name changes via `ON UPDATE CASCADE`. |
| `locality` | `TEXT` | — | No | — | `NOT NULL` | The broader locality or survey area name (e.g., "Omo River Basin"). Required for all records. |
| `continent` | `TEXT` | — | No | `'Africa'` | `NOT NULL`, `CHECK (continent IN ('Africa','Asia',…))` | All OTB specimens are African. The CHECK enforces the controlled vocabulary at the database level. The default of `'Africa'` is dataset-specific and documented in a comment; it reduces data-entry burden without compromising correctness for this collection. |
| `country` | `TEXT` | — | No | — | `NOT NULL`, `CHECK (country IN ('Kenya','Ethiopia',…))` | All OTB localities fall within seven East African Rift Valley nations. `NOT NULL` with no default: country is required and must be stated explicitly. A silent default would misattribute specimens and corrupt biogeographic analyses. The CHECK enforces the vocabulary regardless of how data enters the database (loader, form, psql, DBeaver). |
| `state_province` | `TEXT` | — | Yes | `NULL` | — | Administrative subdivision below country level. Nullable because sub-national divisions are not consistently recorded across all OTB localities. |
| `region` | `TEXT` | — | Yes | `NULL` | — | Named geographic region within the country (e.g., "Turkana Basin"). Nullable; not all localities have a published regional assignment. |
| `subregion` | `TEXT` | — | Yes | `NULL` | — | Finer subdivision within a region. Nullable for the same reasons as `region`. |
| `place` | `TEXT` | — | No | — | `NOT NULL` | The specific named collection locality (e.g., "Koobi Fora", "Ileret"). Required. No CHECK constraint on allowed values: place names will grow as the dataset expands, and adding a new locality should require only an `INSERT`, not an `ALTER TABLE`. The `localities` table itself enforces the controlled vocabulary — a fossil can only reference a locality that exists. |

---

## Table: `fossils`

The central fact table. Each row is one catalogued specimen. `catalog_number` is the natural primary key — it is the stable, externally assigned identifier used by the museum and in publications.

| Field | Type | Key | Nullable | Default | Constraint | Justification |
|-------|------|-----|----------|---------|------------|---------------|
| `catalog_number` | `TEXT` | PK | No | — | `PRIMARY KEY` | Natural key. Catalog numbers (e.g., `KNM-ER 1470`) are assigned by the collecting institution and cited in all published literature. Using them as the PK means the database row shares its identifier with the published record. `TEXT` because formatting conventions vary by institution and no fixed length applies. |
| `organism_id` | `TEXT` | — | Yes | `NULL` | — | Secondary specimen identifier used in some DwC-compliant datasets. Nullable; not present for all records. |
| `preparations` | `TEXT` | — | Yes | `NULL` | — | Free-text description of physical preparation state (e.g., "cranium, cleaned"). Nullable; preparation notes are inconsistently recorded. |
| `year` | `SMALLINT` | — | Yes | `NULL` | `CHECK (year BETWEEN 1800 AND 2100)` | Year of collection. `SMALLINT` (−32768–32767) is appropriate for calendar years and signals the intended range more clearly than `INTEGER`. The CHECK rejects obviously bad values (negative years, far-future dates) without over-constraining legitimate historical collections. Nullable because collection year is not recorded for some specimens. |
| `discovered_by` | `TEXT` | — | Yes | `NULL` | — | Name of the collector or field team. Free text; no controlled vocabulary enforced. Nullable. |
| `taxon_id` | `INTEGER` | FK → `taxa` | Yes | `NULL` | `ON DELETE SET NULL`, `ON UPDATE CASCADE` | References `taxa.taxon_id`. Nullable because many specimens are taxonomically unidentified — the absence of a taxon assignment is meaningful data. `ON DELETE SET NULL` preserves the fossil record if a taxon row is removed; the specimen reverts to unidentified rather than being deleted. `ON UPDATE CASCADE` keeps the FK consistent if the PK is renumbered. |
| `date_identified` | `DATE` | — | Yes | `NULL` | — | Date the taxonomic identification was made. `DATE` (not `TEXT`) enforces ISO 8601 format and enables date arithmetic. Nullable because identification dates are not always recorded. Values in the source TSV must be cleaned to ISO format in the loader before insertion. |
| `verbatim_identification` | `TEXT` | — | Yes | `NULL` | — | The taxonomic name exactly as written in the source record, before normalization. Preserves original wording for audit and traceability. Nullable. |
| `locality_id` | `INTEGER` | FK → `localities` | No | — | `NOT NULL`, `ON DELETE RESTRICT`, `ON UPDATE CASCADE` | References `localities.locality_id`. `NOT NULL` because every specimen must have a known provenance — a fossil with no locality cannot be used in stratigraphic or biogeographic analysis. `ON DELETE RESTRICT` prevents removing a locality that still has fossils assigned to it; specimens must be reassigned first. This is stricter than the taxon FK because provenance loss is irreversible and analytically more damaging than losing a taxonomic assignment. |
| `formation` | `TEXT` | — | Yes | `NULL` | — | Geological formation (e.g., "Koobi Fora Formation"). Stored on `fossils`, not `localities`, because TSV analysis showed that a single place can span multiple formations. Nullable when formation attribution is uncertain. |
| `member` | `TEXT` | — | Yes | `NULL` | — | Stratigraphic member within the formation. On `fossils` (not `localities`) for the same reason as `formation`: individual specimens from a single place may come from different members. Nullable. |
| `bed` | `TEXT` | — | Yes | `NULL` | — | Stratigraphic bed. Same reasoning and nullability as `member`. |
| `earliest_period_or_lowest_system` | `TEXT` | — | Yes | `NULL` | — | Coarsest chronostratigraphic unit (period / system). `TEXT` because these are named units from the International Chronostratigraphic Chart with no natural numeric encoding. Nullable. |
| `latest_period_or_highest_system` | `TEXT` | — | Yes | `NULL` | — | Upper bound of the period/system range. Nullable. |
| `earliest_epoch_or_lowest_series` | `TEXT` | — | Yes | `NULL` | — | Epoch / series lower bound. Nullable. |
| `latest_epoch_or_highest_series` | `TEXT` | — | Yes | `NULL` | — | Epoch / series upper bound. Nullable. |
| `earliest_age_or_lowest_stage` | `TEXT` | — | Yes | `NULL` | — | Age / stage lower bound. Nullable. |
| `latest_age_or_highest_stage` | `TEXT` | — | Yes | `NULL` | — | Age / stage upper bound. Nullable. |
| `earliest_chronometric_age` | `NUMERIC` | — | Yes | `NULL` | CHECK (see below) | Older bound of the radiometric age range in millions of years before present (Ma). `NUMERIC` preserves exact decimal precision (e.g., 1.875 Ma) without floating-point rounding. Nullable when radiometric age is unavailable. |
| `earliest_chronometric_age_reference_system` | `TEXT` | — | Yes | `NULL` | — | The timescale or reference system used for the earliest age (e.g., "Ma"). Nullable. |
| `latest_chronometric_age` | `NUMERIC` | — | Yes | `NULL` | CHECK (see below) | Younger bound of the age range in Ma. Same type and nullability reasoning as `earliest_chronometric_age`. |
| `latest_chronometric_age_reference_system` | `TEXT` | — | Yes | `NULL` | — | Reference system for the latest age. Nullable. |
| `verbatim_chronometric_age` | `TEXT` | — | Yes | `NULL` | — | Age as written in the source publication (e.g., `"1.88–1.65 Ma"`, `"upper Burgi Member"`). Preserves the original wording for audit and for cases where the numeric bounds would lose context. Nullable. |
| `date_created` | `TIMESTAMPTZ` | — | No | `now()` | `NOT NULL` | Timestamp of row insertion. `TIMESTAMPTZ` (timestamp with time zone) records the exact moment of insertion unambiguously across time zones, enables chronological sorting, and supports filtering by load session. The default `now()` means this field never needs to be supplied in an INSERT statement. |

### CHECK constraint on chronometric age fields

```sql
CHECK (
    earliest_chronometric_age IS NULL
    OR latest_chronometric_age IS NULL
    OR earliest_chronometric_age >= latest_chronometric_age
)
```

Geological ages in Ma are measured from the present, so an older age has a *larger* numeric value. This constraint prevents logical inversions (a "latest" age that is numerically older than the "earliest") while permitting either or both fields to be `NULL`. The constraint fires only when both values are populated.

---

## View: `otb_fossils_export`

Reconstructs the original TSV column layout by joining the three tables and replacing surrogate IDs with their human-readable source values. Used for data export and round-trip verification (confirm that a loader round-trip reproduces the original TSV).

This is a read-only view; `INSERT`, `UPDATE`, and `DELETE` are not supported on it.

---

## Design decisions summarised

| Decision | Alternative considered | Reason chosen |
|----------|----------------------|---------------|
| Surrogate PK on `taxa` | Composite `(scientific_name, qualifier)` | Dataset has duplicate names; surrogate key avoids multi-column FK on `fossils` |
| Natural PK on `fossils` (`catalog_number`) | Surrogate `SERIAL` | Catalog numbers are stable, externally assigned, and cited in publications |
| `TEXT` for all string fields | `VARCHAR(n)` | PostgreSQL stores both identically; no meaningful fixed length exists |
| `NUMERIC` for age fields | `FLOAT` / `REAL` | Avoids floating-point rounding; exact decimal precision preserved |
| `country NOT NULL`, no default | `DEFAULT 'Kenya'` | A silent default would misattribute non-Kenyan specimens; the INSERT must fail if country is missing |
| No CHECK on `place` values | Hardcoded CHECK list | Place vocabulary will grow; new localities should require only an INSERT, not a schema change |
| `year SMALLINT` with range CHECK | `INTEGER` | Appropriate range for calendar years; CHECK rejects obviously invalid values |
| `date_identified DATE` | `TEXT` | Enforces ISO 8601 format; enables date arithmetic and ordering |
| `date_created TIMESTAMPTZ DEFAULT now()` | `TEXT DEFAULT CURRENT_TIMESTAMP` | Proper timestamp type; time-zone-aware; supports sorting and filtering by insertion time |
| `formation`, `member`, `bed` on `fossils` | On `localities` | A single place spans multiple stratigraphic units; these fields belong on the specimen, not the site |
| `ON DELETE RESTRICT` on locality FK | `ON DELETE SET NULL` | Provenance loss is irreversible; restrict forces deliberate reassignment before deletion |
| `ON DELETE SET NULL` on taxon FK | `ON DELETE RESTRICT` | A taxonomic revision should not cascade to deleting fossil records |

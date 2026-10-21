# OTB Database — Field Specification Table

**Database:** `otb` (Omo–Turkana Basin Fossil Collection)  
**Schema version:** Week 8  
**Tables:** `taxa`, `localities`, `fossils`

A field specification documents every column in the schema: its data type, key role, nullability, default value, constraints, and the reasoning behind each decision. This table is the written record that justifies the schema choices made in `schema.sql`.

---

## Table: `taxa`

Stores the taxonomic identities assigned to fossil specimens. Because the OTB dataset contains duplicate scientific names paired with different identification qualifiers (e.g., *Homo* cf. and *Homo* indet.), a surrogate primary key is used rather than relying on the name itself.

| Field | Type | Key | Nullable | Default | Constraint | Justification |
|-------|------|-----|----------|---------|------------|---------------|
| `taxon_id` | `SERIAL` | PK | No | auto-increment | — | Surrogate key. Scientific names are not unique in this dataset (same name appears with different qualifiers); a surrogate key avoids composite natural keys and simplifies foreign key references from `fossils`. |
| `scientific_name` | `TEXT` | — | No | — | `NOT NULL` | Every taxon row must have a name. `TEXT` is used instead of `VARCHAR(n)` because no meaningful maximum length exists for taxonomic names, and PostgreSQL stores both identically on disk. |
| `identification_qualifier` | `TEXT` | — | Yes | `NULL` | — | Records the certainty of the identification: `cf.` (confer — probably this taxon), `aff.` (affinis — similar to), `indet.` (indeterminate). Nullable because a confident identification carries no qualifier. A CHECK constraint was considered but omitted: qualifier vocabulary evolves and new values should not require a schema change. |

---

## Table: `localities`

Stores the named collection sites. This is a reference entity — not a thin lookup table — because each place carries its own descriptive attributes (formation, country). The `place` field serves as the human-readable identifier used to match fossils during data loading.

| Field | Type | Key | Nullable | Default | Constraint | Justification |
|-------|------|-----|----------|---------|------------|---------------|
| `locality_id` | `SERIAL` | PK | No | auto-increment | — | Surrogate key. Place names are not globally unique and may be revised; a surrogate key insulates `fossils` from name changes. |
| `place` | `TEXT` | — | No | — | `NOT NULL` | The named collection locality (e.g., "Koobi Fora", "Omo Shungura"). Required: a locality with no name is not meaningful. `TEXT` rather than `VARCHAR` for the same reason as `scientific_name`. |
| `formation` | `TEXT` | — | Yes | `NULL` | — | The geological formation at the locality (e.g., "Koobi Fora Formation"). Nullable because formation attribution is sometimes uncertain or unpublished for a given place. Member and bed are not stored here: TSV analysis showed that a single place spans multiple members and beds, so those fields belong on individual fossil records, not localities. |
| `country` | `TEXT` | — | No | `` | `CHECK (country IN ('Kenya','Ethiopia','Tanzania','Uganda','Eritrea','Djibouti','Somalia'))` | All OTB localities fall within the seven East African Rift Valley nations. The CHECK constraint enforces this controlled vocabulary at the database level. No default assigned. Country is required and must be entered explicitly. A silent default value could misattribute a specimen to the wrong country. |

---

## Table: `fossils`

The central fact table. Each row is one catalogued specimen. `catalog_number` is the natural primary key — it is the stable, externally assigned identifier used by the museum and in publications, and it is guaranteed unique by institutional convention.

| Field | Type | Key | Nullable | Default | Constraint | Justification |
|-------|------|-----|----------|---------|------------|---------------|
| `catalog_number` | `TEXT` | PK | No | — | PRIMARY KEY | Natural key. Catalog numbers (e.g., `KNM-ER 1470`, `L 894-1`) are assigned by the collecting institution and used in all published literature. Using them as the PK means the database row can be cited by the same identifier used in papers. `TEXT` rather than `VARCHAR` because formatting conventions vary by institution and no fixed length applies. |
| `taxon_id` | `INTEGER` | FK → `taxa` | Yes | `NULL` | `ON DELETE SET NULL`, `ON UPDATE CASCADE` | References `taxa.taxon_id`. Nullable because many specimens are taxonomically unidentified (`indet.`): the absence of a taxon assignment is meaningful data, not a data-quality problem. `ON DELETE SET NULL` preserves the fossil record if a taxon row is removed; the specimen is not lost, it simply reverts to unidentified. `ON UPDATE CASCADE` keeps the FK consistent if the surrogate key is ever renumbered (rare but possible). |
| `locality_id` | `INTEGER` | FK → `localities` | No | — | `NOT NULL`, `ON DELETE RESTRICT`, `ON UPDATE CASCADE` | References `localities.locality_id`. `NOT NULL` because every specimen must have a known provenance — a fossil with no locality cannot be meaningfully used in stratigraphic or biogeographic analysis. `ON DELETE RESTRICT` prevents removing a locality that still has fossils assigned to it; the user must reassign specimens first. This is intentionally stricter than the taxon FK: losing provenance is more damaging than losing a taxonomic assignment. |
| `earliest_chronometric_age` | `NUMERIC` | — | Yes | `NULL` | CHECK (see below) | The older bound of the specimen's age range in millions of years before present (Ma). `NUMERIC` preserves exact decimal values without floating-point rounding (relevant for ages like 1.875 Ma). Nullable because age data are available for some but not all specimens. |
| `latest_chronometric_age` | `NUMERIC` | — | Yes | `NULL` | CHECK (see below) | The younger bound of the age range in Ma. Same type and nullability reasoning as `earliest_chronometric_age`. |
| `verbatim_chronometric_age` | `TEXT` | — | Yes | `NULL` | — | The age as written in the source publication (e.g., `"1.88–1.65 Ma"`, `"upper Burgi Member"`). Preserves the original wording for audit purposes and for cases where the numeric bounds would lose context. Nullable. |
| `created_at` | `TEXT` | — | No | `CURRENT_TIMESTAMP` | `NOT NULL` | Records when the row was inserted. Useful for auditing bulk loads and tracking data-entry sessions. `TEXT` rather than `TIMESTAMP` because PostgreSQL's `CURRENT_TIMESTAMP` returns a text-compatible value and no timezone arithmetic is needed for this dataset. The default eliminates the need to supply this field during INSERT. |

### CHECK constraint on age fields

```sql
CHECK (
    earliest_chronometric_age IS NULL
    OR latest_chronometric_age IS NULL
    OR earliest_chronometric_age >= latest_chronometric_age
)
```

Geological ages in Ma are measured from the present, so an older age has a *larger* numeric value. This constraint prevents logical inversions (a "latest" age that is older than the "earliest") while allowing either or both fields to be NULL. The constraint fires only when both fields are populated.

---

## Design decisions summarised

| Decision | Alternative considered | Reason chosen |
|----------|----------------------|---------------|
| Surrogate PK on `taxa` | Composite `(scientific_name, qualifier)` | Dataset has duplicate names; surrogate key avoids multi-column FK on `fossils` |
| Natural PK on `fossils` (`catalog_number`) | Surrogate SERIAL | Catalog numbers are stable, externally assigned, and used in publications; the natural key adds meaning |
| `TEXT` for all string fields | `VARCHAR(n)` | PostgreSQL stores both identically; no meaningful length limit exists for names or catalog numbers |
| `NUMERIC` for age fields | `FLOAT` / `REAL` | Avoids floating-point rounding for values like 1.875; precision is preserved exactly |
| `ON DELETE RESTRICT` on locality FK | `ON DELETE SET NULL` | Provenance loss is irreversible and analytically damaging; restrict forces deliberate reassignment |
| `ON DELETE SET NULL` on taxon FK | `ON DELETE RESTRICT` | A taxonomic revision that removes a name should not cascade to deleting fossil records |
| CHECK on country | Application-layer validation only | Database enforces the constraint regardless of how data is inserted (loader, form, psql, DBeaver) |
| formation stored on `localities` | stored on `fossils` | Formation is consistent per place in this dataset; members and beds are on fossils (they vary per specimen within a place) |

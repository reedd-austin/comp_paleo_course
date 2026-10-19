-- schema_sqlite.sql
-- OTB Fossil Database Schema — SQLite version
-- Week 6 Assignment
--
-- Usage:
--   sqlite3 otb.db < schema_sqlite.sql
--
-- Differences from the PostgreSQL version (schema.sql):
--   - SERIAL PRIMARY KEY  →  INTEGER PRIMARY KEY
--   - NUMERIC             →  REAL
--   - setval() calls      →  not needed (SQLite tracks autoincrement internally)
--   - Foreign keys are NOT enforced by default in SQLite.
--     Run  PRAGMA foreign_keys = ON;  at the start of each session to enable them.

-- Enable foreign key enforcement for this session
PRAGMA foreign_keys = ON;

-- Drop tables if they exist (order matters: dependents first)
DROP TABLE IF EXISTS fossils;
DROP TABLE IF EXISTS localities;
DROP TABLE IF EXISTS taxa;

-- ── Taxa ─────────────────────────────────────────────────────────────────────
CREATE TABLE taxa (
    taxon_id                  INTEGER PRIMARY KEY,
    scientific_name           TEXT NOT NULL,
    identification_qualifier  TEXT
);

-- ── Localities ────────────────────────────────────────────────────────────────
CREATE TABLE localities (
    locality_id     INTEGER PRIMARY KEY,
    place           TEXT NOT NULL,
    subregion       TEXT,
    country         TEXT,
    state_province  TEXT,
    formation       TEXT,
    member          TEXT
);

-- ── Fossils ───────────────────────────────────────────────────────────────────
CREATE TABLE fossils (
    catalog_number              TEXT PRIMARY KEY,
    organism_id                 TEXT,
    preparations                TEXT,
    year                        INTEGER,
    discovered_by               TEXT,
    taxon_id                    INTEGER REFERENCES taxa(taxon_id),
    locality_id                 INTEGER REFERENCES localities(locality_id),
    earliest_epoch              TEXT,
    latest_epoch                TEXT,
    earliest_chronometric_age   REAL,
    latest_chronometric_age     REAL,
    verbatim_chronometric_age   TEXT
);

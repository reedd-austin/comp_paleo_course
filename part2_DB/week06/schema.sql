-- schema.sql
-- OTB Fossil Database Schema
-- Week 6 Assignment

-- Drop tables if they exist (for easy re-running during development)
DROP TABLE IF EXISTS fossils;
DROP TABLE IF EXISTS taxa;
DROP TABLE IF EXISTS localities;

-- ── Taxa ─────────────────────────────────────────────────────────────────────
CREATE TABLE taxa (
    taxon_id                  SERIAL PRIMARY KEY,
    scientific_name           TEXT NOT NULL,
    identification_qualifier  TEXT
);

-- ── Localities ────────────────────────────────────────────────────────────────
CREATE TABLE localities (
    locality_id     SERIAL PRIMARY KEY,
    place           TEXT NOT NULL,
    subregion       TEXT,
    country         TEXT,
    state_province  TEXT,
    formation       TEXT,
    member          TEXT,
    earliest_period_or_lowest_system TEXT,
    latest_period_or_highest_system TEXT,
    earliest_epoch_or_lowest_series TEXT,
    latest_epoch_or_highest_series TEXT,
    earliest_age_or_lowest_stage TEXT,
    latest_age_or_highest_stage TEXT
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
    earliest_chronometric_age   NUMERIC,
    latest_chronometric_age     NUMERIC,
    verbatim_chronometric_age   TEXT
);
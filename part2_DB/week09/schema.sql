-- ── OTB Fossil Database Schema ────────────────────────────────────────────────
-- Denne Reed · Computational Paleobiology · Week 9
-- Three-table design: taxa, localities, fossils
-- Run: psql -d your_db -f schema.sql

-- Drop in reverse dependency order
DROP VIEW IF EXISTS otb_fossils_export;
DROP TABLE IF EXISTS fossils;
DROP TABLE IF EXISTS taxa;
DROP TABLE IF EXISTS localities;

-- ── taxa ──────────────────────────────────────────────────────────────────────
-- Biological taxa identified among OTB specimens
CREATE TABLE taxa (
    taxon_id                 SERIAL PRIMARY KEY,
    scientific_name          TEXT   NOT NULL,       -- not unique: multiple qualifiers may share a name
    identification_qualifier TEXT                   -- NULL permitted: confident IDs carry no qualifier
);

-- ── localities ────────────────────────────────────────────────────────────────
-- Geographic provenience of OTB specimens
CREATE TABLE localities (
    locality_id    SERIAL PRIMARY KEY,
    locality       TEXT   NOT NULL,
    continent      TEXT   NOT NULL  DEFAULT 'Africa'   -- OTB specimens are exclusively African
                   CHECK (continent IN (
                       'Africa','Asia','Europe',
                       'North America','South America','Oceania'
                   )),
    country        TEXT   NOT NULL
                   CHECK (country IN (
                       'Kenya','Ethiopia','Tanzania','Uganda',
                       'Eritrea','Djibouti','Somalia'
                   )),
    state_province TEXT,
    region         TEXT,
    subregion      TEXT,
    place          TEXT   NOT NULL  -- controlled by the localities table itself; no CHECK needed
);

-- ── fossils ───────────────────────────────────────────────────────────────────
-- Individual OTB specimens; catalog_number is stable and literature-cited
CREATE TABLE fossils (
    catalog_number          TEXT     PRIMARY KEY,
    organism_id             TEXT,
    preparations            TEXT,
    year                    SMALLINT CHECK (year BETWEEN 1800 AND 2100),
    discovered_by           TEXT,
    taxon_id                INTEGER
                            REFERENCES taxa(taxon_id)
                            ON DELETE SET NULL
                            ON UPDATE CASCADE,          -- NULL permitted: unidentified specimens
    date_identified         DATE,                       -- NULL permitted: not always recorded
    verbatim_identification TEXT,
    locality_id             INTEGER  NOT NULL
                            REFERENCES localities(locality_id)
                            ON DELETE RESTRICT
                            ON UPDATE CASCADE,          -- provenance is required
    formation               TEXT,                       -- NULL permitted: not always known
    member                  TEXT,
    bed                     TEXT,
    earliest_period_or_lowest_system    TEXT,
    latest_period_or_highest_system     TEXT,
    earliest_epoch_or_lowest_series     TEXT,
    latest_epoch_or_highest_series      TEXT,
    earliest_age_or_lowest_stage        TEXT,
    latest_age_or_highest_stage         TEXT,
    earliest_chronometric_age           NUMERIC,
    earliest_chronometric_age_reference_system TEXT,
    latest_chronometric_age             NUMERIC,
    latest_chronometric_age_reference_system   TEXT,
    verbatim_chronometric_age           TEXT,
    date_created            TIMESTAMPTZ  NOT NULL  DEFAULT now(),

    CHECK (
        earliest_chronometric_age IS NULL
        OR latest_chronometric_age IS NULL
        OR earliest_chronometric_age >= latest_chronometric_age
    )
);

-- ── export view ───────────────────────────────────────────────────────────────
-- TSV-shaped export: locality and taxon IDs replaced with source values,
-- columns follow TSV header order.
CREATE VIEW otb_fossils_export AS
SELECT
    f.catalog_number,
    f.organism_id,
    f.preparations,
    f.year,
    f.discovered_by,
    l.continent,
    l.country,
    l.state_province,
    l.region,
    l.subregion,
    l.place,
    l.locality,
    f.earliest_period_or_lowest_system,
    f.latest_period_or_highest_system,
    f.earliest_epoch_or_lowest_series,
    f.latest_epoch_or_highest_series,
    f.earliest_age_or_lowest_stage,
    f.latest_age_or_highest_stage,
    f.formation,
    f.member,
    f.bed,
    t.scientific_name,
    t.identification_qualifier,
    f.date_identified,
    f.verbatim_identification,
    f.verbatim_chronometric_age,
    f.earliest_chronometric_age,
    f.earliest_chronometric_age_reference_system,
    f.latest_chronometric_age,
    f.latest_chronometric_age_reference_system
FROM fossils AS f
LEFT JOIN taxa       AS t ON t.taxon_id    = f.taxon_id
JOIN      localities AS l ON l.locality_id = f.locality_id;

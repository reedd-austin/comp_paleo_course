#!/usr/bin/env python3
"""
load_otb.py — Load OTB fossil data from TSV into PostgreSQL

Usage:
    python3 load_otb_data.py otb_fossils.tsv
    python3 load_otb_data.py otb_fossils.csv

The file format is inferred from the extension (.tsv → tab-delimited, .csv → comma-delimited).

Requires:
    - psycopg2-binary  (pip install psycopg2-binary)
    - config.py in the same directory with DSN = "dbname=... user=... ..."
    - schema.sql already loaded into the target database

The script is safe to re-run: ON CONFLICT DO NOTHING skips rows that are
already present, so running it twice will not create duplicates.

Insert order respects foreign key dependencies:
    taxa -> localities -> fossils
"""

import csv
import sys
import psycopg2
from config import DSN


def load(path):
    ext = path.rsplit('.', 1)[-1].lower()
    if ext == 'csv':
        delimiter = ','
    elif ext == 'tsv':
        delimiter = '\t'
    else:
        print(f"Unknown extension '.{ext}' — assuming tab-delimited.")
        delimiter = '\t'

    conn = psycopg2.connect(DSN)
    cur  = conn.cursor()

    taxa_cache     = {}   # scientific_name → taxon_id
    locality_cache = {}   # locality attributes → locality_id

    inserted = 0
    skipped  = 0

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        for row in reader:
            catalog_number  = row['catalog_number'].strip()
            organism_id     = row['organism_id'].strip() or None
            preparations    = row['preparations'].strip() or None
            year            = row['year'].strip() or None
            discovered_by   = row['discovered_by'].strip() or None

            locality   = row['locality'].strip() or None
            continent       = row['continent'].strip()       or 'Africa'
            country         = row['country'].strip()         or None
            state_province  = row['state_province'].strip()  or None
            region          = row['region'].strip()          or None
            subregion       = row['subregion'].strip()       or None
            place           = row['place'].strip()
            formation       = row['formation'].strip()       or None
            member          = row['member'].strip()          or None
            bed             = row['bed'].strip()             or None


            scientific_name = row['scientific_name'].strip() or None
            qualifier = row['identification_qualifier'].strip() or None
            
            date_identified = row['date_identified'].strip() or None
            verbatim_identification = row['verbatim_identification'].strip() or None
            earliest_period = row['earliest_period_or_lowest_system'].strip() or None
            latest_period   = row['latest_period_or_highest_system'].strip()   or None
            earliest_epoch  = row['earliest_epoch_or_lowest_series'].strip()   or None
            latest_epoch    = row['latest_epoch_or_highest_series'].strip()    or None
            earliest_stage  = row['earliest_age_or_lowest_stage'].strip()   or None
            latest_stage    = row['latest_age_or_highest_stage'].strip()    or None
            earliest_chronometric_age      = row['earliest_chronometric_age'].strip() or None
            earliest_chronometric_age_reference_system = row['earliest_chronometric_age_reference_system'].strip() or None
            latest_chronometric_age        = row['latest_chronometric_age'].strip()   or None
            latest_chronometric_age_reference_system = row['latest_chronometric_age_reference_system'].strip() or None
            verbatim_chronometric_age      = row['verbatim_chronometric_age'].strip() or None



            locality_key = (
                locality, continent, country, state_province, region, subregion, place
            )
            cur.execute("SAVEPOINT load_row")
            added_taxon_key = None
            added_locality_key = None
            try:
                # ── taxa ──────────────────────────────────────────────────────
                # Empty scientific_name → taxon_id stays NULL (unidentified specimen)
                cache_key = (scientific_name, qualifier)
                # Check if the taxon is already in the cache; if not, query the database
                if cache_key not in taxa_cache:
                    cur.execute("""
                        SELECT taxon_id
                        FROM taxa
                        WHERE scientific_name = %s
                        AND identification_qualifier IS NOT DISTINCT FROM %s
                        ORDER BY taxon_id
                        LIMIT 1
                    """, cache_key)
                    result = cur.fetchone()

                    if result:
                        taxa_cache[cache_key] = result[0]
                    else:
                        cur.execute("""
                            INSERT INTO taxa (scientific_name, identification_qualifier)
                            VALUES (%s, %s)
                            RETURNING taxon_id
                        """, cache_key)
                        taxa_cache[cache_key] = cur.fetchone()[0]
                        added_taxon_key = cache_key

                taxon_id = taxa_cache[cache_key]

                # ── localities ───────────────────────────────────────────────
                if locality_key not in locality_cache:
                    cur.execute("""
                        SELECT locality_id
                        FROM localities
                        WHERE locality = %s
                          AND continent = %s
                          AND country = %s
                          AND state_province IS NOT DISTINCT FROM %s
                          AND region IS NOT DISTINCT FROM %s
                          AND subregion IS NOT DISTINCT FROM %s
                          AND place = %s
                    """, locality_key)
                    result = cur.fetchone()
                    if result:
                        locality_cache[locality_key] = result[0]
                    else:
                        cur.execute("""
                            INSERT INTO localities
                                (locality, continent, country, state_province, region, subregion, place)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            RETURNING locality_id
                        """, locality_key)
                        locality_cache[locality_key] = cur.fetchone()[0]
                        added_locality_key = locality_key

                locality_id = locality_cache[locality_key]

                # ── fossils ──────────────────────────────────────────────────
                cur.execute("""
                    INSERT INTO fossils
                        (catalog_number,
                        organism_id, 
                        preparations, 
                        year, 
                        discovered_by, 
                        taxon_id, 
                        date_identified,
                        verbatim_identification,
                        locality_id,
                        formation, member, bed,
                        earliest_period_or_lowest_system,
                        latest_period_or_highest_system,
                        earliest_epoch_or_lowest_series,
                        latest_epoch_or_highest_series,
                        earliest_age_or_lowest_stage,
                        latest_age_or_highest_stage,
                        earliest_chronometric_age,
                        earliest_chronometric_age_reference_system,
                        latest_chronometric_age,
                        latest_chronometric_age_reference_system,
                        verbatim_chronometric_age)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (catalog_number) DO NOTHING
                """, (catalog_number, 
                      organism_id, 
                      preparations, 
                      year, 
                      discovered_by, 
                      taxon_id, 
                      date_identified,
                      verbatim_identification,
                      locality_id,
                      formation, member, bed,
                      earliest_period, latest_period,
                      earliest_epoch, latest_epoch,
                      earliest_stage, latest_stage,
                      earliest_chronometric_age,
                      earliest_chronometric_age_reference_system,
                      latest_chronometric_age,
                      latest_chronometric_age_reference_system,
                      verbatim_chronometric_age))
                if cur.rowcount:
                    inserted += 1
                else:
                    skipped += 1
                cur.execute("RELEASE SAVEPOINT load_row")
            except Exception as e:
                cur.execute("ROLLBACK TO SAVEPOINT load_row")
                cur.execute("RELEASE SAVEPOINT load_row")
                if added_taxon_key is not None:
                    taxa_cache.pop(added_taxon_key, None)
                if added_locality_key is not None:
                    locality_cache.pop(added_locality_key, None)
                print(f"  SKIP {catalog_number}: {e}")
                skipped += 1
                continue

    conn.commit()
    conn.close()
    print(f"Done: {inserted} inserted, {skipped} skipped")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 load_otb_data.py <file.tsv|file.csv>")
        sys.exit(1)
    load(sys.argv[1])

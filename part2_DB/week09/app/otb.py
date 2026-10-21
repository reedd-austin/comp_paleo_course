import psycopg2
import psycopg2.extras
from psycopg2 import errors as pg_errors
from flask import Flask, render_template, request, redirect, url_for
from config import DSN

app = Flask(__name__)

def get_db():
    conn = psycopg2.connect(DSN, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


# ── Index ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ── Taxa ───────────────────────────────────────────────────────────────────────

@app.route('/taxa')
def list_taxa():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM taxa ORDER BY scientific_name")
    taxa = cur.fetchall()
    conn.close()
    return render_template('taxa_list.html', taxa=taxa)


@app.route('/taxa/new', methods=['GET', 'POST'])
def new_taxon():
    error = None
    if request.method == 'POST':
        name      = request.form['scientific_name'].strip()
        qualifier = request.form.get('identification_qualifier', '').strip() or None
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO taxa (scientific_name, identification_qualifier) VALUES (%s, %s)",
                (name, qualifier)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('list_taxa'))
        except pg_errors.NotNullViolation:
            conn.rollback()
            error = "Scientific name is required."
        except Exception as e:
            conn.rollback()
            error = f"Could not save taxon: {e}"
        finally:
            conn.close()
    return render_template('taxa_form.html', error=error)


# ── Localities ─────────────────────────────────────────────────────────────────

@app.route('/localities')
def list_localities():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM localities ORDER BY place")
    localities = cur.fetchall()
    conn.close()
    return render_template('localities_list.html', localities=localities)


@app.route('/localities/new', methods=['GET', 'POST'])
def new_locality():
    error = None
    if request.method == 'POST':
        place     = request.form['place'].strip()
        formation = request.form.get('formation', '').strip() or None
        country   = request.form.get('country', 'Kenya').strip() or 'Kenya'
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO localities (place, formation, country) VALUES (%s, %s, %s)",
                (place, formation, country)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('list_localities'))
        except pg_errors.NotNullViolation:
            conn.rollback()
            error = "Place is required."
        except pg_errors.CheckViolation:
            conn.rollback()
            error = "Country must be an East African Rift country."
        except Exception as e:
            conn.rollback()
            error = f"Could not save locality: {e}"
        finally:
            conn.close()
    return render_template('localities_form.html', error=error)


# ── Fossils ────────────────────────────────────────────────────────────────────

@app.route('/fossils')
def list_fossils():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT f.catalog_number,
               t.scientific_name,
               l.place,
               f.earliest_chronometric_age,
               f.latest_chronometric_age,
               f.verbatim_chronometric_age
        FROM   fossils f
        LEFT JOIN taxa       t ON f.taxon_id    = t.taxon_id
        LEFT JOIN localities l ON f.locality_id = l.locality_id
        ORDER BY f.catalog_number
    """)
    fossils = cur.fetchall()
    conn.close()
    return render_template('fossils_list.html', fossils=fossils)


@app.route('/fossils/new', methods=['GET', 'POST'])
def new_fossil():
    error = None
    conn  = get_db()
    cur   = conn.cursor()

    if request.method == 'POST':
        catalog_number = request.form['catalog_number'].strip()
        taxon_id       = request.form.get('taxon_id') or None
        locality_id    = request.form['locality_id']
        earliest_age   = request.form.get('earliest_chronometric_age', '').strip() or None
        latest_age     = request.form.get('latest_chronometric_age', '').strip() or None
        verbatim_age   = request.form.get('verbatim_chronometric_age', '').strip() or None
        try:
            cur.execute("""
                INSERT INTO fossils
                    (catalog_number, taxon_id, locality_id,
                     earliest_chronometric_age, latest_chronometric_age,
                     verbatim_chronometric_age)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (catalog_number, taxon_id, locality_id,
                  earliest_age, latest_age, verbatim_age))
            conn.commit()
            conn.close()
            return redirect(url_for('list_fossils'))
        except pg_errors.UniqueViolation:
            conn.rollback()
            error = f"Catalog number '{catalog_number}' already exists."
        except pg_errors.NotNullViolation:
            conn.rollback()
            error = "Catalog number and locality are required."
        except pg_errors.ForeignKeyViolation:
            conn.rollback()
            error = "Selected locality does not exist."
        except pg_errors.CheckViolation:
            conn.rollback()
            error = "Earliest age must be greater than or equal to latest age."
        except Exception as e:
            conn.rollback()
            error = f"Could not save fossil: {e}"

    cur.execute("SELECT taxon_id, scientific_name, identification_qualifier FROM taxa ORDER BY scientific_name")
    taxa = cur.fetchall()
    cur.execute("SELECT locality_id, place FROM localities ORDER BY place")
    localities = cur.fetchall()
    conn.close()
    return render_template('fossils_form.html', taxa=taxa, localities=localities, error=error)


if __name__ == '__main__':
    app.run(debug=True)

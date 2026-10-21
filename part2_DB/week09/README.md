# Week 9 — Populating a Database and Serving It on the Web

**Course:** Computational Paleobiology  
**Section:** 2 — Databases & Ontologies  
**Week:** 9 of 15  
**Due:** Before Week 10 session  
**Submission:** Push all files to `part2_DB/week09/` in your GitHub repository; submit the link to your GitHub repository and your (optional) reflection to Canvas.
**Readings**: DDfMM Ch 11-12

---

## Overview

In Week 8 you designed a schema and argued for every structural decision — primary keys, nullability, foreign keys, constraints. This week you will build the complete workflow that turns that schema into a live, populated database with a browser interface.

The workflow has four stages:

1. **Virtual environments** — isolate Python dependencies per project so packages never conflict across work
2. **Schema + loader** — recreate the database in one command and fill it from a TSV or CSV file
3. **HTML and CSS** — the markup and style primitives that Flask templates are built from
4. **Flask** — a minimal web framework that connects the database to a browser

The OTB fossil dataset serves as the reference example throughout. Every concept is illustrated with working OTB code; you will then apply the same workflow to your own project database.

**Readings:**  
Flask docs — https://flask.palletsprojects.com  
Jinja2 template designer — https://jinja.palletsprojects.com/en/3.x/templates/  
psycopg2 docs — https://www.psycopg.org/docs/  
MDN HTML reference — https://developer.mozilla.org/en-US/docs/Web/HTML  
MDN CSS reference — https://developer.mozilla.org/en-US/docs/Web/CSS  

---

## Topic 1 — Virtual Environments 

### Why virtual environments exist

Each Python project has its own dependency tree. Without isolation, running `pip install flask` affects every project on your machine. Upgrading a package for one project can silently break another. A virtual environment is a self-contained copy of Python and its installed packages, scoped to a single project directory.

Two immediate benefits:

- **Reproducibility.** Anyone cloning your repository can recreate the exact environment with one command.
- **Safety.** You can upgrade, downgrade, or remove packages without touching anything outside the project.

### Creating and activating a virtual environment

All commands below are run from your `week09/` project folder.

```bash
# Create the environment (run once)
python3 -m venv .venv
```

This creates a `.venv/` directory containing a Python interpreter and an empty package tree. The dot prefix keeps it out of the way in most file explorers.

```bash
# Activate (run every time you open a new terminal)
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\Activate.ps1         # Windows PowerShell
```

Your prompt changes to show `(.venv)` when the environment is active. Every `pip install` and every `python` command now runs inside the environment. If Flask or psycopg2 suddenly cannot be found, a forgotten activation is almost always the cause.

```bash
# Deactivate when done
deactivate
```

### Installing packages

```bash
pip install flask psycopg2-binary
```

`psycopg2-binary` bundles the PostgreSQL client library. You do not need PostgreSQL development headers separately.

Verify both installed:

```bash
flask --version
python -c "import psycopg2; print('psycopg2', psycopg2.__version__)"
```

### Pinning dependencies

```bash
pip freeze > requirements.txt
```

`requirements.txt` records every package and its exact version. Anyone replicating your work runs:

```bash
pip install -r requirements.txt
```

Commit `requirements.txt`. Do not commit `.venv/`.

### Protecting credentials with `.gitignore`

Your database connection string contains a username and possibly a password. Store it in `config.py` — a file that must never be pushed to GitHub.

```python
# config.py — DO NOT COMMIT THIS FILE
DSN = "postgresql://dreed@localhost/otb"
```

Add these entries to `.gitignore`:

```
# .gitignore
config.py
.venv/
__pycache__/
*.pyc
```

If you accidentally commit `config.py`, remove it from tracking without deleting the file:

```bash
git rm --cached config.py
git commit -m "stop tracking config.py"
```

The file remains on disk but is no longer tracked by git. Rotate any credentials that were exposed.

---

### Deliverables — Topic 1 

Apply this workflow to your own project folder.

**1a.** Create a virtual environment in your `week09/` folder, activate it, and install `flask` and `psycopg2-binary`.

**1b.** Run `pip freeze > requirements.txt` and commit the result.

**1c.** Create `config.py` with your DSN and verify it is listed in `.gitignore` and absent from `git status`.

**1d.** Take a screenshot showing your terminal prompt with `(.venv)` active and the output of `flask --version`. Save as `screenshots/topic1_venv.png`.

```
part2_DB/week09/
├── .gitignore          ← excludes config.py, .venv/, __pycache__/, *.pyc
├── requirements.txt    ← non-empty; flask and psycopg2-binary present
└── screenshots/
    └── topic1_venv.png ← prompt shows (.venv); flask --version visible
```

**Grading:** `.gitignore` correct (5 pts); `requirements.txt` present with both packages (5 pts); `config.py` absent from tracked files (5 pts); screenshot with active environment (5 pts).

---

## Topic 2 — Schema and Loader

### Recreating a database from `schema.sql`

`schema.sql` makes the database structure repeatable. One command drops any existing tables and recreates them from scratch:

```bash
psql -d otb -f schema.sql
```

The OTB schema drops and recreates three tables in dependency order (fossils first, since it references the others):

```sql
-- schema.sql (OTB)
DROP TABLE IF EXISTS fossils;
DROP TABLE IF EXISTS taxa;
DROP TABLE IF EXISTS localities;

CREATE TABLE taxa (
    taxon_id                 SERIAL PRIMARY KEY,
    scientific_name          TEXT   NOT NULL,
    identification_qualifier TEXT
);

CREATE TABLE localities (
    locality_id  SERIAL PRIMARY KEY,
    place        TEXT NOT NULL,
    formation    TEXT,
    country      TEXT NOT NULL DEFAULT 'Kenya'
                 CHECK (country IN ('Kenya','Ethiopia','Tanzania',
                                    'Uganda','Eritrea','Djibouti','Somalia'))
);

CREATE TABLE fossils (
    catalog_number              TEXT    PRIMARY KEY,
    taxon_id                    INTEGER REFERENCES taxa(taxon_id)
                                    ON DELETE SET NULL ON UPDATE CASCADE,
    locality_id                 INTEGER NOT NULL
                                    REFERENCES localities(locality_id)
                                    ON DELETE RESTRICT ON UPDATE CASCADE,
    earliest_chronometric_age   NUMERIC,
    latest_chronometric_age     NUMERIC,
    verbatim_chronometric_age   TEXT,
    created_at                  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (earliest_chronometric_age IS NULL
        OR latest_chronometric_age IS NULL
        OR earliest_chronometric_age >= latest_chronometric_age)
);
```

Because `DROP TABLE IF EXISTS` runs first, re-running the file always produces a clean state. This is especially useful during schema iteration: change a column definition, re-run the file, re-run the loader.

### Loading data from a TSV file

A Python loader script is more flexible than a `.sql` data file: it can clean values, handle optional fields, resolve foreign keys, and skip duplicates. The pattern:

1. Read the source file row by row with `csv.DictReader`.
2. Resolve parent records first (taxa, localities), caching their IDs.
3. Insert child records (fossils) last, using the cached IDs.

**OTB loader (`load_otb.py`):**

```python
import csv
import sys
import psycopg2
import psycopg2.extras
from config import DSN

TSV_FILE = "otb_fossils.tsv"

def load(path):
    conn = psycopg2.connect(DSN,
        cursor_factory=psycopg2.extras.RealDictCursor)
    cur = conn.cursor()

    taxa_cache     = {}   # (scientific_name, qualifier) → taxon_id
    locality_cache = {}   # place → locality_id

    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh, delimiter='\t')
        for row in reader:
            # ── Taxa ──────────────────────────────────────────────
            sci_name  = row['scientific_name'].strip() or None
            qualifier = row['identification_qualifier'].strip() or None
            taxon_id  = None

            if sci_name:
                key = (sci_name, qualifier)
                if key not in taxa_cache:
                    cur.execute(
                        """INSERT INTO taxa
                               (scientific_name, identification_qualifier)
                           VALUES (%s, %s)
                           RETURNING taxon_id""",
                        (sci_name, qualifier)
                    )
                    taxa_cache[key] = cur.fetchone()['taxon_id']
                taxon_id = taxa_cache[key]

            # ── Localities ────────────────────────────────────────
            place = row['place'].strip()
            if place not in locality_cache:
                formation = row.get('formation', '').strip() or None
                country   = row.get('country', 'Kenya').strip() or 'Kenya'
                cur.execute(
                    """INSERT INTO localities (place, formation, country)
                       VALUES (%s, %s, %s)
                       ON CONFLICT DO NOTHING
                       RETURNING locality_id""",
                    (place, formation, country)
                )
                result = cur.fetchone()
                if result is None:          # row already existed
                    cur.execute(
                        "SELECT locality_id FROM localities WHERE place = %s",
                        (place,)
                    )
                    result = cur.fetchone()
                locality_cache[place] = result['locality_id']
            locality_id = locality_cache[place]

            # ── Fossils ───────────────────────────────────────────
            try:
                earliest = float(row['earliest_chronometric_age']) \
                           if row.get('earliest_chronometric_age','').strip() \
                           else None
                latest   = float(row['latest_chronometric_age']) \
                           if row.get('latest_chronometric_age','').strip() \
                           else None
                verbatim = row.get('verbatim_chronometric_age','').strip() or None

                cur.execute(
                    """INSERT INTO fossils
                           (catalog_number, taxon_id, locality_id,
                            earliest_chronometric_age, latest_chronometric_age,
                            verbatim_chronometric_age)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (catalog_number) DO NOTHING""",
                    (row['catalog_number'].strip(), taxon_id, locality_id,
                     earliest, latest, verbatim)
                )
            except Exception as e:
                conn.rollback()
                print(f"Error on {row.get('catalog_number','?')}: {e}",
                      file=sys.stderr)
                continue

    conn.commit()
    conn.close()
    print("Done.")

if __name__ == '__main__':
    load(TSV_FILE)
```

Key decisions illustrated here:

- **Cache dicts prevent duplicates within a run.** taxa has no UNIQUE constraint, so a dict keyed on `(scientific_name, qualifier)` prevents inserting the same taxon twice. `ON CONFLICT DO NOTHING` on `fossils` (which has a PRIMARY KEY) makes re-running the loader idempotent.
- **`conn.rollback()` after every exception.** psycopg2 leaves a connection in a failed transaction state after any error. Without a rollback, every subsequent query raises `InFailedSqlTransaction`. The rollback resets the state; the `continue` skips the bad row without aborting the rest.
- **Nullable fields use `or None`.** An empty string from a TSV cell becomes Python `None`, which inserts as SQL `NULL`. Without this, `''` would be inserted as a zero-length string, violating NOT NULL constraints or producing misleading data.

Run the loader:

```bash
python load_otb.py
```

Verify the counts:

```bash
psql -d otb -c "SELECT COUNT(*) FROM fossils;"
psql -d otb -c "SELECT COUNT(*) FROM taxa;"
psql -d otb -c "SELECT COUNT(*) FROM localities;"
```

---

### Deliverables — Topic 2

Apply this workflow to your own project.

**2a.** Commit your `schema.sql` (updated from Week 8 if needed). Run it against a fresh database and verify it executes without errors.

**2b.** Write a loader script that reads your source data file (TSV, CSV, or other tabular format) and populates your database. The loader must:
- Use `csv.DictReader` (or an equivalent reader for your format)
- Use parameterized `%s` queries — no string concatenation
- Resolve foreign keys using cache dicts or a SELECT before each INSERT
- Call `conn.rollback()` inside every `except` block
- Print a summary count or "Done." on success

**2c.** Run `psql -d <your_db> -f schema.sql` followed by `python your_loader.py` and confirm the row counts are correct.

**2d.** Take a screenshot showing the terminal output of the schema command and the loader, with the row-count verification queries. Save as `screenshots/topic2_loader.png`.

```
part2_DB/week09/
├── schema.sql
├── your_loader.py      ← parameterized, rollback on exception, cache dicts
└── screenshots/
    └── topic2_loader.png
```

**Grading:** `schema.sql` runs clean (5 pts); loader uses parameterized queries (5 pts); foreign keys resolved correctly (5 pts); rollback in except block (5 pts); screenshot with row counts (5 pts).

---

## Topic 3 — HTML and CSS Primer  *(15 points)*

Flask renders HTML pages from templates. Before writing templates, you need to understand the two languages they use: HTML for structure and CSS for appearance.

### HTML: structure and semantics

HTML is a tree of elements. Every element has an opening tag, content, and a closing tag:

```html
<p>This is a paragraph.</p>
<h2>This is a section heading.</h2>
```

Self-closing elements have no content or closing tag:

```html
<input type="text" name="catalog_number">
<br>
```

Every HTML page has a minimal skeleton:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>OTB Fossils</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <h1>Welcome</h1>
    <p>The Omo–Turkana Basin fossil collection.</p>
</body>
</html>
```

| Element | Purpose |
|---------|---------|
| `<h1>`–`<h6>` | Headings, largest to smallest |
| `<p>` | Paragraph |
| `<a href="...">` | Hyperlink |
| `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>` | Tabular data |
| `<form method="post">` | Form container |
| `<input>` | Text, number, or other single-field input |
| `<select>`, `<option>` | Dropdown menu |
| `<button type="submit">` | Form submit button |
| `<label>` | Accessible label for an input |
| `<div>` | Generic block container |
| `<nav>` | Navigation section |

### Forms: how data reaches Flask

A form submits data to a route. The `method="post"` attribute sends the data as a request body (rather than in the URL). Each `<input>` and `<select>` contributes one key-value pair, identified by its `name` attribute. Flask reads these as `request.form['name']`.

```html
<form method="post" action="/taxa/new">
    <label>Scientific name
        <input type="text" name="scientific_name" required>
    </label>
    <label>Qualifier (optional)
        <input type="text" name="identification_qualifier">
    </label>
    <button type="submit">Save</button>
</form>
```

The `required` attribute prevents submission when the field is empty; validation happens in the browser before the request is sent.

A `<select>` dropdown submits the `value` of the selected `<option>`:

```html
<select name="country">
    <option value="Kenya" selected>Kenya</option>
    <option value="Ethiopia">Ethiopia</option>
    <option value="Tanzania">Tanzania</option>
</select>
```

### CSS: selectors and properties

CSS describes the appearance of HTML elements. A stylesheet is a list of rules:

```css
selector {
    property: value;
    property: value;
}
```

Common selectors:

| Selector | Matches |
|----------|---------|
| `body` | The `<body>` element |
| `h1` | All `<h1>` elements |
| `table` | All `<table>` elements |
| `.card` | All elements with `class="card"` |
| `#nav` | The element with `id="nav"` |
| `a:hover` | Links when the cursor is over them |

Common properties:

```css
body {
    font-family: Georgia, serif;
    background-color: #faf8f5;   /* cream */
    color: #2b2218;              /* dark brown */
    margin: 0;
    padding: 1rem 2rem;
}

nav {
    background-color: #4a3f2f;
    padding: 0.75rem 2rem;
}

nav a {
    color: #e8dcc8;
    text-decoration: none;
    margin-right: 1.5rem;
}

table {
    border-collapse: collapse;
    width: 100%;
}

th, td {
    border: 1px solid #ccc;
    padding: 0.5rem 1rem;
    text-align: left;
}

.error {
    color: #c0392b;
    border: 1px solid #c0392b;
    padding: 0.5rem;
    border-radius: 4px;
}
```

Save the stylesheet as `static/style.css`. Flask serves everything in `static/` automatically. Reference it in HTML with:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
```

The `url_for` call generates the correct URL regardless of where the app is hosted.

---

### Deliverables — Topic 3

**3a.** Create a plain HTML file (`topic3_primer.html`) that demonstrates the following elements — **without any Flask, Jinja2, or Python** — just static HTML and CSS:

- A page title and at least two levels of headings
- A navigation bar with three links (they may link to `#`)
- A table with at least three rows of data from your project
- A form with at least three fields (mix of text inputs and a dropdown), a required field, and a submit button
- An external `style.css` linked with a `<link>` tag, and at least three CSS rules that visibly change the page's appearance

The page must render in a browser without errors.

```
part2_DB/week09/
├── topic3_primer.html
└── topic3_style.css
```

**Grading:** All required HTML elements present and correct (8 pts); CSS linked externally with ≥3 visible rules (4 pts); form uses `name` attributes that match the fields in your schema (3 pts).

---

## Topic 4 — Flask with the OTB Demo

### What Flask does

Flask is a Python web framework. It maps URL paths to Python functions:

```python
@app.route('/taxa')
def list_taxa():
    ...
```

When a browser requests `/taxa`, Flask calls `list_taxa()` and sends its return value back as an HTTP response. The return value is usually a rendered HTML template.

### Project structure

Place your Flask app in an `app/` subdirectory to separate it from the schema and loader:

```
week09/
├── schema.sql
├── otb_fossils.tsv
├── load_otb.py
├── requirements.txt
├── .gitignore
└── app/
    ├── config.py              ← DSN (not committed)
    ├── otb.py                 ← Flask application
    ├── static/
    │   └── style.css
    └── templates/
        ├── base.html
        ├── index.html
        ├── taxa_list.html
        ├── taxa_form.html
        ├── localities_list.html
        ├── localities_form.html
        ├── fossils_list.html
        └── fossils_form.html
```

### The application file

```python
# app/otb.py
import psycopg2
import psycopg2.extras
from psycopg2 import errors as pg_errors
from flask import Flask, render_template, request, redirect, url_for

from config import DSN

app = Flask(__name__)

# ── Database helper ──────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(DSN,
        cursor_factory=psycopg2.extras.RealDictCursor)

# ── Index ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM taxa")
    n_taxa = cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM localities")
    n_localities = cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM fossils")
    n_fossils = cur.fetchone()['n']
    conn.close()
    return render_template('index.html',
        n_taxa=n_taxa, n_localities=n_localities, n_fossils=n_fossils)

# ── Taxa ──────────────────────────────────────────────────────────────────────

@app.route('/taxa')
def list_taxa():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM taxa ORDER BY scientific_name")
    rows = cur.fetchall()
    conn.close()
    return render_template('taxa_list.html', rows=rows)

@app.route('/taxa/new', methods=['GET', 'POST'])
def new_taxon():
    error = None
    if request.method == 'POST':
        name      = request.form['scientific_name'].strip()
        qualifier = request.form.get('identification_qualifier','').strip() or None
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO taxa (scientific_name, identification_qualifier)"
                " VALUES (%s, %s)",
                (name, qualifier)
            )
            conn.commit()
            return redirect(url_for('list_taxa'))
        except pg_errors.NotNullViolation:
            conn.rollback()
            error = "Scientific name is required."
        finally:
            conn.close()
    return render_template('taxa_form.html', error=error)

# ── Localities ────────────────────────────────────────────────────────────────

@app.route('/localities')
def list_localities():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM localities ORDER BY place")
    rows = cur.fetchall()
    conn.close()
    return render_template('localities_list.html', rows=rows)

@app.route('/localities/new', methods=['GET', 'POST'])
def new_locality():
    error = None
    if request.method == 'POST':
        place     = request.form['place'].strip()
        formation = request.form.get('formation','').strip() or None
        country   = request.form.get('country', 'Kenya')
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO localities (place, formation, country)"
                " VALUES (%s, %s, %s)",
                (place, formation, country)
            )
            conn.commit()
            return redirect(url_for('list_localities'))
        except pg_errors.NotNullViolation:
            conn.rollback()
            error = "Place is required."
        except pg_errors.CheckViolation:
            conn.rollback()
            error = "Country must be one of the seven Rift Valley countries."
        finally:
            conn.close()
    return render_template('localities_form.html', error=error)

# ── Fossils ───────────────────────────────────────────────────────────────────

@app.route('/fossils')
def list_fossils():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT f.catalog_number,
               t.scientific_name,
               t.identification_qualifier,
               l.place,
               f.earliest_chronometric_age,
               f.latest_chronometric_age,
               f.verbatim_chronometric_age
        FROM   fossils f
        LEFT JOIN taxa       t ON t.taxon_id    = f.taxon_id
        JOIN      localities l ON l.locality_id = f.locality_id
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
        try:
            taxon_id    = request.form.get('taxon_id') or None
            locality_id = request.form['locality_id']
            earliest    = request.form.get('earliest_chronometric_age') or None
            latest      = request.form.get('latest_chronometric_age')   or None
            verbatim    = request.form.get('verbatim_chronometric_age','').strip() or None
            cur.execute(
                """INSERT INTO fossils
                       (catalog_number, taxon_id, locality_id,
                        earliest_chronometric_age, latest_chronometric_age,
                        verbatim_chronometric_age)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (request.form['catalog_number'].strip(),
                 taxon_id, locality_id, earliest, latest, verbatim)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('list_fossils'))
        except pg_errors.UniqueViolation:
            conn.rollback()
            error = "That catalog number already exists."
        except pg_errors.NotNullViolation:
            conn.rollback()
            error = "Catalog number and locality are required."
        except pg_errors.ForeignKeyViolation:
            conn.rollback()
            error = "Selected locality no longer exists."
        except pg_errors.CheckViolation:
            conn.rollback()
            error = "Earliest age must be >= latest age (older = larger number in Ma)."
        finally:
            if not conn.closed:
                conn.close()
    else:
        conn.close()
        conn = get_db()
        cur  = conn.cursor()

    cur.execute("SELECT taxon_id, scientific_name, identification_qualifier"
                " FROM taxa ORDER BY scientific_name")
    taxa = cur.fetchall()
    cur.execute("SELECT locality_id, place FROM localities ORDER BY place")
    localities = cur.fetchall()
    conn.close()
    return render_template('fossils_form.html',
                           taxa=taxa, localities=localities, error=error)
```

### Template inheritance

`base.html` defines the shared layout. Every page template extends it and fills in `{% block content %}`:

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}OTB{% endblock %}</title>
    <link rel="stylesheet"
          href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<nav>
    <a href="{{ url_for('index') }}">Home</a>
    <a href="{{ url_for('list_taxa') }}">Taxa</a>
    <a href="{{ url_for('list_localities') }}">Localities</a>
    <a href="{{ url_for('list_fossils') }}">Fossils</a>
</nav>
<main>
    {% block content %}{% endblock %}
</main>
</body>
</html>
```

A page template:

```html
<!-- templates/taxa_list.html -->
{% extends 'base.html' %}
{% block title %}Taxa — OTB{% endblock %}
{% block content %}
<h1>Taxa</h1>
<a href="{{ url_for('new_taxon') }}">+ Add taxon</a>
<table>
    <thead>
        <tr><th>ID</th><th>Scientific name</th><th>Qualifier</th></tr>
    </thead>
    <tbody>
        {% for row in rows %}
        <tr>
            <td>{{ row['taxon_id'] }}</td>
            <td><em>{{ row['scientific_name'] }}</em></td>
            <td>{{ row['identification_qualifier'] or '—' }}</td>
        </tr>
        {% else %}
        <tr><td colspan="3">No taxa yet.</td></tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

### Running the app

With the virtual environment active and from inside `app/`:

```bash
flask --app otb run
```

If port 5000 is in use (common on macOS — AirPlay Receiver occupies it):

```bash
flask --app otb run --port 5001
```

Open `http://127.0.0.1:5000` (or 5001) in a browser.

### Constraint handling

Every insert route wraps its `cur.execute()` in a `try/except` block:

```python
try:
    cur.execute("INSERT INTO ...", (...))
    conn.commit()
    return redirect(url_for(...))
except pg_errors.UniqueViolation:
    conn.rollback()
    error = "That record already exists."
except pg_errors.NotNullViolation:
    conn.rollback()
    error = "A required field was left blank."
finally:
    conn.close()
return render_template('form.html', error=error)
```

Rules:
- `conn.rollback()` **must** be called inside the `except` block. A connection in a failed transaction refuses all further queries until rolled back.
- `conn.close()` goes in `finally` so the connection is always released, even when an exception occurs.
- The form re-renders with the error message rather than returning a 500 error page.

---

### Deliverables — Topic 4

Build a Flask application for your own project database following the OTB structure above. Your app must cover every table in your schema.

**4a — Application file.** `app.py` (or named after your project) must contain:
- `get_db()` with `RealDictCursor`
- An index route that displays row counts or a summary from the database
- For every table: a read route (GET, renders an HTML table) and an insert route (GET renders form; POST inserts and redirects)
- FK dropdowns for every foreign-key field, populated by a live SELECT
- `try/except` on every INSERT with `conn.rollback()` and `finally: conn.close()`

**4b — Templates.** One `_list.html` and one `_form.html` per table, all extending `base.html`.

**4c — Stylesheet.** `static/style.css` with at least five rules; referenced via `url_for`.

**4d — Run and verify.** Start the app and navigate to every route. Take a screenshot of each table's read page showing at least one row (loaded by your Topic 2 loader). Save as `screenshots/topic4_<table>.png`.

**4e — Constraint test.** Trigger at least one constraint violation (submit a duplicate primary key, leave a required field blank, or violate a CHECK). Screenshot the user-friendly error message. Save as `screenshots/topic4_constraint_error.png`.

```
part2_DB/week09/app/
├── app.py (or <project>.py)
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── <table>_list.html   ← one per table
    └── <table>_form.html   ← one per table
```


---

## Reflection  *(optional)*

Write `reflection_w9.md` (150–250 words) addressing:

1. **Schema and form feedback.** Did building the insert form reveal anything about your schema you did not anticipate? (A field that needed a default? A constraint too strict or too loose? A missing controlled vocabulary?) Describe any changes made.

2. **Loader vs. manual entry.** What are the practical tradeoffs between loading data from a file with a Python script versus entering it one record at a time through a browser form?

3. **One next step.** Name one feature you would add to make the app genuinely useful for your own research — search and filter, edit and delete, bulk import, authentication, or something else — and explain why that feature would matter for your project.

---

## Submission Checklist

Push to `part2_DB/week09/` in your GitHub repository:

```
week09/
├── .gitignore                          ← Topic 1
├── requirements.txt                    ← Topic 1
├── schema.sql                          ← Topic 2
├── <your_loader>.py                    ← Topic 2
├── topic3_primer.html                  ← Topic 3
├── topic3_style.css                    ← Topic 3
├── app/
│   ├── <project>.py                    ← Topic 4
│   ├── static/
│   │   └── style.css                   ← Topic 4
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── <table>_list.html           ← Topic 4, one per table
│       └── <table>_form.html           ← Topic 4, one per table
├── reflection_w9.md
└── screenshots/
    ├── topic1_venv.png
    ├── topic2_loader.png
    ├── topic4_<table>.png              ← one per table
    └── topic4_constraint_error.png
```

**Do not commit `config.py`.** Verify it is absent from `git status` before pushing.

Submit to Canvas:
- Link to your GitHub repository
- PDF export of `reflection_w9.md` (optional)

---

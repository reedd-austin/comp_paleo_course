import psycopg2
import psycopg2.extras
from psycopg2 import errors as pg_errors
from flask import Flask, render_template, request, redirect, url_for
from config import DSN

app = Flask(__name__)

def get_db():
    conn = psycopg2.connect(DSN, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

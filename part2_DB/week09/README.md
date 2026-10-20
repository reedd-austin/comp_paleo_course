# Week 9 - Data Entry with Flask
**Course:** Computational Paleobiology  
**Section:** 2 — Databases & Ontologies  
**Week:** 9 of 15  
**Due:** Before Week 10 session  
**Submission:** Push all files to `section2-databases/week09/` in your GitHub repository; submit the design reflection and peer review note to the LMS.

---

## Overview

In Week 8 you completed your database schema: primary keys with justifications, full field specifications, referential integrity rules, and a `schema.sql` that runs clean. That schema is the foundation. This week you will build a Flask web application that lets a user enter data into your PostgreSQL database through HTML forms.

By the end of the assignment your app will:

1. Start without errors and serve a navigable index page
2. Display all records from at least one table as an HTML table
3. Accept new records through a parameterized `INSERT` form
4. Populate foreign-key fields with dropdown menus drawn from the referenced table
5. Catch constraint violations and display a user-friendly message instead of crashing
6. Cover every table in your schema with both a read route and an insert route

You will work with your own database project throughout. The OTB fossil dataset is used as the reference example in lecture and in the code samples below.

**Readings:** Flask documentation (https://flask.palletsprojects.com) · Jinja2 template designer docs (https://jinja.palletsprojects.com/en/3.x/templates/) · psycopg2 documentation (https://www.psycopg.org/docs/)

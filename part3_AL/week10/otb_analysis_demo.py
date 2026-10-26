# %% [markdown]
# # Part 1 Positron and Python Basics
# ## 1.1 Why Positron
# Positron is a scientific IDE developed by Posit (the team behind RStudio) and built on VS Code. 
# Like RStudio for R, it is designed around the exploratory data analysis workflow: you write code in an editor, 
# run individual cells interactively, and watch results — DataFrames, plots, variable values — appear in 
# dedicated panels alongside. The **Variables** pane shows every object in the current session; the **Data 
# Explorer** lets you sort, filter, and scroll a DataFrame as if it were a spreadsheet.
# 
# For analysis work, Positron uses ordinary Python scripts (`.py`) rather than notebook JSON files (`.ipynb`). 
# Cells are delimited by `# %%` comment markers. This keeps your analysis in a format that is easy to read in 
# git diffs, easy to run as a script from the command line, and free of the metadata clutter that notebook JSON accumulates.
# 
# Download Positron at **https://positron.posit.co** and install it alongside (not instead of) VS Code — they can coexist.

# %% [markdown]
# ## 1.2 Setting up the environment
# Inside your `week10/` folder, create and then activate a new virtual environment. Install the required packages:

# ```bash
# cd part3_AL/week10
# python3 -m venv .venv
# source .venv/bin/activate
# pip install numpy pandas matplotlib psycopg2-binary sqlalchemy
# pip freeze > requirements.txt
# ```
# 
# Open the `week10/` folder in Positron (`File → Open Folder`). Positron will detect the `.venv` virtual environment automatically. If it does not, select the interpreter with the Python version picker in the bottom status bar and point it at `.venv/bin/python`.
#
# Create a new file named `otb_analysis.py`.

# %% [markdown]
# ## 1.3 The cell format
# %% Setup
import numpy as np
import pandas as pd
import psycopg2

from config import DSN
from sqlalchemy import create_engine



print(np.__version__, pd.__version__)

# %% [markdown]
# ## 1.4 Python language features

# %% Part 1 - language basics
squared = [x**2 for x in range(10)]
print(squared)

filtered = [x for x in range(20) if x % 3 == 0]
print(filtered)

for i, name in enumerate(['Australopithecus', 'Paranthropus', 'Homo']):
    print(i, name)

locality_names = ['Koobi Fora', 'Kanapoi', 'Ileret', 'Allia Bay', 'Kalam Area']
counts = [294, 188, 232, 54, 6]
for loc, count in zip(locality_names, counts):
    print(f"{loc}: {count}")

specimens = pd.DataFrame({
    'specimen_id': ['OTB-001', 'OTB-002', 'OTB-003', 'OTB-004'],
    'taxon':       ['Australopithecus', 'Paranthropus', 'Homo', 'Australopithecus'],
    'locality':    ['FLK', 'KBS', 'FLK', 'Natron'],
    'age_ma':      [1.87, 2.35, 1.65, 2.10],
    'element':     ['femur', 'mandible', 'cranium', 'tibia'],
})

def summarize(*fields, decimals=2):
    for f in fields:
        print(f"{f}: {round(specimens[f].mean(), decimals)}")

summarize('age_ma')

# Lambda functions
specimens['epoch'] = specimens['age_ma'].apply(lambda x: 'Pleistocene' if x < 2.6 else 'Pliocene')


# %% [markdown]
# # Part 2 - Numpy
# ## Part 2.1 The ndarray

# %%
# 1-E array
ages = np.array(age_ma_list)
print(ages.dtype)
print(ages.shape)
print(ages.ndim)

# 2-D array
# 3 specimens × 4 measurements (length, width, height, mass)
measurements = np.array([
    [45.2, 12.1, 8.3, 0.14],
    [38.7, 10.5, 7.1, 0.09],
    [51.0, 14.2, 9.6, 0.21],
])
print(measurements.shape)   # (3, 4)
print(measurements[0, :])   # first specimen, all measurements
print(measurements[:, 2])   # all specimens, height only

# %% [markdown]
# ## 2.2 Vectorized arithmetic

# %% Vectorized arithmetic
ages_bp = ages * 1_000_000          # Ma → years before present
log_ages = np.log(ages)             # natural log of each element
z_scores = (ages - ages.mean()) / ages.std()

# compare to multiplication on a list
print(age_ma_list)
print(age_ma_list * 2)

# %% Universal functions
np.sqrt(measurements)     # element-wise square root
np.abs(z_scores)          # element-wise absolute value
np.log10(ages * 1e6)      # base-10 log

# %% [markdown]
# ## 2.3 Boolean indexng

# %% Boolean indexing
old = ages[ages > 2.0]          # specimens older than 2 Ma
print(old)                      # array of selected values

# Compound conditions require & and |, not 'and' / 'or'
window = ages[(ages > 1.8) & (ages < 2.2)]
print(window)

# Fancy indexing
idx = np.array([0, 2, 5])
print(ages[idx])                # ages at positions 0, 2, 5

# %% [markdown]
# ## 2.4 Axis operations

# %% Axis operations
# Column means (mean of each measurement across all specimens)
col_means = measurements.mean(axis=0)   # shape (4,)

# Row means (mean measurement per specimen)
row_means = measurements.mean(axis=1)   # shape (3,)

# %% [markdown]
# ## 2.5 Deliverables

# %% [markdown]
# # Part 3 Pandas
# ## 3.1 Series

# %%
specimen_counts = pd.Series(
    [312, 187, 244, 98, 402],
    index=['FLK', 'KBS', 'Natron', 'Chesowanja', 'Turkana'],
)
print(specimen_counts['KBS'])          # 187  — label-based access
print(specimen_counts[2])              # 244  — integer position
print(specimen_counts[specimen_counts > 200])   # boolean filter

counts_2022 = pd.Series({'FLK': 312, 'KBS': 187, 'Natron': 244})
counts_2023 = pd.Series({'KBS': 41,  'Natron': 8, 'FLK': 19})
total = counts_2022 + counts_2023    # aligns on locality name

# %% [markdown]
# ## 3.2 Dataframe

# %% Dataframe
# Create a datafram from a dictionary of lists
specimens = pd.DataFrame({
    'specimen_id': ['OTB-001', 'OTB-002', 'OTB-003', 'OTB-004'],
    'taxon':       ['Australopithecus', 'Paranthropus', 'Homo', 'Australopithecus'],
    'locality':    ['FLK', 'KBS', 'FLK', 'Natron'],
    'age_ma':      [1.87, 2.35, 1.65, 2.10],
    'element':     ['femur', 'mandible', 'cranium', 'tibia'],
})

# Load a DataFrame from a CSV
# otb_df = pd.read_csv('otb_fossils.csv') 
# otb_df = pd.read_csv('otb_fossils.tsv', delimiter='\t')

# Load a DataFrame from PostgreSQL tables
engine = create_engine(DSN)
df = pd.read_sql('SELECT * FROM fossils JOIN taxa USING (taxon_id)', engine)
# Load a DataFram from PostgreSQl view
df_exp = pd.read_sql('SELECT * FROM otb_fossils_export', engine)

# %% [markdown]
# ## 3.3 Inspection

# %% Inspection
df.shape          # (rows, columns)
df.dtypes         # column data types
df.head(10)       # first 10 rows
df.tail(5)        # last 5 rows
df.info()         # non-null counts + dtypes
df.describe()     # count, mean, std, min, quartiles, max for numeric columns
df.isnull().sum() # missing values per column
print(df.head(1))

# %% [markdown]
# ## 3.4 Indexing and selection

# %% Indexing and selection
# Correct — selects rows where taxon is Homo, returns the age column
df.loc[df['taxon_id'] == 11, 'formation']

# Correct - select rows where taxon_id is 11 (Homo), returns the formation and preparations columns
df.loc[df['taxon_id'] == 11, ['formation', 'preparations']]

# Correct — select first 10 rows, columns 1 through 3
df.iloc[:10, 1:4]

# This may silently do nothing — the SettingWithCopyWarning
# df[df['taxon'] == 'Homo']['age_ma'] = 0
pliocene_paranthropus = df[(df['earliest_epoch_or_lowest_series'] == 'Pliocene') & df['taxon_id'].isin([3,4,14])]
#pliocene_paranthropus = df[(df['earliest_epoch_or_lowest_series'] == 'Pliocene') & (df['taxon_id'] == '14')]

# %% [markdown]
# ## 3.5 Adding columns and applying functions

# %% 
# Create a colunn showing the average age.
# axis=1 means “average across columns for each row.” Without it, axis=0 is the default and you’d get the mean of each column separately instead.
df_exp['avg_age'] = df[['earliest_chronometric_age', 'latest_chronometric_age']].mean(axis=1)

# Apply a function row-wise (axis=1) or column-wise (axis=0)
df_exp['epoch'] = df_exp['avg_age'].apply(lambda x: 'Pleistocene' if x < 2.6 else 'Pliocene')

# String methods via .str accessor
df_exp['taxon_short'] = df_exp['scientific_name'].str.split().str[0]   # genus only


# %% [markdown]
# ## 3.6 Sorting and Summarizing

# %% Sorting and summarizing
# Sort by a column
df_exp = df_exp.sort_values('avg_age', ascending=False)

# Count occurrences
df_exp['taxon_short'].value_counts()

# Group and aggregate
by_taxon = df_exp.groupby('taxon_short')['avg_age'].agg(['mean', 'min', 'max', 'count'])
by_locality = df_exp.groupby('locality').size()
by_place = df_exp.groupby('place').size()

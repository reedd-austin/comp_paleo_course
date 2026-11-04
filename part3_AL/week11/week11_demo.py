# %% [markdown]
# # Week 11 Demonstration

# %% Setup
import json
import os

import pandas as pd
from sqlalchemy import create_engine

from config import DSN

path = 'part3_AL/week11/'

# %% load ecv json to df
file_path = os.path.join(path, 'ecv_otb_subset.json')
with open(file_path) as f:
    ecv_raw = json.load(f)

print(type(ecv_raw))                    # dict
print(ecv_raw['source'])                # citation string
print(ecv_raw['region'])
print(len(ecv_raw['specimens']))        # 20 specimens
print(ecv_raw['specimens'][0])          # first record as a dict

# %% Flatten a JSON file to a dataframe
ecv_otb = pd.json_normalize(ecv_raw['specimens']) # Note that we read in the specimen portion of the raw file.
print(ecv_otb.head())
print(ecv_otb.dtypes)
print(ecv_otb.shape)

# %% Alternatively, an easier import when 'specimens' is a flat data structure.
ecv_otb2 = pd.DataFrame(ecv_raw['specimens'])
print(ecv_otb2.head())
print(ecv_otb2.dtypes)
print(ecv_otb2.shape)


# %% Read in the full dataset
ecv_full = pd.read_csv(os.path.join(path, 'ecv_by_specimen.csv'))
print(ecv_full.shape)     # (95, 8)
print(ecv_full.dtypes)
print(ecv_full.head())

# %% Comparing formats

# Column names are the same — confirm the subset is a true subset of the full CSV
print(set(ecv_otb.columns) == set(ecv_full.columns))   # True

# Confirm the 20 OTB specimen IDs are all present in the full CSV
print(ecv_otb['ID'].isin(ecv_full['ID']).all())         # True

# %% [markdown]
# # Part 2 - Data Cleaning

# %% 2.1 Missing Values
ecv_full.isnull().sum()                            # count per column, shows there is no missing data
ecv_full.dropna(subset=['ecv_median_cm3'])         # drop rows missing ECV
ecv_full['ecv_median_cm3'].fillna(ecv_full['ecv_median_cm3'].mean())

# %% 2.2 The n_estimatess column as a data quality indicator
print(ecv_full['n_estimates'].value_counts().sort_index())

# How many specimens have only one estimate?
single = (ecv_full['n_estimates'] == 1).sum()
print(f"{single} of {len(ecv_full)} specimens have n_estimates == 1")

# Compare mean ECV for single-estimate vs multi-estimate specimens
print(ecv_full.groupby(ecv_full['n_estimates'] > 1)['ecv_median_cm3'].mean())

# %% The grade column
grade_labels = {
    'archaic': 'Archaic australopith',
    'mega':    'Robust australopith / Paranthropus',
    'trans':   'Transitional (H. habilis)',
    'pre.mod': 'Pre-modern Homo'
}
ecv_full['grade_label'] = ecv_full['grade'].map(grade_labels)
print(ecv_full['grade_label'].value_counts())

# %% Binning by age
bins   = [0.0, 1.0, 2.0, 2.6, 3.5]
labels = ['Late Pleistocene', 'Early Pleistocene', 'Plio-Pleistocene', 'Pliocene']

ecv_full['time_bin'] = pd.cut(ecv_full['age_mid_Ma'],
                               bins=bins, labels=labels)
print(ecv_full['time_bin'].value_counts())

# %% 2.5 String cleaning
taxa = ecv_full['taxon'].unique()

ecv_full.taxon.value_counts()


# %% 3.2 Preparing the join keys
engine = create_engine(DSN)
fossils = pd.read_sql(
    "SELECT f.*, t.scientific_name FROM fossils f JOIN taxa t USING (taxon_id)",
    engine
)

# Compare taxon names
print("OTB taxa:", sorted(fossils['scientific_name'].unique()))
print("ECV taxa:", sorted(ecv_full['taxon'].unique()))

taxon_map = {
 'Australopithecus Dart, 1925': 'Australopithecus',
 'Australopithecus anamensis Leakey et al., 1995': 'Au. anamensis',
 'Hominini': 'Hominini',
 'Homo Linnaeus, 1758': 'Homo',
 'Homo erectus (Dubois, 1892)': 'H. erectus',
 'Homo habilis Leakey, Tobias & Napier, 1964': 'H. habilis',
 'Kenyanthropus platyops Leakey et al., 2001': 'K. platyops',
 'Paranthropus Broom, 1938': 'Paranthropus',
 'Paranthropus aethiopicus (Arambourg & Coppens, 1967)': 'P. aethiopicus',
 'Paranthropus boisei (Leakey, 1959)': 'P. boisei'
}

# Create a taxon_name row in the fossils.df
fossils['taxon_name']=fossils['scientific_name'].map(taxon_map)
print(fossils['taxon_name'])
print(fossils['taxon_name'].isnull().sum())

#  %%
# In Pandas, as in R, loops are usually the least efficient solution to a problem, 
# because the Pandas Series and Datafram objects are designed to behave more like their R counterparts. 

# For example, why doesn't this work. Can you fix it?
for n in fossils['scientific_name']: 
    fossils['taxon_name']=taxon_map[n]


# Solution
for i, n in fossils['scientific_name'].items():
    fossils.loc[i, 'taxon_name'] = taxon_map[n]

# %% Summarizing ECV by taxon
# An example of grouping and aggregating. 
# The resulting table has taxon as an index not as a regular column; 
# the reset_index method adds a numbered index for each row and converts
# the taxon column to a regular field, which is necessary for the next step.
ecv_by_taxon = (
    ecv_full
    .groupby('taxon')['ecv_median_cm3']
    .agg(ecv_mean='mean', ecv_median='median',
         ecv_min='min', ecv_max='max', ecv_n='count')
    .reset_index()
)
print(ecv_by_taxon)

# %% Join by taxon
# An example join using Pandas merge method. 
# What is the difference between left join, inner join, outer join?
# What is the difference between a method and an attribute for a Python class?
fossils_ecv = pd.merge(
    fossils,
    ecv_by_taxon,
    left_on='taxon_name', right_on='taxon',
    how='left'
)
print(fossils_ecv.shape)        # rows should equal fossils.shape (left join preserves all rows)
print(fossils_ecv['ecv_mean'].isnull().sum())   # taxa with no ECV data

# %% Include Age uncertainty
# Specimen-level join — only works where catalog_number == ECV specimen ID. Why is this problematic?
specimen_join = pd.merge(
    fossils,
    ecv_full[['ID', 'ecv_median_cm3', 'age_lo_Ma', 'age_hi_Ma', 'n_estimates']],
    left_on='organism_id', right_on='ID',
    how='inner'
)
print(f"{len(specimen_join)} OTB fossils matched a published ECV measurement")
print(specimen_join[['catalog_number', 'taxon_name', 'ecv_median_cm3', 'n_estimates']])

# %% Aggregate by organism_id instead of catalog_number
# Use the first argument to apply the first value encountered as the value for the aggregate
fossils_by_individual = (
    fossils
    .groupby('organism_id')
    .agg(
        taxon_name=('taxon_name', 'first'),
        n_elements=('catalog_number', 'count'),
    )
    .reset_index()
)

# A quicker way to take the first record and include all columns.individuals
individuals = fossils.drop_duplicates(subset='organism_id')

# I can then merge these two to get all the data plus the counts
individuals_merged = pd.merge(fossils_by_individual, individuals, on='organism_id', how='left')

# The methods above often assume that for a column of interests, e.g. scientific_name, all specimens
# belonging to the same organism_id have the same scientific_name value. Worth running a sanity check. 
inconsistent = fossils.groupby('organism_id')['taxon_name'].nunique()
print(inconsistent[inconsistent > 1])  # should be empty

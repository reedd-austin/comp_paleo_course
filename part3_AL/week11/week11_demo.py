# %% [markdown]
# # Week 11 Demonstration

# %% Setup
import json

import pandas as pd

# %% load ecv json to df
with open('ecv_otb_subset.json') as f:
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
ecv_full = pd.read_csv('ecv_by_specimen.csv')
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



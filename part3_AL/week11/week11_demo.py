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

# %%
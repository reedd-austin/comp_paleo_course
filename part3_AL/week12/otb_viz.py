# %% Imports
import os

import pandas as pd
from plotnine import *
from sqlalchemy import create_engine

from config import DSN

# %% Load data
engine = create_engine(DSN)

fossils = pd.read_sql(
    """
    SELECT f.*, t.scientific_name, l.*
    FROM fossils f
    JOIN taxa t USING (taxon_id)
    JOIN localities l USING (locality_id)
    """, engine
)

path = os.path.join("part3_AL/week11/ecv_by_specimen.csv")
ecv_full = pd.read_csv(path)

# Grade is a ordered categorical variable. 
# We need to set the ordering or else it will default
# to alphabetical. 
grade_order = ['archaic', 'mega', 'trans', 'pre.mod']
ecv_full['grade'] = pd.Categorical(ecv_full['grade'], 
    categories=grade_order, 
    ordered=True)

# %% Rereate fossils_ecv
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

ecv_by_taxon = (
    ecv_full
    .groupby('taxon')['ecv_median_cm3']
    .agg(ecv_mean='mean', ecv_median='median',
         ecv_min='min', ecv_max='max', ecv_n='count')
    .reset_index()
)

fossils_ecv = pd.merge(
    fossils,
    ecv_by_taxon,
    left_on='taxon_name', right_on='taxon',
    how='left'
)
print(fossils_ecv.shape)

# %% 1.1 Histogram
# Experiment with different bin width settings.
p1 = (ggplot(ecv_full, aes(x='ecv_median_cm3'))
      + geom_histogram(binwidth=50, fill='steelblue', color='white')
      + labs(x='Endocranial volume (cm³)', y='Count',
             title='Distribution of hominin ECV estimates')
      + theme_bw()
)
p1.save('ecv_histogram.png', dpi=150)

# %% 1.2
p2 = (ggplot(ecv_full, aes(x='ecv_median_cm3', fill='grade'))
      + geom_density(alpha=0.4)
      + scale_fill_brewer(type='qual', palette='Set2')
      + labs(x='Endocranial volume (cm³)', fill='Grade')
      + theme_bw()
)
p2.save('ecv_density_by_grade.png', dpi=150)

# %% 1.3 deliverables

# %% 2.1 Scatter plot
p3 = (ggplot(ecv_full, aes(x='age_mid_Ma', y='ecv_median_cm3',
                            color='grade', size='n_estimates'))
      + geom_point(alpha=0.7)
      + scale_x_reverse()          # older ages on the left
      + scale_color_brewer(type='qual', palette='Set1')
      + labs(x='Age (Ma)', y='ECV (cm³)',
             color='Grade', size='N estimates',
             title='Hominin ECV through time')
      + theme_bw()
)
p3.save('ecv_vs_age.png', dpi=150)

# %% Add a trend line
p4 = (ggplot(ecv_full, aes(x='age_mid_Ma', y='ecv_median_cm3'))
      + geom_point(aes(color='grade'), alpha=0.6)
      + geom_smooth(method='lm', color='black', linetype='dashed')
      + scale_x_reverse()
      + labs(x='Age (Ma)', y='ECV (cm³)')
      + theme_bw()
)
p4.save('ecv_trend.png', dpi=150)

# %% Add trends per grade
p4_2 = (ggplot(ecv_full,
             aes(x='age_mid_Ma', y='ecv_median_cm3', color='grade'))
      + geom_point(alpha=0.6)
      + geom_smooth(method='lm', linetype='dashed', se=False)
      + scale_x_reverse()
      + scale_color_brewer(type='qual', palette='Set1')
      + labs(x='Age (Ma)', y='ECV (cm³)', color='Grade')
      + theme_bw()
)
p4_2.save('ecv_trend2.png', dpi=200)

# %% 2.3 Boxplot
taxon_order = (ecv_full.groupby('taxon')['ecv_median_cm3']
               .median()
               .sort_values()
               .index.tolist())

ecv_full['taxon'] = pd.Categorical(ecv_full['taxon'],
                                    categories=taxon_order,
                                    ordered=True)

p5 = (ggplot(ecv_full, aes(x='taxon', y='ecv_median_cm3', fill='grade'))
      + geom_boxplot()
      + coord_flip()               # horizontal boxes, easier to read long labels
      + labs(x='', y='ECV (cm³)', fill='Grade')
      + theme_bw()
      + theme(legend_position='bottom')
)
p5.save('ecv_boxplot_taxon.png', dpi=150)

# Find the outlier P. boisei
ecv_full[ecv_full['taxon'] == 'P. boisei'].nlargest(3, 'ecv_median_cm3')


# %% 3.1 Specimen counts by taxon and locality
counts = (fossils_ecv
          .groupby(['taxon_name', 'subregion'])
          .size()
          .reset_index(name='n_specimens'))

p6 = (ggplot(counts, aes(x='subregion', y='n_specimens', fill='taxon_name'))
      + geom_col()                 # stacked bar (geom_col uses a pre-computed y)
      + coord_flip()
      + labs(x='', y='Specimens', fill='Taxon')
      + theme_bw()
      + theme(legend_position='bottom',
              figure_size=(8, 5))
)
p6.save('otb_counts.png', dpi=150)


# %% 3.2 Faceting
# Find taxa with 2 or more specimens
taxon_counts = ecv_full['taxon'].value_counts()
multi_specimen_taxa = taxon_counts[taxon_counts > 1].index

p7 = (ggplot(ecv_full[ecv_full['taxon'].isin(multi_specimen_taxa)],
             aes(x='age_mid_Ma', y='ecv_median_cm3', color='taxon'))
      + geom_point(alpha=0.6)
      + geom_smooth(method='lm', se=False, linetype='dashed', size=0.8)
      + facet_wrap('~taxon', scales='free_y')
      + scale_x_reverse()
      + labs(x='Age (Ma)', y='Median ECV (cm³)')
      + theme_bw()
      + theme(legend_position='none',  # redundant with facet labels
              figure_size=(10, 6))
)
p7.save('otb_ecv_faceted.png', dpi=150)
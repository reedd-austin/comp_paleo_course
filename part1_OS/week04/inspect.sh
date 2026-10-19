#!/usr/bin/env bash

# My first bash script

#DATASET="otb_fossils.tsv"
DATASET=$1
DATADIR=~/comp_paleo/week03
TODAY=$(date)
ROW_COUNT=$(wc -l < "$DATADIR/$DATASET")
COL_COUNT=$(head -1 "$DATADIR/$DATASET" | tr '\t' '\n' | wc -l )

echo "Dataset: $DATASET"
echo "Date: $TODAY"
echo "Rows: $ROW_COUNT"

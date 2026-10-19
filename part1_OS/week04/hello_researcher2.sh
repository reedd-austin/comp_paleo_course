#!/usr/bin/env bash
# hello_researcher.sh — with variables

RESEARCHER="$(whoami)"
TODAY="$(date +%Y-%m-%d)"
DATASET="otb_fossils.tsv"
DATADIR=~/comp_paleo/week03

echo "Researcher: $RESEARCHER"
echo "Date: $TODAY"
echo "Dataset: $DATASET"
echo "Row count: $(wc -l < $DATADIR/$DATASET)"


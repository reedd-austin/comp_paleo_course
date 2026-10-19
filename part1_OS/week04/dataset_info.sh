#!/usr/bin/env bash
# dataset_info.sh
# Print basic information about a TSV data file.
# Usage: ./dataset_info.sh <filepath>

# Check that exactly one argument was provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <filepath>"
    echo "Example: $0 ~/comp_paleo/part01_OS/week03/otb_fossils.tsv"
    exit 1
fi

FILEPATH="$1"

# Check that the file exists
if [ ! -f "$FILEPATH" ]; then
    echo "Error: file not found: $FILEPATH"
    exit 1
fi

FILENAME=$(basename "$FILEPATH")
ROWS=$(tail -n +2 "$FILEPATH" | wc -l)
COLS=$(head -1 "$FILEPATH" | tr '\t' '\n' | wc -l)

if ["$ROWS" -lt 100]; then
    echo "Warning, short file."
    exit 1
fi

echo "====================================="
echo "File:    $FILENAME"
echo "Rows:    $ROWS (excluding header)"
echo "Columns: $COLS"
echo "Header fields:"
head -1 "$FILEPATH" | tr '\t' '\n' | cat -n
echo "====================================="

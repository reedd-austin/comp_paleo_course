#!/usr/bin/env bash
# validate_tsv.sh
# Check a TSV file for common problems.
# Usage: ./validate_tsv.sh <filepath> <expected_columns>

if [ $# -ne 2 ]; then
    echo "Usage: $0 <filepath> <expected_columns>"
    exit 1
fi

FILEPATH="$1"
EXPECTED_COLS="$2"
ERRORS=0

echo "Validating: $FILEPATH"
echo "Expected columns: $EXPECTED_COLS"
echo "---"

# Check file exists
if [ ! -f "$FILEPATH" ]; then
    echo "FAIL: file does not exist"
    exit 1
fi

# Check file is non-empty
if [ ! -s "$FILEPATH" ]; then
    echo "FAIL: file is empty"
    exit 1
fi

# Check header column count
HEADER_COLS=$(head -1 "$FILEPATH" | tr '\t' '\n' | wc -l | tr -d ' ')
if [ "$HEADER_COLS" -eq "$EXPECTED_COLS" ]; then
    echo "PASS: header has $HEADER_COLS columns"
else
    echo "FAIL: header has $HEADER_COLS columns (expected $EXPECTED_COLS)"
    ERRORS=$((ERRORS + 1))
fi

# Check total row count
TOTAL_ROWS=$(wc -l < "$FILEPATH")
DATA_ROWS=$((TOTAL_ROWS - 1))
echo "INFO: $DATA_ROWS data rows (plus 1 header)"

if [ "$DATA_ROWS" -lt 10 ]; then
    echo "WARN: file has fewer than 10 data rows — may be incomplete"
fi

# Check for rows with wrong column count
BAD_ROWS=$(awk -F'\t' -v cols="$EXPECTED_COLS" 'NF != cols {print NR}' "$FILEPATH" | wc -l | tr -d ' ')
if [ "$BAD_ROWS" -eq 0 ]; then
    echo "PASS: all rows have $EXPECTED_COLS columns"
else
    echo "FAIL: $BAD_ROWS row(s) have wrong column count"
    echo "      First 5 offending line numbers:"
    awk -F'\t' -v cols="$EXPECTED_COLS" 'NF != cols {print "  Line", NR, "has", NF, "columns"}' \
        "$FILEPATH" | head -5
    ERRORS=$((ERRORS + 1))
fi

echo "---"
if [ "$ERRORS" -eq 0 ]; then
    echo "RESULT: PASSED ($ERRORS errors)"
    exit 0
else
    echo "RESULT: FAILED ($ERRORS errors)"
    exit 1
fi

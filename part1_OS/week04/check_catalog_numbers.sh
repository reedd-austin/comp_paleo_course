#!/usr/bin/env bash
# check_catalog_numbers.sh
# Check that all catalog numbers in a TSV begin with a given prefix.
# Usage: ./check_catalog_numbers.sh <tsv_file> <prefix>
# Example: ./check_catalog_numbers.sh eppe_fossils.tsv "EP "

if [ $# -ne 2 ]; then
    echo "Usage: $0 <tsv_file> <prefix>"
    exit 1
fi

FILEPATH="$1"
PREFIX="$2"
LINE_NUM=1
BAD_COUNT=0
LOG_FILE="bad_catalog_numbers.log"

# Clear the log file
> "$LOG_FILE"

echo "Checking catalog numbers in: $(basename $FILEPATH)"
echo "Expected prefix: '$PREFIX'"
echo ""

tail -n +2 "$FILEPATH" | while IFS=$'\t' read -r CATALOG_NUM REST; do
    LINE_NUM=$((LINE_NUM + 1))
    if [[ "$CATALOG_NUM" != "$PREFIX"* ]]; then
        echo "Line $LINE_NUM: unexpected catalog number: '$CATALOG_NUM'" | tee -a "$LOG_FILE"
        BAD_COUNT=$((BAD_COUNT + 1))
    fi
done

echo ""
echo "Check complete. Problems logged to: $LOG_FILE"


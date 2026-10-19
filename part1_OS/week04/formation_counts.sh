#!/usr/bin/env bash
# formation_counts.sh
# Count specimens per formation in the OTB dataset.
# Usage: ./formation_counts.sh <tsv_file>

if [ $# -ne 1 ]; then
    echo "Usage: $0 <tsv_file>"
    exit 1
fi

FILEPATH="$1"
FORMATION_COL=19   # column number for 'formation'

echo "Specimen counts by formation"
echo "Dataset: $(basename $FILEPATH)"
echo "================================"

for FORMATION in "Koobi Fora" "Shungura" "Nachukui" "Nawata" "Kanapoi" "Usno"; do
    COUNT=$(tail -n +2 "$FILEPATH" | awk -F'\t' -v f="$FORMATION" '$19 == f' | wc -l | tr -d ' ')
    printf "%-20s  %d\n" "$FORMATION" "$COUNT"
done

echo "================================"
TOTAL=$(tail -n +2 "$FILEPATH" | wc -l | tr -d ' ')
printf "%-20s  %d\n" "TOTAL" "$TOTAL"


#!/usr/bin/env bash
# batch inspect

DIRPATH="$1"
echo "Inspecting files in $DIRPATH"
echo ""

for FILEPATH in "$DIRPATH"/*.sh; do
  FILENAME=$(basename "$FILEPATH")
  #printf "%-35s \n" "$FILENAME"
  echo "filename: $FILENAME"
done


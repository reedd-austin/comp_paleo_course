#!/usr/bin/env python3
"""
fix_newlines.py
Reads a CSV file, removes embedded newlines from all fields,
and writes the result as a tab-separated (TSV) file.

Usage: python3 fix_newlines.py input.csv output.tsv
"""

import csv
import sys

def fix_newlines(input_path, output_path):
    rows_fixed = 0

    with open(input_path, newline='', encoding='utf-8') as infile, \
         open(output_path, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.reader(infile)
        writer = csv.writer(outfile, delimiter='\t')

        for i, row in enumerate(reader):
            cleaned = []
            row_had_newline = False

            for field in row:
                if '\n' in field or '\r' in field:
                    cleaned.append(field.replace('\n', ' ').replace('\r', '').strip())
                    row_had_newline = True
                else:
                    cleaned.append(field)

            if row_had_newline:
                rows_fixed += 1
                print(f"  Row {i}: embedded newline removed", file=sys.stderr)

            writer.writerow(cleaned)

    print(f"Done. {rows_fixed} row(s) fixed.")
    print(f"Output written to: {output_path}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 fix_newlines.py input.csv output.tsv")
        sys.exit(1)

    fix_newlines(sys.argv[1], sys.argv[2])
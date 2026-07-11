"""
Extract the first N rows of a large CSV file without loading
the whole file into memory (good for multi-GB files like the
CFPB Consumer Complaints dataset).

Usage:
    python sample_csv.py
    (edit INPUT_FILE, OUTPUT_FILE, NUM_ROWS below, or pass as args)
"""

import csv
import sys

def sample_csv(input_file, output_file, num_rows=2000):
    with open(input_file, "r", newline="", encoding="utf-8") as infile, \
         open(output_file, "w", newline="", encoding="utf-8") as outfile:

        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        header = next(reader)          # keep the header row
        writer.writerow(header)

        for i, row in enumerate(reader):
            if i >= num_rows:
                break
            writer.writerow(row)

    print(f"Done. Wrote header + {min(i+1, num_rows)} rows to {output_file}")


if __name__ == "__main__":
    # Defaults — change these paths to match your file
    INPUT_FILE = "complaints.csv"
    OUTPUT_FILE = "complaints_sample_2000.csv"
    NUM_ROWS = 2000

    # Allow overriding via command line: python sample_csv.py in.csv out.csv 2000
    if len(sys.argv) >= 3:
        INPUT_FILE = sys.argv[1]
        OUTPUT_FILE = sys.argv[2]
    if len(sys.argv) >= 4:
        NUM_ROWS = int(sys.argv[3])

    sample_csv(INPUT_FILE, OUTPUT_FILE, NUM_ROWS)
#!/usr/bin/env python3

import csv
import os
import sys

# Function to apply corrections to the audit data file
def apply_corrections(source_file, corrections_file, output_file):
    # Read corrections
    corrections = {}
    with open(corrections_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 5 and row[5] == 'high':  # Only apply high confidence corrections
                school_name = row[0]
                current_region = row[2]
                correct_region = row[3]
                corrections[school_name] = {
                    'current': current_region,
                    'correct': correct_region
                }
    
    # Read and update source file
    updated_rows = []
    correction_count = 0
    
    with open(source_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        updated_rows.append(headers)
        
        for row in reader:
            if len(row) > 1:
                school_name = row[0].strip()
                if school_name in corrections:
                    current_region = row[1].strip()
                    if current_region == corrections[school_name]['current']:
                        row[1] = corrections[school_name]['correct']
                        correction_count += 1
            updated_rows.append(row)
    
    # Write updated data
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(updated_rows)
    
    return correction_count

if __name__ == "__main__":
    source_file = 'src/data/SchoolsAuditData2018-2023.csv'
    corrections_file = 'education_region_corrections.csv'
    output_file = 'src/data/SchoolsAuditData2018-2023.csv.corrected'
    
    count = apply_corrections(source_file, corrections_file, output_file)
    print(f"Applied {count} corrections to {output_file}")
    print("Review the file and rename it to replace the original if satisfied.")

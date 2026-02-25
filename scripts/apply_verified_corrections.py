#!/usr/bin/env python3

import csv
import os
import sys

# Function to apply corrections to the audit data file
def apply_corrections(source_file, corrections_file, output_file):
    # Read corrections
    corrections = {}
    region_mappings = {}
    
    with open(corrections_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 3:
                school_name = row[0]
                current_region = row[1]
                correct_region = row[2]
                
                # Track region mappings for schools without exact name matches
                if current_region not in region_mappings:
                    region_mappings[current_region] = correct_region
                
                corrections[school_name] = {
                    'current': current_region,
                    'correct': correct_region
                }
    
    # Read and update source file
    updated_rows = []
    correction_count = 0
    region_standardization_count = 0
    
    with open(source_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        updated_rows.append(headers)
        
        for row in reader:
            if len(row) > 1:
                school_name = row[0].strip()
                current_region = row[1].strip()
                
                # Direct school match
                if school_name in corrections:
                    if current_region == corrections[school_name]['current']:
                        row[1] = corrections[school_name]['correct']
                        correction_count += 1
                # Region standardization
                elif current_region in region_mappings:
                    row[1] = region_mappings[current_region]
                    region_standardization_count += 1
                    
            updated_rows.append(row)
    
    # Write updated data
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(updated_rows)
    
    return correction_count, region_standardization_count

if __name__ == "__main__":
    source_file = 'src/data/SchoolsAuditData2018-2023.csv'
    corrections_file = 'verified_corrections.csv'
    output_file = 'src/data/SchoolsAuditData2018-2023.csv.corrected'
    
    direct_count, region_count = apply_corrections(source_file, corrections_file, output_file)
    print(f"Applied {direct_count} direct school corrections")
    print(f"Applied {region_count} region standardization corrections")
    print(f"Total of {direct_count + region_count} corrections applied to {output_file}")
    print("Review the file and rename it to replace the original if satisfied.")

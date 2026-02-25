#!/usr/bin/env python3

import csv
import os
from difflib import SequenceMatcher

# Load corrections
corrections = []
with open('education_region_corrections.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    headers = next(reader)  # Skip header
    
    for row in reader:
        if len(row) >= 6:
            corrections.append({
                'audit_name': row[0],
                'directory_name': row[1],
                'audit_region': row[2],
                'directory_region': row[3],
                'match_method': row[4],
                'confidence': row[5]
            })

# Load unmatched schools
unmatched = []
with open('unmatched_schools.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    headers = next(reader)  # Skip header
    
    for row in reader:
        if len(row) >= 4:
            unmatched.append({
                'name': row[0],
                'region': row[1],
                'latitude': row[2],
                'longitude': row[3]
            })

# Filter corrections by confidence
high_confidence = [c for c in corrections if c['confidence'] == 'high']
medium_confidence = [c for c in corrections if c['confidence'] == 'medium']

# Check for duplicate schools in corrections
school_corrections = {}
for correction in high_confidence:
    school_name = correction['audit_name']
    if school_name in school_corrections:
        school_corrections[school_name].append(correction)
    else:
        school_corrections[school_name] = [correction]

# Check for multiple region mappings
region_mappings = {}
for correction in high_confidence:
    audit_region = correction['audit_region']
    directory_region = correction['directory_region']
    
    if audit_region in region_mappings:
        if region_mappings[audit_region] != directory_region:
            print(f"WARNING: Region {audit_region} maps to multiple directory regions: {region_mappings[audit_region]} and {directory_region}")
    else:
        region_mappings[audit_region] = directory_region

# Print summary
print(f"Total corrections found: {len(corrections)}")
print(f"High confidence corrections: {len(high_confidence)}")
print(f"Medium confidence corrections: {len(medium_confidence)}")
print(f"Unmatched schools: {len(unmatched)}")
print(f"Unique schools needing correction: {len(school_corrections)}")

# Create verified corrections file
with open('verified_corrections.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['School Name', 'Current Region', 'Correct Region', 'Match Method'])
    
    # Handle each school only once with highest confidence match
    for school_name, school_corrs in school_corrections.items():
        # Use the first correction for now (they should all have the same region for high confidence)
        correction = school_corrs[0]
        writer.writerow([
            correction['audit_name'],
            correction['audit_region'],
            correction['directory_region'],
            correction['match_method']
        ])

# Print region mappings
print("\nRegion mappings:")
for audit_region, directory_region in sorted(region_mappings.items()):
    print(f"{audit_region} -> {directory_region}")

# Create apply_verified_corrections.py script
with open('apply_verified_corrections.py', 'w', encoding='utf-8') as f:
    f.write('''#!/usr/bin/env python3

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
''')

print("Created apply_verified_corrections.py script for applying verified corrections")
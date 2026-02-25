#!/usr/bin/env python3

import csv
import os
import re
from difflib import SequenceMatcher

# Function to calculate string similarity
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Function to calculate distance between coordinates
def coord_distance(lat1, lon1, lat2, lon2):
    # Simple Euclidean distance for now
    # This is not geographically accurate but sufficient for matching
    return ((float(lat1) - float(lat2))**2 + (float(lon1) - float(lon2))**2)**0.5

# Function to normalize region names for comparison
def normalize_region_name(region):
    # Remove quotes
    region = region.strip('"\'')
    
    # Normalize separators: replace comma+space with forward slash
    region = re.sub(r', ', '/', region)
    
    # Remove any trailing text like 'Region' or 'Office'
    region = re.sub(r' Region$| Office$', '', region)
    
    return region

# Load directory data (authoritative source)
directory_schools = {}
directory_path = os.path.join(os.getcwd(), 'School directory 5Sep24.csv')

# Track region name mappings
region_mappings = {}

with open(directory_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    headers = next(reader)
    
    # Find indices for relevant columns
    name_idx = headers.index('School Name')
    region_idx = headers.index('Education Region')
    lat_idx = headers.index('Latitude')
    lon_idx = headers.index('Longitude')
    
    for row in reader:
        if len(row) <= max(name_idx, region_idx, lat_idx, lon_idx):
            continue  # Skip rows that are too short
            
        school_name = row[name_idx].strip()
        region = row[region_idx].strip()
        
        # Store the raw region and a normalized version for comparison
        normalized_region = normalize_region_name(region)
        if normalized_region not in region_mappings:
            region_mappings[normalized_region] = region
        
        directory_schools[school_name] = {
            'name': school_name,
            'region': region,
            'normalized_region': normalized_region,
            'latitude': row[lat_idx].strip() if row[lat_idx].strip() else None,
            'longitude': row[lon_idx].strip() if row[lon_idx].strip() else None
        }

# Load audit data (file to check)
audit_schools = []
audit_path = os.path.join(os.getcwd(), 'src/data/SchoolsAuditData2018-2023.csv')

with open(audit_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    headers = next(reader)
    
    # Find indices for relevant columns
    name_idx = 0  # School name is in first column
    region_idx = 1  # Education region is in second column
    lon_idx = 9  # Longitude
    lat_idx = 10  # Latitude
    
    for row in reader:
        if len(row) <= max(name_idx, region_idx, lat_idx, lon_idx):
            continue  # Skip rows that are too short
            
        school_name = row[name_idx].strip()
        region = row[region_idx].strip()
        
        # Skip header rows or problematic data
        if (school_name == 'School' or region == 'Education region' or 
            school_name.startswith('Highlighted matter') or 
            'drew attention to' in school_name):
            continue
            
        # Normalize region for comparison
        normalized_region = normalize_region_name(region)
        
        audit_schools.append({
            'name': school_name,
            'region': region,
            'normalized_region': normalized_region,
            'latitude': row[lat_idx].strip() if row[lat_idx].strip() else None,
            'longitude': row[lon_idx].strip() if row[lon_idx].strip() else None,
            'matched': False,
            'directory_match': None,
            'directory_region': None
        })

# Perform matching
corrections = []
unmatched = []
exact_name_matches = 0
fuzzy_name_matches = 0
coord_matches = 0

for audit_school in audit_schools:
    best_match = None
    best_score = 0
    best_coord_match = None
    best_coord_distance = float('inf')
    
    # Try direct name match first
    if audit_school['name'] in directory_schools:
        best_match = directory_schools[audit_school['name']]
        best_score = 1.0
        exact_name_matches += 1
    else:
        # Try fuzzy matching
        for dir_name, dir_school in directory_schools.items():
            # Name similarity
            score = similarity(audit_school['name'], dir_name)
            
            # Coordinate distance if coordinates are available
            coord_score = float('inf')
            if (audit_school['latitude'] and audit_school['longitude'] and 
                dir_school['latitude'] and dir_school['longitude']):
                try:
                    coord_score = coord_distance(
                        audit_school['latitude'], audit_school['longitude'], 
                        dir_school['latitude'], dir_school['longitude']
                    )
                    
                    # Keep track of best coordinate match separately
                    if coord_score < best_coord_distance:
                        best_coord_distance = coord_score
                        best_coord_match = dir_school
                except (ValueError, TypeError):
                    # Handle potential coordinate conversion errors
                    pass
            
            # Update best match based on name similarity
            if score > best_score:
                best_score = score
                best_match = dir_school
    
    # Determine final match
    final_match = None
    match_method = None
    
    if best_score >= 0.9:  # High confidence name match
        final_match = best_match
        match_method = f"name match (score: {best_score:.2f})"
        if best_score < 1.0:
            fuzzy_name_matches += 1
    elif best_coord_match and best_coord_distance < 0.005:  # Close coordinate match
        final_match = best_coord_match
        match_method = f"coordinate match (distance: {best_coord_distance:.6f})"
        coord_matches += 1
    
    # Set matched info
    if final_match:
        audit_school['matched'] = True
        audit_school['directory_match'] = final_match['name']
        audit_school['directory_region'] = final_match['region']
        audit_school['match_method'] = match_method
        
        # Check if regions don't match - compare normalized regions first
        if audit_school['normalized_region'] != final_match['normalized_region']:
            corrections.append({
                'audit_name': audit_school['name'],
                'directory_name': final_match['name'],
                'audit_region': audit_school['region'],
                'directory_region': final_match['region'],
                'match_method': match_method,
                'confidence': 'high' if best_score >= 0.95 or best_coord_distance < 0.001 else 'medium'
            })
    else:
        unmatched.append(audit_school)

# Write corrections to a file
with open('education_region_corrections.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Audit School Name', 'Directory School Name', 'Current Region', 'Correct Region', 'Match Method', 'Confidence'])
    for correction in corrections:
        writer.writerow([
            correction['audit_name'],
            correction['directory_name'],
            correction['audit_region'],
            correction['directory_region'],
            correction['match_method'],
            correction['confidence']
        ])

# Write unmatched schools to a file
with open('unmatched_schools.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['School Name', 'Current Region', 'Latitude', 'Longitude'])
    for school in unmatched:
        writer.writerow([
            school['name'],
            school['region'],
            school['latitude'],
            school['longitude']
        ])

# Print summary
print(f"Total schools in audit data: {len(audit_schools)}")
print(f"Matched via exact name: {exact_name_matches}")
print(f"Matched via fuzzy name: {fuzzy_name_matches}")
print(f"Matched via coordinates: {coord_matches}")
print(f"Schools with region corrections needed: {len(corrections)}")
print(f"Schools not matched: {len(unmatched)}")
print("Results written to education_region_corrections.csv and unmatched_schools.csv")

# Create a script to apply corrections
with open('apply_corrections.py', 'w', encoding='utf-8') as f:
    f.write('''#!/usr/bin/env python3

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
''')

print("Created apply_corrections.py script for applying high-confidence corrections")
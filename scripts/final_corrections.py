#!/usr/bin/env python3

import csv
import os
import re
from collections import defaultdict

# Define the final region mappings based on our authoritative source
STANDARD_REGION_MAPPINGS = {
    "Auckland": "Tāmaki Herenga Waka", # Based on most common mapping
    "Bay of Plenty/Waiariki": "Bay of Plenty, Waiariki",
    "Canterbury/Chatham Islands": "Canterbury, Chatham Islands",
    "Hawke's Bay/Tairāwhiti": "Hawke's Bay, Tairāwhiti",
    "Nelson/Marlborough/West Coast": "Nelson, Marlborough, West Coast",
    "Northland": "Tai Tokerau",
    "Otago/Southland": "Otago, Southland",
    "Taranaki/Whanganui/Manawatū": "Taranaki, Whanganui, Manawatū" 
}

# Keep track of the schools we fully trust the matches for
TRUSTED_SCHOOL_MATCHES = {
    # High-confidence exact name matches (score=1.0) in Auckland
    "Howick Intermediate": "Tāmaki Herenga Manawa",
    "Kadimah School": "Tāmaki Herenga Manawa",
    "Horizon School": "Tāmaki Herenga Tāngata",
    "Manurewa West School": "Tāmaki Herenga Waka",
    "Albany Junior High School": "Tāmaki Herenga Tāngata",
    "Papatoetoe North School": "Tāmaki Herenga Waka",
    "Okiwi School": "Tāmaki Herenga Manawa",
    "Sacred Heart College (Auckland)": "Tāmaki Herenga Manawa",
    "Westminster Christian School": "Tāmaki Herenga Tāngata",
    "Ponsonby Primary School": "Tāmaki Herenga Manawa",
    "Howick College": "Tāmaki Herenga Manawa",
    "Orere School": "Tāmaki Herenga Waka",
    "Vanguard Military School": "Tāmaki Herenga Tāngata",
    "Brookby School": "Tāmaki Herenga Manawa",
    "Clendon Park School": "Tāmaki Herenga Waka",
    "Jireh Christian School": "Tāmaki Herenga Manawa",
    "St Joseph's School (Grey Lynn)": "Tāmaki Herenga Manawa",
    
    # High-confidence name matches for Northland/Tai Tokerau
    "Matauri Bay School": "Tai Tokerau",
    "Northland College": "Tai Tokerau",
    
    # Other highly confident matches
    "Liston College": "Tāmaki Herenga Tāngata",
    
    # Edge cases we're confident about based on coordinates
    "TKKM o Otara": "Tāmaki Herenga Waka",
    "Christian Renewal School": "Tai Tokerau",
    "Omanaia School": "Tai Tokerau",
}

def load_corrections(corrections_file):
    """Load corrections from the corrections file."""
    corrections = []
    with open(corrections_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)  # Skip header
        
        for row in reader:
            if len(row) >= 4:
                corrections.append({
                    'school_name': row[0],
                    'current_region': row[1],
                    'correct_region': row[2],
                    'match_method': row[3]
                })
    return corrections

def apply_corrections(source_file, output_file):
    """Apply corrections directly to the source file."""
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
                
                # Skip header or problematic rows
                if school_name == 'School' or current_region == 'Education region':
                    updated_rows.append(row)
                    continue
                
                # 1. Check trusted school matches first
                if school_name in TRUSTED_SCHOOL_MATCHES:
                    new_region = TRUSTED_SCHOOL_MATCHES[school_name]
                    if current_region != new_region:
                        row[1] = new_region
                        correction_count += 1
                
                # 2. Apply standard region mappings
                elif current_region in STANDARD_REGION_MAPPINGS:
                    new_region = STANDARD_REGION_MAPPINGS[current_region]
                    if current_region != new_region:
                        row[1] = new_region
                        region_standardization_count += 1
                
            updated_rows.append(row)
    
    # Write updated data
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(updated_rows)
    
    return correction_count, region_standardization_count

def create_report(source_file, corrections_file, unmatched_file, output_file):
    """Create a report of all corrections and issues."""
    corrections = load_corrections(corrections_file)
    
    # Load unmatched schools
    unmatched = []
    with open(unmatched_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)  # Skip header
        
        for row in reader:
            if len(row) >= 2:
                unmatched.append(row[0])
    
    # Track issues found
    issues = []
    
    # Check for school names in corrections that don't match our trusted list
    for correction in corrections:
        school_name = correction['school_name']
        suggested_region = correction['correct_region']
        
        if school_name in TRUSTED_SCHOOL_MATCHES:
            if TRUSTED_SCHOOL_MATCHES[school_name] != suggested_region:
                issues.append(f"Conflict for {school_name}: trusted={TRUSTED_SCHOOL_MATCHES[school_name]}, suggested={suggested_region}")
        else:
            match_method = correction['match_method']
            # Only flag name matches with score < 1.0 as potential issues
            if 'name match' in match_method and 'score: 1.00' not in match_method:
                issues.append(f"Potential incorrect match: {school_name} -> {suggested_region} ({match_method})")
    
    # Write report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Education Region Standardization Report\n\n")
        
        f.write("## Standard Region Mappings\n\n")
        f.write("| Current Region | Standard Region |\n")
        f.write("|----------------|----------------|\n")
        for old_region, new_region in sorted(STANDARD_REGION_MAPPINGS.items()):
            f.write(f"| {old_region} | {new_region} |\n")
        
        f.write("\n## Trusted School-Specific Mappings\n\n")
        f.write("| School Name | Education Region |\n")
        f.write("|-------------|----------------|\n")
        for school, region in sorted(TRUSTED_SCHOOL_MATCHES.items()):
            f.write(f"| {school} | {region} |\n")
        
        f.write("\n## Unmatched Schools\n\n")
        if unmatched:
            f.write("| School Name |\n")
            f.write("|------------|\n")
            for school in unmatched:
                f.write(f"| {school} |\n")
        else:
            f.write("No unmatched schools found.\n")
        
        f.write("\n## Potential Issues\n\n")
        if issues:
            for issue in issues:
                f.write(f"- {issue}\n")
        else:
            f.write("No issues found.\n")

if __name__ == "__main__":
    source_file = 'src/data/SchoolsAuditData2018-2023.csv'
    corrections_file = 'verified_corrections.csv'
    unmatched_file = 'unmatched_schools.csv'
    output_file = 'src/data/SchoolsAuditData2018-2023.csv.corrected'
    report_file = 'education_region_report.md'
    
    # Apply corrections
    direct_count, region_count = apply_corrections(source_file, output_file)
    print(f"Applied {direct_count} trusted school corrections")
    print(f"Applied {region_count} region standardization corrections")
    print(f"Total of {direct_count + region_count} corrections applied to {output_file}")
    
    # Generate report
    create_report(source_file, corrections_file, unmatched_file, report_file)
    print(f"Created report in {report_file}")
    
    print("Review the corrected file and rename it to replace the original if satisfied:")
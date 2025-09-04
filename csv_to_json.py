import csv
import json
import sys
import os

def csv_to_json(csv_file_path, json_file_path=None):
    """Convert CSV to JSON with first column as primary key"""
    
    result = {}
    
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Get column headers
        
        for row in reader:
            if row:  # Skip empty rows
                primary_key = row[0]
                record = {}
                
                # Create key-value pairs for remaining columns
                for i in range(1, len(headers)):
                    if i < len(row):
                        record[headers[i]] = row[i]
                
                result[primary_key] = record
    
    # Save to JSON file or return
    if json_file_path:
        with open(json_file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(result, jsonfile, indent=2)
        print(f"JSON saved to: {json_file_path}")
    else:
        print(json.dumps(result, indent=2))
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python csv_to_json.py <csv_file> [output_json_file]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    json_file = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(sys.argv[1]).replace('.csv', '.json')
    
    csv_to_json(csv_file, json_file)
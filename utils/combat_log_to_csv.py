#!/usr/bin/env python3
"""
Script to convert combat logs to CSV format.

This utility parses combat log files from the Smite 2 RallyHere API and converts them
to a structured CSV format for analysis.
"""

import os
import re
import json
import csv
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Regular expressions for parsing combat logs
COMBAT_EVENT_PATTERN = re.compile(
    r"\[([^]]+)\] \[(\d+):([^]]+)\] (\w+)(?:\((.*)\))?: (.*)"
)
STARTING_LOG_PATTERN = re.compile(r"Starting Combat log")

def parse_filename(filename):
    """Extract match_id and session_id from the filename."""
    # Expected format: match_id_CombatLog_session_id.log
    parts = Path(filename).stem.split('_')
    if len(parts) >= 3 and parts[1] == "CombatLog":
        match_id = parts[0]
        session_id = "_".join(parts[2:])
        return match_id, session_id
    return None, None

def parse_params(params_str):
    """Parse parameters from a combat event."""
    if not params_str:
        return {}
    
    # Handle different parameter formats
    params = {}
    
    # Try to parse as comma-separated key=value pairs
    if '=' in params_str:
        try:
            param_pairs = params_str.split(',')
            for pair in param_pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    params[key.strip()] = value.strip()
        except Exception:
            params['raw_params'] = params_str
    else:
        # Store as raw params if not in key=value format
        params['raw_params'] = params_str
    
    return params

def parse_combat_log(file_path):
    """Parse a single combat log file and extract event data."""
    match_id, session_id = parse_filename(file_path)
    if not match_id or not session_id:
        print(f"Warning: Could not parse IDs from filename: {file_path}")
        return []
    
    results = []
    line_index = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
            # Skip empty files or files with just the header
            if len(lines) <= 2:
                return []
                
            for line in lines:
                line = line.strip()
                
                # Skip the header line
                if STARTING_LOG_PATTERN.match(line):
                    line_index = 1
                    continue
                
                # Parse combat event line
                match = COMBAT_EVENT_PATTERN.match(line)
                if match:
                    timestamp, entity_id, entity_name, event_type, params_str, event_details = match.groups()
                    
                    # Parse parameters
                    params = parse_params(params_str)
                    
                    # Create event record
                    event = {
                        'match_id': match_id,
                        'session_id': session_id,
                        'timestamp': timestamp,
                        'entity_id': entity_id,
                        'entity_name': entity_name,
                        'event_type': event_type,
                        'event_details': event_details
                    }
                    
                    # Add parameters as columns
                    for key, value in params.items():
                        event[f'param_{key}'] = value
                    
                    results.append(event)
                
                line_index += 1
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
    
    return results

def collect_fieldnames(all_events):
    """Collect all possible fieldnames from the events."""
    base_fieldnames = [
        'match_id', 'session_id', 'timestamp', 'entity_id', 'entity_name',
        'event_type', 'event_details'
    ]
    
    # Collect all parameter keys
    param_keys = set()
    for event in all_events:
        for key in event.keys():
            if key.startswith('param_'):
                param_keys.add(key)
    
    # Sort parameter keys for consistent order
    sorted_param_keys = sorted(list(param_keys))
    
    return base_fieldnames + sorted_param_keys

def process_directory(input_dir, output_file, max_workers=4):
    """Process all combat log files in a directory and write to CSV."""
    input_path = Path(input_dir)
    
    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Input directory {input_dir} does not exist or is not a directory")
        return False
    
    # Get list of combat log files
    combat_log_files = list(input_path.glob("*CombatLog*.log"))
    
    if not combat_log_files:
        print(f"No combat log files found in {input_dir}")
        return False
    
    print(f"Found {len(combat_log_files)} combat log files to process")
    
    # Process files with a progress bar
    all_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for result in tqdm(
            executor.map(parse_combat_log, combat_log_files),
            total=len(combat_log_files),
            desc="Processing combat logs"
        ):
            all_results.extend(result)
    
    if not all_results:
        print("No combat events found in the log files")
        return False
    
    # Collect all possible fieldnames
    fieldnames = collect_fieldnames(all_results)
    
    # Write results to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for event_data in all_results:
            writer.writerow(event_data)
    
    print(f"Successfully processed {len(combat_log_files)} files with {len(all_results)} events")
    print(f"CSV output written to {output_file}")
    
    # Generate event type summary
    event_types = {}
    for event in all_results:
        event_type = event['event_type']
        if event_type not in event_types:
            event_types[event_type] = 0
        event_types[event_type] += 1
    
    print("\nEvent type summary:")
    for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {event_type}: {count}")
    
    return True

def main():
    """Main function to process command line arguments."""
    parser = argparse.ArgumentParser(description="Convert combat logs to CSV format")
    parser.add_argument(
        "--input-dir", "-i", 
        default="combat_logs", 
        help="Directory containing combat log files (default: combat_logs)"
    )
    parser.add_argument(
        "--output-file", "-o", 
        default="combat_logs.csv", 
        help="Output CSV file path (default: combat_logs.csv)"
    )
    parser.add_argument(
        "--max-workers", "-w", 
        type=int, 
        default=4, 
        help="Maximum number of worker threads (default: 4)"
    )
    parser.add_argument(
        "--sample", "-s", 
        action="store_true", 
        help="Process only 5 files as a sample"
    )
    
    args = parser.parse_args()
    
    # Create sample of 5 files if requested
    if args.sample:
        input_path = Path(args.input_dir)
        combat_log_files = list(input_path.glob("*CombatLog*.log"))
        
        if len(combat_log_files) > 5:
            sample_dir = "combat_logs_sample"
            os.makedirs(sample_dir, exist_ok=True)
            
            print(f"Creating sample of 5 files in {sample_dir}")
            for i, file_path in enumerate(combat_log_files[:5]):
                with open(file_path, 'r', encoding='utf-8') as src:
                    with open(f"{sample_dir}/{file_path.name}", 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            args.input_dir = sample_dir
    
    # Process the directory
    process_directory(args.input_dir, args.output_file, args.max_workers)

if __name__ == "__main__":
    main() 
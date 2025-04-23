#!/usr/bin/env python3
"""
Script to convert chat logs to CSV format.

This utility parses chat log files from the Smite 2 RallyHere API and converts them
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

# Regular expressions for parsing chat logs
CHAT_MESSAGE_PATTERN = re.compile(
    r"Sender Id: ([0-9A-F]+) -- Is only for TeamId: (\d+) -- MESSAGE: (.*)"
)
MODERATION_PATTERN = re.compile(r"\{.*\}", re.DOTALL)
STARTING_LOG_PATTERN = re.compile(r"Starting Chat log")

def parse_filename(filename):
    """Extract match_id and session_id from the filename."""
    # Expected format: match_id_ChatLog_session_id.log
    parts = Path(filename).stem.split('_')
    if len(parts) >= 3 and parts[1] == "ChatLog":
        match_id = parts[0]
        session_id = "_".join(parts[2:])
        return match_id, session_id
    return None, None

def extract_moderation_data(json_str):
    """Extract moderation data from JSON string."""
    try:
        data = json.loads(json_str)
        
        # Initialize moderation results
        mod_result = "Unknown"
        scores = {
            "hate": 0.0,
            "selfharm": 0.0, 
            "sexual": 0.0,
            "violence": 0.0
        }
        
        # Extract Azure moderation results from azureResults array
        if "azureResults" in data and data["azureResults"]:
            # Get the first result (or any result that corresponds to the current message)
            azure_result = data["azureResults"][0]
            
            if "resultType" in azure_result:
                mod_result = azure_result.get("resultType", "Unknown")
            
            # Extract category scores from azureCategories
            if "azureCategories" in azure_result:
                categories = azure_result["azureCategories"]
                
                for category_obj in categories:
                    category = category_obj.get("category", "").lower()
                    if category in scores:
                        scores[category] = float(category_obj.get("result", 0))
        
        return mod_result, scores
    except Exception as e:
        print(f"Error parsing moderation data: {str(e)}")
        return "Error", {"hate": 0.0, "selfharm": 0.0, "sexual": 0.0, "violence": 0.0}

def parse_chat_log(file_path):
    """Parse a single chat log file and extract message data."""
    match_id, session_id = parse_filename(file_path)
    if not match_id or not session_id:
        print(f"Warning: Could not parse IDs from filename: {file_path}")
        return []
    
    results = []
    line_index = 0
    messages = []
    json_content = None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Skip empty files
            if not content or len(content.strip()) <= 20:  # "Starting Chat log" + empty JSON
                return []
            
            # Extract chat messages
            for line in content.split('\n'):
                line = line.strip()
                
                # Skip the header line
                if STARTING_LOG_PATTERN.match(line):
                    continue
                
                # Parse chat message line
                chat_match = CHAT_MESSAGE_PATTERN.match(line)
                if chat_match:
                    sender_id, team_id, message = chat_match.groups()
                    messages.append({
                        'sender_id': sender_id,
                        'team_id': team_id,
                        'message': message,
                        'line_index': line_index
                    })
                    line_index += 1
            
            # Extract JSON data (containing moderation results)
            json_match = MODERATION_PATTERN.search(content)
            if json_match:
                try:
                    json_content = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    print(f"Warning: Failed to parse JSON in {file_path}")
            
            # Match messages with moderation results if available
            if json_content and 'azureResults' in json_content and messages:
                azure_results = json_content['azureResults']
                
                # If we have the same number of messages and results, match them directly
                if len(azure_results) == len(messages):
                    for i, (message_data, azure_result) in enumerate(zip(messages, azure_results)):
                        mod_result = azure_result.get('resultType', 'Unknown')
                        
                        # Extract scores
                        scores = {
                            'hate': 0.0,
                            'selfharm': 0.0,
                            'sexual': 0.0,
                            'violence': 0.0
                        }
                        
                        for category_obj in azure_result.get('azureCategories', []):
                            category = category_obj.get('category', '').lower()
                            if category in scores:
                                scores[category] = float(category_obj.get('result', 0))
                        
                        # Create complete message record
                        results.append({
                            'match_id': match_id,
                            'session_id': session_id,
                            'sender_id': message_data['sender_id'],
                            'team_id': message_data['team_id'],
                            'message': message_data['message'],
                            'mod_result': mod_result,
                            'hate_score': scores['hate'],
                            'selfharm_score': scores['selfharm'],
                            'sexual_score': scores['sexual'],
                            'violence_score': scores['violence'],
                            'line_index': message_data['line_index']
                        })
                else:
                    # If counts don't match, just use basic message data
                    for message_data in messages:
                        results.append({
                            'match_id': match_id,
                            'session_id': session_id,
                            'sender_id': message_data['sender_id'],
                            'team_id': message_data['team_id'],
                            'message': message_data['message'],
                            'mod_result': 'Unknown',
                            'hate_score': 0.0,
                            'selfharm_score': 0.0,
                            'sexual_score': 0.0,
                            'violence_score': 0.0,
                            'line_index': message_data['line_index']
                        })
            else:
                # No JSON moderation data found, just use basic message data
                for message_data in messages:
                    results.append({
                        'match_id': match_id,
                        'session_id': session_id,
                        'sender_id': message_data['sender_id'],
                        'team_id': message_data['team_id'],
                        'message': message_data['message'],
                        'mod_result': 'Unknown',
                        'hate_score': 0.0,
                        'selfharm_score': 0.0,
                        'sexual_score': 0.0,
                        'violence_score': 0.0,
                        'line_index': message_data['line_index']
                    })
    
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
    
    return results

def process_directory(input_dir, output_file, max_workers=4):
    """Process all chat log files in a directory and write to CSV."""
    input_path = Path(input_dir)
    
    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Input directory {input_dir} does not exist or is not a directory")
        return False
    
    # Get list of chat log files
    chat_log_files = list(input_path.glob("*ChatLog*.log"))
    
    if not chat_log_files:
        print(f"No chat log files found in {input_dir}")
        return False
    
    print(f"Found {len(chat_log_files)} chat log files to process")
    
    # Process files with a progress bar
    all_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for result in tqdm(
            executor.map(parse_chat_log, chat_log_files),
            total=len(chat_log_files),
            desc="Processing chat logs"
        ):
            all_results.extend(result)
    
    if not all_results:
        print("No chat messages found in the log files")
        return False
    
    # Define fieldnames
    fieldnames = [
        'match_id', 'session_id', 'sender_id', 'team_id', 'message', 
        'mod_result', 'hate_score', 'selfharm_score', 'sexual_score', 'violence_score',
        'line_index'
    ]
    
    # Write results to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for message_data in all_results:
            writer.writerow(message_data)
    
    print(f"Successfully processed {len(chat_log_files)} files with {len(all_results)} messages")
    print(f"CSV output written to {output_file}")
    
    # Generate moderation result summary
    mod_results = {}
    for message in all_results:
        result = message['mod_result']
        if result not in mod_results:
            mod_results[result] = 0
        mod_results[result] += 1
    
    print("\nModeration result summary:")
    for result, count in sorted(mod_results.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(all_results)) * 100
        print(f"  {result}: {count} ({percentage:.1f}%)")
    
    return True

def main():
    """Main function to process command line arguments."""
    parser = argparse.ArgumentParser(description="Convert chat logs to CSV format")
    parser.add_argument(
        "--input-dir", "-i", 
        default="chat_logs", 
        help="Directory containing chat log files (default: chat_logs)"
    )
    parser.add_argument(
        "--output-file", "-o", 
        default="chat_logs.csv", 
        help="Output CSV file path (default: chat_logs.csv)"
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
        chat_log_files = list(input_path.glob("*ChatLog*.log"))
        
        if len(chat_log_files) > 5:
            sample_dir = "chat_logs_sample"
            os.makedirs(sample_dir, exist_ok=True)
            
            print(f"Creating sample of 5 files in {sample_dir}")
            for i, file_path in enumerate(chat_log_files[:5]):
                with open(file_path, 'r', encoding='utf-8') as src:
                    with open(f"{sample_dir}/{file_path.name}", 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            args.input_dir = sample_dir
    
    # Process the directory
    process_directory(args.input_dir, args.output_file, args.max_workers)

if __name__ == "__main__":
    main() 
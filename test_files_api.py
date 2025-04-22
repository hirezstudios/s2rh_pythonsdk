#!/usr/bin/env python3
"""
Test script for the Files API SDK extension.

This script tests the functionality of the Files API methods by:
1. Getting an access token
2. Checking if a match exists
3. Listing files for the match
4. Downloading files for the match

Usage:
    python test_files_api.py --match-id <match_id>
"""

import os
import sys
import argparse
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import the SDK
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the SDK components
from smite2_rh_sdk import Smite2RallyHereSDK
from files_api import FileTypeConstants, FileNotFoundException, MatchNotFoundException
from typing import List, Dict, Any

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test the RallyHere Files API')
    parser.add_argument('--match-id', required=True, help='Match ID to test')
    parser.add_argument('--session-id', help='Session ID for the match (optional)')
    parser.add_argument('--output-dir', default='test_output', help='Directory to store output files')
    return parser.parse_args()

def print_separator(title):
    """Print a separator with a title."""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")

def preview_file_content(file_path: str, max_lines: int = 10) -> str:
    """
    Preview the content of a text file.
    
    Args:
        file_path: Path to the file.
        max_lines: Maximum number of lines to preview.
        
    Returns:
        A string containing the first max_lines lines of the file.
    """
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
        
    try:
        preview_lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                preview_lines.append(line.rstrip())
        
        return "\n".join(preview_lines)
    except UnicodeDecodeError:
        return f"[Binary content or non-UTF-8 encoding in {file_path}]"

def main():
    """Main function."""
    args = parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize SDK
    sdk = Smite2RallyHereSDK()
    
    print_separator("GETTING ACCESS TOKEN")
    token = sdk._get_env_access_token()
    print(f"Access token acquired successfully: {token[:10]}...{token[-10:]}")
    
    print_separator("CHECKING IF MATCH EXISTS")
    try:
        match_exists = sdk.files.check_match_exists(args.match_id, token)
        print(f"Match exists: {match_exists}")
        
        if not match_exists:
            print("Match does not exist. Exiting.")
            return
    except Exception as e:
        print(f"Error checking if match exists: {e}")
        return
    
    print_separator("LISTING MATCH FILES")
    try:
        files = sdk.files.list_match_files(args.match_id, token)
        print(f"Files found: {len(files)}")
        
        for i, file_info in enumerate(files, 1):
            print(f"\nFile {i}:")
            for key, value in file_info.items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error listing match files: {e}")
    
    if args.session_id:
        print_separator(f"DOWNLOADING COMBAT LOG FOR SESSION {args.session_id}")
        try:
            output_path = sdk.files.download_combat_log(
                args.match_id, 
                args.session_id, 
                args.output_dir, 
                token
            )
            if output_path:
                print(f"Combat log downloaded successfully to: {output_path}")
                
                # Preview file content
                print("\nFile preview:")
                print(preview_file_content(output_path, 10))
            else:
                print("Failed to download combat log.")
        except Exception as e:
            print(f"Error downloading combat log: {e}")
    
    print_separator("DOWNLOADING ALL MATCH FILES")
    try:
        downloaded_files = sdk.files.download_all_match_files(
            args.match_id, 
            args.output_dir, 
            token
        )
        print(f"Downloaded {len(downloaded_files)} files:")
        
        for file_path in downloaded_files:
            file_name = os.path.basename(file_path)
            print(f"  {file_name}: {file_path}")
            
            # Preview text files
            if file_name.endswith('.log') or file_name.endswith('.txt') or file_name.endswith('.json'):
                try:
                    print(f"\nPreview of {file_name}:")
                    print(preview_file_content(file_path, 5))
                    print("...")
                except Exception as e:
                    print(f"  Error previewing file: {e}")
    except Exception as e:
        print(f"Error downloading match files: {e}")

if __name__ == "__main__":
    main() 
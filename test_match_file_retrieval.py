#!/usr/bin/env python3
"""
Test script to retrieve files for a specific match using the Files API.
"""

import os
import sys
import argparse
import textwrap
from typing import List, Dict, Any, Optional
import time
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import SDK
from s2rh_pythonsdk import Smite2RallyHereSDK  # Adjust if import path is different
from files_api import Smite2RallyHereFilesAPI, FileTypeConstants, FileNotFoundException, MatchNotFoundException, DownloadError

# Default match details for testing
DEFAULT_MATCH_ID = "28257fd8-88c1-40ed-9bad-4151bcc601a5"
DEFAULT_SESSION_ID = "60ce5622-4b06-44f3-8663-0030d6c23d11"
DEFAULT_INSTANCE_ID = "5e928b29-ffc2-4354-b930-dd09993189f6"
DEFAULT_OUTPUT_DIR = "test_match_files"

# Default file details for testing
DEFAULT_CHAT_LOG_FILENAME = f"ChatLog_{DEFAULT_SESSION_ID}.log"
DEFAULT_COMBAT_LOG_FILENAME = f"CombatLog_{DEFAULT_SESSION_ID}.log"

def preview_file(file_path: str, max_lines: int = 5) -> None:
    """
    Preview the contents of a text file.
    
    Args:
        file_path: Path to the file.
        max_lines: Maximum number of lines to show.
    """
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
            
        # Only try to read text files
        if not file_path.endswith(('.log', '.txt', '.json')):
            print(f"Preview not available for {file_path} (not a text file)")
            return
            
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        if not lines:
            print(f"File is empty: {file_path}")
            return
            
        print(f"\nPreview of {file_path} ({min(max_lines, len(lines))} of {len(lines)} lines):")
        print("=" * 50)
        for i in range(min(max_lines, len(lines))):
            print(lines[i].rstrip())
        print("=" * 50)
        print()
    except Exception as e:
        print(f"Error previewing file {file_path}: {e}")

def list_match_files(sdk: Smite2RallyHereSDK, files_api: Smite2RallyHereFilesAPI, match_id: str) -> None:
    """
    List all files for a match.
    
    Args:
        sdk: The SDK instance.
        files_api: The Files API extension.
        match_id: The match ID.
    """
    token = sdk._get_env_access_token()
    
    # Get files from both 'file' and 'developer-file' types
    all_files = []
    
    try:
        print(f"Fetching files for match {match_id}")
        files = files_api.list_match_files(match_id, token, file_type="file")
        all_files.extend(files)
        print(f"Found {len(files)} regular files")
    except Exception as e:
        print(f"Error fetching regular files: {e}")
    
    try:
        dev_files = files_api.list_match_files(match_id, token, file_type="developer-file")
        all_files.extend(dev_files)
        print(f"Found {len(dev_files)} developer files")
    except Exception as e:
        print(f"Error fetching developer files: {e}")
    
    if not all_files:
        print("No files found for this match.")
        return
    
    print(f"\nTotal files found: {len(all_files)}")
    print("\nFile List:")
    print("=" * 80)
    print(f"{'Filename':<50} {'Size':<10} {'Type':<15} {'API Source':<10}")
    print("-" * 80)
    
    for file_info in all_files:
        name = file_info.get("name", "Unknown")
        size = file_info.get("size", 0)
        file_type = FileTypeConstants.identify_file_type(name) or "Unknown"
        api_type = file_info.get("api_type", "Unknown")
        
        print(f"{name:<50} {size:<10} {file_type:<15} {api_type:<10}")

def download_files_by_type(
    sdk: Smite2RallyHereSDK, 
    files_api: Smite2RallyHereFilesAPI, 
    match_id: str, 
    session_id: Optional[str],
    output_dir: str,
    file_type: str
) -> List[str]:
    """
    Download files of a specific type for a match.
    
    Args:
        sdk: The SDK instance.
        files_api: The Files API extension.
        match_id: The match ID.
        session_id: The session ID.
        output_dir: The output directory.
        file_type: The file type to download.
        
    Returns:
        Paths to the downloaded files.
    """
    try:
        print(f"\nDownloading {file_type} files...")
        files = files_api.download_match_file_by_type(
            match_id=match_id,
            file_type=file_type,
            session_id=session_id,
            output_dir=output_dir
        )
        
        print(f"Successfully downloaded {len(files)} {file_type} files")
        return files
    except FileNotFoundException:
        print(f"No {file_type} files found for match {match_id}")
        return []
    except Exception as e:
        print(f"Error downloading {file_type} files: {e}")
        return []

def download_all_match_files(
    sdk: Smite2RallyHereSDK, 
    files_api: Smite2RallyHereFilesAPI, 
    match_id: str, 
    output_dir: str
) -> List[str]:
    """
    Download all files for a match.
    
    Args:
        sdk: The SDK instance.
        files_api: The Files API extension.
        match_id: The match ID.
        output_dir: The output directory.
        
    Returns:
        Paths to the downloaded files.
    """
    try:
        print(f"\nDownloading all files for match {match_id}...")
        files = files_api.download_all_match_files(
            match_id=match_id,
            output_dir=output_dir
        )
        
        print(f"Successfully downloaded {len(files)} files")
        return files
    except Exception as e:
        print(f"Error downloading files: {e}")
        return []

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Test script to retrieve files for a specific match using the Files API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(f"""
        Examples:
          # List files for the default match
          python {os.path.basename(__file__)} --list
          
          # Download all files for the default match
          python {os.path.basename(__file__)} --all
          
          # Download only combat logs for the default match
          python {os.path.basename(__file__)} --type COMBAT_LOG
          
          # Download all files for a specific match
          python {os.path.basename(__file__)} --match-id YOUR_MATCH_ID --all
        """)
    )
    
    # Add arguments
    parser.add_argument("--match-id", default=DEFAULT_MATCH_ID, help="Match ID")
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID, help="Session ID")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--list", action="store_true", help="List all files for the match")
    parser.add_argument("--all", action="store_true", help="Download all files for the match")
    parser.add_argument("--type", choices=[
        "COMBAT_LOG", "CHAT_LOG", "CONSOLE_LOG", 
        "GAME_SESSION_SUMMARY", "MATCH_SUMMARY", "SERVER_METADATA"
    ], help="Download only files of this type")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Initialize SDK
    sdk = Smite2RallyHereSDK()
    
    # Initialize Files API extension
    files_api = Smite2RallyHereFilesAPI(sdk)
    
    # Get an access token
    token = sdk._get_env_access_token()
    
    try:
        # Check if match exists
        print(f"Checking if match {args.match_id} exists...")
        match_exists = files_api.check_match_exists(args.match_id, token)
        
        if not match_exists:
            print(f"Match {args.match_id} not found")
            return 1
            
        print(f"Match {args.match_id} exists")
        
        # List files if requested
        if args.list:
            list_match_files(sdk, files_api, args.match_id)
            
        # Download files by type if requested
        if args.type:
            files = download_files_by_type(
                sdk=sdk,
                files_api=files_api,
                match_id=args.match_id,
                session_id=args.session_id,
                output_dir=args.output_dir,
                file_type=args.type
            )
            
            # Preview downloaded files
            for file_path in files:
                preview_file(file_path)
                
        # Download all files if requested
        if args.all:
            files = download_all_match_files(
                sdk=sdk,
                files_api=files_api,
                match_id=args.match_id,
                output_dir=args.output_dir
            )
            
            # Preview downloaded text files
            for file_path in files:
                preview_file(file_path)
                
        # Download specific logs if no other download option was specified
        if not (args.all or args.type):
            try:
                # Download combat log
                print(f"\nDownloading combat log...")
                combat_log_path = files_api.download_combat_log(
                    match_id=args.match_id,
                    session_id=args.session_id,
                    output_dir=args.output_dir,
                    token=token
                )
                
                print(f"Combat log downloaded: {combat_log_path}")
                preview_file(combat_log_path)
                
            except Exception as e:
                print(f"Error downloading combat log: {e}")
                
            try:
                # Download chat log
                print(f"\nDownloading chat log...")
                chat_log_path = files_api.download_chat_log(
                    match_id=args.match_id,
                    session_id=args.session_id,
                    output_dir=args.output_dir,
                    token=token
                )
                
                print(f"Chat log downloaded: {chat_log_path}")
                preview_file(chat_log_path)
                
            except Exception as e:
                print(f"Error downloading chat log: {e}")
                
        print("\nScript execution completed successfully")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
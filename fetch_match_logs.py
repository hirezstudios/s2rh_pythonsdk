#!/usr/bin/env python3
"""
Script to fetch chat logs for matches matching specific criteria.
This script uses the Smite2RallyHereSDK with the Files API extension.

Usage:
  python fetch_match_logs.py [options]

Options:
  --start-date DATE    Start date in YYYY-MM-DD format (default: yesterday)
  --end-date DATE      End date in YYYY-MM-DD format (default: today)
  --region-id ID       Filter by region ID (e.g., "1", "2")
  --game-mode MODE     Filter by game mode (e.g., "Conquest", "Arena")
  --min-duration SECS  Minimum match duration in seconds
  --max-duration SECS  Maximum match duration in seconds
  --matches COUNT      Maximum matches to process (default: 10, use 0 for no limit)
  --output-dir DIR     Directory to save files (default: chat_logs)
  --match-id ID        Specific match ID to retrieve (overrides filters)
  --batch-size SIZE    Number of matches to request per API call (default: 100)
  --file-types TYPES   Comma-separated list of file types to download (default: CHAT_LOG)
                       Options: CHAT_LOG, COMBAT_LOG, CONSOLE_LOG, etc.
  --preview            Preview the contents of downloaded files
  --fallback-all       Download all available files if no files of the specified types are found
  --concurrent INT     Maximum number of concurrent downloads (default: 3)

Note:
  This script saves all files in a single directory (by default 'chat_logs'), 
  using a unique naming pattern: "{match_id}_{original_filename}".
"""

import os
import sys
import argparse
import datetime
import time
from typing import List, Dict, Any, Optional, Set
from dotenv import load_dotenv, find_dotenv

# Import SDK
from smite2_rh_sdk import Smite2RallyHereSDK
from files_api import Smite2RallyHereFilesAPI, FileTypeConstants, MatchNotFoundException, FileNotFoundException

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Fetch logs for matches meeting specific criteria")
    
    # Date range options
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    
    parser.add_argument("--start-date", type=str, default=yesterday.strftime("%Y-%m-%d"),
                       help=f"Start date in YYYY-MM-DD format (default: {yesterday.strftime('%Y-%m-%d')})")
    parser.add_argument("--end-date", type=str, default=now.strftime("%Y-%m-%d"),
                       help=f"End date in YYYY-MM-DD format (default: {now.strftime('%Y-%m-%d')})")
    
    # Filter options
    parser.add_argument("--region-id", type=str,
                       help="Filter by region ID (e.g., '1', '2')")
    parser.add_argument("--game-mode", type=str,
                       help="Filter by game mode (e.g., 'Conquest', 'Arena')")
    parser.add_argument("--min-duration", type=int,
                       help="Minimum match duration in seconds")
    parser.add_argument("--max-duration", type=int,
                       help="Maximum match duration in seconds")
    
    # Other options
    parser.add_argument("--matches", type=int, default=10,
                       help="Maximum matches to process (default: 10, use 0 for no limit)")
    parser.add_argument("--output-dir", type=str, default="chat_logs",
                       help="Directory to save files (default: chat_logs)")
    parser.add_argument("--match-id", type=str,
                       help="Specific match ID to retrieve (overrides filters)")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Number of matches to request per API call (default: 100)")
    parser.add_argument("--file-types", type=str, default="CHAT_LOG",
                        help="Comma-separated list of file types to download (default: CHAT_LOG)")
    parser.add_argument("--preview", action="store_true",
                        help="Preview downloaded files")
    parser.add_argument("--fallback-all", action="store_true",
                        help="Download all available files if no files of the specified types are found")
    parser.add_argument("--concurrent", type=int, default=3,
                        help="Maximum number of concurrent downloads (default: 3)")
    
    return parser.parse_args()

def preview_file(file_path: str, max_lines: int = 10) -> None:
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

def report_download_progress(filename: str, downloaded: int, total: int) -> None:
    """
    Report download progress for a file.
    
    Args:
        filename: Name of the file being downloaded.
        downloaded: Number of bytes downloaded.
        total: Total size of the file in bytes.
    """
    if total > 0:
        percent = (downloaded / total) * 100
        print(f"\rDownloading {filename}: {downloaded}/{total} bytes ({percent:.1f}%)", end="")
    else:
        print(f"\rDownloading {filename}: {downloaded} bytes", end="")
    
    # Add newline when download is complete
    if downloaded == total:
        print()

def download_match_logs(files_api: Smite2RallyHereFilesAPI, match_id: str, 
                       output_dir: str, file_types: List[str], preview: bool = False,
                       fallback_all: bool = False, max_concurrent: int = 3) -> List[str]:
    """
    Download logs for a specific match.
    
    Args:
        files_api: The Files API extension.
        match_id: The match ID.
        output_dir: Directory to save files.
        file_types: List of file types to download.
        preview: Whether to preview downloaded files.
        fallback_all: Whether to download all available files if no files of the specified types are found.
        max_concurrent: Maximum number of concurrent downloads.
        
    Returns:
        List of paths to downloaded files.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    all_downloaded = []
    token = files_api.sdk._get_env_access_token()
    
    try:
        # List all files for the match from all endpoints
        all_files = files_api.list_all_match_files(match_id, token)
        
        # Group files by their types
        files_by_type = {}
        for file_info in all_files:
            filename = file_info.get("name", "")
            if not filename:
                continue
                
            file_type = FileTypeConstants.identify_file_type(filename)
            if file_type:
                if file_type not in files_by_type:
                    files_by_type[file_type] = []
                files_by_type[file_type].append(file_info)
        
        # Download files of specified types
        for file_type in file_types:
            if file_type in files_by_type and files_by_type[file_type]:
                type_files = files_by_type[file_type]
                print(f"Found {len(type_files)} {file_type} files for match {match_id}")
                
                # Download files using the enhanced batch download method
                downloaded = files_api.download_match_files(
                    match_id=match_id,
                    files=type_files,
                    output_dir=output_dir,
                    token=token,
                    filename_pattern="{match_id}_{filename}",
                    progress_callback=report_download_progress,
                    max_concurrent_downloads=max_concurrent
                )
                
                if downloaded:
                    all_downloaded.extend(downloaded)
                    print(f"Downloaded {len(downloaded)} {file_type} files for match {match_id}")
                else:
                    print(f"No {file_type} files could be downloaded for match {match_id}")
            else:
                print(f"No {file_type} files found for match {match_id}")
        
        # If no files of the specified types were found and fallback_all is True, download all files
        if not all_downloaded and fallback_all:
            print(f"No files of specified types found. Attempting to download all available files...")
            
            # Download all available files
            downloaded = files_api.download_match_files(
                match_id=match_id,
                files=all_files,
                output_dir=output_dir,
                token=token,
                filename_pattern="{match_id}_{filename}",
                progress_callback=report_download_progress,
                max_concurrent_downloads=max_concurrent
            )
            
            if downloaded:
                all_downloaded.extend(downloaded)
                print(f"Downloaded {len(downloaded)} files of various types for match {match_id}")
            else:
                print(f"No files found for match {match_id}")
                
        # Preview files if requested
        if preview and all_downloaded:
            for file_path in all_downloaded:
                preview_file(file_path)
                
        return all_downloaded
    
    except MatchNotFoundException:
        print(f"Match {match_id} not found")
        return []
    except Exception as e:
        print(f"Error downloading files for match {match_id}: {e}")
        return []

def main():
    """Main entry point for the script."""
    # Parse command-line arguments
    args = parse_args()
    
    # Set the default output directory to "chat_logs" if not specified
    if args.output_dir == "match_logs":  # If it's the old default
        args.output_dir = "chat_logs"
        
    # Find and load .env file
    env_file = find_dotenv()
    if env_file:
        print(f"Loading environment from: {env_file}")
        load_dotenv(env_file)
    else:
        print("No .env file found")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize SDK
    sdk = Smite2RallyHereSDK()
    
    # Initialize Files API extension
    files_api = Smite2RallyHereFilesAPI(sdk)
    
    # Parse file types
    file_types = [ft.strip() for ft in args.file_types.split(",")]
    
    if args.match_id:
        # If specific match ID provided, just get that match
        print(f"\nFetching logs for specific match: {args.match_id}")
        downloaded_files = download_match_logs(
            files_api=files_api,
            match_id=args.match_id,
            output_dir=args.output_dir,
            file_types=file_types,
            preview=args.preview,
            fallback_all=args.fallback_all,
            max_concurrent=args.concurrent
        )
        
        print(f"Downloaded {len(downloaded_files)} files to {os.path.abspath(args.output_dir)}")
        
    else:
        # Otherwise, get matches by time range and filter using the SDK method
        max_matches = args.matches
        if max_matches == 0:
            print(f"\nFetching ALL matches from {args.start_date} to {args.end_date} (no limit)")
        else:
            print(f"\nFetching up to {max_matches} matches from {args.start_date} to {args.end_date}")
            
        # Print filter criteria
        if args.region_id:
            print(f"Filtering by region ID: {args.region_id}")
        if args.game_mode:
            print(f"Filtering by game mode: {args.game_mode}")
        if args.min_duration:
            print(f"Filtering by minimum duration: {args.min_duration} seconds")
        if args.max_duration:
            print(f"Filtering by maximum duration: {args.max_duration} seconds")
            
        # Get matches using the SDK extension's get_filtered_matches method
        filtered_matches = files_api.get_filtered_matches(
            start_date=args.start_date,
            end_date=args.end_date,
            region_id=args.region_id,
            game_mode=args.game_mode,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            limit=max_matches,
            batch_size=args.batch_size
        )
        
        print(f"Found {len(filtered_matches)} matches matching the criteria")
        
        # Get logs for each filtered match
        logs_found = 0
        files_downloaded = 0
        total_matches = len(filtered_matches)
        
        for i, match in enumerate(filtered_matches, 1):
            match_id = match.get("match_id")
            print(f"\nProcessing match {i}/{total_matches}: {match_id}")
            
            if "duration_seconds" in match:
                duration = match.get("duration_seconds")
                print(f"Match duration: {duration} seconds ({duration//60}m {duration%60}s)")
            
            downloaded_files = download_match_logs(
                files_api=files_api,
                match_id=match_id,
                output_dir=args.output_dir,
                file_types=file_types,
                preview=(args.preview and i <= 3),  # Only preview first 3 matches
                fallback_all=args.fallback_all,
                max_concurrent=args.concurrent
            )
            
            if downloaded_files:
                logs_found += 1
                files_downloaded += len(downloaded_files)
            
            # Print progress for large jobs
            if i % 10 == 0 or i == total_matches:
                print(f"\nProgress: {i}/{total_matches} matches processed, "
                      f"{logs_found} matches with files, {files_downloaded} total files downloaded")
        
        print(f"\nSummary: Found files for {logs_found} out of {total_matches} filtered matches")
        print(f"Total files downloaded: {files_downloaded}")
        print(f"All logs saved to: {os.path.abspath(args.output_dir)} (without match-specific subdirectories)")

if __name__ == "__main__":
    main() 
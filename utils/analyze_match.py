#!/usr/bin/env python3
"""
Script to download, process, and analyze logs from a match.

This script combines three steps:
1. Download match files using the Files API
2. Process combat and chat logs to CSV format
3. Analyze the processed logs to generate visualizations and insights
"""

import os
import argparse
import subprocess
from pathlib import Path
import shutil
import sys

def run_command(command, description=None):
    """Run a command and handle errors."""
    if description:
        print(f"\n=== {description} ===")
    
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        print(f"Error message: {e.stderr}")
        return False

def download_match_files(match_id, session_id=None, instance_id=None, output_dir="match_files"):
    """Download all files for a match."""
    command = [
        sys.executable,
        "utils/test_match_file_retrieval.py",
        "--match-id", match_id,
        "--output-dir", output_dir
    ]
    
    if session_id:
        command.extend(["--session-id", session_id])
    
    if instance_id:
        command.extend(["--instance-id", instance_id])
    
    return run_command(command, "Downloading match files")

def process_combat_logs(input_dir, output_file="combat_logs.csv"):
    """Process combat logs to CSV format."""
    combat_logs_dir = os.path.join(input_dir, "combat_logs")
    
    # Create directory for combat logs if it doesn't exist
    os.makedirs(combat_logs_dir, exist_ok=True)
    
    # Move combat logs to dedicated directory
    for file in os.listdir(input_dir):
        if "CombatLog" in file and file.endswith(".log"):
            src = os.path.join(input_dir, file)
            dst = os.path.join(combat_logs_dir, file)
            shutil.copy2(src, dst)
    
    # Process combat logs
    command = [
        sys.executable,
        "utils/combat_log_to_csv.py",
        "--input-dir", combat_logs_dir,
        "--output-file", output_file
    ]
    
    return run_command(command, "Processing combat logs")

def process_chat_logs(input_dir, output_file="chat_logs.csv"):
    """Process chat logs to CSV format."""
    chat_logs_dir = os.path.join(input_dir, "chat_logs")
    
    # Create directory for chat logs if it doesn't exist
    os.makedirs(chat_logs_dir, exist_ok=True)
    
    # Move chat logs to dedicated directory
    for file in os.listdir(input_dir):
        if "ChatLog" in file and file.endswith(".log"):
            src = os.path.join(input_dir, file)
            dst = os.path.join(chat_logs_dir, file)
            shutil.copy2(src, dst)
    
    # Process chat logs
    command = [
        sys.executable,
        "utils/chat_log_to_csv.py",
        "--input-dir", chat_logs_dir,
        "--output-file", output_file
    ]
    
    return run_command(command, "Processing chat logs")

def analyze_logs(combat_csv, chat_csv, output_dir="analysis_results"):
    """Analyze processed logs."""
    command = [
        sys.executable,
        "utils/analyze_match_logs.py",
        "--combat-csv", combat_csv,
        "--chat-csv", chat_csv,
        "--output-dir", output_dir
    ]
    
    return run_command(command, "Analyzing logs")

def main():
    """Main function to process command line arguments and run analysis workflow."""
    parser = argparse.ArgumentParser(description="Download, process, and analyze match logs")
    parser.add_argument(
        "--match-id", "-m", 
        required=True,
        help="Match ID to analyze"
    )
    parser.add_argument(
        "--session-id", "-s", 
        help="Optional session ID"
    )
    parser.add_argument(
        "--instance-id", "-i", 
        help="Optional instance ID"
    )
    parser.add_argument(
        "--working-dir", "-w", 
        default="match_analysis",
        help="Working directory for the analysis (default: match_analysis)"
    )
    parser.add_argument(
        "--skip-download", 
        action="store_true",
        help="Skip downloading files and use existing files in working directory"
    )
    parser.add_argument(
        "--skip-processing", 
        action="store_true",
        help="Skip processing logs and use existing CSV files"
    )
    
    args = parser.parse_args()
    
    # Create working directory
    os.makedirs(args.working_dir, exist_ok=True)
    print(f"Working directory: {args.working_dir}")
    
    # Paths for files
    files_dir = os.path.join(args.working_dir, "files")
    combat_csv = os.path.join(args.working_dir, "combat_logs.csv")
    chat_csv = os.path.join(args.working_dir, "chat_logs.csv")
    analysis_dir = os.path.join(args.working_dir, "analysis")
    
    # Step 1: Download match files
    if not args.skip_download:
        os.makedirs(files_dir, exist_ok=True)
        if not download_match_files(args.match_id, args.session_id, args.instance_id, files_dir):
            print("Failed to download match files. Exiting.")
            return
    
    # Step 2: Process combat logs
    if not args.skip_processing:
        if not process_combat_logs(files_dir, combat_csv):
            print("Warning: Failed to process combat logs.")
    
    # Step 3: Process chat logs
    if not args.skip_processing:
        if not process_chat_logs(files_dir, chat_csv):
            print("Warning: Failed to process chat logs.")
    
    # Step 4: Analyze logs
    analyze_logs(combat_csv, chat_csv, analysis_dir)
    
    print(f"\nAnalysis workflow complete. Results are in: {analysis_dir}")
    print(f"To view the analysis summary, open: {os.path.join(analysis_dir, 'analysis_summary.txt')}")

if __name__ == "__main__":
    main() 
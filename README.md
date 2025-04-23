# Smite2 RallyHere SDK

A Python SDK for interacting with Smite 2 data through the RallyHere APIs. This SDK provides methods for accessing player data, match data, statistics, and match files.

## Features

- Player data retrieval (search by name, get player details, stats)
- Match data access (match details, timeline, stats)
- Match filtering and searching (by time range, player, game mode, etc.)
- Files API for accessing match logs and other files
  - Automatic endpoint selection for different file types
  - Concurrent downloads with progress reporting
  - Customizable file naming patterns
- Utilities for data transformation and filtering

## Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/your-username/s2rh_pythonsdk.git
cd s2rh_pythonsdk
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root directory with your RallyHere API credentials:

```
RH_BASE_URL=your_base_url
RH_OAUTH_URL=your_oauth_url
RH_CLIENT_ID=your_client_id
RH_CLIENT_SECRET=your_client_secret
```

## Usage Examples

### Basic SDK Usage

```python
from smite2_rh_sdk import Smite2RallyHereSDK
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the SDK
sdk = Smite2RallyHereSDK()

# Get player ID by name
player_id = sdk.rh_fetch_player_id_by_name("PlayerName")

# Get player data
player_data = sdk.rh_fetch_player_data(player_id)

# Get player matches
matches = sdk.rh_fetch_player_matches(player_id, limit=10)

# Get match details
match_id = matches[0]["match_id"]
match_details = sdk.rh_fetch_match_details(match_id)
```

### Using the Files API

The Files API extension allows you to retrieve and download files associated with Smite 2 matches, such as combat logs, chat logs, and other game data.

```python
from smite2_rh_sdk import Smite2RallyHereSDK
from files_api import Smite2RallyHereFilesAPI, FileTypeConstants
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the SDK and Files API
sdk = Smite2RallyHereSDK()
files_api = Smite2RallyHereFilesAPI(sdk)

# Define match and output directory
match_id = "28257fd8-88c1-40ed-9bad-4151bcc601a5"
output_dir = "match_files"
os.makedirs(output_dir, exist_ok=True)

# Check if match exists
if files_api.check_match_exists(match_id):
    # List all files for the match from all endpoints
    all_files = files_api.list_all_match_files(match_id)
    print(f"Found {len(all_files)} files for match {match_id}")
    
    # Progress callback function
    def report_progress(filename, downloaded, total):
        if total > 0:
            percent = (downloaded / total) * 100
            print(f"\rDownloading {filename}: {percent:.1f}% complete", end="")
        if downloaded == total:
            print()  # Add newline when complete
    
    # Download combat logs with progress reporting
    combat_logs = files_api.download_match_file_by_type(
        match_id=match_id,
        file_type=FileTypeConstants.COMBAT_LOG,
        output_dir=output_dir,
        filename_pattern="{match_id}_{filename}",
        progress_callback=report_progress
    )
    print(f"Downloaded {len(combat_logs)} combat logs")
    
    # Download all files with concurrent downloads
    all_files = files_api.download_all_match_files(
        match_id=match_id,
        output_dir=output_dir,
        filename_pattern="{match_id}_{filename}",
        progress_callback=report_progress
    )
    print(f"Downloaded {len(all_files)} files to {output_dir}")
    
    # Get filtered matches
    matches = files_api.get_filtered_matches(
        start_date="2025-04-20",
        end_date="2025-04-21",
        region_id="1",
        game_mode="Conquest",
        min_duration=600,
        limit=100
    )
    print(f"Found {len(matches)} matches matching criteria")
```

## Files API Documentation

The Files API extension provides methods for working with match files:

### Class: `FileTypeConstants`

Constants for file types supported by the Files API.

- File Types:
  - `COMBAT_LOG`: Combat log files
  - `CHAT_LOG`: Chat log files
  - `CONSOLE_LOG`: Console log files
  - `GAME_SESSION_SUMMARY`: Game session summary files
  - `MATCH_SUMMARY`: Match summary files
  - `SERVER_METADATA`: Server metadata files

### Class: `Smite2RallyHereFilesAPI`

Main class for interacting with match files.

#### Key Methods:

- **Match Files:**
  - `check_match_exists(match_id, token=None)`: Check if a match exists
  - `list_match_files(match_id, token=None, file_type="file")`: List files for a match from specific endpoint
  - `list_all_match_files(match_id, token=None)`: List files from all available endpoints
  - `get_file_metadata(match_id, filename, token=None)`: Get metadata for a specific file

- **File Downloads:**
  - `download_match_file(match_id, filename, output_path=None, token=None)`: Download a specific file
  - `download_match_files(match_id, files, output_dir, token=None, filename_pattern=None, progress_callback=None, max_concurrent_downloads=3)`: Download multiple files concurrently
  - `download_all_match_files(match_id, output_dir, token=None, file_types=None, filename_pattern=None)`: Download all files for a match
  - `download_match_file_by_type(match_id, file_type, output_dir=None, session_id=None, token=None, filename_pattern=None)`: Download files of a specific type

- **Log Specific Methods:**
  - `download_combat_log(match_id, session_id=None, output_dir=None, token=None)`: Download combat log
  - `download_chat_log(match_id, session_id=None, output_dir=None, token=None)`: Download chat log

- **Match Filtering:**
  - `get_filtered_matches(start_date, end_date, region_id=None, game_mode=None, min_duration=None, max_duration=None, limit=10, batch_size=100)`: Get matches filtered by various criteria

### Exceptions:

- `FileNotFoundException`: Raised when a file is not found
- `MatchNotFoundException`: Raised when a match is not found
- `DownloadError`: Raised when a file download fails

## Advanced Usage

See the utility scripts in the repository for more advanced usage examples:

- `test_files_api.py`: Basic usage of the Files API
- `test_match_file_retrieval.py`: Command-line tool for retrieving match files
- `fetch_match_logs.py`: Utility for batch retrieval of match logs with filtering options

### Fetch Match Logs Utility

The `fetch_match_logs.py` script provides a powerful way to fetch logs from multiple matches based on filtering criteria:

```bash
python fetch_match_logs.py --min-duration 600 --region-id 1 --game-mode Conquest --matches 100 --start-date 2025-04-20 --end-date 2025-04-21 --file-types CHAT_LOG,COMBAT_LOG --concurrent 5 --preview
```

#### Options:
- `--start-date DATE`: Start date in YYYY-MM-DD format (default: yesterday)
- `--end-date DATE`: End date in YYYY-MM-DD format (default: today)
- `--region-id ID`: Filter by region ID (e.g., "1", "2")
- `--game-mode MODE`: Filter by game mode (e.g., "Conquest", "Arena")
- `--min-duration SECS`: Minimum match duration in seconds
- `--max-duration SECS`: Maximum match duration in seconds
- `--matches COUNT`: Maximum matches to process (default: 10, use 0 for no limit)
- `--output-dir DIR`: Directory to save files (default: chat_logs)
- `--match-id ID`: Specific match ID to retrieve (overrides filters)
- `--batch-size SIZE`: Number of matches per API call (default: 100)
- `--file-types TYPES`: Comma-separated list of file types (default: CHAT_LOG)
- `--preview`: Preview downloaded files
- `--fallback-all`: Download all available files if specified types not found
- `--concurrent INT`: Maximum number of concurrent downloads (default: 3)

#### Output Structure:
Files are saved in a single directory, with filenames that include the match ID:
```
chat_logs/
  ├── match_id_1_ChatLog_session_id.log
  ├── match_id_1_CombatLog_session_id.log
  ├── match_id_2_ChatLog_session_id.log
  └── ...
```

## License

[MIT License](LICENSE)


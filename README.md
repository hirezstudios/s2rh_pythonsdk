# Smite2 RallyHere SDK

A Python SDK for interacting with Smite 2 data through the RallyHere APIs. This SDK provides methods for accessing player data, match data, statistics, and match files.

## Features

- Player data retrieval (search by name, get player details, stats)
- Match data access (match details, timeline, stats)
- Match filtering and searching (by time range, player, game mode, etc.)
- Files API for accessing match logs and other files
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
from files_api import FileTypeConstants
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the SDK
sdk = Smite2RallyHereSDK()

# Define match and output directory
match_id = "28257fd8-88c1-40ed-9bad-4151bcc601a5"
output_dir = "match_files"
os.makedirs(output_dir, exist_ok=True)

# Check if match exists
if sdk.files.check_match_exists(match_id):
    # List all files for the match
    match_files = sdk.files.list_match_files(match_id)
    print(f"Found {len(match_files)} files for match {match_id}")
    
    # Download combat log
    try:
        combat_log_path = sdk.files.download_combat_log(match_id, output_dir=output_dir)
        print(f"Combat log downloaded to: {combat_log_path}")
    except Exception as e:
        print(f"Error downloading combat log: {str(e)}")
    
    # Download chat log
    try:
        chat_log_path = sdk.files.download_chat_log(match_id, output_dir=output_dir)
        print(f"Chat log downloaded to: {chat_log_path}")
    except Exception as e:
        print(f"Error downloading chat log: {str(e)}")
    
    # Download all match files
    all_files = sdk.files.download_all_match_files(match_id, output_dir)
    print(f"Downloaded {len(all_files)} files to {output_dir}")
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

#### Methods:

- `check_match_exists(match_id, token=None)`: Check if a match exists
- `list_match_files(match_id, token=None)`: List all files for a match
- `get_file_metadata(match_id, filename, token=None)`: Get metadata for a specific file
- `download_match_file(match_id, filename, output_path=None, token=None)`: Download a specific file
- `download_all_match_files(match_id, output_dir, token=None, file_types=None)`: Download all files for a match
- `download_combat_log(match_id, session_id=None, output_dir=None, token=None)`: Download combat log
- `download_chat_log(match_id, session_id=None, output_dir=None, token=None)`: Download chat log
- `filter_match_files_by_type(match_id, file_type, token=None)`: Filter match files by type
- `filter_match_files_by_session(match_id, session_id, token=None)`: Filter match files by session ID
- `download_match_file_by_type(match_id, file_type, session_id=None, output_dir=None, token=None)`: Download files of a specific type

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
python fetch_match_logs.py --min-duration 600 --region-id 1 --game-mode Conquest --matches 100 --start-date 2025-04-20 --end-date 2025-04-21
```

#### Options:
- `--start-date DATE`: Start date in YYYY-MM-DD format (default: yesterday)
- `--end-date DATE`: End date in YYYY-MM-DD format (default: today)
- `--region-id ID`: Filter by region ID (e.g., "1", "2")
- `--game-mode MODE`: Filter by game mode (e.g., "Conquest", "Arena")
- `--min-duration SECS`: Minimum match duration in seconds
- `--max-duration SECS`: Maximum match duration in seconds
- `--matches COUNT`: Maximum matches to process (default: 10, use 0 for no limit)
- `--output-dir DIR`: Directory to save files (default: match_logs)
- `--match-id ID`: Specific match ID to retrieve (overrides filters)
- `--batch-size SIZE`: Number of matches per API call (default: 100)
- `--file-types TYPES`: Comma-separated list of file types (default: CHAT_LOG)
- `--preview`: Preview downloaded files
- `--fallback-all`: Download all available files if specified types not found

#### Output Structure:
Files are organized by match ID in the output directory:
```
match_logs/
  ├── match_id_1/
  │   ├── ChatLog_session_id.log
  │   └── CombatLog_session_id.log
  ├── match_id_2/
  │   └── ...
```

## License

[MIT License](LICENSE)


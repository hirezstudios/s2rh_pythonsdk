# RallyHere Files API Exploration

This README documents the findings from exploring the RallyHere Files API for match data retrieval.

## Overview

The RallyHere Files API allows retrieving files associated with matches, such as combat logs, chat logs, and other match-related data files. This functionality can be useful for post-match analysis and data processing.

## API Exploration Results

From our initial exploration, we discovered:

1. The API endpoints generally follow this pattern:
   ```
   GET /file/v1/:file_type/:entity_type/:entity_id[/files]
   ```
   
   Where:
   - `file_type` is one of: `file` or `developer-file`
   - `entity_type` is one of: `match` or `unknown`
   - `entity_id` is the match ID (UUID format)

2. Required permissions:
   - Most endpoints require permissions like `file:read` or `file:*`
   - The directory info endpoint requires `file:read:stats` or `file:*`

3. Common errors:
   - `entity_not_found`: The match ID doesn't exist or there are no files for this match
   - `insufficient_permissions`: The token doesn't have the required permissions

## Usage of Exploration Script

The `explore_match_files.py` script is designed to help discover and test the Files API. It allows:

1. Checking if a match exists
2. Testing various file API endpoints
3. Attempting to access common file types (e.g., combat_log.txt, match_summary.json)

### Requirements

- A valid RallyHere Environment API token with appropriate permissions
- A valid match ID that exists in the system

### Command Line Arguments

```
python explore_match_files.py [--match-id MATCH_ID] [--file-type {file,developer-file}] [--entity-type ENTITY_TYPE]
```

Options:
- `--match-id`: A valid match ID (UUID format)
- `--file-type`: Type of file (default: file)
- `--entity-type`: Type of entity (default: match)

Example:
```
python explore_match_files.py --match-id 123e4567-e89b-12d3-a456-426614174000
```

## SDK Integration

The SDK now includes comprehensive Files API functionality:

### Base Methods

1. **rh_check_match_exists(match_id, token)** - Verifies if a match exists
2. **rh_list_match_files(match_id, token, file_type="file")** - Lists available files for a match
3. **rh_download_match_file(match_id, file_name, token, output_path=None, file_type="file")** - Downloads a specific file
4. **rh_get_entity_directory_info(token, file_type="file", entity_type="match")** - Gets information about the entity directory

### Convenience Methods

1. **S2_get_match_logs(match_id, output_dir=None, file_types=None)** - Downloads all log files for a match
2. **S2_get_match_combat_log(match_id, output_dir=None, session_id=None)** - Downloads the combat log for a match
3. **S2_get_match_chat_log(match_id, session_id=None, output_dir=None)** - Downloads the chat log for a match
4. **S2_get_match_files_by_type(match_id, file_types="All", session_id=None, output_dir=None)** - Downloads files by type

### NEW: Match Filtering Capabilities

The SDK now includes the ability to filter matches by various criteria before retrieving their files:

**S2_get_filtered_match_files(token=None, start_time=None, end_time=None, limit=10, page_size=10, status="closed", region_id=None, map_name=None, game_mode=None, host_type=None, file_types="All", output_dir=None)**

This method allows:
- Fetching matches within a time range
- Filtering matches by:
  - `region_id` (e.g., "1", "2")
  - `map_name` (e.g., "L_MatchLobby_P", "L_CQ_F2P_P")
  - `game_mode` (e.g., containing "Conquest", "Arena", "Joust")
  - `host_type` (e.g., "dedicated")
- Downloading specified file types for matching matches

#### Example Usage:

```python
# Initialize FileApiMethods
file_api = FileApiMethods()
file_api.env_base_url = sdk.env_base_url
file_api._get_env_access_token = sdk._get_env_access_token

# Get chat and combat logs for recent Conquest matches in region 1
result = file_api.S2_get_filtered_match_files(
    start_time="2023-05-01T00:00:00Z",
    end_time="2023-05-02T00:00:00Z",
    limit=5,
    region_id="1",
    game_mode="Conquest",
    file_types=["ChatLog", "CombatLog"],
    output_dir="conquest_match_files"
)
```

## Example Scripts

1. **test_match_file_retrieval.py** - Demonstrates retrieving files for a specific match
2. **test_filtered_match_files.py** - Shows how to filter matches and download their files
3. **test_match_file_retrieval_enhanced.py** - Combines both approaches with command-line options

### Running the Example Scripts

```bash
# For specific match retrieval:
python test_match_file_retrieval.py

# For filtered match retrieval:
python test_filtered_match_files.py --region-id 1 --game-mode Conquest --file-types ChatLog,CombatLog

# For the enhanced script with both capabilities:
python test_match_file_retrieval_enhanced.py --mode specific
python test_match_file_retrieval_enhanced.py --mode filtered --region-id 1 --game-mode Arena
```

## API Access Considerations

- Ensure the token has sufficient permissions (`file:read`, `file:*`, etc.)
- Match IDs must be valid and existing within the system
- Consider implementing caching mechanisms for frequently accessed files
- When filtering matches, be aware that fetching a large number of matches may be time-consuming 
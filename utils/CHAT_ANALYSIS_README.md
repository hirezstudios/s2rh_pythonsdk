# Chat Log Analysis Tools

## Overview
These utilities process and analyze chat logs from Smite 2 matches. They extract messages, moderation decisions, content scores, and other metadata, then convert them to CSV format for analysis and visualization.

## Scripts

### `chat_log_to_csv.py`
Extracts data from raw chat log files and generates a structured CSV file.

**Features:**
- Parses chat messages and sender information
- Extracts moderation decisions (Passed, Filtered, etc.)
- Captures content moderation scores (hate, self-harm, sexual, violence)
- Handles multi-threaded processing for faster conversion
- Supports sample mode for testing with a subset of files

**Usage:**
```bash
python utils/chat_log_to_csv.py --input-dir chat_logs --output-file chat_data.csv
```

**Parameters:**
- `--input-dir`, `-i`: Directory containing chat log files (default: chat_logs)
- `--output-file`, `-o`: Output CSV file path (default: chat_logs.csv)
- `--max-workers`, `-w`: Maximum number of worker threads (default: 4)
- `--sample`, `-s`: Process only 5 files as a sample

### `analyze_match_logs.py`
Generates visualizations and statistics from the processed chat log data.

**Features:**
- Analyzes message patterns
- Visualizes moderation result distribution
- Shows message length statistics
- Creates team-based message distribution
- Generates content score distribution charts

**Usage:**
```bash
python utils/analyze_match_logs.py --chat-csv chat_data.csv --output-dir chat_analysis
```

**Parameters:**
- `--chat-csv`, `-m`: Chat log CSV file path (default: chat_logs.csv)
- `--combat-csv`, `-c`: Combat log CSV file path (default: combat_logs.csv)
- `--output-dir`, `-o`: Output directory for analysis results (default: analysis_results)

## File Format
The chat log files follow this format:
```
Starting Chat log
Sender Id: [HEX_ID] -- Is only for TeamId: [TEAM_ID] -- MESSAGE: [MESSAGE_TEXT]
...additional messages...
{
    "azureResults": [
        {
            "message": "[MESSAGE_TEXT]",
            "concatenatedMessage": "...",
            "resultType": "[RESULT_TYPE]",
            "azureCategories": [
                {"category": "Hate", "result": [SCORE], "configuredThreshold": [THRESHOLD]},
                {"category": "SelfHarm", "result": [SCORE], "configuredThreshold": [THRESHOLD]},
                {"category": "Sexual", "result": [SCORE], "configuredThreshold": [THRESHOLD]},
                {"category": "Violence", "result": [SCORE], "configuredThreshold": [THRESHOLD]}
            ]
        },
        ...additional results...
    ]
}
```

## Output Data Format
The CSV output contains the following columns:
- `match_id`: Unique match identifier
- `session_id`: Session identifier
- `sender_id`: Hexadecimal ID of the message sender
- `team_id`: Team ID (1 or 2)
- `message`: Message content
- `mod_result`: Moderation result (Passed, FilteredByBlocklist, FilteredByAI, etc.)
- `hate_score`: Content score for hate speech (0-1)
- `selfharm_score`: Content score for self-harm content (0-1)
- `sexual_score`: Content score for sexual content (0-1)
- `violence_score`: Content score for violent content (0-1)
- `line_index`: Line position in the original file

## Analysis Output
The analysis generates:
1. `moderation_results.png`: Distribution of moderation decisions
2. `message_length_distribution.png`: Histogram of message lengths
3. `messages_by_team.png`: Distribution of messages between teams
4. `moderation_score_distributions.png`: Distribution of content scores across categories

## Requirements
- Python 3.6+
- pandas
- matplotlib
- seaborn
- tqdm 
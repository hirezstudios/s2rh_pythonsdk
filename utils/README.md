# Match Log Analysis Utilities

This directory contains utility scripts for working with Smite 2 match logs obtained through the RallyHere Files API. These tools allow you to download, process, and analyze match data.

## Scripts Overview

### Download Match Files
- **test_match_file_retrieval.py**: Downloads files for a specified match from the RallyHere Files API.

### Log Processing
- **combat_log_to_csv.py**: Processes combat log files into structured CSV format for analysis.
- **chat_log_to_csv.py**: Processes chat log files into structured CSV format for analysis, including chat message content and moderation data.

### Analysis
- **analyze_match_logs.py**: Analyzes processed log files and generates visualizations and statistics.

### Complete Workflow
- **analyze_match.py**: Combines all steps (downloading, processing, and analysis) into a single workflow.

## Quick Start

To analyze a match, simply run:

```bash
python utils/analyze_match.py --match-id MATCH_ID
```

Replace `MATCH_ID` with the actual match ID. You can optionally provide `--session-id` and `--instance-id` if known.

## Chat Log Analysis

For detailed chat log analysis, we provide specialized tools:

```bash
# Step 1: Convert chat logs to CSV
python utils/chat_log_to_csv.py --input-dir chat_logs --output-file chat_data.csv

# Step 2: Generate visualizations and statistics
python utils/analyze_match_logs.py --chat-csv chat_data.csv --output-dir chat_analysis
```

See [CHAT_ANALYSIS_README.md](CHAT_ANALYSIS_README.md) for detailed documentation on chat log analysis tools.

## Individual Script Usage

### Download Match Files

```bash
python utils/test_match_file_retrieval.py --match-id MATCH_ID [--session-id SESSION_ID] [--instance-id INSTANCE_ID] [--output-dir OUTPUT_DIR]
```

### Process Combat Logs

```bash
python utils/combat_log_to_csv.py --input-dir INPUT_DIR [--output-file OUTPUT_FILE] [--max-workers MAX_WORKERS] [--sample]
```

The `--sample` flag will process only 5 files as a test.

### Process Chat Logs

```bash
python utils/chat_log_to_csv.py --input-dir INPUT_DIR [--output-file OUTPUT_FILE] [--max-workers MAX_WORKERS] [--sample]
```

### Analyze Logs

```bash
python utils/analyze_match_logs.py [--combat-csv COMBAT_CSV] [--chat-csv CHAT_CSV] [--output-dir OUTPUT_DIR]
```

## Analysis Output

The analysis scripts generate:

1. CSV files containing structured log data
2. Visualizations of key metrics:
   - Event type distributions
   - Damage statistics
   - Chat message patterns
   - Moderation analysis
   - Time-based analysis
3. A summary text file with key findings

Results are saved to the specified output directory (default: `analysis_results`).

## Example Workflows

### Combat Log Analysis

```bash
# Download match files
python utils/test_match_file_retrieval.py --match-id 28257fd8-88c1-40ed-9bad-4151bcc601a5

# Process combat logs
python utils/combat_log_to_csv.py --input-dir test_match_files

# Analyze combat logs
python utils/analyze_match_logs.py --combat-csv combat_logs.csv
```

### Chat Log Analysis

```bash
# Process a directory containing chat logs
python utils/chat_log_to_csv.py --input-dir chat_logs --output-file chat_data.csv

# Analyze chat messages and moderation data
python utils/analyze_match_logs.py --chat-csv chat_data.csv --output-dir chat_analysis
```

### Combined Analysis

```bash
# Run the full analysis pipeline
python utils/analyze_match.py --match-id 28257fd8-88c1-40ed-9bad-4151bcc601a5
```

## Requirements

These scripts require:
- Python 3.6+
- pandas
- matplotlib
- seaborn
- tqdm
- numpy

Install requirements with:
```bash
pip install pandas matplotlib seaborn tqdm numpy
``` 
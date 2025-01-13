# Smite2RallyHereSDK

A unified Python SDK for interacting with RallyHere APIs (Environment and Developer endpoints), returning data in a SMITE 2–friendly format. This SDK aims to simplify and standardize how SMITE 2 developers integrate RallyHere functionality—offering methods to obtain access tokens, fetch match data, transform it, and call various developer- and environment-based endpoints (such as items, sandbox KVs, and player settings).

---

## Table of Contents
- [Overview](#overview)
- [Installation & Requirements](#installation--requirements)
- [Environment Variables](#environment-variables)
- [Initialization](#initialization)
- [Usage](#usage)  
  - [Obtaining Environment Credentials](#obtaining-environment-credentials)  
  - [Obtaining Developer Credentials](#obtaining-developer-credentials)  
- [New & Updated SDK Functions](#new--updated-sdk-functions)  
  - [Environment API Functions](#environment-api-functions)  
  - [Developer API Functions](#developer-api-functions)  
  - [SMITE 2 Transformations](#smite-2-transformations)  
  - [Recent Features & Examples](#recent-features--examples)
- [Example Test Harness (smite2_rh_sdk_examples.py)](#example-test-harness-smite2_rh_sdk_examplespy)
- [Testing and JSON Samples](#testing-and-json-samples)
- [Extensibility](#extensibility)
- [FAQ / Troubleshooting](#faq--troubleshooting)
- [License](#license)

---

## Overview

The Smite2RallyHereSDK class (in "smite2_rh_sdk.py") provides a suite of methods to:
1. Authenticate against both the RallyHere Environment and Developer APIs.  
2. Fetch and transform match data for players and instances.  
3. Retrieve presence, player info (ID from UUID or by platform display name), platform user data, items, sandbox KVs, and various settings.  
4. Optionally transform RallyHere data (like match records) into a "SMITE 2–friendly" format, offering consistency for your game logic.  
5. Access or manipulate new endpoints—such as fetching single or multiple player settings and retrieving linked portals in a single API call.

You can find example usage in "smite2_rh_sdk_examples.py," which demonstrates how to call each function and optionally saves the data (for reference) as JSON files in the "json_samples" directory.

---

## Installation & Requirements

1. Clone or download this repository.  
2. Ensure you have Python 3.7+ installed.  
3. Install dependencies (for example, via pip):
   ```bash
   pip install -r requirements.txt
   ```
   (If using a virtual environment, activate it first:  
   macOS/Linux: `source venv/bin/activate`  
   Windows: `.\venv\Scripts\activate`)

4. Make sure you have an account / credentials for RallyHere (both environment and developer if needed).

---

## Environment Variables

The SDK can be configured via environment variables if you do not provide them directly as constructor arguments.

Required for Environment API:  
- `CLIENT_ID`  
- `CLIENT_SECRET`  
- `RH_BASE_URL`  

Required for Developer API:  
- `RH_DEV_ACCOUNT_ID`  
- `RH_DEV_SECRET_KEY`  
- `RH_DEV_BASE_URL`  
- `RH_DEV_SANDBOX_ID` (when fetching items or sandbox KVs, if sandbox ID is not provided to the method)

You can also pass these values directly to the `Smite2RallyHereSDK` constructor (optional arguments).

---

## Initialization

```python
from smite2_rh_sdk import Smite2RallyHereSDK

# Rely on environment variables for credentials:
sdk = Smite2RallyHereSDK()

# Or pass explicit arguments:
sdk = Smite2RallyHereSDK(
    env_client_id="YOUR_ENV_CLIENT_ID",
    env_client_secret="YOUR_ENV_CLIENT_SECRET",
    env_base_url="https://your-env.rally-here.io",
    dev_client_id="YOUR_DEV_ACCOUNT_ID",
    dev_secret_key="YOUR_DEV_SECRET_KEY",
    dev_base_url="https://your-dev.rally-here.io"
)
```

---

## Usage

### Obtaining Environment Credentials

By default, the SDK attempts to get your environment credentials (`CLIENT_ID`, `CLIENT_SECRET`, `RH_BASE_URL`) from environment variables. If any are not found, you must provide them via the constructor arguments.  
Use `_get_env_access_token()` if you need the environment token directly, but typically the SDK manages tokens internally when calling environment endpoints.

### Obtaining Developer Credentials

Similarly, if you need to call developer endpoints, ensure your developer-related environment variables (e.g., `RH_DEV_ACCOUNT_ID`, `RH_DEV_SECRET_KEY`, `RH_DEV_BASE_URL`) are set or pass them into the constructor.  
Use `_get_dev_access_token()` if you need the developer token directly, but again, the SDK typically handles this automatically.

---

## New & Updated SDK Functions

This section highlights the newly added or updated environment API methods and the main developer API calls.

### Environment API Functions

1. **_get_env_access_token()**  
   - Internal usage to fetch an environment access token using client credentials.

2. **rh_fetch_player_id_from_player_uuid(player_uuid, token)**  
   - Retrieve a player’s integer ID from their UUID.

3. **rh_fetch_player_presence_by_UUID(player_uuid, token, use_cache=True, if_none_match=None)**  
   - Fetch presence data (status, message, platform, etc.) for a player by UUID.

4. **rh_fetch_matches_by_player_uuid(player_uuid, token, page_size=10, max_matches=100)**  
   - Retrieve raw match data for a player (in RallyHere’s native format).

5. **rh_fetch_player_stats(player_uuid, token)**  
   - Retrieve player stats for each match (in RallyHere’s native format).

6. **rh_fetch_matches_by_instance(instance_id, token, page_size=10)**  
   - Retrieve raw match data for a specific instance ID (in RallyHere’s native format).

7. **rh_fetch_player_by_platform_user_id(token, platform, platform_user_id, use_cache=True, if_none_match=None)**  
   - Find an environment player record by their platform user ID (e.g., "Steam" / "Weak3n").

8. **rh_fetch_player_with_displayname(token, display_names, platform=None, identity_platform=None, identities=None, include_linked_portals=True)**  
   - Lookup one or more players by display name. Optionally fetch/attach "linked_portals" information in a single returned JSON.

9. **rh_fetch_player_setting(token, player_uuid, setting_type_id, key, [conditional headers])**  
   - Fetch a single player setting under a specific "setting_type" and key.

10. **rh_fetch_player_settings_all(token, player_uuid, setting_type_id, keys=None, [conditional headers])**  
   - Get all (or selected) player settings under a specific "setting_type."

### Developer API Functions

1. **_get_dev_access_token()**  
   - Obtain a developer access token using your Developer Account ID and Secret Key.

2. **get_items(...params...)**  
   - Get a list of items in your developer sandbox with optional filters.

3. **get_sandbox_kvs(sandbox_id=None)**  
   - Retrieve all key-value pairs for the provided (or default) sandbox environment.

### SMITE 2 Transformations

RallyHere’s native data often needs to be reshaped to a "SMITE 2–friendly" structure. The SDK provides helper methods:

1. **S2_transform_player(player_data)**  
   - Transforms a single RallyHere "player data" dictionary into a standardized SMITE 2 structure.

2. **S2_transform_matches(rh_matches)**  
   - Takes a list of "player in match" records from RallyHere and returns them as a more uniform SMITE 2 list.

3. **S2_fetch_matches_by_player_uuid(player_uuid, page_size=10, max_matches=100)**  
   - Automatically fetches and transforms matches (calls rh_fetch_matches_by_player_uuid then S2_transform_matches).

4. **S2_transform_player_stats(raw_stats)**  
   - Converts raw "player stats" into SMITE 2 format.

5. **S2_fetch_player_stats(player_uuid)**  
   - Fetches raw player stats from RallyHere, then transforms them into SMITE 2 format.

6. **S2_transform_matches_by_instance(rh_matches)**  
   - Similar transformation but specifically handles instance-based match data with segments.

7. **S2_fetch_matches_by_instance(instance_id, page_size=10)**  
   - Fetches raw instance-based match data and transforms it into SMITE 2 format.

---

## Recent Features & Examples

• Added "rh_fetch_player_with_displayname" to look up players by display name(s) plus an optional platform, with an option to include "linked_portals" data in a single returned JSON.  
• Created new player settings endpoints:  
  – "rh_fetch_player_setting" to retrieve a single setting.  
  – "rh_fetch_player_settings_all" to retrieve many settings (all or specified keys) under a given "setting_type."  
• Extended the "smite2_rh_sdk_examples.py" file to act as a comprehensive test harness. It now has boolean flags at the top enabling or disabling specific tests. This helps you selectively run one or more examples at a time.  

---

## Example Test Harness (smite2_rh_sdk_examples.py)

We provide an enhanced example file, [smite2_rh_sdk_examples.py](./smite2_rh_sdk_examples.py), which demonstrates how to call each function in the SDK. The file is now structured with configuration flags at the top, letting you enable or disable individual calls:

---

## Testing and JSON Samples

All example outputs from the SDK calls can be saved as JSON in the **json_samples** directory by running:
```bash
python smite2_rh_sdk_examples.py
```
Regardless of which flags are enabled, each successful function call will save a file with a corresponding name (e.g., "json_sample_rh_fetch_player_with_displayname.json").  
You can inspect these outputs to better understand the structure of RallyHere’s native data or the SMITE 2–friendly transformations.

---

## Extensibility

We anticipate that more endpoints may be needed or that transformations may evolve. Here is how you can extend the SDK:

1. **Add new RallyHere endpoints**  
   - Create a new method in `Smite2RallyHereSDK`.  
   - Follow existing patterns for making requests (e.g., `requests.get`, `requests.post`), handle errors, and return JSON.

2. **Modify or enhance transformations**  
   - Update or add new methods that parse and restructure JSON to meet your specific SMITE 2 data model requirements.

3. **Expand or modify the test harness**  
   - Adjust **smite2_rh_sdk_examples.py** to call any new or updated functions.  
   - Use the JSON output to confirm the returned structure.

---

## FAQ / Troubleshooting

1. **I get an error about missing environment variables.**  
   - Ensure you’ve set `CLIENT_ID`, `CLIENT_SECRET`, and `RH_BASE_URL` for environment calls (and `RH_DEV_ACCOUNT_ID`, `RH_DEV_SECRET_KEY`, `RH_DEV_BASE_URL` for developer calls), or pass them to the constructor.  

2. **I get a 401/403 error when calling an endpoint.**  
   - Check your credentials and tokens. Make sure you’re using the correct environment or developer token for the endpoint.  
   - Confirm that your RallyHere account has the necessary scopes/permissions (e.g., "setting:*:*" or "user:platform:read").

3. **I get a 422 (Unprocessable Entity) error.**  
   - Typically indicates invalid query parameters (e.g., incorrect platform name, or sending a display name that doesn’t match actual data). Check the spelling, case-sensitivity, or required fields.

4. **Why does `S2_fetch_` data differ from `rh_fetch_` data?**  
   - The `S2_fetch_` methods transform RallyHere’s raw responses into a consolidated SMITE 2–friendly format. If you need the raw data, use the corresponding `rh_fetch_` method instead.

5. **How do I selectively test a single function or avoid spamming any environment calls?**  
   - In **smite2_rh_sdk_examples.py**, set the `ENABLE_...` flags to `False` for any calls you do not want to run this time.

6. **I need to see the raw JSON. Where is it stored?**  
   - Check the **json_samples** directory (generated after running the example script). Each file is named "json_sample_<function_name>.json."


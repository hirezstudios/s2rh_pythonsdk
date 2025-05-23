import os
import json
from dotenv import load_dotenv, find_dotenv
import datetime

# Explicitly find and load the .env file
env_file = find_dotenv()
if env_file:
    print(f"Loading environment from: {env_file}")
    load_dotenv(env_file)
else:
    print("No .env file found, will use existing environment variables")

from smite2_rh_sdk import Smite2RallyHereSDK

# ------------------------------------------------------------------------------
# Quick-Config Flags & Test Variables
# ------------------------------------------------------------------------------
# These flags let you toggle specific tests on/off without commenting out code.
# Set any of them to False if you don't want to run that test when you execute this file.
ENABLE_RH_FETCH_PLAYER_ID_FROM_PLAYER_UUID = False
ENABLE_RH_FETCH_PLAYER_PRESENCE_BY_UUID = False
ENABLE_RH_FETCH_MATCHES_BY_PLAYER_UUID = False
ENABLE_RH_FETCH_PLAYER_STATS = False
ENABLE_RH_FETCH_MATCHES_BY_INSTANCE = False
ENABLE_S2_FETCH_MATCHES_BY_PLAYER_UUID = False
ENABLE_S2_FETCH_PLAYER_STATS = False
ENABLE_S2_FETCH_MATCHES_BY_INSTANCE = False
ENABLE_RH_FETCH_PLAYER_BY_PLATFORM_USER_ID = False
ENABLE_RH_FETCH_PLAYER_WITH_DISPLAYNAME_NO_LINKED = False
ENABLE_RH_FETCH_PLAYER_WITH_DISPLAYNAME_LINKED = False
ENABLE_RH_FETCH_PLAYER_SETTING = False
ENABLE_RH_FETCH_PLAYER_SETTINGS_ALL = False
ENABLE_GET_ITEMS = False
ENABLE_GET_SANDBOX_KVS = False
ENABLE_S2_SUMMARIZE_BUILDS_BY_PLAYER_WITH_DISPLAYNAME = False
ENABLE_S2_FETCH_FULL_PLAYER_DATA_BY_DISPLAYNAME = False
ENABLE_RH_FETCH_PLAYER_RANKS_BY_UUID = False
ENABLE_GET_ALL_ORG_PRODUCTS = False #PERMISSIONS ISSUE
ENABLE_GET_SANDBOXES_FOR_PRODUCT = False
# Files API methods
ENABLE_S2_GET_MATCH_COMBAT_LOG = False
ENABLE_S2_GET_MATCH_CHAT_LOG = False
ENABLE_S2_GET_MATCH_LOGS = False
ENABLE_S2_GET_MATCH_FILES_BY_TYPE = False
# Time range match methods
ENABLE_RH_FETCH_MATCHES_BY_TIME_RANGE = True
ENABLE_S2_FETCH_MATCHES_BY_TIME_RANGE = True

# This controls how many matches are pulled by S2_fetch_full_player_data_by_displayname,
# as well as S2_fetch_matches_by_player_uuid, etc.
MAX_MATCHES_TO_TEST = 2

# Example time range for matches
# Using ISO 8601 format: YYYY-MM-DDThh:mm:ssZ
# One week time range ending at the current time
current_time = datetime.datetime.utcnow()
# Start time is 7 days ago
start_time = (current_time - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
# End time is current time
end_time = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")

# Maximum matches to retrieve in one query
MAX_MATCHES_TIME_RANGE = 20

# You can quickly change the test values here:
# These IDs are examples—adjust them according to your environment or scenario.
#PLAYER_UUID = "e3438d31-c3ee-5377-b645-5a604b0e2b0e"  # Example valid player UUID
PLAYER_UUID = "a80c9e7c-d09d-5687-913a-b5f2083c94df" #PBM
INSTANCE_ID = "55b5f41a-0526-45fa-b992-b212fd12a849"  # Example instance ID
SANDBOX_ID = os.getenv("RH_DEV_SANDBOX_ID", "demo_sandbox_id")  # Example sandbox ID or fallback
EXAMPLE_ITEM_IDS = [
    "00000000-0000-0000-0000-00000000008c",
    "00000000-0000-0000-0000-0000000000af"
]

# Example org identifier
# Hi-Rez Studios
ORG_IDENTIFIER_TO_TEST = "1806a824-d204-41f2-b411-ffe5beb1b624"


# Example platform / user data
PLATFORM_TO_TEST = "Steam"
PLATFORM_USER_ID_TO_TEST = "weak3n"
DISPLAY_NAME_TO_TEST = "Weak3n"

# Example setting type and key for the new rh_fetch_player_setting endpoint
SETTING_TYPE_ID_TO_TEST = "godloadouts"
SETTING_KEY_TO_TEST = "cardVFXItemId"

# Example match ID, session ID, and instance ID for Files API
MATCH_ID_TO_TEST = "28257fd8-88c1-40ed-9bad-4151bcc601a5"
SESSION_ID_TO_TEST = "60ce5622-4b06-44f3-8663-0030d6c23d11"
FILE_OUTPUT_DIR = "match_files_examples"

# ------------------------------------------------------------------------------
# Helper function to save JSON responses
# ------------------------------------------------------------------------------
def save_json(data, function_name):
    """
    Saves 'data' (Python object) as JSON into a file named 'json_sample_<function_name>.json'
    within the json_samples directory.
    """
    os.makedirs("json_samples", exist_ok=True)
    filename = f"json_sample_{function_name}.json"
    file_path = os.path.join("json_samples", filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved result of {function_name} to {file_path}")

# ------------------------------------------------------------------------------
# Main demonstration of Smite2RallyHereSDK usage
# ------------------------------------------------------------------------------
def main():
    """
    Demonstrates calling various methods from Smite2RallyHereSDK and saving their
    return data as JSON files for documentation and testing purposes.

    You can selectively enable/disable each test via the flags at the top of this file.
    """
    # Instantiate the SDK
    sdk = Smite2RallyHereSDK()

    # Obtain environment token for environment-based endpoints
    try:
        env_token = sdk._get_env_access_token()  # internal usage
    except Exception as e:
        print(f"Error acquiring env access token: {e}")
        return

    # 1) rh_fetch_player_id_from_player_uuid
    if ENABLE_RH_FETCH_PLAYER_ID_FROM_PLAYER_UUID:
        try:
            player_id = sdk.rh_fetch_player_id_from_player_uuid(PLAYER_UUID, env_token)
            save_json({"player_id": player_id}, "rh_fetch_player_id_from_player_uuid")
        except Exception as e:
            print(f"Error calling rh_fetch_player_id_from_player_uuid: {e}")

    # 2) rh_fetch_player_presence_by_UUID
    if ENABLE_RH_FETCH_PLAYER_PRESENCE_BY_UUID:
        try:
            presence_data = sdk.rh_fetch_player_presence_by_UUID(PLAYER_UUID, env_token)
            save_json(presence_data, "rh_fetch_player_presence_by_UUID")
        except Exception as e:
            print(f"Error calling rh_fetch_player_presence_by_UUID: {e}")
    
    # 3) rh_fetch_matches_by_player_uuid
    if ENABLE_RH_FETCH_MATCHES_BY_PLAYER_UUID:
        try:
            raw_matches = sdk.rh_fetch_matches_by_player_uuid(PLAYER_UUID, env_token)
            save_json(raw_matches, "rh_fetch_matches_by_player_uuid")
        except Exception as e:
            print(f"Error calling rh_fetch_matches_by_player_uuid: {e}")
    
    # 4) rh_fetch_player_stats
    if ENABLE_RH_FETCH_PLAYER_STATS:
        try:
            raw_stats = sdk.rh_fetch_player_stats(PLAYER_UUID, env_token)
            save_json(raw_stats, "rh_fetch_player_stats")
        except Exception as e:
            print(f"Error calling rh_fetch_player_stats: {e}")

    # 5) rh_fetch_matches_by_instance
    if ENABLE_RH_FETCH_MATCHES_BY_INSTANCE:
        try:
            instance_matches = sdk.rh_fetch_matches_by_instance(INSTANCE_ID, env_token)
            save_json(instance_matches, "rh_fetch_matches_by_instance")
        except Exception as e:
            print(f"Error calling rh_fetch_matches_by_instance: {e}")

    # 6) S2_fetch_matches_by_player_uuid (transformed data)
    if ENABLE_S2_FETCH_MATCHES_BY_PLAYER_UUID:
        try:
            s2_matches = sdk.S2_fetch_matches_by_player_uuid(PLAYER_UUID, max_matches=300)
            save_json(s2_matches, "S2_fetch_matches_by_player_uuid")
        except Exception as e:
            print(f"Error calling S2_fetch_matches_by_player_uuid: {e}")

    # 7) S2_fetch_player_stats (transformed stats)
    if ENABLE_S2_FETCH_PLAYER_STATS:
        try:
            s2_player_stats = sdk.S2_fetch_player_stats(PLAYER_UUID)
            save_json(s2_player_stats, "S2_fetch_player_stats")
        except Exception as e:
            print(f"Error calling S2_fetch_player_stats: {e}")

    # 8) S2_fetch_matches_by_instance (transformed data)
    if ENABLE_S2_FETCH_MATCHES_BY_INSTANCE:
        try:
            s2_instance_matches = sdk.S2_fetch_matches_by_instance(INSTANCE_ID)
            save_json(s2_instance_matches, "S2_fetch_matches_by_instance")
        except Exception as e:
            print(f"Error calling S2_fetch_matches_by_instance: {e}")

    # 9) rh_fetch_player_by_platform_user_id
    if ENABLE_RH_FETCH_PLAYER_BY_PLATFORM_USER_ID:
        try:
            platform_user_data = sdk.rh_fetch_player_by_platform_user_id(
                token=env_token,
                platform=PLATFORM_TO_TEST,
                platform_user_id=PLATFORM_USER_ID_TO_TEST
            )
            save_json(platform_user_data, "rh_fetch_player_by_platform_user_id")
        except Exception as e:
            print(f"Error calling rh_fetch_player_by_platform_user_id: {e}")

    # 10) rh_fetch_player_with_displayname (no linked portals)
    if ENABLE_RH_FETCH_PLAYER_WITH_DISPLAYNAME_NO_LINKED:
        try:
            player_lookup_data = sdk.rh_fetch_player_with_displayname(
                token=env_token,
                display_names=[DISPLAY_NAME_TO_TEST],
                platform="Steam",       # Possibly case-sensitive
                include_linked_portals=False
            )
            save_json(player_lookup_data, "rh_fetch_player_with_displayname_no_linked")
        except Exception as e:
            print(f"Error calling rh_fetch_player_with_displayname (no linked portals): {e}")

    # 11) rh_fetch_player_with_displayname (with linked portals)
    if ENABLE_RH_FETCH_PLAYER_WITH_DISPLAYNAME_LINKED:
        try:
            player_lookup_data_linked = sdk.rh_fetch_player_with_displayname(
                token=env_token,
                display_names=[DISPLAY_NAME_TO_TEST],
                platform="Steam",
                include_linked_portals=True
            )
            save_json(player_lookup_data_linked, "rh_fetch_player_with_displayname_linked")
        except Exception as e:
            print(f"Error calling rh_fetch_player_with_displayname (with linked portals): {e}")

    # 12) rh_fetch_player_setting
    if ENABLE_RH_FETCH_PLAYER_SETTING:
        try:
            fetched_setting = sdk.rh_fetch_player_setting(
                token=env_token,
                player_uuid=PLAYER_UUID,
                setting_type_id=SETTING_TYPE_ID_TO_TEST,
                key=SETTING_KEY_TO_TEST
            )
            save_json(fetched_setting, "rh_fetch_player_setting")
        except Exception as e:
            print(f"Error calling rh_fetch_player_setting: {e}")

    # 13) (NEW) rh_fetch_player_settings_all
    if ENABLE_RH_FETCH_PLAYER_SETTINGS_ALL:
        try:
            # Optionally, you could pass a list of keys if you only want certain ones:
            # e.g., keys=[SETTING_KEY_TO_TEST]
            # Passing None or an empty list fetches all keys for that setting type.
            settings_all = sdk.rh_fetch_player_settings_all(
                token=env_token,
                player_uuid=PLAYER_UUID,
                setting_type_id=SETTING_TYPE_ID_TO_TEST,
                keys=None  # or [], or [SETTING_KEY_TO_TEST]
            )
            save_json(settings_all, "rh_fetch_player_settings_all")
        except Exception as e:
            print(f"Error calling rh_fetch_player_settings_all: {e}")

    # (NEW) s2_summarize_builds_by_player_with_displayname
    if ENABLE_S2_SUMMARIZE_BUILDS_BY_PLAYER_WITH_DISPLAYNAME:
        try:
            summary_data = sdk.s2_summarize_builds_by_player_with_displayname(
                platform=PLATFORM_TO_TEST,
                display_name=DISPLAY_NAME_TO_TEST,
                max_matches_per_player=300
            )
            save_json(summary_data, "s2_summarize_builds_by_player_with_displayname")
        except Exception as e:
            print(f"Error calling s2_summarize_builds_by_player_with_displayname: {e}")

    # (NEW) s2_fetch_full_player_data_by_displayname
    if ENABLE_S2_FETCH_FULL_PLAYER_DATA_BY_DISPLAYNAME:
        try:
            full_data = sdk.S2_fetch_full_player_data_by_displayname(
                platform=PLATFORM_TO_TEST,
                display_name=DISPLAY_NAME_TO_TEST,
                max_matches=MAX_MATCHES_TO_TEST
            )
            save_json(full_data, "S2_fetch_full_player_data_by_displayname")
        except Exception as e:
            print(f"Error calling S2_fetch_full_player_data_by_displayname: {e}")

    # (NEW) rh_fetch_player_ranks_by_uuid
    if ENABLE_RH_FETCH_PLAYER_RANKS_BY_UUID:
        try:
            ranks_data = sdk.rh_fetch_player_ranks_by_uuid(env_token, PLAYER_UUID)
            save_json(ranks_data, "rh_fetch_player_ranks_by_uuid")
        except Exception as e:
            print(f"Error calling rh_fetch_player_ranks_by_uuid: {e}")

    # Obtain dev token for developer-based endpoints (if running get_items/get_sandbox_kvs)
    try:
        dev_token = sdk._get_dev_access_token()  # Developer API token
        print(f"Acquired dev access token: {dev_token[:10]}...")  # Partially shown for demonstration
    except Exception as e:
        print(f"Error acquiring dev access token: {e}")
        dev_token = None

    # 14) get_items
    if dev_token and ENABLE_GET_ITEMS:
        try:
            items_response = sdk.get_items(
                sandbox_id=SANDBOX_ID,
                item_ids=EXAMPLE_ITEM_IDS
            )
            save_json(items_response, "get_items")
        except Exception as e:
            print(f"Error calling get_items: {e}")

    # 15) get_sandbox_kvs
    if dev_token and ENABLE_GET_SANDBOX_KVS:
        try:
            kvs_response = sdk.get_sandbox_kvs(sandbox_id=SANDBOX_ID)
            save_json(kvs_response, "get_sandbox_kvs")
        except Exception as e:
            print(f"Error calling get_sandbox_kvs: {e}")

    # 16) get_all_org_products
    if dev_token and ENABLE_GET_ALL_ORG_PRODUCTS:
        try:
            org_products = sdk.get_all_org_products(ORG_IDENTIFIER_TO_TEST)
            save_json(org_products, "get_all_org_products")
        except Exception as e:
            print(f"Error calling get_all_org_products: {e}")

    # (NEW) get_all_sandboxes_for_product
    if dev_token and ENABLE_GET_SANDBOXES_FOR_PRODUCT:
        try:
            sandboxes = sdk.get_all_sandboxes_for_product()
            save_json(sandboxes, "get_all_sandboxes_for_product")
        except Exception as e:
            print(f"Error calling get_all_sandboxes_for_product: {e}")

    # Files API endpoints
    # Note: For these endpoints, we'll need to import the FileApiMethods class
    # and attach it to the SDK to simulate integration
    if ENABLE_S2_GET_MATCH_COMBAT_LOG or ENABLE_S2_GET_MATCH_CHAT_LOG or ENABLE_S2_GET_MATCH_LOGS or ENABLE_S2_GET_MATCH_FILES_BY_TYPE:
        try:
            # Import the FileApiMethods class
            from files_api_sdk_extension import FileApiMethods
            
            # Create a FileApiMethods instance and attach SDK properties
            file_api = FileApiMethods()
            file_api.env_base_url = sdk.env_base_url
            file_api._get_env_access_token = sdk._get_env_access_token
            
            # Create output directory
            os.makedirs(FILE_OUTPUT_DIR, exist_ok=True)
            
            # S2_get_match_combat_log: Get the combat log for a match
            if ENABLE_S2_GET_MATCH_COMBAT_LOG:
                try:
                    combat_log_path = file_api.S2_get_match_combat_log(
                        MATCH_ID_TO_TEST,
                        output_dir=FILE_OUTPUT_DIR
                    )
                    # Since this returns a file path, let's save the metadata
                    log_info = {
                        "match_id": MATCH_ID_TO_TEST, 
                        "file_path": combat_log_path,
                        "success": combat_log_path is not None
                    }
                    save_json(log_info, "S2_get_match_combat_log")
                except Exception as e:
                    print(f"Error calling S2_get_match_combat_log: {e}")
            
            # S2_get_match_chat_log: Get the chat log for a match
            if ENABLE_S2_GET_MATCH_CHAT_LOG:
                try:
                    chat_log_path = file_api.S2_get_match_chat_log(
                        MATCH_ID_TO_TEST,
                        SESSION_ID_TO_TEST,
                        FILE_OUTPUT_DIR
                    )
                    # Since this returns a file path, let's save the metadata
                    log_info = {
                        "match_id": MATCH_ID_TO_TEST, 
                        "session_id": SESSION_ID_TO_TEST,
                        "file_path": chat_log_path,
                        "success": chat_log_path is not None
                    }
                    save_json(log_info, "S2_get_match_chat_log")
                except Exception as e:
                    print(f"Error calling S2_get_match_chat_log: {e}")
            
            # S2_get_match_logs: Get all logs for a match
            if ENABLE_S2_GET_MATCH_LOGS:
                try:
                    logs = file_api.S2_get_match_logs(
                        MATCH_ID_TO_TEST,
                        FILE_OUTPUT_DIR
                    )
                    # Since this returns a dictionary of file paths, let's save the metadata
                    log_info = {
                        "match_id": MATCH_ID_TO_TEST,
                        "file_count": len(logs),
                        "files": {name: path for name, path in logs.items()}
                    }
                    save_json(log_info, "S2_get_match_logs")
                except Exception as e:
                    print(f"Error calling S2_get_match_logs: {e}")
            
            # S2_get_match_files_by_type: Get files by type using friendly names
            if ENABLE_S2_GET_MATCH_FILES_BY_TYPE:
                try:
                    # Example 1: Get specific file types
                    logs_by_type = file_api.S2_get_match_files_by_type(
                        MATCH_ID_TO_TEST,
                        file_types=["ChatLog", "Diagnostics"],
                        session_id=SESSION_ID_TO_TEST,
                        output_dir=FILE_OUTPUT_DIR
                    )
                    
                    # Save the results
                    results = {
                        "match_id": MATCH_ID_TO_TEST,
                        "session_id": SESSION_ID_TO_TEST,
                        "file_types_requested": ["ChatLog", "Diagnostics"],
                        "file_count": len(logs_by_type),
                        "files": {name: path for name, path in logs_by_type.items()}
                    }
                    save_json(results, "S2_get_match_files_by_type")
                    
                    # Example 2: Get all file types (for documentation)
                    all_file_types = file_api.S2_get_match_files_by_type(
                        MATCH_ID_TO_TEST,
                        file_types="All",
                        session_id=SESSION_ID_TO_TEST,
                        output_dir=FILE_OUTPUT_DIR
                    )
                    
                    # Save the results
                    all_results = {
                        "match_id": MATCH_ID_TO_TEST,
                        "session_id": SESSION_ID_TO_TEST,
                        "file_types_requested": "All",
                        "file_count": len(all_file_types),
                        "files": {name: path for name, path in all_file_types.items()}
                    }
                    save_json(all_results, "S2_get_match_files_by_type_all")
                except Exception as e:
                    print(f"Error calling S2_get_match_files_by_type: {e}")
        except ImportError as e:
            print(f"Error importing FileApiMethods: {e}")

    print("\nDone running all example SDK calls.")

    # Time range match methods
    # Test rh_fetch_matches_by_time_range
    if ENABLE_RH_FETCH_MATCHES_BY_TIME_RANGE:
        try:
            print(f"\nFetching matches by time range: {start_time} to {end_time}")
            matches_by_time = sdk.rh_fetch_matches_by_time_range(
                token=env_token,
                start_time=start_time,
                end_time=end_time,
                limit=MAX_MATCHES_TIME_RANGE,
                page_size=MAX_MATCHES_TIME_RANGE,
                status="closed"
            )
            save_json(matches_by_time, "rh_fetch_matches_by_time_range")
            print(f"Retrieved {len(matches_by_time.get('data', []))} matches by time range")
        except Exception as e:
            print(f"Error calling rh_fetch_matches_by_time_range: {e}")
    
    # Test S2_fetch_matches_by_time_range
    if ENABLE_S2_FETCH_MATCHES_BY_TIME_RANGE:
        try:
            print(f"\nFetching and transforming matches by time range: {start_time} to {end_time}")
            s2_matches_by_time = sdk.S2_fetch_matches_by_time_range(
                start_time=start_time,
                end_time=end_time,
                limit=MAX_MATCHES_TIME_RANGE,
                page_size=MAX_MATCHES_TIME_RANGE,
                status="closed"
            )
            save_json(s2_matches_by_time, "S2_fetch_matches_by_time_range")
            print(f"Retrieved and transformed {len(s2_matches_by_time)} matches by time range")
        except Exception as e:
            print(f"Error calling S2_fetch_matches_by_time_range: {e}")

if __name__ == "__main__":
    main() 
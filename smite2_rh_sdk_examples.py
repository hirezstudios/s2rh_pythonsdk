import os
import json
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
ENABLE_RH_FETCH_PLAYER_SETTING = True

# New flag for fetching all player settings of a specific type
ENABLE_RH_FETCH_PLAYER_SETTINGS_ALL = True

ENABLE_GET_ITEMS = False
ENABLE_GET_SANDBOX_KVS = False

# You can quickly change the test values here:
# These IDs are examples—adjust them according to your environment or scenario.
PLAYER_UUID = "e3438d31-c3ee-5377-b645-5a604b0e2b0e"  # Example valid player UUID
INSTANCE_ID = "55b5f41a-0526-45fa-b992-b212fd12a849"  # Example instance ID
SANDBOX_ID = os.getenv("RH_DEV_SANDBOX_ID", "demo_sandbox_id")  # Example sandbox ID or fallback
EXAMPLE_ITEM_IDS = [
    "00000000-0000-0000-0000-00000000008c",
    "00000000-0000-0000-0000-0000000000af"
]

# Example platform / user data
PLATFORM_TO_TEST = "steam"
PLATFORM_USER_ID_TO_TEST = "weak3n"
DISPLAY_NAME_TO_TEST = "Weak3n"

# Example setting type and key for the new rh_fetch_player_setting endpoint
SETTING_TYPE_ID_TO_TEST = "godloadouts"
SETTING_KEY_TO_TEST = "cardVFXItemId"

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
            s2_matches = sdk.S2_fetch_matches_by_player_uuid(PLAYER_UUID)
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

    print("Done running all example SDK calls.")

if __name__ == "__main__":
    main() 
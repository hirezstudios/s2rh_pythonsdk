import os
import requests
import base64
import json
from typing import Optional, List, Union, Dict, Set, Callable, Any
import time
from datetime import datetime, timezone

from files_api import Smite2RallyHereFilesAPI

class MatchFilter:
    """Base class for match filtering."""
    
    def apply(self, match: Dict[str, Any]) -> bool:
        """
        Apply the filter to a match.
        
        Args:
            match: The match dictionary to filter.
            
        Returns:
            bool: True if the match passes the filter, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement apply()")
    
    def __and__(self, other: 'MatchFilter') -> 'AndFilter':
        """Combine with another filter using AND logic."""
        return AndFilter(self, other)
    
    def __or__(self, other: 'MatchFilter') -> 'OrFilter':
        """Combine with another filter using OR logic."""
        return OrFilter(self, other)

class AndFilter(MatchFilter):
    """Filter that combines two filters with AND logic."""
    
    def __init__(self, filter1: MatchFilter, filter2: MatchFilter):
        self.filter1 = filter1
        self.filter2 = filter2
    
    def apply(self, match: Dict[str, Any]) -> bool:
        return self.filter1.apply(match) and self.filter2.apply(match)

class OrFilter(MatchFilter):
    """Filter that combines two filters with OR logic."""
    
    def __init__(self, filter1: MatchFilter, filter2: MatchFilter):
        self.filter1 = filter1
        self.filter2 = filter2
    
    def apply(self, match: Dict[str, Any]) -> bool:
        return self.filter1.apply(match) or self.filter2.apply(match)

class DurationFilter(MatchFilter):
    """Filter matches by duration."""
    
    def __init__(self, min_duration: Optional[int] = None, max_duration: Optional[int] = None):
        self.min_duration = min_duration
        self.max_duration = max_duration
    
    def apply(self, match: Dict[str, Any]) -> bool:
        duration = match.get("duration_seconds", 0)
        
        if self.min_duration is not None and duration < self.min_duration:
            return False
        
        if self.max_duration is not None and duration > self.max_duration:
            return False
        
        return True

class RegionFilter(MatchFilter):
    """Filter matches by region ID."""
    
    def __init__(self, region_id: str):
        self.region_id = region_id
    
    def apply(self, match: Dict[str, Any]) -> bool:
        instances = match.get("instances", [])
        if not instances:
            return False
        
        # Check if any instance matches the region ID
        return any(instance.get("region_id") == self.region_id for instance in instances)

class GameModeFilter(MatchFilter):
    """Filter matches by game mode."""
    
    def __init__(self, game_mode: str):
        self.game_mode = game_mode
    
    def apply(self, match: Dict[str, Any]) -> bool:
        instances = match.get("instances", [])
        if not instances:
            return False
        
        # Check if any instance's game mode contains the specified game mode
        return any(self.game_mode in instance.get("game_mode", "") for instance in instances)

class HostTypeFilter(MatchFilter):
    """Filter matches by host type."""
    
    def __init__(self, host_type: str):
        self.host_type = host_type
    
    def apply(self, match: Dict[str, Any]) -> bool:
        instances = match.get("instances", [])
        if not instances:
            return False
        
        # Check if any instance matches the host type
        return any(instance.get("host_type") == self.host_type for instance in instances)

class CustomFilter(MatchFilter):
    """Filter matches using a custom function."""
    
    def __init__(self, filter_func: Callable[[Dict[str, Any]], bool]):
        self.filter_func = filter_func
    
    def apply(self, match: Dict[str, Any]) -> bool:
        return self.filter_func(match)

class Smite2RallyHereSDK:
    """
    A unified Python SDK for interacting with RallyHere Environment & Developer APIs,
    returning data in a SMITE 2–friendly format.
    """

    def __init__(
        self,
        env_client_id: Optional[str] = None,
        env_client_secret: Optional[str] = None,
        env_base_url: Optional[str] = None,
        dev_client_id: Optional[str] = None,
        dev_secret_key: Optional[str] = None,
        dev_base_url: Optional[str] = None
    ):
        """
        Constructor for the unified Smite2RallyHereSDK.

        :param env_client_id: (Optional) Env client ID. If not provided, uses env var CLIENT_ID.
        :param env_client_secret: (Optional) Env client secret. If not provided, uses env var CLIENT_SECRET.
        :param env_base_url: (Optional) Env base URL. If not provided, uses env var RH_BASE_URL.
        :param dev_client_id: (Optional) Dev client ID. If not provided, uses env var RH_DEV_ACCOUNT_ID.
        :param dev_secret_key: (Optional) Dev secret key. If not provided, uses env var RH_DEV_SECRET_KEY.
        :param dev_base_url: (Optional) Dev API base URL. If not provided, uses env var RH_DEV_BASE_URL.
        """
        # Environment API credentials
        self.env_client_id = env_client_id or os.getenv("CLIENT_ID")
        self.env_client_secret = env_client_secret or os.getenv("CLIENT_SECRET")
        self.env_base_url = env_base_url or os.getenv("RH_BASE_URL")

        # Developer API credentials
        self.dev_client_id = dev_client_id or os.getenv('RH_DEV_ACCOUNT_ID')
        self.dev_secret_key = dev_secret_key or os.getenv('RH_DEV_SECRET_KEY')
        self.dev_base_url = dev_base_url or os.getenv('RH_DEV_BASE_URL')

        # Basic validation
        # You can make these checks more or less strict depending on usage
        if not self.env_client_id or not self.env_client_secret or not self.env_base_url:
            raise ValueError("Missing environment credentials or base URL; "
                             "provide env_client_id/env_client_secret/env_base_url or set environment variables.")

        if not self.dev_client_id or not self.dev_secret_key or not self.dev_base_url:
            raise ValueError("Missing dev credentials or base URL; "
                             "provide dev_client_id/dev_secret_key/dev_base_url or set environment variables.")

        # Initialize the FilesAPI extension
        self.files = Smite2RallyHereFilesAPI(self)

    # -------------------------------------------------------------------------
    # ENV API: Environment Token & Fetch Methods
    # -------------------------------------------------------------------------
    def _get_env_access_token(self) -> str:
        """
        Fetches a RallyHere environment token via client_credentials.
        """
        creds = f"{self.env_client_id}:{self.env_client_secret}"
        encoded = base64.b64encode(creds.encode()).decode()

        url = f"{self.env_base_url}/users/v2/oauth/token"
        headers = {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {"grant_type": "client_credentials"}

        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def rh_fetch_matches_by_player_uuid(
        self,
        player_uuid: str,
        token: str,
        page_size: int = 10,
        max_matches: int = 100
    ) -> list:
        """
        Fetch raw match data for the specified player from RallyHere.
        Returns a list of match dictionaries in RallyHere's native format.
        """
        matches = []
        cursor = None

        while len(matches) < max_matches:
            url = f"{self.env_base_url}/match/v1/player/{player_uuid}/match?page_size={page_size}"
            if cursor:
                url += f"&cursor={cursor}"

            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            matches.extend(data.get("player_matches", []))
            cursor = data.get("cursor")

            if not cursor:
                break

        return matches[:max_matches]

    def rh_fetch_player_stats(self, player_uuid: str, token: str) -> dict:
        """
        Fetch raw player stats from RallyHere using the /stats endpoint
        instead of /match. Returns the raw stats data as a dictionary.
        """
        url = f"{self.env_base_url}/match/v1/player/{player_uuid}/stats"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data

    def rh_fetch_matches_by_instance(
        self,
        instance_id: str,
        token: str,
        page_size: int = 10
    ) -> list:
        """
        Fetch raw match data filtered by instance_id from RallyHere.
        Returns a list of match dictionaries, typically with 'match_id', 'segments', 'players', etc.
        """
        matches = []
        cursor = None

        while True:
            url = f"{self.env_base_url}/match/v1/match?instance_id={instance_id}&page_size={page_size}"
            if cursor:
                url += f"&cursor={cursor}"

            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            matches.extend(data.get("matches", []))

            cursor = data.get("cursor")
            if not cursor:
                break

        return matches
    
    def rh_fetch_player_id_from_player_uuid(self, player_uuid: str, token: str) -> int:
        """
        Fetch a player's integer ID from their UUID using the RallyHere Environment API.

        Endpoint:
            GET /users/v2/player/:player_uuid/id
        
        :param player_uuid: The UUID of the player.
        :param token: A valid environment token (retrieved via _get_env_access_token).
        :return: The integer player ID.
        """
        url = f"{self.env_base_url}/users/v2/player/{player_uuid}/id"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        return data["player_id"]

    def rh_fetch_player_presence_by_UUID(
        self,
        player_uuid: str,
        token: str,
        use_cache: bool = True,
        if_none_match: Optional[str] = None
    ) -> dict:
        """
        Fetch a player's presence information from the RallyHere Environment API by UUID.

        Endpoint:
            GET /presence/v1/player/uuid/:player_uuid/presence

        Query Parameters:
            - use_cache: (bool) Whether to use a cached result on the server side. Defaults to True.

        Header Parameters:
            - if_none_match: (Optional) Provide an ETag to potentially receive a 304 response 
              if the resource has not changed since your last request.

        :param player_uuid: A valid UUID identifying a player. 
        :param token: A valid environment token (retrieved via _get_env_access_token).
        :param use_cache: Defaults to True.
        :param if_none_match: Optional ETag from a previous response.

        :return: A dictionary representing the player's presence data, such as status, platform, 
                 display_name, etc.
        """
        url = f"{self.env_base_url}/presence/v1/player/uuid/{player_uuid}/presence"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        if if_none_match:
            headers["If-None-Match"] = if_none_match

        params = {
            "use_cache": str(use_cache).lower()  # "true" or "false"
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        # If not changed, server should respond with a 304 and no content
        # but raise_for_status() wouldn't throw an error, so we handle that scenario
        if response.status_code == 304:
            return {"status": "not_modified"}

        return response.json()
    
    def rh_fetch_player_by_platform_user_id(
        self,
        token: str,
        platform: str,
        platform_user_id: str
    ) -> dict:
        """
        Find an existing platform user via platform identity.

        Endpoint:
            GET /users/v1/platform-user?platform={platform}&platform_user_id={platform_user_id}

        Required Permissions:
          For any player (including themselves), any of: user:*, user:platform:read

        :param token: A valid environment token (retrieved via _get_env_access_token).
        :param platform: Platform to search (e.g., 'XboxLive', 'PSN', 'Steam', etc.)
        :param platform_user_id: The user's platform-specific ID (up to 2048 characters).
        :return: A dictionary with fields including platform, platform_user_id, display_name, player_uuid, etc.
        """
        url = f"{self.env_base_url}/users/v1/platform-user"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        params = {
            "platform": platform,
            "platform_user_id": platform_user_id
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    # -------------------------------------------------------------------------
    # SMITE 2: Transformations
    # -------------------------------------------------------------------------
    def S2_transform_player(self, player_data: dict) -> dict:
        """
        Transform a single player's record from RallyHere's native format
        into a SMITE 2–friendly format.
        """
        custom_data = player_data.get("custom_data", {})

        transformed = {
            "player_uuid": player_data.get("player_uuid"),
            "team_id": player_data.get("team_id"),
            "placement": player_data.get("placement"),
            "joined_match_timestamp": player_data.get("joined_match_timestamp"),
            "left_match_timestamp": player_data.get("left_match_timestamp"),
            "duration_seconds": player_data.get("duration_seconds"),
        }

        # God / Character
        character_choice = custom_data.get("CharacterChoice", "")
        if character_choice.startswith("Gods."):
            god_name = character_choice.split(".", 1)[1]
        else:
            god_name = character_choice or "UnknownGod"
        transformed["god_name"] = god_name

        # Convert certain keys to int
        basic_stats_keys = [
            "Kills", "Deaths", "Assists", "TowerKills", "PhoenixKills", "TitanKills",
            "TotalDamage", "TotalNPCDamage", "TotalDamageTaken", "TotalDamageMitigated",
            "TotalGoldEarned", "TotalXPEarned", "TotalStructureDamage", "TotalMinionDamage",
            "TotalAllyHealing", "TotalSelfHealing", "TotalWardsPlaced", "PlayerLevel"
        ]
        basic_stats = {}
        for stat_key in basic_stats_keys:
            raw_val = custom_data.get(stat_key)
            basic_stats[stat_key] = int(raw_val) if (raw_val and raw_val.isdigit()) else 0
        transformed["basic_stats"] = basic_stats

        # Role info
        transformed["assigned_role"] = custom_data.get("AssignedRole")
        transformed["played_role"] = custom_data.get("PlayedRole")

        # Potentially parse JSON fields (e.g., items)
        items_str = custom_data.get("Items")
        if items_str:
            try:
                transformed["items"] = json.loads(items_str)
            except (json.JSONDecodeError, TypeError):
                transformed["items"] = {}
        role_prefs_str = custom_data.get("RolePreferences")
        if role_prefs_str:
            try:
                transformed["role_preferences"] = json.loads(role_prefs_str)
            except (json.JSONDecodeError, TypeError):
                transformed["role_preferences"] = {}

        # Damage breakdown
        damage_breakdown = {}
        for key, raw_val in custom_data.items():
            if not isinstance(raw_val, str):
                continue
            if not raw_val.isdigit():
                continue

            if key.startswith("Gods."):
                segments = key.split(".")
                if len(segments) >= 3:
                    god_part = segments[1]
                    stat_part = ".".join(segments[2:])
                    damage_breakdown.setdefault(god_part, {})
                    damage_breakdown[god_part][stat_part] = int(raw_val)
            elif key.startswith("Items."):
                segments = key.split(".")
                if len(segments) == 3:
                    _, item_name, item_stat = segments
                    damage_breakdown.setdefault(item_name, {})
                    damage_breakdown[item_name][item_stat] = int(raw_val)
                else:
                    item_name = segments[1] if len(segments) > 1 else "UnknownItem"
                    damage_breakdown.setdefault(item_name, {})
                    damage_breakdown[item_name]["value"] = int(raw_val)
            elif key.startswith("NPC.") or key.startswith("Ability.Type.Item"):
                damage_breakdown.setdefault("Misc", {})
                damage_breakdown["Misc"][key] = int(raw_val)
            else:
                damage_breakdown.setdefault("misc_stats", {})
                damage_breakdown["misc_stats"][key] = int(raw_val)

        transformed["damage_breakdown"] = damage_breakdown

        return transformed

    def S2_transform_matches(self, rh_matches: list) -> list:
        """
        Example transformation for a "playerMatches" style list,
        where each dict is a single 'player in match' record from RallyHere.
        """
        s2_matches = []
        for record in rh_matches:
            player_transformed = self.S2_transform_player(record)

            # Additional match-level fields
            match_info = record.get("match", {})
            match_custom = match_info.get("custom_data", {})

            player_transformed["match_id"] = match_info.get("match_id")
            player_transformed["match_start"] = match_info.get("start_timestamp")
            player_transformed["match_end"] = match_info.get("end_timestamp")
            player_transformed["map"] = match_custom.get("CurrentMap")
            player_transformed["mode"] = match_custom.get("CurrentMode")
            player_transformed["lobby_type"] = match_custom.get("LobbyType")
            player_transformed["winning_team"] = match_custom.get("WinningTeam")

            s2_matches.append(player_transformed)

        return s2_matches

    def S2_fetch_matches_by_player_uuid(
        self,
        player_uuid: str,
        page_size: int = 10,
        max_matches: int = 100
    ) -> list:
        """
        SMITE 2–specific version of fetching match data by player UUID.
        After fetching, transforms each record so it's SMITE 2–friendly,
        then runs _enrich_matches_with_item_data to replace item IDs.
        """
        token = self._get_env_access_token()
        rh_matches = self.rh_fetch_matches_by_player_uuid(player_uuid, token, page_size, max_matches)

        # Transform the raw RallyHere data into SMITE 2–friendly structures.
        # This likely returns a list of "player" dicts, each with 'items'.
        s2_players = self.S2_transform_matches(rh_matches)

        # Now unify the item data (handling the "player-based" shape).
        s2_players = self._enrich_matches_with_item_data(s2_players)

        return s2_players

    def S2_transform_matches_by_instance(self, rh_matches: list) -> list:
        """
        Transform the raw instance-based match data from RallyHere
        into a structure that's more approachable in SMITE 2 form.
        """
        s2_matches = []

        for match_info in rh_matches:
            match_id = match_info.get("match_id")
            start_ts = match_info.get("start_timestamp")
            end_ts = match_info.get("end_timestamp")
            duration_seconds = match_info.get("duration_seconds")
            custom_data = match_info.get("custom_data", {})

            s2_match = {
                "match_id": match_id,
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "duration_seconds": duration_seconds,
                "map": custom_data.get("CurrentMap"),
                "mode": custom_data.get("CurrentMode"),
                "lobby_type": custom_data.get("LobbyType"),
                "winning_team": custom_data.get("WinningTeam"),
                "segments": [],
                "final_players": []
            }

            # Transform each segment
            segments = match_info.get("segments", [])
            for seg in segments:
                segment_label = seg.get("match_segment")
                seg_start = seg.get("start_timestamp")
                seg_end = seg.get("end_timestamp")
                seg_duration = seg.get("duration_seconds")

                seg_players = seg.get("players", [])
                transformed_players = [self.S2_transform_player(p) for p in seg_players]

                s2_segment = {
                    "segment_label": segment_label,
                    "start_timestamp": seg_start,
                    "end_timestamp": seg_end,
                    "duration_seconds": seg_duration,
                    "players": transformed_players
                }
                s2_match["segments"].append(s2_segment)

            # top-level "players" if it exists
            top_level_players = match_info.get("players", [])
            s2_final_players = [self.S2_transform_player(p) for p in top_level_players]
            s2_match["final_players"] = s2_final_players

            s2_matches.append(s2_match)

        # NEW: After building s2_matches, enrich items with full data:
        s2_matches = self._enrich_matches_with_item_data(s2_matches)

        return s2_matches

    def _enrich_matches_with_item_data(self, s2_data: list) -> list:
        """
        For each entity (match record or player record) in s2_data, go through
        and replace the 'items' IDs with full item data from items.json.
        
        Detects if we have an "instance-based" shape with segments/final_players,
        or if each element is an individual player record with 'items'.
        """
        item_map = self._load_items_map()

        if not s2_data:
            return s2_data

        first = s2_data[0]
        if isinstance(first, dict):
            # If it has segments/final_players, assume instance-based match shape
            if "segments" in first and "final_players" in first:
                for match in s2_data:
                    # handle top-level players
                    for player in match.get("final_players", []):
                        self._replace_item_ids(player, item_map)
                    # handle segment-based players
                    for segment in match.get("segments", []):
                        for player in segment.get("players", []):
                            self._replace_item_ids(player, item_map)
            else:
                # Otherwise, assume it's a list of player records (player-based shape).
                for player_record in s2_data:
                    self._replace_item_ids(player_record, item_map)

        return s2_data

    def _replace_item_ids(self, player: dict, item_map: dict) -> None:
        """
        Given a single player's dictionary, replace each item ID in player["items"]
        with a fully described item node from the item_map, if found. Otherwise,
        provide a fallback item structure.
        """
        items_dict = player.get("items", {})
        for slot_key, item_id in list(items_dict.items()):
            # If the item ID is in our map, replace the string ID with the full item data
            if item_id in item_map:
                items_dict[slot_key] = item_map[item_id]
            else:
                # Provide a lightweight fallback structure with placeholder display name
                items_dict[slot_key] = {
                    "Item_Id": item_id,
                    "DisplayName": "<display name missing>"
                }

    def _load_items_map(self) -> dict:
        """
        Load items.json from disk, creating a dictionary mapping
        Item_Id -> item data object.
        """
        # Adjust this path to wherever your items.json file lives:
        items_json_path = os.path.join(os.path.dirname(__file__), "items.json")

        try:
            with open(items_json_path, "r", encoding="utf-8") as f:
                items_data = json.load(f)
        except Exception as e:
            print(f"Error loading items.json: {e}")
            return {}

        # Build a map of { "0000000000000000000000000000009F": {...full item data...}, ... }
        item_map = {}
        for item_obj in items_data:
            item_id = item_obj.get("Item_Id")
            if item_id:
                item_map[item_id] = item_obj
        return item_map

    def S2_fetch_matches_by_instance(
        self,
        instance_id: str,
        page_size: int = 10
    ) -> list:
        """
        SMITE 2–specific version of fetching match data by instance ID,
        returning transformed match records (with segments, players, etc.).
        """
        token = self._get_env_access_token()
        rh_matches = self.rh_fetch_matches_by_instance(instance_id, token, page_size)
        return self.S2_transform_matches_by_instance(rh_matches)

    def S2_fetch_player_stats(self, player_uuid: str) -> dict:
        """
        Fetch the (simplified) player stats from RallyHere in 'S2' form.
        Since the stats endpoint returns minimal fields (e.g., {"total_matches_played": 735}),
        we simply return the raw dictionary from rh_fetch_player_stats.
        """
        token = self._get_env_access_token()
        raw_stats = self.rh_fetch_player_stats(player_uuid, token)
        return raw_stats

    def S2_fetch_full_player_data_by_displayname(
        self,
        platform: str,
        display_name: str,
        max_matches: int = 100
    ) -> dict:
        """
        Fetch a consolidated JSON for a player's data by display name (and platform).
        1) Calls rh_fetch_player_with_displayname (including linked portals).
        2) Collects all player UUIDs from that data.
        3) Fetches match history (S2_fetch_matches_by_player_uuid) and stats (S2_fetch_player_stats).
        4) (NEW) Fetches rank data (rh_fetch_player_ranks_by_uuid).
        5) Returns a simplified JSON blob with:
           {
               "PlayerInfo": {...},
               "PlayerStats": [],
               "PlayerRanks": [],    # <-- new node
               "MatchHistory": []
           }
        """
        token = self._get_env_access_token()

        # 1) Get the base "player info" data (including linked portals).
        player_info = self.rh_fetch_player_with_displayname(
            token=token,
            display_names=[display_name],
            platform=platform,
            include_linked_portals=True
        )

        # 2) Gather all player_uuids (including linked portals).
        all_player_uuids = set()
        for display_name_dict in player_info.get("display_names", []):
            for _, player_array in display_name_dict.items():
                for player_obj in player_array:
                    main_uuid = player_obj.get("player_uuid")
                    if main_uuid:
                        all_player_uuids.add(main_uuid)
                    for lp in player_obj.get("linked_portals", []):
                        lp_uuid = lp.get("player_uuid")
                        if lp_uuid:
                            all_player_uuids.add(lp_uuid)

        combined_data = {
            "PlayerInfo": player_info,
            "PlayerStats": [],
            "PlayerRanks": [],   # (NEW) for rank data
            "MatchHistory": []
        }

        # 3) For each UUID found, fetch stats & match history, accumulate in combined_data.
        for uuid_val in all_player_uuids:
            stats_data = self.S2_fetch_player_stats(uuid_val)
            matches_data = self.S2_fetch_matches_by_player_uuid(uuid_val, max_matches=max_matches)

            combined_data["PlayerStats"].append({
                "player_uuid": uuid_val,
                "stats": stats_data
            })
            combined_data["MatchHistory"].extend(matches_data)

            # (NEW) 4) Fetch rank data
            ranks_data = self.rh_fetch_player_ranks_by_uuid(token, uuid_val)
            # The response typically includes {"player_ranks": [ ... ]}, so we grab that list
            combined_data["PlayerRanks"].extend(ranks_data.get("player_ranks", []))

        # 5) Return the consolidated structure
        return combined_data

    # -------------------------------------------------------------------------
    # DEV API: Developer Token & Methods
    # -------------------------------------------------------------------------
    def _get_dev_access_token(self) -> str:
        """
        Obtains an access token from the RallyHere Dev API using Basic Auth
        with dev_client_id (account ID) and dev_secret_key.
        """
        credentials = f"{self.dev_client_id}:{self.dev_secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

        try:
            response = requests.post(
                f'{self.dev_base_url}/api/v1/auth/token',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Basic {encoded_credentials}'
                },
                json={
                    'grant_type': 'client_credentials',
                    # Update or remove 'audience' if your API doesn't require it
                    'audience': 'your_audience_here'
                }
            )
            response.raise_for_status()
            token_data = response.json()
            return token_data['access_token']
        except requests.exceptions.RequestException as e:
            print(f'Error fetching dev access token: {e}')
            raise

    def get_items(
        self,
        sandbox_id: Optional[str] = None,
        item_ids: Optional[List[str]] = None,
        legacy_item_ids: Optional[List[int]] = None,
        types: Optional[List[str]] = None,
        coupon_currency_item_ids: Optional[List[str]] = None,
        inventory_bucket_use_rule_set_ids: Optional[List[str]] = None,
        level_xp_ids: Optional[List[str]] = None,
        name: Optional[str] = None,
        smart_search: Optional[str] = None,
        last_modified_account_ids: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        expand: Optional[List[str]] = None,
        sort_order: Optional[str] = None,
        cursor: Optional[str] = None,
        page_size: Optional[int] = None
    ) -> dict:
        """
        Retrieves a list of items from the RallyHere Dev API with various optional filters.
        """
        if sandbox_id is None:
            sandbox_id = os.getenv('RH_DEV_SANDBOX_ID')
            if not sandbox_id:
                raise ValueError("Missing sandbox_id. Provide as param or set env var RH_DEV_SANDBOX_ID.")

        access_token = self._get_dev_access_token()
        params = {}

        # Build query parameters only if provided
        if item_ids:
            params['item_ids'] = item_ids
        if legacy_item_ids:
            params['legacy_item_ids'] = legacy_item_ids
        if types:
            params['types'] = types
        if coupon_currency_item_ids:
            params['coupon_currency_item_ids'] = coupon_currency_item_ids
        if inventory_bucket_use_rule_set_ids:
            params['inventory_bucket_use_rule_set_ids'] = inventory_bucket_use_rule_set_ids
        if level_xp_ids:
            params['level_xp_ids'] = level_xp_ids
        if name:
            params['name'] = name
        if smart_search:
            params['smart_search'] = smart_search
        if last_modified_account_ids:
            params['last_modified_account_ids'] = last_modified_account_ids
        if sort_by:
            params['sort_by'] = sort_by
        if expand:
            params['expand'] = expand
        if sort_order:
            params['sort_order'] = sort_order
        if cursor:
            params['cursor'] = cursor
        if page_size:
            params['page_size'] = page_size

        try:
            response = requests.get(
                f'{self.dev_base_url}/api/v1/sandbox/{sandbox_id}/item',
                headers={'Authorization': f'Bearer {access_token}'},
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f'Error fetching items: {e}')
            raise

    def get_sandbox_kvs(self, sandbox_id: Optional[str] = None) -> List[dict]:
        """
        Retrieve all Key-Value pairs for a given Sandbox from the RallyHere Dev API.

        Endpoint:
            GET /api/v1/sandbox/:sandbox_id/kv

        Requires any of:
            - sandbox:config:view
            - sandbox:config:edit

        :param sandbox_id: (Optional) Sandbox ID. If not provided, uses env var RH_DEV_SANDBOX_ID.
        :return: A list of dictionaries, each representing a KV pair
        """
        if sandbox_id is None:
            sandbox_id = os.getenv('RH_DEV_SANDBOX_ID')
            if not sandbox_id:
                raise ValueError("Missing sandbox_id. Provide as param or set env var RH_DEV_SANDBOX_ID.")

        access_token = self._get_dev_access_token()
        try:
            response = requests.get(
                f'{self.dev_base_url}/api/v1/sandbox/{sandbox_id}/kv',
                headers={'Authorization': f'Bearer {access_token}'},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f'Error fetching KV pairs: {e}')
            raise

    def rh_fetch_player_with_displayname(
        self,
        token: str,
        display_names: List[str],
        platform: Optional[str] = None,
        identity_platform: Optional[str] = None,
        identities: Optional[List[str]] = None,
        include_linked_portals: bool = True
    ) -> dict:
        """
        Lookup one or more players by display name (and optionally by platform or identities),
        and optionally fetch their linked_portals data in one consolidated JSON.

        Endpoint:
            GET /users/v1/player

        Query Parameters:
          - display_name: string[]
            One or more display names to look up (<= 256 characters each)
          - platform: (Optional) platform to look up by
          - identity_platform: (Optional, deprecated) identity platform to look up by
          - identities: (Optional) list of portal identities to look up by
          - include_linked_portals: if True, also calls /v1/player/{player_id}/linked_portals
            for each returned player to nest that data in the final JSON.

        Responses:
          200: Returns player data that matches the query
          403: Forbidden (likely missing permission user:*)
          422: Unprocessable (invalid query parameters)

        :param token: A valid environment token (retrieved via _get_env_access_token).
        :param display_names: A list of display names to find.
        :param platform: (Optional) platform to look up by (case-sensitive: e.g., "Steam").
        :param identity_platform: (Optional) identity platform to look up by (deprecated).
        :param identities: (Optional) list of identities to look up by.
        :param include_linked_portals: set to True to also fetch each player's linked portals.
        :return: A dictionary containing player data (display_names, identity_platforms, etc.),
                 with nested "linked_portals" if requested.
        """
        # Step 1: Call the main endpoint to find players by display name / platform
        url = f"{self.env_base_url}/users/v1/player"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        params = {}
        if display_names:
            params["display_name"] = display_names
        if platform:
            params["platform"] = platform
        if identity_platform:
            params["identity_platform"] = identity_platform
        if identities:
            params["identities"] = identities

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        base_result = response.json()

        # If we do not want the linked portals, just return what we got
        if not include_linked_portals:
            return base_result

        # Step 2: For each player in the "display_names" array, also fetch linked portals
        #         Then nest that data in the returned structure.
        # The base_result typically looks like:
        # {
        #   "display_names": [
        #       { "Weak3n": [
        #           { "player_id": 123, "player_uuid": "..." },
        #           ...
        #         ]
        #       }
        #     ]
        #   }
        # We'll iterate over each player, call /v1/player/{player_id}/linked_portals, 
        # and attach that field to the entry in base_result.

        # Helper method to fetch linked portals for a single player_id
        def _fetch_linked_portals(pid: int) -> list:
            linked_url = f"{self.env_base_url}/users/v1/player/{pid}/linked_portals"
            resp = requests.get(linked_url, headers=headers)
            resp.raise_for_status()
            portals_json = resp.json()
            # Typically returns something like { "linked_portals": [ {...}, ... ] }
            return portals_json.get("linked_portals", [])

        display_names_list = base_result.get("display_names", [])
        for display_name_dict in display_names_list:
            # each dict is something like  { "Weak3n": [ {...player...}, {...} ] }
            for key, player_array in display_name_dict.items():
                # player_array is [ { player_id: 123, player_uuid: ... }, ... ]
                for player_obj in player_array:
                    pid = player_obj.get("player_id")
                    if pid is not None:
                        # fetch linked portals
                        try:
                            lp = _fetch_linked_portals(pid)
                            # attach to our original data structure
                            player_obj["linked_portals"] = lp
                        except requests.exceptions.RequestException as e:
                            # If there's an error (e.g., 403), you can decide how to handle it
                            # For now we just put an empty list or store an error note
                            player_obj["linked_portals"] = []
                            player_obj["linked_portals_error"] = str(e)

        return base_result

    def rh_fetch_player_setting(
        self,
        token: str,
        player_uuid: str,
        setting_type_id: str,
        key: str,
        if_match: Optional[str] = None,
        if_none_match: Optional[str] = None,
        if_modified_since: Optional[str] = None,
        if_unmodified_since: Optional[str] = None
    ) -> dict:
        """
        Fetch a single player setting document from RallyHere Environment API.

        Endpoint:
            GET /settings/v2/player/{player_uuid}/setting_type/{setting_type_id}/key/{key}

        Required Permissions:
          - Any of: setting:*:*, setting:read
          - For the player themselves: setting:read:self

        :param token: A valid environment token (retrieved via _get_env_access_token).
        :param player_uuid: The target player's UUID.
        :param setting_type_id: The type of setting to retrieve (must be a known valid type).
        :param key: The specific key within that setting type to fetch.
        :param if_match: (Optional) If-Match header for conditional requests based on ETag. 
        :param if_none_match: (Optional) If-None-Match header for conditional requests based on ETag.
        :param if_modified_since: (Optional) If-Modified-Since header for conditional requests by date (ignored if if_none_match is provided).
        :param if_unmodified_since: (Optional) If-Unmodified-Since header for conditional requests by date (ignored if if_match is provided).
        :return: A dictionary representing the fetched player setting. If the server returns 304 (Not Modified),
                 we return a dict with {"not_modified": True}, otherwise we return the JSON body from the server.

        Possible Server Status Codes:
          200: Success - returns JSON with v, value, etag, last_modified, etc.
          304: Not Modified (if the conditions specified in If-None-Match or If-Modified-Since apply)
          400, 403, 404, 412, 422: Various errors (permissions, missing data, etc.)
        """
        url = f"{self.env_base_url}/settings/v2/player/{player_uuid}/setting_type/{setting_type_id}/key/{key}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }

        # Add optional conditional headers if provided
        if if_match:
            headers["If-Match"] = if_match
        if if_none_match:
            headers["If-None-Match"] = if_none_match
        if if_modified_since:
            headers["If-Modified-Since"] = if_modified_since
        if if_unmodified_since:
            headers["If-Unmodified-Since"] = if_unmodified_since

        response = requests.get(url, headers=headers)

        # If the resource hasn't changed since the provided condition (If-None-Match or If-Modified-Since),
        # RallyHere may respond with 304 Not Modified. This isn't an error code, so requests won't raise,
        # but we can handle it as a special case:
        if response.status_code == 304:
            # No new data changed
            return {"not_modified": True}

        # For other codes (200, 4xx, 5xx), let's raise if it's an error:
        response.raise_for_status()

        return response.json()

    def rh_fetch_player_settings_all(
        self,
        token: str,
        player_uuid: str,
        setting_type_id: str,
        keys: Optional[List[str]] = None,
        if_match: Optional[str] = None,
        if_none_match: Optional[str] = None,
        if_modified_since: Optional[str] = None,
        if_unmodified_since: Optional[str] = None
    ) -> dict:
        """
        Get all player setting documents for a specific Setting Type from the RallyHere Environment API.

        Endpoint:
            GET /settings/v2/player/{player_uuid}/setting_type/{setting_type_id}/key

        Required Permissions:
          - Any of: setting:*:*, setting:read
          - For the player themselves: setting:read:self

        Path Parameters:
          - player_uuid: The target player's UUID (required).
          - setting_type_id: The setting type to retrieve (must be a known valid type).

        Query Parameters:
          - key: (Optional) List of setting keys to fetch. If not provided, all settings under the setting_type_id
                 will be returned. Each key must be non-empty and <= 256 characters.

        Conditional Headers:
          - if_match: (Optional) If-Match header for conditional requests based on ETag.
          - if_none_match: (Optional) If-None-Match header for conditional requests based on ETag.
          - if_modified_since: (Optional) If-Modified-Since header for conditional requests by date (ignored if if_none_match is provided).
          - if_unmodified_since: (Optional) If-Unmodified-Since header for conditional requests by date (ignored if if_match is provided).

        Response:
          - 200: Success. Returns a dictionary of key -> setting data (v, value, etag, last_modified, etc.).
          - 304: Not Modified (if conditions specified in If-None-Match/If-Modified-Since apply). Returns {"not_modified": True}.
          - 400, 403, 404, 412, 422: Errors (permissions, missing data, etc.).

        :param token: A valid environment token (retrieved via _get_env_access_token).
        :param player_uuid: The target player's UUID.
        :param setting_type_id: The type of setting to retrieve.
        :param keys: Optional list of specific keys. If not provided, all keys will be returned.
        :param if_match: (Optional) ETag check. Only proceed if the resource's ETag matches.
        :param if_none_match: (Optional) ETag check. Only proceed if the resource's ETag does not match.
        :param if_modified_since: (Optional) Only proceed if resource was modified after this date/time.
        :param if_unmodified_since: (Optional) Only proceed if resource was unmodified after this date/time.
        :return: A dictionary containing the requested settings (key -> dict).
                 If 304, returns {"not_modified": True}.
        """
        url = f"{self.env_base_url}/settings/v2/player/{player_uuid}/setting_type/{setting_type_id}/key"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }

        # Add optional conditional headers if provided
        if if_match:
            headers["If-Match"] = if_match
        if if_none_match:
            headers["If-None-Match"] = if_none_match
        if if_modified_since:
            headers["If-Modified-Since"] = if_modified_since
        if if_unmodified_since:
            headers["If-Unmodified-Since"] = if_unmodified_since

        # Build query params if keys are passed
        # The endpoint expects repeated "key" params (i.e. ?key=A&key=B).
        params = {}
        if keys:
            params["key"] = keys

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 304:
            return {"not_modified": True}

        response.raise_for_status()
        return response.json()

    def rh_fetch_player_ranks_by_uuid(
        self,
        token: str,
        player_uuid: str
    ) -> dict:
        """
        Fetch all of a specific player's ranks from the RallyHere Environment API,
        then:
          1) Call the Rank Config V3 endpoint for each rank_id to enrich the data
             with 'rank_name' and 'rank_description'.
          2) Call the single rank V2 endpoint (/rank/v2/player/{player_uuid}/rank/{rank_id})
             to retrieve 'custom_data' for each rank.

        Endpoint Workflow:
          a) GET /rank/v2/player/{player_uuid}/rank               (list of ranks)
          b) For each rank_id, GET /rank/v3/rank/{rank_id}        (rank's config)
          c) For each rank_id, GET /rank/v2/player/{player_uuid}/rank/{rank_id}  (custom_data)

        Required Permissions:
          - rank:read:self for the player themselves, or rank:read:any otherwise
          - rank:read:config for fetching rank metadata

        :param token: A valid environment token (retrieved via _get_env_access_token).
        :param player_uuid: The UUID of the player.
        :return: The JSON object with "player_ranks", enriched with:
                 - rank_name
                 - rank_description
                 - rank["custom_data"] from the single rank endpoint
                 Example structure:
                 {
                     "player_ranks": [
                         {
                             "player_uuid": "...",
                             "rank_id": "...",
                             "rank": {
                                 "mu": ...,
                                 "sigma": ...,
                                 "custom_data": {...}
                             },
                             "rank_name": "...",
                             "rank_description": "..."
                         },
                         ...
                     ]
                 }
        """
        # Step 1a: Fetch the player's rank list from /rank/v2/player/{player_uuid}/rank
        list_url = f"{self.env_base_url}/rank/v2/player/{player_uuid}/rank"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        list_resp = requests.get(list_url, headers=headers)
        list_resp.raise_for_status()

        data = list_resp.json()  # Expected shape: {"player_ranks": [...]}
        player_ranks = data.get("player_ranks", [])

        # Step 1b & 1c: For each rank_id in the rank list, fetch config (rank_name, rank_description)
        # and also fetch single-rank data (custom_data).
        for rank_obj in player_ranks:
            rank_id = rank_obj.get("rank_id")
            if rank_id:
                # -- b) Rank Config V3 for the name / description
                config_url = f"{self.env_base_url}/rank/v3/rank/{rank_id}"
                config_resp = requests.get(config_url, headers=headers)
                config_resp.raise_for_status()
                config_data = config_resp.json()
                configs_list = config_data.get("rank_configs", [])
                if configs_list:
                    rank_info = configs_list[0]
                    rank_obj["rank_name"] = rank_info.get("name")
                    rank_obj["rank_description"] = rank_info.get("description")
                else:
                    rank_obj["rank_name"] = "<no_config>"
                    rank_obj["rank_description"] = "<no_config>"

                # -- c) Single Rank V2 for custom_data
                single_rank_url = f"{self.env_base_url}/rank/v2/player/{player_uuid}/rank/{rank_id}"
                single_resp = requests.get(single_rank_url, headers=headers)
                single_resp.raise_for_status()
                single_data = single_resp.json()  # shape: {"player_ranks": [ { ... } ]}

                sr_list = single_data.get("player_ranks", [])
                if sr_list:
                    # Typically only one rank object in this array
                    detailed_rank_obj = sr_list[0]
                    # Merge in the "custom_data" if it exists
                    if "rank" in detailed_rank_obj and "custom_data" in detailed_rank_obj["rank"]:
                        # Ensure our original rank_obj["rank"] is a dict
                        rank_obj.setdefault("rank", {})
                        rank_obj["rank"]["custom_data"] = detailed_rank_obj["rank"].get("custom_data", {})

        # Step 2: Return the enriched rank data
        return data

    def get_all_org_products(self, org_identifier: str) -> List[dict]:
        """
        Retrieves all products for a given organization from the RallyHere Dev API.

        Endpoint:
            GET /api/v1/org/:org_identifier/product

        Required Permission:
            - org:config:view

        :param org_identifier: The ID or short name of the organization.
        :return: A list of product dictionaries, each containing fields such as
                 product_id, org_id, name, short_name, unique_name, etc.
        :raises ValueError: If org_identifier is invalid or missing.
        :raises RequestException: If an error occurs while making the request.
        """
        if not org_identifier:
            raise ValueError("Missing org_identifier. Provide the organization ID or short name.")

        access_token = self._get_dev_access_token()
        try:
            response = requests.get(
                f"{self.dev_base_url}/api/v1/org/{org_identifier}/product",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching org products: {e}")
            raise

    def get_all_sandboxes_for_product(self) -> List[dict]:
        """
        Retrieves all sandboxes for a given product from the RallyHere Dev API.

        Endpoint:
            GET /api/v1/org/:org_identifier/product/:product_identifier/sandboxes

        Required Permissions:
            - product:config:view or product:config:edit

        The ORG_IDENTIFIER and PRODUCT_ID are expected to be set in environment variables:
            RH_DEV_ORG_ID and RH_DEV_PRODUCT_ID

        :return: A list of sandbox dictionaries, each containing fields like sandbox_id,
                 product_id, short_name, name, archive, readonly, etc.
        :raises ValueError: If environment variables are missing or invalid.
        :raises RequestException: If an error occurs while making the request.
        """
        org_identifier = os.getenv("RH_DEV_ORG_ID")
        product_identifier = os.getenv("RH_DEV_PRODUCT_ID")

        if not org_identifier:
            raise ValueError("Missing environment variable RH_DEV_ORG_ID.")
        if not product_identifier:
            raise ValueError("Missing environment variable RH_DEV_PRODUCT_ID.")

        access_token = self._get_dev_access_token()
        try:
            url = f"{self.dev_base_url}/api/v1/org/{org_identifier}/product/{product_identifier}/sandboxes"
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching product sandboxes: {e}")
            raise

    def rh_fetch_matches_by_time_range(
        self, 
        token: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
        region_id: Optional[str] = None,
        game_mode: Optional[str] = None,
        limit: int = 10,
        page_size: int = 10,
        status: str = "closed",
        callback: Optional[callable] = None,
        filters: Optional[List[MatchFilter]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch matches within a specified time range with filtering options.
        
        Args:
            token: A valid environment token.
            start_time: Optional start time in ISO 8601 format (e.g., "2023-01-01T00:00:00Z").
            end_time: Optional end time in ISO 8601 format.
            min_duration: Optional minimum match duration in seconds.
            max_duration: Optional maximum match duration in seconds.
            region_id: Optional region ID filter (e.g., "1", "2").
            game_mode: Optional game mode filter (e.g., "Conquest", "Arena").
            limit: Maximum number of matches to return (default: 10, use 0 for all).
            page_size: Number of matches per page (default: 10).
            status: Match status filter (default: "closed").
            callback: Optional callback function(matches_so_far, count) for progress updates.
            filters: Optional list of additional MatchFilter objects to apply.
            
        Returns:
            A list of match dictionaries.
            
        Note:
            The server API doesn't directly support all filters, so some are applied client-side.
        """
        url = f"{self.env_base_url}/match/v1/match"
        params = {"page_size": page_size, "status": status}
        
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
            
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        # Combine standard filters with custom filters
        all_filters = []
        
        if min_duration is not None or max_duration is not None:
            all_filters.append(DurationFilter(min_duration, max_duration))
        
        if region_id is not None:
            all_filters.append(RegionFilter(region_id))
            
        if game_mode is not None:
            all_filters.append(GameModeFilter(game_mode))
            
        # Add custom filters
        if filters:
            all_filters.extend(filters)
        
        all_matches = []
        matches_processed = 0
        cursor = None
        no_limit = (limit == 0)
        
        # Fetch matches with pagination
        while no_limit or matches_processed < limit:
            if cursor:
                params["cursor"] = cursor
                
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                matches = data.get("matches", [])
                if not matches:
                    break
                    
                # Apply all filters
                filtered_matches = self._apply_filters(matches, all_filters)
                
                all_matches.extend(filtered_matches)
                matches_processed += len(matches)  # Count original matches for pagination
                
                # Call the callback if provided
                if callback and filtered_matches:
                    callback(all_matches, len(all_matches))
                
                # Get the next page cursor
                cursor = data.get("cursor")
                if not cursor:
                    break
                    
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error fetching matches: {e}")
                # Add a longer delay after an error
                time.sleep(1)
                break
        
        # Apply limit if specified
        if limit > 0:
            return all_matches[:limit]
        return all_matches
    
    def _apply_filters(self, matches: List[Dict[str, Any]], filters: List[MatchFilter]) -> List[Dict[str, Any]]:
        """
        Apply all filters to a list of matches.
        
        Args:
            matches: List of match dictionaries to filter.
            filters: List of MatchFilter objects to apply.
            
        Returns:
            A list of filtered match dictionaries.
        """
        if not filters:
            return matches
            
        filtered = []
        for match in matches:
            # A match passes if it passes all filters
            if all(filter_obj.apply(match) for filter_obj in filters):
                filtered.append(match)
                
        return filtered
    
    def _filter_matches(
        self,
        matches: List[dict],
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
        region_id: Optional[str] = None,
        game_mode: Optional[str] = None
    ) -> List[dict]:
        """
        Legacy method to filter matches by various criteria.
        This is kept for backward compatibility.
        """
        filters = []
        
        if min_duration is not None or max_duration is not None:
            filters.append(DurationFilter(min_duration, max_duration))
            
        if region_id is not None:
            filters.append(RegionFilter(region_id))
            
        if game_mode is not None:
            filters.append(GameModeFilter(game_mode))
            
        return self._apply_filters(matches, filters)
        
    def rh_fetch_match_by_id(
        self,
        match_id: str,
        token: str
    ) -> dict:
        """
        Fetch a single match by its ID.
        
        Args:
            match_id: The UUID of the match.
            token: A valid environment token.
            
        Returns:
            A dictionary containing the match details.
            
        Raises:
            requests.exceptions.HTTPError: If the request fails.
            FileNotFoundError: If the match doesn't exist.
        """
        url = f"{self.env_base_url}/match/v1/match/{match_id}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            raise FileNotFoundError(f"Match with ID {match_id} not found")
            
        response.raise_for_status()
        return response.json()
    
    def S2_fetch_matches_by_time_range(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 10,
        page_size: int = 10,
        status: str = "closed"
    ) -> list:
        """
        Fetch and transform matches within a specified time range into SMITE 2 format.
        
        This method calls rh_fetch_matches_by_time_range and transforms the results
        into a SMITE 2 friendly format.
        
        Args:
            start_time: ISO 8601 formatted timestamp for the start of the time range (e.g., "2025-04-20T00:00:00Z").
            end_time: ISO 8601 formatted timestamp for the end of the time range (e.g., "2025-04-22T23:59:59Z").
            limit: Maximum total number of matches to return.
            page_size: Number of matches to return per page (default: 10).
            status: Match status to filter by (default: "closed").
            
        Returns:
            A list of matches in SMITE 2 format.
            
        Raises:
            requests.exceptions.HTTPError: If the request fails.
            ValueError: If provided parameters are invalid.
        """
        token = self._get_env_access_token()
        
        raw_matches = self.rh_fetch_matches_by_time_range(
            token=token,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            page_size=page_size,
            status=status
        )
        
        # Transform the raw matches data
        s2_matches = self.S2_transform_matches_by_instance(raw_matches)
        
        return s2_matches
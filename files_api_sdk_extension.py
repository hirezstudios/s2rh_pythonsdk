"""
Draft implementation of RallyHere Files API methods for the Smite2RallyHereSDK.

This file contains the methods that would be added to the SDK to support accessing match files.
"""
import os
import requests
from typing import Optional, List, Dict, Union, BinaryIO

class FileApiMethods:
    """
    These methods would be integrated into the Smite2RallyHereSDK class.
    They provide functionality for accessing files through the RallyHere Files API.
    """
    
    def rh_get_entity_directory_info(
        self,
        token: str,
        file_type: str = "file",
        entity_type: str = "match"
    ) -> dict:
        """
        Get information about an entity type's storage container.
        
        Note: This is resource intensive, use sparingly.
        
        Args:
            token: A valid environment token.
            file_type: Type of file. Options are 'file' or 'developer-file'.
            entity_type: Type of entity. Options are 'match' or 'unknown'.
            
        Returns:
            A dictionary containing information about the entity directory, including:
            - total_files: Total number of files
            - total_size_bytes: Total size in bytes
            - total_size_mb: Total size in megabytes
            
        Raises:
            requests.exceptions.HTTPError: If the request fails.
            ValueError: If invalid parameters are provided.
        """
        if file_type not in ["file", "developer-file"]:
            raise ValueError("file_type must be 'file' or 'developer-file'")
        
        if entity_type not in ["match", "unknown"]:
            raise ValueError("entity_type must be 'match' or 'unknown'")
            
        url = f"{self.env_base_url}/file/v1/{file_type}/{entity_type}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses
        
        return response.json()
    
    def rh_check_match_exists(
        self,
        match_id: str,
        token: str
    ) -> bool:
        """
        Check if a match exists in the RallyHere system.
        
        Args:
            match_id: The UUID of the match to check.
            token: A valid environment token.
            
        Returns:
            True if the match exists, False otherwise.
        """
        url = f"{self.env_base_url}/match/v1/match/{match_id}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers)
        
        return response.status_code == 200
    
    def rh_list_match_files(
        self,
        match_id: str,
        token: str,
        file_type: str = "file"
    ) -> List[dict]:
        """
        List all files available for a specific match.
        
        Args:
            match_id: The UUID of the match.
            token: A valid environment token.
            file_type: Type of file. Options are 'file' or 'developer-file'.
            
        Returns:
            A list of dictionaries, each containing information about a file:
            - name: The file name
            - size: Size in bytes
            - content_type: The MIME type of the file
            - created_timestamp: When the file was created
            
        Raises:
            requests.exceptions.HTTPError: If the request fails.
            FileNotFoundError: If the match doesn't exist.
        """
        # Check if match exists first to provide a better error message
        if not self.rh_check_match_exists(match_id, token):
            raise FileNotFoundError(f"Match with ID {match_id} not found")
            
        # Based on our exploration, this is the correct endpoint to list files
        url = f"{self.env_base_url}/file/v1/{file_type}/match/{match_id}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers)
        
        # Handle specific error codes
        if response.status_code != 200:
            response.raise_for_status()
            
        # The response is a dictionary with a "files" array
        data = response.json()
        return data.get("files", [])
    
    def rh_download_match_file(
        self,
        match_id: str,
        file_name: str,
        token: str,
        output_path: Optional[str] = None,
        file_type: str = "file"
    ) -> str:
        """
        Download a specific file for a match.
        
        Args:
            match_id: The UUID of the match.
            file_name: The name of the file to download (e.g., 'CombatLog_<session_id>.log').
            token: A valid environment token.
            output_path: Optional path where the file will be saved. If None, a path will be generated.
            file_type: Type of file. Options are 'file' or 'developer-file'.
            
        Returns:
            The path where the file was saved.
            
        Raises:
            requests.exceptions.HTTPError: If the request fails.
            FileNotFoundError: If the match or file doesn't exist.
            IOError: If there's an issue writing the file.
        """
        # Construct the URL for the file - based on our exploration, this is the correct pattern
        url = f"{self.env_base_url}/file/v1/{file_type}/match/{match_id}/{file_name}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers, stream=True)
        
        # Handle specific error codes
        if response.status_code == 404:
            error_text = ""
            try:
                error_data = response.json()
                error_text = error_data.get("desc", "")
            except:
                error_text = response.text
            
            if "file_not_found" in response.text or "File not found" in error_text:
                raise FileNotFoundError(f"File {file_name} not found for match {match_id}")
            else:
                response.raise_for_status()
        elif response.status_code != 200:
            response.raise_for_status()
            
        # Determine where to save the file
        if output_path is None:
            # Create default directory if it doesn't exist
            os.makedirs("match_files", exist_ok=True)
            output_path = os.path.join("match_files", file_name)
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
        # Save the file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return output_path
    
    def S2_get_match_logs(
        self,
        match_id: str,
        output_dir: Optional[str] = None,
        file_types: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        High-level function to fetch all log files for a match.
        
        This is a convenience function that:
        1. Gets an environment token
        2. Lists all files available for the match (from both file types)
        3. Downloads each file
        
        Args:
            match_id: The UUID of the match.
            output_dir: Optional directory where files will be saved. If None, 'match_files/{match_id}' will be used.
            file_types: Optional list of file types to search. If None, will search both 'file' and 'developer-file'.
            
        Returns:
            A dictionary mapping file names to their saved paths.
            
        Raises:
            requests.exceptions.HTTPError: If the request fails.
            FileNotFoundError: If the match doesn't exist.
            IOError: If there's an issue writing the files.
        """
        # Get token
        token = self._get_env_access_token()
        
        # Set output directory
        if output_dir is None:
            output_dir = os.path.join("match_files", match_id)
            
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Determine which file types to search
        if file_types is None:
            file_types = ["file", "developer-file"]
        
        downloaded_files = {}
        
        # Search each file type
        for file_type in file_types:
            try:
                # Get the list of files for this file type
                files = self.rh_list_match_files(match_id, token, file_type)
                
                # Download each file
                for file_info in files:
                    file_name = file_info.get("name")
                    if file_name:
                        try:
                            output_path = os.path.join(output_dir, file_name)
                            self.rh_download_match_file(match_id, file_name, token, output_path, file_type)
                            downloaded_files[file_name] = output_path
                        except Exception as e:
                            print(f"Error downloading {file_name} from {file_type}: {e}")
            except Exception as e:
                print(f"Error listing files for {file_type}: {e}")
                
        return downloaded_files
    
    def S2_get_match_combat_log(
        self,
        match_id: str,
        output_dir: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Download the combat log for a specific match.
        
        Combat logs are found in the 'file' type.
        If session_id is provided, will attempt to find a combat log containing that session_id.
        Otherwise, will return the first combat log found.
        
        Args:
            match_id: The UUID of the match.
            output_dir: Optional directory where files will be saved. If None, 'match_files/{match_id}' will be used.
            session_id: Optional session ID. If provided, will be used to filter files.
            
        Returns:
            Path to the downloaded combat log file, or None if not found.
            
        Raises:
            requests.exceptions.HTTPError: If the request fails.
            FileNotFoundError: If the match doesn't exist.
            IOError: If there's an issue writing the file.
        """
        # Get token
        token = self._get_env_access_token()
        
        # Set output directory
        if output_dir is None:
            output_dir = os.path.join("match_files", match_id)
            
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Combat logs are found in the 'file' type
        file_type = "file"
        
        # Always list the files first to find the appropriate combat log
        try:
            files = self.rh_list_match_files(match_id, token, file_type)
            
            # Filter for combat logs
            combat_logs = [f for f in files if f.get("name", "").lower().startswith("combatlog_")]
            
            if not combat_logs:
                print(f"No combat logs found for match {match_id}")
                return None
            
            # If session_id is provided, try to find a match
            if session_id:
                matching_logs = [f for f in combat_logs if session_id in f.get("name", "")]
                if matching_logs:
                    selected_log = matching_logs[0]
                else:
                    print(f"No combat logs matching session ID {session_id} found. Using first available combat log.")
                    selected_log = combat_logs[0]
            else:
                selected_log = combat_logs[0]
            
            # Download the selected combat log
            file_name = selected_log.get("name")
            output_path = os.path.join(output_dir, file_name)
            self.rh_download_match_file(match_id, file_name, token, output_path, file_type)
            return output_path
            
        except Exception as e:
            print(f"Error getting combat log: {e}")
        
        return None
    
    def S2_get_match_chat_log(
        self,
        match_id: str,
        session_id: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        Download the chat log for a specific match.
        
        Chat logs are found in the 'developer-file' type.
        If session_id is provided, will attempt to find a chat log containing that session_id.
        Otherwise, will return the first chat log found.
        
        Args:
            match_id: The UUID of the match.
            session_id: Optional session ID. If provided, will be used to filter files.
            output_dir: Optional directory where files will be saved. If None, 'match_files/{match_id}' will be used.
            
        Returns:
            Path to the downloaded chat log file, or None if not found.
            
        Raises:
            requests.exceptions.HTTPError: If the request fails.
            FileNotFoundError: If the match doesn't exist.
            IOError: If there's an issue writing the file.
        """
        # Get token
        token = self._get_env_access_token()
        
        # Set output directory
        if output_dir is None:
            output_dir = os.path.join("match_files", match_id)
            
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Chat logs are found in the 'developer-file' type
        file_type = "developer-file"
        
        # Always list the files first to find the appropriate chat log
        try:
            files = self.rh_list_match_files(match_id, token, file_type)
            
            # Filter for chat logs
            chat_logs = [f for f in files if f.get("name", "").lower().startswith("chatlog_")]
            
            if not chat_logs:
                print(f"No chat logs found for match {match_id}")
                return None
            
            # If session_id is provided, try to find a match
            if session_id:
                matching_logs = [f for f in chat_logs if session_id in f.get("name", "")]
                if matching_logs:
                    selected_log = matching_logs[0]
                else:
                    print(f"No chat logs matching session ID {session_id} found. Using first available chat log.")
                    selected_log = chat_logs[0]
            else:
                selected_log = chat_logs[0]
            
            # Download the selected chat log
            file_name = selected_log.get("name")
            output_path = os.path.join(output_dir, file_name)
            self.rh_download_match_file(match_id, file_name, token, output_path, file_type)
            return output_path
            
        except Exception as e:
            print(f"Error getting chat log: {e}")
        
        return None

    def S2_get_match_files_by_type(
        self,
        match_id: str,
        file_types: Union[str, List[str]] = "All",
        session_id: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Download specific types of match files using user-friendly names.
        
        This method allows specifying files by category names instead of exact filenames.
        Available categories:
        - "All": All available files
        - "ChatLog": Chat log files
        - "CombatLog": Combat log files
        - "Diagnostics": Diagnostic JSON files
        - "ServerLog": Server log files (typically named Inst_*)
        - "PEX_Summary": Performance summary JSON
        - "PEX_Timeline": Performance timeline CSV
        
        Args:
            match_id: The UUID of the match.
            file_types: Either "All" or a list of file type names to download.
            session_id: Optional session ID to help filter relevant files.
            output_dir: Optional directory where files will be saved. If None, 'match_files/{match_id}' will be used.
            
        Returns:
            A dictionary mapping file names to their saved paths.
            
        Raises:
            requests.exceptions.HTTPError: If the request fails.
            FileNotFoundError: If the match doesn't exist.
            IOError: If there's an issue writing the files.
            ValueError: If an invalid file type is specified.
        """
        # Get token
        token = self._get_env_access_token()
        
        # Set output directory
        if output_dir is None:
            output_dir = os.path.join("match_files", match_id)
            
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Define mapping between friendly names and file patterns
        file_type_patterns = {
            "ChatLog": {
                "api_type": "developer-file",
                "pattern": lambda name: name.lower().startswith("chatlog_")
            },
            "CombatLog": {
                "api_type": "file",
                "pattern": lambda name: name.lower().startswith("combatlog_")
            },
            "Diagnostics": {
                "api_type": "developer-file",
                "pattern": lambda name: name.lower().startswith("diagnostics_")
            },
            "ServerLog": {
                "api_type": "developer-file",
                "pattern": lambda name: name.lower().startswith("inst_")
            },
            "PEX_Summary": {
                "api_type": "developer-file",
                "pattern": lambda name: name.lower().startswith("pex_summary_")
            },
            "PEX_Timeline": {
                "api_type": "developer-file",
                "pattern": lambda name: name.lower().startswith("pex_timeline_")
            },
        }
        
        # Validate file types
        if isinstance(file_types, str):
            if file_types != "All" and file_types not in file_type_patterns:
                raise ValueError(f"Invalid file type: {file_types}. Must be 'All' or one of {list(file_type_patterns.keys())}")
            file_types_list = list(file_type_patterns.keys()) if file_types == "All" else [file_types]
        else:
            for ft in file_types:
                if ft not in file_type_patterns:
                    raise ValueError(f"Invalid file type: {ft}. Must be one of {list(file_type_patterns.keys())}")
            file_types_list = file_types
            
        # Collect all required API types
        api_types_needed = set()
        for ft in file_types_list:
            api_types_needed.add(file_type_patterns[ft]["api_type"])
        
        # Download files
        downloaded_files = {}
        all_files = {}
        
        # Get files from each needed API type
        for api_type in api_types_needed:
            try:
                files = self.rh_list_match_files(match_id, token, api_type)
                for file_info in files:
                    file_name = file_info.get("name", "")
                    if file_name:
                        # Store by API type for easier filtering later
                        if api_type not in all_files:
                            all_files[api_type] = []
                        all_files[api_type].append(file_info)
            except Exception as e:
                print(f"Error listing files for {api_type}: {e}")
        
        # Filter and download files by requested type
        for file_type in file_types_list:
            pattern_info = file_type_patterns[file_type]
            api_type = pattern_info["api_type"]
            pattern_func = pattern_info["pattern"]
            
            if api_type in all_files:
                matching_files = [f for f in all_files[api_type] if pattern_func(f.get("name", ""))]
                
                # If session_id is provided, try to find files matching that session
                if session_id and len(matching_files) > 1:
                    session_matches = [f for f in matching_files if session_id in f.get("name", "")]
                    if session_matches:
                        matching_files = session_matches
                
                # Download all matching files
                for file_info in matching_files:
                    file_name = file_info.get("name", "")
                    try:
                        output_path = os.path.join(output_dir, file_name)
                        self.rh_download_match_file(match_id, file_name, token, output_path, api_type)
                        downloaded_files[file_name] = output_path
                        print(f"Downloaded {file_type}: {file_name}")
                    except Exception as e:
                        print(f"Error downloading {file_name}: {e}")
        
        if not downloaded_files:
            print(f"No matching files found for the requested types: {file_types_list}")
            
        return downloaded_files

    def S2_get_filtered_match_files(
        self,
        token: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 10,
        page_size: int = 10,
        status: str = "closed",
        region_id: Optional[str] = None,
        map_name: Optional[str] = None,
        game_mode: Optional[str] = None,
        host_type: Optional[str] = None,
        file_types: Union[str, List[str]] = "All",
        output_dir: Optional[str] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Fetch matches within a time range, filter them by instance properties,
        and download their files.
        
        Args:
            token: Optional access token. If None, one will be obtained automatically.
            start_time: Optional ISO 8601 formatted start time.
            end_time: Optional ISO 8601 formatted end time.
            limit: Maximum number of matches to process (default: 10).
            page_size: Page size for match API calls (default: 10).
            status: Match status to filter by (default: "closed").
            region_id: Optional region ID to filter matches by.
            map_name: Optional map name to filter matches by.
            game_mode: Optional game mode to filter matches by.
            host_type: Optional host type to filter matches by.
            file_types: Types of files to download. See S2_get_match_files_by_type.
            output_dir: Base output directory for downloaded files.
            
        Returns:
            A dictionary mapping match IDs to dictionaries of file names and paths.
            
        Raises:
            requests.exceptions.HTTPError: If any API request fails.
        """
        # Get token if not provided
        if token is None:
            token = self._get_env_access_token()
            
        # First, fetch matches by time range
        url = f"{self.env_base_url}/match/v1/match"
        params = {
            "page_size": page_size,
            "status": status
        }
        
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
            
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        all_matches = []
        matches_processed = 0
        cursor = None
        
        while matches_processed < limit:
            if cursor:
                params["cursor"] = cursor
                
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            matches = data.get("matches", [])
            if not matches:
                break
                
            all_matches.extend(matches)
            matches_processed += len(matches)
            
            cursor = data.get("cursor")
            if not cursor:
                break
                
        # Apply filters to the matches
        filtered_matches = []
        
        for match in all_matches:
            # Extract instances data
            instances = match.get("instances", [])
            if not instances:
                continue
                
            # Use the first instance for filtering (typically there's only one)
            instance = instances[0]
            
            # Check if the match meets all filter criteria
            if region_id and instance.get("region_id") != region_id:
                continue
                
            if map_name and instance.get("map") != map_name:
                continue
                
            if game_mode:
                instance_game_mode = instance.get("game_mode", "")
                if game_mode not in instance_game_mode:
                    continue
                    
            if host_type and instance.get("host_type") != host_type:
                continue
                
            # If we reach here, the match has passed all filters
            filtered_matches.append(match)
            
            # Respect the original limit
            if len(filtered_matches) >= limit:
                break
                
        print(f"Found {len(filtered_matches)} matches after filtering")
        
        # Download files for each filtered match
        result = {}
        
        for match in filtered_matches:
            match_id = match.get("match_id")
            if not match_id:
                continue
                
            # Get session_id if available for better file filtering
            session_id = None
            sessions = match.get("sessions", [])
            if sessions and len(sessions) > 0:
                session_id = sessions[0].get("session_id")
                
            # Set up match-specific output directory
            match_output_dir = output_dir
            if output_dir:
                match_output_dir = os.path.join(output_dir, match_id)
                
            # Download files for this match
            try:
                downloaded_files = self.S2_get_match_files_by_type(
                    match_id=match_id,
                    file_types=file_types,
                    session_id=session_id,
                    output_dir=match_output_dir
                )
                
                if downloaded_files:
                    result[match_id] = downloaded_files
                    
            except Exception as e:
                print(f"Error downloading files for match {match_id}: {e}")
                
        return result

# Implementation notes:
# 1. These methods would be integrated into the Smite2RallyHereSDK class.
# 2. Error handling should be consistent with the rest of the SDK.
# 3. The Files API requires appropriate permissions in the token.
# 4. The file_type parameter is included for flexibility, but 'file' seems to be the most common.
# 5. We've added a specific method for combat logs based on our findings.
# 6. The API pattern we've confirmed is:
#    - GET /file/v1/{file_type}/match/{match_id} to list files
#    - GET /file/v1/{file_type}/match/{match_id}/{file_name} to download a file 
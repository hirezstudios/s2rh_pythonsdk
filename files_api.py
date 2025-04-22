import os
import re
import requests
from typing import List, Dict, Optional, Union, Any, BinaryIO, Set, Callable
from enum import Enum, auto
import time
from concurrent.futures import ThreadPoolExecutor

class FileTypeConstants:
    """Constants for file types supported by the Files API."""
    
    # File types
    COMBAT_LOG = "COMBAT_LOG"
    CHAT_LOG = "CHAT_LOG"
    CONSOLE_LOG = "CONSOLE_LOG"
    GAME_SESSION_SUMMARY = "GAME_SESSION_SUMMARY"
    MATCH_SUMMARY = "MATCH_SUMMARY"
    SERVER_METADATA = "SERVER_METADATA"

    # API source types
    SOURCE_TYPE_MATCH = "MATCH"
    SOURCE_TYPE_SESSION = "SESSION"
    SOURCE_TYPE_INSTANCE = "INSTANCE"
    
    # API endpoints
    ENDPOINT_FILE = "file"
    ENDPOINT_DEVELOPER_FILE = "developer-file"
    
    # Map file types to their common endpoints
    FILE_TYPE_ENDPOINTS = {
        CHAT_LOG: [ENDPOINT_DEVELOPER_FILE],  # Chat logs typically only in developer-file
        COMBAT_LOG: [ENDPOINT_FILE, ENDPOINT_DEVELOPER_FILE],  # Combat logs can be in either
        CONSOLE_LOG: [ENDPOINT_FILE, ENDPOINT_DEVELOPER_FILE],
        GAME_SESSION_SUMMARY: [ENDPOINT_FILE, ENDPOINT_DEVELOPER_FILE],
        MATCH_SUMMARY: [ENDPOINT_FILE, ENDPOINT_DEVELOPER_FILE],
        SERVER_METADATA: [ENDPOINT_FILE, ENDPOINT_DEVELOPER_FILE]
    }
    
    # Mapping patterns for file recognition
    FILE_TYPE_PATTERNS = {
        COMBAT_LOG: re.compile(r"CombatLog_.*\.log$", re.IGNORECASE),
        CHAT_LOG: re.compile(r"ChatLog_.*\.log$", re.IGNORECASE),
        CONSOLE_LOG: re.compile(r"ConsoleLog_.*\.log$", re.IGNORECASE),
        GAME_SESSION_SUMMARY: re.compile(r"GameSessionSummary_.*\.json$", re.IGNORECASE),
        MATCH_SUMMARY: re.compile(r"MatchSummary_.*\.json$", re.IGNORECASE),
        SERVER_METADATA: re.compile(r"ServerMetadata_.*\.json$", re.IGNORECASE)
    }
    
    @classmethod
    def identify_file_type(cls, filename: str) -> Optional[str]:
        """
        Identify the file type based on the filename pattern.
        
        Args:
            filename: The filename to identify.
            
        Returns:
            The file type constant, or None if not recognized.
        """
        if not filename:
            return None
            
        for file_type, pattern in cls.FILE_TYPE_PATTERNS.items():
            if pattern.match(filename):
                return file_type
        return None
    
    @classmethod
    def get_endpoints_for_file_type(cls, file_type: str) -> List[str]:
        """
        Get the appropriate API endpoints for a given file type.
        
        Args:
            file_type: The file type constant.
            
        Returns:
            List of endpoint names to check for this file type.
        """
        return cls.FILE_TYPE_ENDPOINTS.get(file_type, [cls.ENDPOINT_FILE, cls.ENDPOINT_DEVELOPER_FILE])


class FileNotFoundException(Exception):
    """Exception raised when a file is not found."""
    pass


class MatchNotFoundException(Exception):
    """Exception raised when a match is not found."""
    pass


class DownloadError(Exception):
    """Exception raised when a file download fails."""
    pass


class Smite2RallyHereFilesAPI:
    """
    Files API extension for Smite2RallyHereSDK.
    
    This class provides methods for accessing match files through the RallyHere Files API.
    """
    
    def __init__(self, sdk):
        """
        Initialize the Files API extension.
        
        Args:
            sdk: The Smite2RallyHereSDK instance.
        """
        self.sdk = sdk
        self.base_url = f"{self.sdk.env_base_url}/file/v1"
    
    def get_entity_directory_info(self, entity_type: str, entity_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about an entity type's storage container.
        
        Args:
            entity_type: The entity type (MATCH, SESSION, INSTANCE).
            entity_id: The entity ID.
            token: An optional token. If not provided, one will be obtained automatically.
            
        Returns:
            Information about the entity's storage container.
            
        Raises:
            requests.exceptions.HTTPError: If the request fails.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        url = f"{self.base_url}/{entity_type.lower()}/{entity_id}/directory"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def check_match_exists(self, match_id: str, token: Optional[str] = None) -> bool:
        """
        Check if a match exists in the RallyHere system.
        
        Args:
            match_id: The match ID.
            token: An optional token. If not provided, one will be obtained automatically.
            
        Returns:
            True if the match exists, False otherwise.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        try:
            self.sdk.rh_fetch_match_by_id(match_id, token)
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False
            raise
    
    def list_match_files(self, match_id: str, token: Optional[str] = None, file_type: str = "file") -> List[Dict[str, Any]]:
        """
        List all files available for a specific match.
        
        Args:
            match_id: The match ID.
            token: An optional token. If not provided, one will be obtained automatically.
            file_type: Type of file. Options are 'file' or 'developer-file'. Default is 'file'.
            
        Returns:
            A list of file metadata objects.
            
        Raises:
            MatchNotFoundException: If the match is not found.
            requests.exceptions.HTTPError: If the request fails.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        # Check if the match exists
        if not self.check_match_exists(match_id, token):
            raise MatchNotFoundException(f"Match {match_id} not found")
            
        # Use the correct URL format with file_type parameter
        url = f"{self.base_url}/{file_type}/match/{match_id}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Extract the files array from the response
        files = response.json().get("files", [])
        
        # Add api_type to each file record for later reference
        for file_info in files:
            file_info["api_type"] = file_type
            
        return files
    
    def get_file_metadata(self, 
                         match_id: str, 
                         filename: str, 
                         token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metadata for a specific file without downloading it.
        
        Args:
            match_id: The match ID.
            filename: The filename to get metadata for.
            token: An optional token. If not provided, one will be obtained automatically.
            
        Returns:
            Metadata for the file.
            
        Raises:
            FileNotFoundException: If the file is not found.
            MatchNotFoundException: If the match is not found.
        """
        files = self.list_match_files(match_id, token)
        
        for file_info in files:
            if file_info.get("name") == filename:
                return file_info
                
        raise FileNotFoundException(f"File {filename} not found for match {match_id}")
    
    def download_match_file(self, 
                           match_id: str, 
                           filename: str, 
                           output_path: Optional[str] = None, 
                           token: Optional[str] = None,
                           session_id: Optional[str] = None) -> str:
        """
        Download a specific file for a match.
        
        Args:
            match_id: The match ID.
            filename: The filename to download.
            output_path: The path to save the file to. If not provided, the file will be saved to the current directory.
            token: An optional token. If not provided, one will be obtained automatically.
            session_id: Optional session ID. If not provided, it will be extracted from file metadata.
            
        Returns:
            The path to the downloaded file.
            
        Raises:
            FileNotFoundException: If the file is not found.
            MatchNotFoundException: If the match is not found.
            DownloadError: If the download fails.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        # Get all files to find the session ID if not provided
        files = self.list_match_files(match_id, token)
        
        # Find the file and get its session ID
        file_info = None
        for f in files:
            if f.get("name") == filename:
                file_info = f
                break
                
        if not file_info:
            raise FileNotFoundException(f"File {filename} not found for match {match_id}")
            
        # Extract session ID from file_info if not provided
        if session_id is None:
            session_id = file_info.get("sessionId")
            if not session_id:
                raise DownloadError(f"No session ID available for file {filename}")
            
        # Set output path
        if output_path is None:
            output_path = filename
        elif os.path.isdir(output_path):
            output_path = os.path.join(output_path, filename)
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
        # Use the correct URL format from file_api_extension.py
        url = f"{self.base_url}/match/{match_id}/session/{session_id}/file/{filename}/download"
        headers = {
            "Accept": "application/octet-stream",
            "Authorization": f"Bearer {token}"
        }
        
        # Download the file
        try:
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return output_path
        except Exception as e:
            raise DownloadError(f"Failed to download file {filename}: {str(e)}")
    
    def download_all_match_files(self, 
                                match_id: str, 
                                output_dir: str, 
                                token: Optional[str] = None,
                                file_types: Optional[List[str]] = None,
                                filename_pattern: Optional[str] = None) -> List[str]:
        """
        Download all files for a match.
        
        Args:
            match_id: The match ID.
            output_dir: The directory to save the files to.
            token: An optional token. If not provided, one will be obtained automatically.
            file_types: Optional list of file types to download. If not provided, all files will be downloaded.
            filename_pattern: Optional pattern for saving files. Use {match_id} and {filename} as placeholders.
                Default is just the original filename.
            
        Returns:
            A list of paths to the downloaded files.
            
        Raises:
            MatchNotFoundException: If the match is not found.
            DownloadError: If a download fails.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        # Make sure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
            
        # Get files from both 'file' and 'developer-file' types
        all_files = []
        api_types = [FileTypeConstants.ENDPOINT_FILE, FileTypeConstants.ENDPOINT_DEVELOPER_FILE]
        
        for api_type in api_types:
            try:
                files = self.list_match_files(match_id, token, api_type)
                for file_info in files:
                    file_info["api_type"] = api_type  # Add the API type
                all_files.extend(files)
            except Exception as e:
                print(f"Warning: Error getting files from {api_type}: {str(e)}")
        
        # Filter by file type if specified
        if file_types:
            filtered_files = []
            for f in all_files:
                filename = f.get("name", "")
                file_type = FileTypeConstants.identify_file_type(filename)
                if file_type in file_types:
                    filtered_files.append(f)
            all_files = filtered_files
            
        # Download each file
        downloaded_files = []
        for file_info in all_files:
            filename = file_info.get("name", "")
            
            # Skip if no filename
            if not filename:
                continue
                
            # Apply filename pattern if provided
            if filename_pattern:
                output_filename = filename_pattern.format(match_id=match_id, filename=filename)
            else:
                output_filename = filename
            
            # Get API type for URL construction
            api_type = file_info.get("api_type", "file")
            output_path = os.path.join(output_dir, output_filename)
            
            try:
                # Use direct URL download approach for all files
                url = f"{self.base_url}/{api_type}/match/{match_id}/{filename}"
                headers = {
                    "Authorization": f"Bearer {token}"
                }
                
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()
                
                # Save the file
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                downloaded_files.append(output_path)
                print(f"Downloaded: {os.path.basename(output_path)}")
            except Exception as e:
                # Log the error but continue downloading other files
                print(f"Warning: Error downloading {filename}: {str(e)}")
                
        return downloaded_files
    
    def download_combat_log(self, 
                           match_id: str, 
                           session_id: str = None,
                           output_dir: Optional[str] = None, 
                           token: Optional[str] = None) -> str:
        """
        Download the combat log for a specific match and session.
        
        Args:
            match_id: The match ID.
            session_id: The session ID. If not provided, will try to find any combat log.
            output_dir: The directory to save the file to. If not provided, the file will be saved to the current directory.
            token: An optional token. If not provided, one will be obtained automatically.
            
        Returns:
            The path to the downloaded file.
            
        Raises:
            FileNotFoundException: If the combat log is not found.
            MatchNotFoundException: If the match is not found.
            DownloadError: If the download fails.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        # Get list of files
        files = self.list_match_files(match_id, token)
        
        # Find combat log
        combat_logs = []
        for file_info in files:
            filename = file_info.get("name", "")
            if FileTypeConstants.identify_file_type(filename) == FileTypeConstants.COMBAT_LOG:
                combat_logs.append(file_info)
        
        if not combat_logs:
            raise FileNotFoundException(f"No combat logs found for match {match_id}")
            
        # If session_id is provided, filter by session_id
        selected_log = None
        if session_id:
            for log in combat_logs:
                filename = log.get("name", "")
                if f"CombatLog_{session_id}.log" == filename:
                    selected_log = log
                    break
        else:
            # Just take the first one
            selected_log = combat_logs[0]
            
        if not selected_log:
            raise FileNotFoundException(f"Combat log for session {session_id} not found")
            
        # Download the file
        filename = selected_log.get("name")
        log_session_id = selected_log.get("sessionId")
        
        # If sessionId not available in metadata, extract it from filename
        if not log_session_id:
            log_session_id = FileTypeConstants.extract_session_id(filename)
            
        if not log_session_id:
            raise DownloadError(f"Could not determine session ID for file {filename}")
        
        if output_dir:
            output_path = os.path.join(output_dir, filename)
        else:
            output_path = filename
            
        # Use the direct URL download method
        api_type = selected_log.get("api_type", "file")
        url = f"{self.base_url}/{api_type}/match/{match_id}/{filename}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Save the file
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return output_path
        except Exception as e:
            raise DownloadError(f"Failed to download file {filename}: {str(e)}")
    
    def download_chat_log(self, 
                         match_id: str, 
                         session_id: str = None,
                         output_dir: Optional[str] = None, 
                         token: Optional[str] = None) -> str:
        """
        Download the chat log for a specific match and session.
        
        Args:
            match_id: The match ID.
            session_id: The session ID. If not provided, will try to find any chat log.
            output_dir: The directory to save the file to. If not provided, the file will be saved to the current directory.
            token: An optional token. If not provided, one will be obtained automatically.
            
        Returns:
            The path to the downloaded file.
            
        Raises:
            FileNotFoundException: If the chat log is not found.
            MatchNotFoundException: If the match is not found.
            DownloadError: If the download fails.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        # Get list of files
        files = self.list_match_files(match_id, token, "developer-file")
        
        # Find chat log
        chat_logs = []
        for file_info in files:
            filename = file_info.get("name", "")
            if FileTypeConstants.identify_file_type(filename) == FileTypeConstants.CHAT_LOG:
                chat_logs.append(file_info)
        
        if not chat_logs:
            raise FileNotFoundException(f"No chat logs found for match {match_id}")
            
        # If session_id is provided, filter by session_id
        selected_log = None
        if session_id:
            for log in chat_logs:
                filename = log.get("name", "")
                if f"ChatLog_{session_id}.log" == filename:
                    selected_log = log
                    break
        else:
            # Just take the first one
            selected_log = chat_logs[0]
            
        if not selected_log:
            raise FileNotFoundException(f"Chat log for session {session_id} not found")
            
        # Download the file
        filename = selected_log.get("name")
        log_session_id = selected_log.get("sessionId")
        
        # If sessionId not available in metadata, extract it from filename
        if not log_session_id:
            log_session_id = FileTypeConstants.extract_session_id(filename)
            
        if not log_session_id:
            raise DownloadError(f"Could not determine session ID for file {filename}")
        
        if output_dir:
            output_path = os.path.join(output_dir, filename)
        else:
            output_path = filename
            
        # Use the direct URL download method
        api_type = selected_log.get("api_type", "developer-file")
        url = f"{self.base_url}/{api_type}/match/{match_id}/{filename}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Save the file
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return output_path
        except Exception as e:
            raise DownloadError(f"Failed to download file {filename}: {str(e)}")
    
    def filter_match_files_by_type(self, 
                                  match_id: str, 
                                  file_type: str, 
                                  token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Filter match files by type.
        
        Args:
            match_id: The match ID.
            file_type: The file type to filter by.
            token: An optional token. If not provided, one will be obtained automatically.
            
        Returns:
            A list of file metadata objects.
            
        Raises:
            MatchNotFoundException: If the match is not found.
        """
        files = self.list_match_files(match_id, token)
        return [f for f in files if FileTypeConstants.identify_file_type(f.get("name")) == file_type]
    
    def filter_match_files_by_session(self, 
                                     match_id: str, 
                                     session_id: str, 
                                     token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Filter match files by session ID.
        
        Args:
            match_id: The match ID.
            session_id: The session ID to filter by.
            token: An optional token. If not provided, one will be obtained automatically.
            
        Returns:
            A list of file metadata objects.
            
        Raises:
            MatchNotFoundException: If the match is not found.
        """
        files = self.list_match_files(match_id, token)
        return [f for f in files if session_id in f.get("name", "")]
    
    def download_match_file_by_type(self, 
                                   match_id: str, 
                                   file_type: str,
                                   output_dir: Optional[str] = None, 
                                   session_id: Optional[str] = None,
                                   token: Optional[str] = None,
                                   filename_pattern: Optional[str] = None) -> List[str]:
        """
        Download files of a specific type for a match.
        
        Args:
            match_id: The match ID.
            file_type: The file type to download.
            output_dir: The directory to save the files to. If not provided, the files will be saved to the current directory.
            session_id: Optional session ID to filter by.
            token: An optional token. If not provided, one will be obtained automatically.
            filename_pattern: Optional pattern for saving files. Use {match_id} and {filename} as placeholders.
                Default is just the original filename.
            
        Returns:
            A list of paths to the downloaded files.
            
        Raises:
            MatchNotFoundException: If the match is not found.
            FileNotFoundException: If no files of the specified type are found.
            DownloadError: If a download fails.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        # Determine which endpoints to check for this file type
        endpoints = FileTypeConstants.get_endpoints_for_file_type(file_type)
        
        # Find all matching files across all appropriate endpoints
        all_files = []
        
        for endpoint in endpoints:
            try:
                files = self.list_match_files(match_id, token, endpoint)
                
                # Add endpoint info to each file record for later use
                for file_info in files:
                    file_info["api_type"] = endpoint
                    
                # Filter to get only files of the requested type
                type_files = []
                for file_info in files:
                    filename = file_info.get("name", "")
                    if FileTypeConstants.identify_file_type(filename) == file_type:
                        type_files.append(file_info)
                        
                # Filter by session_id if provided
                if session_id and type_files:
                    filtered_files = []
                    for file_info in type_files:
                        name = file_info.get("name", "")
                        if session_id in name:
                            filtered_files.append(file_info)
                    if filtered_files:
                        type_files = filtered_files
                        
                all_files.extend(type_files)
            except Exception as e:
                print(f"Warning: Error fetching files from {endpoint} endpoint: {e}")
                
        if not all_files:
            raise FileNotFoundException(f"No files of type {file_type} found for match {match_id}")
            
        # Ensure the output directory exists
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        # Download each file
        downloaded_files = []
        for file_info in all_files:
            filename = file_info.get("name", "")
            api_type = file_info.get("api_type", "file")
            
            if not filename:
                continue
                
            # Apply filename pattern if provided
            if filename_pattern:
                output_filename = filename_pattern.format(match_id=match_id, filename=filename)
            else:
                output_filename = filename
            
            # Determine output path
            if output_dir:
                output_path = os.path.join(output_dir, output_filename)
            else:
                output_path = output_filename
            
            try:
                # Use direct URL download
                url = f"{self.base_url}/{api_type}/match/{match_id}/{filename}"
                
                headers = {
                    "Authorization": f"Bearer {token}"
                }
                
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()
                
                # Save the file
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                downloaded_files.append(output_path)
                print(f"Downloaded: {os.path.basename(output_path)}")
            except Exception as e:
                print(f"Warning: Error downloading {filename}: {e}")
                
        return downloaded_files

    def _download_file(self, 
                      url: str, 
                      headers: Dict[str, str], 
                      output_path: str,
                      progress_callback: Optional[Callable[[str, int, int], None]] = None) -> str:
        """
        Internal helper method for downloading files with consistent error handling.
        
        Args:
            url: The URL to download from.
            headers: The headers to use for the request.
            output_path: The path to save the file to.
            progress_callback: Optional callback for progress reporting.
            
        Returns:
            The path to the downloaded file.
            
        Raises:
            DownloadError: If the download fails.
        """
        try:
            # Make sure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Download the file
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Get content length if available
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Report progress if callback provided and content length known
                    if progress_callback and total_size > 0:
                        progress_callback(os.path.basename(output_path), downloaded, total_size)
            
            # Final progress report
            if progress_callback:
                progress_callback(os.path.basename(output_path), downloaded, downloaded)
            
            return output_path
        except Exception as e:
            raise DownloadError(f"Failed to download file to {output_path}: {str(e)}")

    def list_all_match_files(self, 
                            match_id: str, 
                            token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all files for a match from all available endpoints.
        
        Args:
            match_id: The match ID.
            token: An optional token. If not provided, one will be obtained automatically.
            
        Returns:
            Combined list of file metadata objects from all endpoints.
            
        Raises:
            MatchNotFoundException: If the match is not found.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        # Check if the match exists
        if not self.check_match_exists(match_id, token):
            raise MatchNotFoundException(f"Match {match_id} not found")
            
        all_files = []
        endpoints = [FileTypeConstants.ENDPOINT_FILE, FileTypeConstants.ENDPOINT_DEVELOPER_FILE]
        
        for endpoint in endpoints:
            try:
                # Use the correct URL format with endpoint parameter
                url = f"{self.base_url}/{endpoint}/match/{match_id}"
                headers = {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
                
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                # Extract the files array from the response
                files = response.json().get("files", [])
                
                # Add endpoint info to each file record
                for file_info in files:
                    file_info["api_type"] = endpoint
                    
                all_files.extend(files)
            except Exception as e:
                print(f"Warning: Error listing files from {endpoint}: {str(e)}")
            
        return all_files

    def download_match_files(self,
                           match_id: str,
                           files: List[Dict[str, Any]],
                           output_dir: str,
                           token: Optional[str] = None,
                           filename_pattern: Optional[str] = None,
                           progress_callback: Optional[Callable[[str, int, int], None]] = None,
                           max_concurrent_downloads: int = 3) -> List[str]:
        """
        Download multiple files for a match.
        
        Args:
            match_id: The match ID.
            files: List of file metadata objects.
            output_dir: The directory to save the files to.
            token: An optional token. If not provided, one will be obtained automatically.
            filename_pattern: Optional pattern for saving files. Use {match_id} and {filename} as placeholders.
            progress_callback: Optional callback for progress reporting.
            max_concurrent_downloads: Maximum number of concurrent downloads (default: 3).
            
        Returns:
            A list of paths to the downloaded files.
            
        Raises:
            DownloadError: If a download fails.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        # Make sure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Define the download function for a single file
        def download_single_file(file_info):
            filename = file_info.get("name", "")
            if not filename:
                return None
            
            # Apply filename pattern if provided
            if filename_pattern:
                output_filename = filename_pattern.format(match_id=match_id, filename=filename)
            else:
                output_filename = filename
            
            # Determine output path
            output_path = os.path.join(output_dir, output_filename)
            
            # Get API type for URL construction
            api_type = file_info.get("api_type", "file")
            
            # Download the file
            url = f"{self.base_url}/{api_type}/match/{match_id}/{filename}"
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            try:
                downloaded_path = self._download_file(url, headers, output_path, progress_callback)
                print(f"Downloaded: {os.path.basename(output_path)}")
                return downloaded_path
            except Exception as e:
                print(f"Warning: Error downloading {filename}: {e}")
                return None
        
        # Download files concurrently with a thread pool
        downloaded_files = []
        if max_concurrent_downloads <= 1:
            # Sequential download
            for file_info in files:
                result = download_single_file(file_info)
                if result:
                    downloaded_files.append(result)
        else:
            # Concurrent download
            with ThreadPoolExecutor(max_workers=max_concurrent_downloads) as executor:
                results = list(executor.map(download_single_file, files))
                downloaded_files = [r for r in results if r]
            
        return downloaded_files

    def get_filtered_matches(self,
                            start_date: str,
                            end_date: str,
                            region_id: Optional[str] = None,
                            game_mode: Optional[str] = None,
                            min_duration: Optional[int] = None,
                            max_duration: Optional[int] = None,
                            limit: int = 10,
                            batch_size: int = 100) -> List[Dict[str, Any]]:
        """
        Get matches filtered by various criteria.
        
        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            region_id: Optional region ID to filter by.
            game_mode: Optional game mode to filter by.
            min_duration: Optional minimum match duration in seconds.
            max_duration: Optional maximum match duration in seconds.
            limit: Maximum number of matches to return (0 for no limit).
            batch_size: Number of matches to request per API call.
            
        Returns:
            List of filtered match data.
        """
        token = self.sdk._get_env_access_token()
        
        # Format dates as ISO 8601
        start_time = f"{start_date}T00:00:00Z"
        end_time = f"{end_date}T23:59:59Z"
        
        url = f"{self.sdk.env_base_url}/match/v1/match"
        
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "page_size": min(batch_size, 100),  # Max 100 per page
            "status": "closed"
        }
        
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        all_matches = []
        matches_processed = 0
        cursor = None
        no_limit = (limit == 0)
        
        try:
            # Fetch matches with pagination
            while no_limit or matches_processed < limit:
                if cursor:
                    params["cursor"] = cursor
                
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                matches = data.get("matches", [])
                if not matches:
                    break
                
                # Filter matches based on criteria
                filtered_batch = self._filter_matches_by_criteria(
                    matches,
                    region_id=region_id,
                    game_mode=game_mode,
                    min_duration=min_duration,
                    max_duration=max_duration
                )
                
                all_matches.extend(filtered_batch)
                matches_processed += len(matches)
                
                cursor = data.get("cursor")
                if not cursor:
                    break
                
                # Print progress for large fetches
                if matches_processed % 100 == 0:
                    print(f"Fetched {matches_processed} matches so far...")
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.1)
        except Exception as e:
            print(f"Error fetching matches: {e}")
            # Add a longer delay after an error
            time.sleep(1)
        
        if limit > 0 and len(all_matches) > limit:
            return all_matches[:limit]
        return all_matches

    def _filter_matches_by_criteria(self,
                                   matches: List[Dict[str, Any]],
                                   region_id: Optional[str] = None,
                                   game_mode: Optional[str] = None,
                                   min_duration: Optional[int] = None,
                                   max_duration: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Internal method to filter matches by criteria.
        
        Args:
            matches: List of match data dictionaries.
            region_id: Optional region ID to filter by.
            game_mode: Optional game mode to filter by.
            min_duration: Optional minimum match duration in seconds.
            max_duration: Optional maximum match duration in seconds.
            
        Returns:
            List of filtered match data.
        """
        filtered = []
        
        for match in matches:
            # Check duration if specified
            if min_duration is not None and (
                "duration_seconds" not in match or 
                match.get("duration_seconds", 0) < min_duration
            ):
                continue
            
            if max_duration is not None and (
                "duration_seconds" in match and 
                match.get("duration_seconds", 0) > max_duration
            ):
                continue
            
            # Extract instances data
            instances = match.get("instances", [])
            if not instances:
                continue
            
            # Use the first instance for filtering
            instance = instances[0]
            
            # Check if the match meets all filter criteria
            if region_id and instance.get("region_id") != region_id:
                continue
            
            if game_mode:
                instance_game_mode = instance.get("game_mode", "")
                if game_mode.lower() not in instance_game_mode.lower():
                    continue
                
            # If we reach here, the match has passed all filters
            filtered.append(match)
        
        return filtered 
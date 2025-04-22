import os
import re
import requests
from typing import List, Dict, Optional, Union, Any, BinaryIO, Set
from enum import Enum, auto
import time

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
    def extract_session_id(cls, filename: str) -> Optional[str]:
        """
        Extract the session ID from a filename.
        
        Args:
            filename: The filename to extract from.
            
        Returns:
            The session ID if found, None otherwise.
        """
        if not filename:
            return None
            
        # Look for patterns like CombatLog_SESSION_ID.log or ChatLog_SESSION_ID.log
        for prefix in ["CombatLog_", "ChatLog_", "ConsoleLog_"]:
            if filename.startswith(prefix):
                # Extract part between prefix and file extension
                session_part = filename[len(prefix):].split(".")[0]
                if len(session_part) >= 36:  # UUID is typically 36 chars
                    return session_part
        
        return None


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
                                file_types: Optional[List[str]] = None) -> List[str]:
        """
        Download all files for a match.
        
        Args:
            match_id: The match ID.
            output_dir: The directory to save the files to.
            token: An optional token. If not provided, one will be obtained automatically.
            file_types: Optional list of file types to download. If not provided, all files will be downloaded.
            
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
        api_types = ["file", "developer-file"]
        
        for api_type in api_types:
            try:
                files = self.list_match_files(match_id, token, api_type)
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
                
            # Get API type for URL construction
            api_type = file_info.get("api_type", "file")
            output_path = os.path.join(output_dir, filename)
            
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
                print(f"Downloaded: {filename}")
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
                                   session_id: Optional[str] = None,
                                   output_dir: Optional[str] = None, 
                                   token: Optional[str] = None) -> List[str]:
        """
        Download files of a specific type for a match.
        
        Args:
            match_id: The match ID.
            file_type: The file type to download.
            session_id: Optional session ID to filter by.
            output_dir: The directory to save the files to. If not provided, the files will be saved to the current directory.
            token: An optional token. If not provided, one will be obtained automatically.
            
        Returns:
            A list of paths to the downloaded files.
            
        Raises:
            MatchNotFoundException: If the match is not found.
            FileNotFoundException: If no files of the specified type are found.
            DownloadError: If a download fails.
        """
        if token is None:
            token = self.sdk._get_env_access_token()
            
        # Get files of both API types
        all_files = []
        api_types = ["file", "developer-file"]
        
        for api_type in api_types:
            try:
                files = self.list_match_files(match_id, token, api_type)
                all_files.extend(files)
            except Exception as e:
                print(f"Warning: Error fetching files from {api_type}: {e}")
        
        # Filter to get only files of the requested type
        type_files = []
        for file_info in all_files:
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
            
        if not type_files:
            raise FileNotFoundException(f"No files of type {file_type} found for match {match_id}")
            
        # Download each file
        downloaded_files = []
        for file_info in type_files:
            filename = file_info.get("name", "")
            api_type = file_info.get("api_type", "file")
            
            if output_dir:
                output_path = os.path.join(output_dir, filename)
            else:
                output_path = filename
                
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
                print(f"Downloaded: {filename}")
            except Exception as e:
                print(f"Warning: Error downloading {filename}: {e}")
                
        return downloaded_files 
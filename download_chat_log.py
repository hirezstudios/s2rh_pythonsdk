#!/usr/bin/env python3
"""
Download the chat log file from a match using the RallyHere Files API.
"""
import os
import requests
from dotenv import load_dotenv
from smite2_rh_sdk import Smite2RallyHereSDK

# Load environment variables from .env file
load_dotenv()

# Configuration
MATCH_ID = "28257fd8-88c1-40ed-9bad-4151bcc601a5"
FILE_NAME = "ChatLog_60ce5622-4b06-44f3-8663-0030d6c23d11.log"
OUTPUT_DIR = "match_files"

# Initialize the SDK and get a token
sdk = Smite2RallyHereSDK()
token = sdk._get_env_access_token()
base_url = os.environ.get("RH_BASE_URL", "https://demo.rally-here.io")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(OUTPUT_DIR, FILE_NAME)

# Construct the URL for downloading the file
url = f"{base_url}/file/v1/file/match/{MATCH_ID}/{FILE_NAME}"

# Make the request
print(f"Attempting to download {FILE_NAME} from match {MATCH_ID}...")
headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.get(url, headers=headers, stream=True)
print(f"Response status: {response.status_code}")

# Check if successful
if response.status_code == 200:
    # Save the file
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Successfully downloaded file to: {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")
    
    # Display the first few lines if it's a text file
    try:
        with open(output_path, 'r') as f:
            preview = f.read(500)  # First 500 characters
        print("\nFile preview:")
        print("=============")
        print(preview)
        print("=============")
    except UnicodeDecodeError:
        print("File is not text or uses a different encoding.")
else:
    print(f"Failed to download file. Error: {response.text}") 
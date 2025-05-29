#!/usr/bin/env python3
"""
Upload job CSVs to the prprpr API.

Usage:
    python upload_jobs_to_prprpr.py <csv_folder>

CSV files should be named: <assignee>_<job_name>.csv
where job_name can contain underscores that will be replaced with spaces.

Each CSV should have columns matching JobItem fields:
- student_id (required)
- problem (required)
- subquestion (required)
- answer
- suggested_score
- adjusted_score
- standard_error
- general_error
- feedback
- internal_comments
- is_flagged_for_follow_up
- page_numbers
- is_submitted
"""

import os
import sys
import random
import string
import base64
import socket
import hashlib
import requests
import webbrowser
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from urllib.parse import urlparse, parse_qs


PRPRPR_DEBUG = os.getenv("PRPRPR_DEBUG", "0") == "1"
if PRPRPR_DEBUG:
    CLIENT_ID = "w1pagvvYT00eDrxMykMyPDviS1gMwO4XJtiHajCN"
    CLIENT_SECRET = "oawdfeOl6eqAiemWePB4k8M19HhjT4VNgSzR1MialtusFfltcExzYhfoeOAzat0N6pNoE6E7aMMXFASOIBEFEWlUqwq9qRm4Aw2xJ283upImVu8vKJdy6zHmudKxUzF6"
    BASE_URL = "http://127.0.0.1:8000"
else:
    CLIENT_ID = "Wf42oWVR2YsYfwQYT2Aoh6dqgZyo23FQ0ofOIdEZ"
    CLIENT_SECRET = "BIojMEaDVRcnKgmMdoUNnSv3FErvimiFhQnInv7zZrE5ZYYVODpbdfUOYPYn5O6OKJAguKdCMc3Xd3WxA99242fMG4l8JjtcorrOYwkuBJ92VpneVAuKSxPO55e9FIp7"
    BASE_URL = "https://clrify.it"


def get_access_token() -> str:
    """Get OAuth2 access token using PKCE flow."""
    code_verifier = ''.join(random.choice(string.ascii_uppercase + string.digits) 
                           for _ in range(random.randint(43, 128)))

    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').replace('=', '')

    # Open a socket to listen for the response from authentication
    with socket.socket() as s:
        s.bind(("localhost", 0))
        s.listen()

        port = s.getsockname()[1]
        redirect_uri = f"http://127.0.0.1:{port}"
        auth_url = (f"{BASE_URL}/o/authorize/?response_type=code&"
                   f"code_challenge={code_challenge}&code_challenge_method=S256&"
                   f"client_id={CLIENT_ID}&redirect_uri={redirect_uri}")
        
        print(f"Please visit this URL to authorize this application: {auth_url}")

        webbrowser.open(auth_url)

        conn, _ = s.accept()
        request = conn.recv(4096)

        # Send success message to browser
        conn.send(b"HTTP/1.1 200 OK\n"
                  b"Content-Type: text/html\n\n"
                  b"<html><body>The authentication flow has completed. You may close this window and return to the terminal.</body></html>")

    # Extract authorization code from URL
    url = request.decode().split()[1]
    query = parse_qs(urlparse(url).query)
    auth_code = query["code"][0]

    # Exchange authorization code for access token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    r = requests.post(f"{BASE_URL}/o/token/", data=data)
    r.raise_for_status()
    return r.json()["access_token"]


def convert_roman_to_int(roman: str) -> int:
    """
    Convert a Roman numeral to an integer.
    
    Args:
        roman (str): Roman numeral string.
        
    Returns:
        int: Integer value of the Roman numeral.
    """
    if not roman:
        return 0
    
    # Define mapping of Roman numerals to integers
    roman_numerals = {
        "I" : 1,
        "V" : 5,
        "X" : 10,
        "L" : 50,
        "C" : 100,
        "D" : 500,
        "M" : 1000
    }

    int_value = 0

    for i in range(len(roman)):
        if roman[i] in roman_numerals:
            if i + 1 < len(roman) and roman_numerals[roman[i]] < roman_numerals[roman[i + 1]]:
                int_value -= roman_numerals[roman[i]]
            else:
                int_value += roman_numerals[roman[i]]
        else:
            raise ValueError(f"Invalid Roman numeral character: {roman[i]}")
    
    return int_value



def csv_to_job_items(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Convert CSV file to list of job items.
    
    Returns:
        List of job item dictionaries
    """
    df = pd.read_csv(csv_path)
    
    # Required columns
    required_cols = ['student_id', 'problem', 'subquestion']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {csv_path}: {missing_cols}")
    
    # Convert DataFrame to list of dictionaries
    items = []
    for idx, row in df.iterrows():
        subquestion = row['subquestion']

        # Convert Roman numeral subquestion to integer if needed
        if isinstance(subquestion, str) and subquestion.isalpha():
            try:
                subquestion = convert_roman_to_int(subquestion.upper())
            except ValueError as e:
                raise ValueError(f"Invalid Roman numeral in row {idx + 1}: {e}")
        elif not isinstance(subquestion, int):
            raise ValueError(f"Subquestion must be an integer or Roman numeral in row {idx + 1}, got {subquestion} of type {type(subquestion)}")
        elif subquestion < 1:
            raise ValueError(f"Subquestion must be a positive integer in row {idx + 1}, got {subquestion}")

        item = {
            'student_id': str(row['student_id']),
            'problem': int(row['problem']),
            'subquestion': subquestion,
        }
        
        # Add optional fields if they exist
        optional_fields = [
            'answer', 'suggested_score', 'adjusted_score', 
            'standard_error', 'general_error', 'feedback',
            'internal_comments', 'page_numbers'
        ]
        
        for field in optional_fields:
            if field in df.columns and pd.notna(row[field]):
                if field in ['suggested_score', 'adjusted_score']:
                    # Convert to float if numeric
                    try:
                        item[field] = float(row[field])
                    except:
                        item[field] = str(row[field])
                else:
                    item[field] = str(row[field])
        
        # Boolean fields
        if 'is_flagged_for_follow_up' in df.columns:
            item['is_flagged_for_follow_up'] = bool(row.get('is_flagged_for_follow_up', False))
        if 'is_submitted' in df.columns:
            item['is_submitted'] = bool(row.get('is_submitted', False))
            
        items.append(item)
    
    return items


def upload_job(headers: dict[str, str], job_name: str, assignee: str, items: List[Dict]) -> Dict:
    """
    Upload a job to the prprpr API.
    
    Returns:
        Response data from API
    """
    endpoint = f"{BASE_URL}/api/jobs/create/"
    
    payload = {
        'name': job_name,
        'assignee': assignee,
        'items': items
    }
    
    response = requests.post(endpoint, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()


def main():
    # Get the arguments that were passed to the script
    _, script_args = sys.argv[0], sys.argv[1:]

    # If less than one argument was given to the script, we need the csv folder
    if len(script_args) < 1:
        print("Error: not enough arguments were given to the script")
        print("Usage: python upload_jobs_to_prprpr.py <csv_folder>")
        sys.exit(1)

    csv_folder = Path(script_args[0])

    if not csv_folder.is_dir():
        print(f"Error: {csv_folder} is not a valid directory")
        sys.exit(1)

    if not PRPRPR_DEBUG:
        input("You are about to upload jobs to production. Press Enter to continue...")

    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Find all CSV files
    csv_files = list(csv_folder.glob('**/*.csv'))
    if not csv_files:
        print(f"No CSV files found in {csv_folder}")
        sys.exit(1)
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    # Process each CSV file
    successful = 0
    failed = 0

    for i, csv_file in enumerate(csv_files):
        print(f"Creating jobs...{i}/{len(csv_files)}", end='\r', flush=True)
        
        try:
            # Parse filename
            assignee, job_name = csv_file.stem.split('_', 1)
            if not job_name:
                print(f"Invalid job name in filename: {csv_file.name}. Continuing to next file.")
                continue

            job_name = job_name.replace('_', ' ')  # Replace underscores with spaces
            
            # Convert CSV to job items
            items = csv_to_job_items(csv_file)

            # Upload to API
            upload_job(headers, job_name, assignee, items)
            successful += 1
        except requests.HTTPError as e:
            print(f"  ✗ HTTP error: {e.response.status_code} - {e.response.text}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Job creation error: {str(e)}")
            failed += 1

    print("Creating jobs...Done     ")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(csv_files)}")
    
    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
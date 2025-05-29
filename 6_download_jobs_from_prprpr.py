#!/usr/bin/env python3
"""
Download jobs from the prprpr API and save them as CSV files.

Usage:
    python download_jobs_from_prprpr.py <output_folder>

Jobs will be saved as: <assignee>_<job_name>.csv
where spaces in job_name will be replaced with underscores.

Each CSV will have columns matching JobItem fields:
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


def fetch_all_jobs(headers: dict[str, str]) -> List[Dict[str, Any]]:
    """
    Fetch all jobs from the prprpr API.
    
    Returns:
        List of job dictionaries
    """
    endpoint = f"{BASE_URL}/api/jobs/"
    
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    
    return response.json()["jobs"]


def fetch_job_items(headers: dict[str, str], job_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all items for a specific job.
    
    Returns:
        List of job item dictionaries
    """
    endpoint = f"{BASE_URL}/api/jobs/{job_id}/"
    
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    
    return response.json()["job"]["items"]


def job_items_to_csv(items: List[Dict[str, Any]], csv_path: Path) -> None:
    """
    Convert list of job items to CSV file.
    """
    if not items:
        print(f"  Warning: No items found for job, skipping CSV creation")
        return
    
    # Convert items to DataFrame
    df = pd.DataFrame(items)
    
    # Ensure required columns exist
    required_cols = ['student_id', 'problem', 'subquestion']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''
    
    # Order columns with required first, then optional
    column_order = [
        'student_id', 'problem', 'subquestion',
        'answer', 'suggested_score', 'adjusted_score',
        'standard_error', 'general_error', 'feedback',
        'internal_comments', 'is_flagged_for_follow_up',
        'page_numbers', 'is_submitted'
    ]
    
    # Only include columns that exist in the data
    columns_to_write = [col for col in column_order if col in df.columns]
    
    # Save to CSV
    df[columns_to_write].to_csv(csv_path, index=False)


def main():
    # Get the arguments that were passed to the script
    _, script_args = sys.argv[0], sys.argv[1:]

    # If less than one argument was given to the script, we need the output folder
    if len(script_args) < 1:
        print("Error: not enough arguments were given to the script")
        print("Usage: python download_jobs_from_prprpr.py <output_folder>")
        sys.exit(1)

    output_folder = Path(script_args[0])

    # Create output folder if it doesn't exist
    output_folder.mkdir(parents=True, exist_ok=True)

    if not PRPRPR_DEBUG:
        input("You are about to download jobs from production. Press Enter to continue...")

    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Fetch all jobs
        print("Fetching jobs list...")
        jobs = fetch_all_jobs(headers)
        print(f"Found {len(jobs)} jobs")
        
        if not jobs:
            print("No jobs found to download")
            sys.exit(0)
        
        # Process each job
        successful = 0
        failed = 0
        
        for i, job in enumerate(jobs):
            print(f"Downloading jobs...{i+1}/{len(jobs)}", end='\r', flush=True)
            
            try:
                job_id = job['id']
                job_name = job['name']
                assignee = job.get('assignee', 'unknown')
                
                # Create filename
                safe_job_name = job_name.replace(' ', '_')
                csv_filename = f"{assignee}_{safe_job_name}.csv"
                csv_path = output_folder / csv_filename
                
                # Fetch job items
                items = fetch_job_items(headers, job_id)
                
                # Save to CSV
                job_items_to_csv(items, csv_path)
                
                successful += 1
                
            except requests.HTTPError as e:
                print(f"\n  ✗ HTTP error for job {job.get('name', 'unknown')}: {e.response.status_code} - {e.response.text}")
                failed += 1
            except Exception as e:
                print(f"\n  ✗ Error downloading job {job.get('name', 'unknown')}: {str(e)}")
                failed += 1
        
        print("\nDownloading jobs...Done     ")
        
        # Summary
        print(f"\n{'='*50}")
        print(f"Summary:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total: {len(jobs)}")
        print(f"  Output folder: {output_folder.absolute()}")
        
        if failed > 0:
            sys.exit(1)
            
    except requests.HTTPError as e:
        print(f"Error fetching jobs: {e.response.status_code} - {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
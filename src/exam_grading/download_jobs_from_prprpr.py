"""Download jobs from the prprpr API and save them as CSV files."""
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

from .common.auth import get_prprpr_access_token
from .common.progress import ProgressPrinter
from .common.config import PRPRPR_DEBUG, PRPRPR_BASE_URL


def fetch_all_jobs(headers: dict[str, str]) -> List[Dict[str, Any]]:
    """
    Fetch all jobs from the prprpr API.
    
    Returns:
        List of job dictionaries
    """
    endpoint = f"{PRPRPR_BASE_URL}/api/jobs/"
    
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    
    return response.json()["jobs"]


def fetch_job_items(headers: dict[str, str], job_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all items for a specific job.
    
    Returns:
        List of job item dictionaries
    """
    endpoint = f"{PRPRPR_BASE_URL}/api/jobs/{job_id}/"
    
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


def download_jobs_from_prprpr(output_folder_path: str) -> None:
    """
    Download jobs from prprpr API and save as CSV files.
    
    Args:
        output_folder_path: Path to folder where CSV files will be saved
    """
    output_folder = Path(output_folder_path)
    
    # Create output folder if it doesn't exist
    output_folder.mkdir(parents=True, exist_ok=True)
    
    if not PRPRPR_DEBUG:
        input("You are about to download jobs from production. Press Enter to continue...")
    
    access_token = get_prprpr_access_token()
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
            return
        
        # Process each job
        successful = 0
        failed = 0
        progress = ProgressPrinter("Downloading jobs", len(jobs))
        
        for i, job in enumerate(jobs):
            progress.update(i + 1)
            
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
        
        progress.done()
        
        # Summary
        print(f"\n{'='*50}")
        print(f"Summary:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total: {len(jobs)}")
        print(f"  Output folder: {output_folder.absolute()}")
        
        if failed > 0:
            raise RuntimeError(f"Failed to download {failed} jobs")
            
    except requests.HTTPError as e:
        print(f"Error fetching jobs: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise
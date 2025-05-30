"""Download jobs from the prprpr API and save them as CSV files.

This module retrieves completed grading jobs from the prprpr service,
de-anonymizes student IDs, and saves the results as CSV files. It handles
the reverse transformation from the upload process, converting data back
to the original format.
"""
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

from .common.auth import get_prprpr_access_token
from .common.progress import ProgressPrinter
from .common.config import PRPRPR_DEBUG, PRPRPR_BASE_URL
from .common.roman_numerals import convert_int_to_roman
from .common.anonymization import StudentAnonymizer


def fetch_all_jobs(headers: dict[str, str]) -> List[Dict[str, Any]]:
    """Fetch all jobs from the prprpr API.
    
    This function retrieves the list of all grading jobs available
    on the prprpr service for the authenticated user.
    
    Args:
        headers: HTTP headers including Authorization token
    
    Returns:
        List of job dictionaries containing job metadata
        
    Raises:
        requests.HTTPError: If API request fails
    """
    endpoint = f"{PRPRPR_BASE_URL}/api/jobs/"
    
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    
    return response.json()["jobs"]


def fetch_job_items(headers: dict[str, str], job_id: str) -> List[Dict[str, Any]]:
    """Fetch all grading items for a specific job.
    
    This function retrieves the detailed grading data for a single job,
    including all problems, scores, and feedback.
    
    Args:
        headers: HTTP headers including Authorization token
        job_id: Unique identifier for the job
    
    Returns:
        List of job item dictionaries with grading details
        
    Raises:
        requests.HTTPError: If API request fails
    """
    endpoint = f"{PRPRPR_BASE_URL}/api/jobs/{job_id}/"
    
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    
    return response.json()["job"]["items"]


def job_items_to_csv(items: List[Dict[str, Any]], csv_path: Path, anonymizer: StudentAnonymizer) -> None:
    """Convert list of job items to CSV file with de-anonymization.
    
    This function transforms the API response data back to the CSV format,
    including de-anonymization of student IDs and conversion of subquestion
    numbers back to Roman numerals.
    
    Args:
        items: List of job item dictionaries from API
        csv_path: Path to save the output CSV file
        anonymizer: StudentAnonymizer for de-anonymizing student IDs (required)
        
    Data Transformations:
        - student_id: De-anonymized from anonymous IDs
        - subquestion: Converted from integers to Roman numerals
        - adjusted_score: null/None converted to empty string (0 preserved)
        - Column ordering: Maintains consistent order for readability
        
    Raises:
        RuntimeError: If anonymizer is not provided
        ValueError: If de-anonymization fails for any student ID
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
    
    # De-anonymize student IDs (required)
    if not anonymizer:
        raise RuntimeError("Anonymizer is required for de-anonymization but not available")
    if 'student_id' in df.columns:
        df['student_id'] = df['student_id'].apply(lambda x: anonymizer.deanonymize(str(x)))
    
    # Convert integer subquestion values to Roman numerals
    if 'subquestion' in df.columns:
        df['subquestion'] = df['subquestion'].apply(lambda x: convert_int_to_roman(int(x)))
    
    # Handle adjusted_score: convert null/None to empty string, keep 0 as 0
    if 'adjusted_score' in df.columns:
        df['adjusted_score'] = df['adjusted_score'].apply(
            lambda x: '' if pd.isna(x) or x is None else x
        )
    
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


def download_jobs_from_prprpr(output_folder_path: str, students_csv_path: str = None) -> None:
    """Download jobs from prprpr API and save as CSV files with de-anonymization.
    
    This is the main function that retrieves all grading jobs from the prprpr
    service and saves them as CSV files. It handles authentication, de-anonymization
    of student IDs, and data format conversion.
    
    Args:
        output_folder_path: Path to folder where CSV files will be saved
        students_csv_path: Path to students CSV for de-anonymization (required)
        
    Output Files:
        Creates CSV files named: {assignee}_{job_name}.csv
        Example: ta1_Job_1.csv
        
    Environment:
        - Debug mode: Downloads from localhost without confirmation
        - Production mode: Prompts for confirmation before download
        
    Raises:
        ValueError: If students_csv_path not provided
        RuntimeError: If any jobs fail to download or de-anonymize
        requests.HTTPError: If API requests fail
        
    Note:
        - De-anonymization is mandatory for all downloads
        - Failed downloads are reported but don't stop the batch
        - Progress is displayed during download
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
    
    # Initialize anonymizer (required for de-anonymization)
    if not students_csv_path:
        raise ValueError("students_csv_path is required for de-anonymization")
    
    try:
        anonymizer = StudentAnonymizer(students_csv_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load de-anonymization mappings: {e}")
    
    try:
        # Fetch all jobs
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
                
                # Save to CSV with optional de-anonymization
                job_items_to_csv(items, csv_path, anonymizer)
                
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
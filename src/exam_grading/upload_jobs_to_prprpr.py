"""Upload job CSVs to the prprpr API."""
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

from .common.auth import get_prprpr_access_token
from .common.validators import validate_directory
from .common.progress import ProgressPrinter
from .common.config import PRPRPR_DEBUG, PRPRPR_BASE_URL
from .common.roman_numerals import convert_roman_to_int


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
                subquestion = convert_roman_to_int(subquestion)
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
    endpoint = f"{PRPRPR_BASE_URL}/api/jobs/create/"
    
    payload = {
        'name': job_name,
        'assignee': assignee,
        'items': items
    }
    
    response = requests.post(endpoint, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()


def upload_jobs_to_prprpr(csv_folder_path: str) -> None:
    """
    Upload job CSVs to the prprpr API.
    
    Args:
        csv_folder_path: Path to folder containing CSV files
    """
    csv_folder = Path(csv_folder_path)
    validate_directory(csv_folder, "CSV folder")
    
    if not PRPRPR_DEBUG:
        input("You are about to upload jobs to production. Press Enter to continue...")
    
    access_token = get_prprpr_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Find all CSV files
    csv_files = list(csv_folder.glob('**/*.csv'))
    if not csv_files:
        print(f"No CSV files found in {csv_folder}")
        return
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    # Process each CSV file
    successful = 0
    failed = 0
    progress = ProgressPrinter("Creating jobs", len(csv_files))

    for i, csv_file in enumerate(csv_files):
        progress.update(i + 1)
        
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

    progress.done()
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(csv_files)}")
    
    if failed > 0:
        raise RuntimeError(f"Failed to upload {failed} jobs")
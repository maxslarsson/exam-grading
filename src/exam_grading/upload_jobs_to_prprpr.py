"""Upload job CSVs to the prprpr API.

This module handles uploading grading jobs to the prprpr grading service.
It converts CSV files to the API format, anonymizes student IDs, and manages
the OAuth2 authentication flow. The module supports both development and
production environments.
"""
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

from .common.auth import get_prprpr_access_token
from .common.validators import validate_directory
from .common.progress import ProgressPrinter
from .common.config import PRPRPR_DEBUG, PRPRPR_BASE_URL
from .common.roman_numerals import convert_roman_to_int
from .common.anonymization import StudentAnonymizer


def csv_to_job_items(csv_path: Path, anonymizer: StudentAnonymizer = None) -> List[Dict[str, Any]]:
    """Convert CSV file to list of job items for the prprpr API.
    
    This function reads a grading job CSV and converts it to the format expected
    by the prprpr API. It handles Roman numeral conversion for subquestions and
    applies student ID anonymization for privacy.
    
    Args:
        csv_path: Path to CSV file with grading items
        anonymizer: StudentAnonymizer for anonymizing student IDs (required)
    
    Returns:
        List of job item dictionaries ready for API upload
        
    Required CSV columns:
        - student_id: Student identifier
        - problem: Problem number (integer)
        - subquestion: Subquestion (Roman numeral or integer)
        
    Optional CSV columns:
        - answer: Student's answer
        - suggested_score: AI/OMR suggested score
        - adjusted_score: Human-adjusted score
        - standard_error: Error message
        - general_error: General feedback
        - feedback: Individual feedback
        - internal_comments: Grader notes
        - page_numbers: Comma-separated page numbers
        - is_flagged_for_follow_up: Boolean flag
        - is_submitted: Boolean submission status
        
    Raises:
        ValueError: If required columns are missing or data is invalid
        RuntimeError: If anonymizer is not provided
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

        # Anonymize student ID (required)
        student_id = str(row['student_id'])
        if not anonymizer:
            raise RuntimeError("Anonymizer is required but not available")
        student_id = anonymizer.anonymize(student_id)
        
        item = {
            'student_id': student_id,
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
    """Upload a single job to the prprpr API.
    
    This function makes the actual API request to create a grading job
    on the prprpr service.
    
    Args:
        headers: HTTP headers including Authorization token
        job_name: Name for the grading job (e.g., "Job 1")
        assignee: Username of the grader assigned to this job
        items: List of job items (problems/subquestions to grade)
    
    Returns:
        Dict: Response data from API including job ID and status
        
    Raises:
        requests.HTTPError: If API request fails
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


def upload_jobs_to_prprpr(csv_folder_path: str, students_csv_path: str = None) -> None:
    """Upload job CSVs to the prprpr API with student ID anonymization.
    
    This is the main function that processes all CSV files in a folder and
    uploads them as grading jobs to the prprpr service. It handles authentication,
    anonymization, and batch processing with progress tracking.
    
    Args:
        csv_folder_path: Path to folder containing job CSV files
        students_csv_path: Path to students CSV for anonymization (required)
        
    File Naming Convention:
        CSV files must be named: {assignee}_{job_name}.csv
        Example: ta1_Job_1.csv → assignee="ta1", job_name="Job 1"
        
    Environment:
        - Debug mode: Uploads to localhost without confirmation
        - Production mode: Prompts for confirmation before upload
        
    Raises:
        ValueError: If students_csv_path not provided or CSV format invalid
        RuntimeError: If any jobs fail to upload
        
    Note:
        - Anonymization is mandatory for all uploads
        - Failed uploads are reported but don't stop the batch
        - OAuth2 authentication is handled automatically
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
    
    # Initialize anonymizer (required)
    if not students_csv_path:
        raise ValueError("students_csv_path is required for anonymization")
    
    try:
        anonymizer = StudentAnonymizer(students_csv_path)
        print(f"Loaded anonymization mappings from {students_csv_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to load anonymization mappings: {e}")
    
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
            
            # Convert CSV to job items with optional anonymization
            items = csv_to_job_items(csv_file, anonymizer)

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
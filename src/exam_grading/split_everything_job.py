"""Split the everything_job.csv into separate job files based on job_number.

This module takes the master grading job file and splits it into individual
job files based on the job_number column. This allows different graders to
work on different portions of the exam independently.

The job_number column should be populated before running this module, typically
by assigning job numbers based on grader workload or problem groupings.
"""
import pandas as pd
from pathlib import Path

from .common.validators import validate_csv_file, validate_directory
from .common.progress import ProgressPrinter


def split_everything_job(everything_job_csv: str, csv_jobs_folder: str) -> list[str]:
    """Split the everything_job.csv into separate job files based on job_number.
    
    This function reads the master job file and creates individual CSV files
    for each unique job_number. The job_number column is removed from the
    output files since it's no longer needed once split.
    
    Args:
        everything_job_csv: Path to the everything_job.csv file containing
                          all grading tasks with job_number assignments
        csv_jobs_folder: Path to folder where individual job CSV files will be saved
        
    Returns:
        list[str]: List of paths to the created job CSV files
        
    Output format:
        Each job file is named Job_{number}.csv and contains all rows
        with that job_number, minus the job_number column itself.
        
    Example:
        Input with job_numbers 1, 2, 3 creates:
        - Job_1.csv
        - Job_2.csv  
        - Job_3.csv
        
    Raises:
        ValueError: If job_number column is missing or no valid job numbers found
    """
    everything_job_path = Path(everything_job_csv)
    csv_jobs_folder_path = Path(csv_jobs_folder)
    
    # Validate inputs
    validate_csv_file(everything_job_path, "Everything job CSV")
    
    # Create output folder if it doesn't exist
    csv_jobs_folder_path.mkdir(parents=True, exist_ok=True)
    
    # Load the everything job CSV
    df = pd.read_csv(everything_job_path)
    
    # Check if job_number column exists
    if 'job_number' not in df.columns:
        raise ValueError("job_number column not found in everything_job.csv")
    
    # Remove rows where job_number is empty or NaN
    df_filtered = df[df['job_number'].notna() & (df['job_number'] != '')]
    
    if len(df_filtered) == 0:
        print("Warning: No rows with job_number found. No job files will be created.")
        return []
    
    # Get unique job numbers
    unique_job_numbers = df_filtered['job_number'].unique()
    print(f"Found {len(unique_job_numbers)} unique job numbers: {sorted(unique_job_numbers)}")
    
    # Split into separate files
    created_files = []
    progress = ProgressPrinter("Creating job files", len(unique_job_numbers))
    
    for i, job_number in enumerate(sorted(unique_job_numbers)):
        progress.update(i + 1)
        
        # Filter rows for this job number
        job_df = df_filtered[df_filtered['job_number'] == job_number].copy()
        
        # Create filename
        job_filename = f"Job_{job_number}.csv"
        job_file_path = csv_jobs_folder_path / job_filename
        
        # Remove the job_number column from the output (it's no longer needed in individual files)
        job_df_output = job_df.drop(columns=['job_number'])
        
        # Save to CSV
        job_df_output.to_csv(job_file_path, index=False)
        created_files.append(str(job_file_path))
        
        # print(f"  Created {job_filename} with {len(job_df)} rows")
    
    progress.done()
    
    print(f"\nSplit completed! Created {len(created_files)} job files in {csv_jobs_folder_path}")
    return created_files
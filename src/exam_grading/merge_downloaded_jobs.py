"""Merge downloaded grading jobs from multiple graders.

This module combines grading results from multiple graders into a single
consolidated file. It handles conflicts where the same student/problem/subquestion
was graded by multiple people, allowing interactive resolution of discrepancies.
This is essential for courses with multiple TAs or when problems are split
across graders.
"""
from pathlib import Path
import pandas as pd
from typing import Optional

from .common.validators import validate_directory
from .common.progress import ProgressPrinter


def merge_downloaded_jobs(downloaded_jobs_folder: str, output_file: Optional[str] = None) -> str:
    """Merge all downloaded job CSV files into a single consolidated file.
    
    This function combines grading data from multiple CSV files, detecting and
    resolving conflicts where the same item was graded by multiple people. It
    provides an interactive interface for choosing which grader's work to keep
    when conflicts arise.
    
    Args:
        downloaded_jobs_folder: Path to folder containing downloaded job CSV files
        output_file: Optional output file path. Defaults to "merged_grading_jobs.csv"
                    in the parent directory of the input folder.
        
    Returns:
        str: Path to the merged CSV file
        
    Conflict Resolution:
        When multiple graders have graded the same student/problem/subquestion:
        1. Shows all graders' scores and feedback
        2. Prompts user to choose which grader's work to keep
        3. Preserves the chosen grader's entire row of data
        
    Output Format:
        The merged file includes all columns from the input files plus:
        - grader_id: Extracted from the filename prefix
        - source_file: Original filename for traceability
        
    Example:
        Input files: ta1_Job_1.csv, ta2_Job_2.csv with overlapping items
        Output: merged_grading_jobs.csv with conflicts resolved
        
    Note:
        - Conflicts are identified by (student_id, problem, subquestion) tuples
        - All grading data (scores, feedback, flags) is preserved for chosen rows
        - User interaction is required for conflict resolution
    """
    downloaded_jobs_folder = Path(downloaded_jobs_folder)
    validate_directory(downloaded_jobs_folder, "Downloaded jobs folder")
    
    # Find all CSV files
    csv_files = list(downloaded_jobs_folder.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {downloaded_jobs_folder}")
    
    print(f"\nFound {len(csv_files)} job files to merge")
    
    # Load all CSV files with grader info
    all_jobs = []
    progress = ProgressPrinter("Loading job files", len(csv_files))
    
    for i, csv_file in enumerate(csv_files):
        progress.update(i + 1)
        
        # Extract grader ID from filename (before first underscore)
        grader_id = csv_file.stem.split('_')[0]
        
        # Load CSV and add grader column
        df = pd.read_csv(csv_file)
        df['grader_id'] = grader_id
        df['source_file'] = csv_file.name
        all_jobs.append(df)
    
    progress.done()
    
    # Concatenate all dataframes
    merged_df = pd.concat(all_jobs, ignore_index=True)
    print(f"\nTotal rows before deduplication: {len(merged_df)}")
    
    # Find duplicates based on student, problem, and subquestion
    duplicate_key_columns = ['student_id', 'problem', 'subquestion']
    
    # Check if these columns exist
    missing_cols = [col for col in duplicate_key_columns if col not in merged_df.columns]
    if missing_cols:
        print(f"Warning: Missing columns {missing_cols}. Available columns: {list(merged_df.columns)}")
    
    # Group by the key columns to find duplicates
    grouped = merged_df.groupby(duplicate_key_columns)
    
    # Process each group
    final_rows = []
    conflicts_resolved = 0
    
    for group_key, group_df in grouped:
        if len(group_df) == 1:
            # No conflict, use the single row
            final_rows.append(group_df.iloc[0])
        else:
            # Conflict detected - multiple graders for same student/problem/subquestion
            conflicts_resolved += 1
            
            print(f"\n{'='*60}")
            print(f"Conflict #{conflicts_resolved}: Multiple graders for:")
            print(f"  Student: {group_key[0]}")
            print(f"  Problem: {group_key[1]}")
            print(f"  Subquestion: {group_key[2]}")
            print(f"\nGraders and their scores:")
            
            # Show each grader's work
            for idx, (_, row) in enumerate(group_df.iterrows()):
                score_col = 'adjusted_score' if 'adjusted_score' in row else None
                score_info = f", Score: {row[score_col]}" if score_col else ""
                
                print(f"  {idx + 1}. Grader: {row['grader_id']} (from {row['source_file']}){score_info}")
                
                # Show additional grading info if available
                if 'feedback' in row and pd.notna(row['feedback']):
                    print(f"     Feedback: {row['feedback'][:100]}...")

            # Ask user to choose
            while True:
                try:
                    choice = input(f"\nWhich grader's work should be used? (1-{len(group_df)}): ").strip()
                    choice_idx = int(choice) - 1
                    
                    if 0 <= choice_idx < len(group_df):
                        chosen_row = group_df.iloc[choice_idx].copy()
                        final_rows.append(chosen_row)
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(group_df)}")
                except (ValueError, KeyboardInterrupt):
                    print("Invalid input. Please enter a number.")
    
    # Create final dataframe
    final_df = pd.DataFrame(final_rows)
    
    # Determine output file path
    if output_file is None:
        output_file = downloaded_jobs_folder.parent / "merged_grading_jobs.csv"
    else:
        output_file = Path(output_file)
    
    # Save merged file
    final_df.to_csv(output_file, index=False)
    
    print(f"\n{'='*60}")
    print(f"Merge complete!")
    print(f"  Total rows after deduplication: {len(final_df)}")
    print(f"  Conflicts resolved: {conflicts_resolved}")
    print(f"  Output file: {output_file}")
    
    return str(output_file)
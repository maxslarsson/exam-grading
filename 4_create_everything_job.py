#!/usr/bin/env python3
"""
Create everything_job.csv that combines bubble sheet data with student answers.
For each student_id/problem/subquestion combination, includes the page number
from bubbles.csv if it exists.

Usage: python 4_create_everything_job.py <bubbles_csv_path> <consolidated_answers_csv_path>
"""

import sys
import pandas as pd
from pathlib import Path

def create_everything_job(bubbles_path, answers_path):
    """Create everything_job.csv with all student/problem/subquestion combinations"""
    # Define paths
    output_dir = bubbles_path.parent / 'csv_jobs'
    output_path = output_dir / 'everything_job.csv'
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Read bubbles.csv and create mapping
    bubbles_df = pd.read_csv(bubbles_path)
    # Convert question to string for consistent mapping
    bubbles_df['question'] = bubbles_df['question'].astype(str)
    # Ensure page is stored as integer
    bubbles_df['page'] = bubbles_df['page'].astype(int)
    # Keep only the first occurrence of each question-subquestion pair
    bubble_map = bubbles_df.drop_duplicates(subset=['question', 'subquestion']).set_index(['question', 'subquestion'])['page'].to_dict()
    
    # Read consolidated answers
    answers_df = pd.read_csv(answers_path)
    
    # Melt the answers dataframe to long format
    melted_df = answers_df.melt(id_vars=['student_id'], var_name='question_subquestion', value_name='answer')
    
    # Filter out rows that don't have the expected format
    melted_df = melted_df[melted_df['question_subquestion'].str.contains('.')]
    
    # Split question.subquestion into separate columns
    melted_df[['problem', 'subquestion']] = melted_df['question_subquestion'].str.split('.', expand=True)
    
    # Add page numbers from bubble_map
    # For each subquestion, include both its own page and the root problem page (first subquestion)
    def get_page_numbers(row):
        pages = []
        
        # Get the page for the current subquestion
        current_page = bubble_map.get((row['problem'], row['subquestion']), None)
        
        # Also get the problem statement page
        problem_statement_page = bubble_map.get((row['problem'], 'i'), None)
        if problem_statement_page and str(problem_statement_page - 1) not in pages:
            pages.append(str(problem_statement_page - 1))

        if current_page:
            pages.append(str(current_page))
        
        return ','.join(pages)
    
    melted_df['page_numbers'] = melted_df.apply(get_page_numbers, axis=1)
    
    # Select and reorder columns
    output_df = melted_df[['student_id', 'problem', 'subquestion', 'answer', 'page_numbers']].copy()
    
    # Fill NaN values with empty strings
    output_df['answer'] = output_df['answer'].fillna('')
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)
    
    print(f"Created {output_path} with {len(output_df)} rows")

def main():
    # Get the arguments that were passed to the script
    _, script_args = sys.argv[0], sys.argv[1:]
    
    # If less than two arguments were given to the script, we do not have the CSV files we need
    if len(script_args) < 2:
        print("Error: not enough arguments were given to the script")
        print("Usage: python 4_create_everything_job.py <bubbles_csv_path> <consolidated_answers_csv_path>")
        sys.exit(1)
    
    # Parse arguments
    bubbles_path = Path(script_args[0])
    answers_path = Path(script_args[1])
    
    # Validate paths
    if not bubbles_path.is_file():
        print(f"Error: bubbles CSV file not found: {bubbles_path}")
        sys.exit(1)
    
    if not answers_path.is_file():
        print(f"Error: consolidated answers CSV file not found: {answers_path}")
        sys.exit(1)
    
    # Create everything job
    create_everything_job(bubbles_path, answers_path)

if __name__ == "__main__":
    main()
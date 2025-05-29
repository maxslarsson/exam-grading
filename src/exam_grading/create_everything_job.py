"""Create everything_job.csv that combines bubble sheet data with student answers."""
import pandas as pd
from pathlib import Path

from .common.validators import validate_csv_file


def create_everything_job(bubbles_csv_path: str, consolidated_answers_csv_path: str) -> str:
    """
    Create everything_job.csv with all student/problem/subquestion combinations.
    
    Args:
        bubbles_csv_path: Path to bubbles.csv file
        consolidated_answers_csv_path: Path to consolidated answers CSV file
        
    Returns:
        Path to the created everything_job.csv file
    """
    bubbles_path = Path(bubbles_csv_path)
    answers_path = Path(consolidated_answers_csv_path)
    
    # Validate paths
    validate_csv_file(bubbles_path, "Bubbles CSV file")
    validate_csv_file(answers_path, "Consolidated answers CSV file")
    
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
    return str(output_path)
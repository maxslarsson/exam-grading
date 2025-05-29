"""Create everything_job.csv that combines bubble sheet data with student answers."""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from fuf_service.questiondb import QuestionDB, QuestionDBMapping
from fuf_service.problem import Problem, AnswerValue, Subquestion, ChoiceType
from TexSoup import TexSoup
from pydantic import TypeAdapter

from .common.roman_numerals import convert_roman_to_int
from .common.validators import validate_csv_file


def path_relative_to(source: Path, path: Path) -> Path:
    """Returns the path `path` relative to a source path.

    For example, if path is `./folder/file.txt` and we want it relative to `~/folder2`, then this function would return
    the path `~/folder2/folder/file.txt`.

    Args:
        source: The base path.
        path: The relative path that will be converted to be relative to the source path.

    Returns:
        The path relative to the source path.
    """
    if source.is_file():
        return (source.parent / path).resolve()
    else:
        return (source / path).resolve()
    

def load_questiondb(questiondb_path: Path) -> list[Problem]:
    """
    Load QuestionDB and parse all problems.
    
    Args:
        questiondb_path: Path to questiondb.json file
        
    Returns:
        Dictionary mapping problem names to Problem objects
    """
    
    if not questiondb_path.exists():
        print(f"Warning: QuestionDB not found at {questiondb_path}")
        return []
    
    try:
        ta = TypeAdapter(QuestionDB)
        questiondb = ta.validate_json(questiondb_path.read_bytes())

        problems = []
        for mapping in questiondb:
            problem_path = path_relative_to(questiondb_path.parent, Path(mapping.path))
            soup = TexSoup(problem_path.read_text())
            problem = Problem.from_latex(soup)
            problems.append(problem)
        return problems
    except Exception as e:
        print(f"Error loading QuestionDB: {e}")
        return []


def calculate_suggested_score(subquestion: Subquestion, student_answer: str) -> Optional[float]:
    """
    Calculate suggested score based on student answer and problem definition.
    Args:
        subquestion: Subquestion object containing answer values
        student_answer: Student's answer

    Returns:
        Suggested score or None if cannot be determined
    """


    for answer_value in subquestion.answer_values:
        if answer_value.name == student_answer:
            if answer_value.default_score is not None:
                return answer_value.default_score
        
        if answer_value.point == student_answer:
            if answer_value.default_score is not None:
                return answer_value.default_score

    return None


def create_everything_job(bubbles_csv_path: str, consolidated_answers_csv_path: str, questiondb_path: str) -> str:
    """
    Create everything_job.csv with all student/problem/subquestion combinations.
    
    Args:
        bubbles_csv_path: Path to bubbles.csv file
        consolidated_answers_csv_path: Path to consolidated answers CSV file
        questiondb_path: Optional path to questiondb.json file. If not provided, will search in parent directories.
        
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
    
    # Add suggested_score column
    output_df['suggested_score'] = None

    # Load QuestionDB
    qdb_path = Path(questiondb_path)
    if qdb_path.exists() and qdb_path.is_file():
        problems = load_questiondb(qdb_path)
        
        if problems:
            print(f"Loaded {len(problems)} problems from QuestionDB")

            # Calculate suggested scores
            for idx, row in output_df.iterrows():
                try:
                    # Convert to int and adjust for 0-based indexing
                    problem_idx = int(row['problem']) - 1
                    if problem_idx < 0 or problem_idx >= len(problems):
                        print(f"Warning: Problem {row['problem']} not found in QuestionDB")
                        continue
                    
                    problem = problems[problem_idx]

                    # Convert subquestion to int (assuming 1-based indexing)
                    subquestion_idx = convert_roman_to_int(row['subquestion']) - 1
                    if subquestion_idx < 0 or subquestion_idx >= len(problem.subquestions):
                        print(f"Warning: Subquestion {row['subquestion']} not found in problem {row['problem']}")
                        continue

                    subquestion = problem.subquestions[subquestion_idx]
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid problem/subquestion indices: {row['problem']}, {row['subquestion']} - {e}")
                    continue

                suggested = calculate_suggested_score(subquestion, row['answer'])
                output_df.at[idx, 'suggested_score'] = suggested
            
            # Count how many scores were suggested
            suggested_count = (output_df['suggested_score'] != '').sum()
            print(f"Calculated {suggested_count} suggested scores")
    else:
        print(f"QuestionDB path not found or not a file: {qdb_path}")

    # Write to CSV
    output_df.to_csv(output_path, index=False)
    
    print(f"Created {output_path} with {len(output_df)} rows")
    return str(output_path)
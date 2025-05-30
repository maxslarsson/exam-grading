"""Create everything_job.csv that combines bubble sheet data with student answers.

This module generates the master grading job CSV file that combines:
1. Student answers from OMR processing
2. Bubble position data to determine page numbers
3. Question database information for scoring
4. All metadata needed for the grading service

The output is a long-format CSV with one row per student/problem/subquestion
combination, ready to be split and uploaded to the grading service.
"""
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
    """Convert a relative path to be relative to a source path.
    
    This utility function resolves relative paths in the question database
    to absolute paths based on the database location.

    For example, if path is `./problems/problem1.tex` and source is 
    `/home/user/exam/questiondb.json`, this returns 
    `/home/user/exam/problems/problem1.tex`.

    Args:
        source: The base path (typically the questiondb.json location)
        path: The relative path to resolve

    Returns:
        Path: Absolute path resolved relative to the source
    """
    if source.is_file():
        # If source is a file, use its parent directory as base
        return (source.parent / path).resolve()
    else:
        # If source is a directory, use it directly as base
        return (source / path).resolve()
    

def load_questiondb(questiondb_path: Path) -> list[Problem]:
    """Load QuestionDB and parse all problems from LaTeX sources.
    
    This function reads the question database JSON file and parses the
    LaTeX source for each problem to extract metadata like answer values
    and default scores.
    
    Args:
        questiondb_path: Path to questiondb.json file containing problem mappings
        
    Returns:
        List of Problem objects with parsed metadata
        
    Note:
        The questiondb.json format is:
        [
            {
                "name": "Problem 1",
                "path": "./problems/problem1.tex",
                "metadata": {...}
            },
            ...
        ]
    """
    if not questiondb_path.exists():
        print(f"Warning: QuestionDB not found at {questiondb_path}")
        return []
    
    try:
        # Use TypeAdapter for Pydantic v2 JSON parsing
        ta = TypeAdapter(QuestionDB)
        questiondb = ta.validate_json(questiondb_path.read_bytes())

        problems = []
        for mapping in questiondb:
            # Resolve relative problem paths
            problem_path = path_relative_to(questiondb_path.parent, Path(mapping.path))
            
            # Parse LaTeX to extract problem structure
            soup = TexSoup(problem_path.read_text())
            problem = Problem.from_latex(soup)
            problems.append(problem)
        return problems
    except Exception as e:
        print(f"Error loading QuestionDB: {e}")
        return []


def calculate_suggested_score(subquestion: Subquestion, student_answer: str) -> Optional[float]:
    """Calculate suggested score based on student answer and problem definition.
    
    This function matches the student's answer against the defined answer values
    in the problem database and returns the default score if available. It checks
    both the answer name (e.g., "a", "b") and point value (e.g., "\\pi", "2").
    
    Args:
        subquestion: Subquestion object containing answer values with default scores
        student_answer: Student's answer string from OMR
        
    Returns:
        Optional[float]: Default score for the answer, or None if no match found
        
    Example:
        If subquestion has answer_values:
        - name="a", point="\\pi", default_score=1.0
        - name="b", point="2\\pi", default_score=0.5
        
        And student_answer="a", returns 1.0
    """
    # Check each defined answer value for the subquestion
    for answer_value in subquestion.answer_values:
        # Match by answer name (e.g., "a", "b", "c")
        if answer_value.name == student_answer:
            if answer_value.default_score is not None:
                return answer_value.default_score
        
        # Also match by point value (e.g., mathematical expressions)
        if answer_value.point == student_answer:
            if answer_value.default_score is not None:
                return answer_value.default_score

    # No match found
    return None


def create_everything_job(bubbles_csv_path: str, consolidated_answers_csv_path: str, questiondb_path: str, output_path: str) -> str:
    """Create everything_job.csv with all student/problem/subquestion combinations.
    
    This is the main function that combines all data sources to create the master
    grading job file. It transforms the wide-format answer data into long format,
    adds page numbers from bubble positions, and calculates suggested scores from
    the question database.
    
    Args:
        bubbles_csv_path: Path to bubbles.csv file with bubble position definitions
        consolidated_answers_csv_path: Path to consolidated answers from OMR (wide format)
        questiondb_path: Path to questiondb.json file with problem definitions
        output_path: Path for the output everything_job.csv file
        
    Returns:
        str: Path to the created everything_job.csv file
        
    Output CSV format:
        student_id,problem,subquestion,answer,page_numbers,suggested_score,job_number
        abc123,1,i,a,"0,1",1.0,
        abc123,1,ii,b,"0,1",0.5,
        ...
        
    Note:
        - page_numbers includes both the problem statement page and subquestion page
        - suggested_score is populated from the question database if available
        - job_number is left blank for later assignment during job splitting
    """
    bubbles_path = Path(bubbles_csv_path)
    answers_path = Path(consolidated_answers_csv_path)
    
    # Validate paths
    validate_csv_file(bubbles_path, "Bubbles CSV file")
    validate_csv_file(answers_path, "Consolidated answers CSV file")
    
    output_path = Path(output_path)
    output_dir = output_path.parent
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
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
        """Get comma-separated page numbers for a question/subquestion.
        
        Returns both the problem statement page (subquestion 'i' minus 1) and
        the actual subquestion page. This allows graders to see the full context.
        """
        pages = []
        
        # Get the page for the current subquestion
        current_page = bubble_map.get((row['problem'], row['subquestion']), None)
        
        # Also get the problem statement page (typically where subquestion 'i' is)
        # We subtract 1 because the problem statement is usually on the previous page
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

    # Add blank "job_number" column at the end
    output_df['job_number'] = ''

    # Write to CSV
    output_df.to_csv(output_path, index=False)
    
    print(f"Created {output_path} with {len(output_df)} rows")
    return str(output_path)
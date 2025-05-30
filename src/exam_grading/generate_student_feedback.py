"""Generate personalized feedback for students based on their exam performance."""

import shutil
import pandas as pd
from pathlib import Path
from typing import List, Optional
from fuf.latex.create_homework_feedback import generate_student_feedback
from fuf_service.questiondb import QuestionDB
from pydantic import TypeAdapter

from .common.progress import ProgressPrinter
from .common.validators import validate_csv_file, validate_file


COURSE_NAME = "Test Course"


def get_subquestion_page_numbers(problem_name: str, subquestion_name: str, student_id: str, df_merged_jobs: pd.DataFrame) -> List[int]:
    """Extract page numbers for a specific subquestion from merged grading jobs.
    
    Args:
        problem_name: The name/identifier of the problem (e.g., "1", "2", etc.)
        subquestion_name: The name/identifier of the subquestion (e.g., "i", "ii", etc.)
        student_id: The student's ID
        df_merged_jobs: DataFrame containing grading jobs with page_numbers column
        
    Returns:
        List of page numbers (1-indexed) for this subquestion
    """
    # Filter for this student, problem, and subquestion
    try:
        problem_int = int(problem_name)
    except ValueError:
        return []
    
    student_jobs = df_merged_jobs[
        (df_merged_jobs['student_id'] == student_id) & 
        (df_merged_jobs['problem'] == problem_int) &
        (df_merged_jobs['subquestion'] == subquestion_name)
    ]
    
    if student_jobs.empty:
        return []
    
    # Get all unique page_numbers values for this subquestion
    page_numbers_set = set()
    for _, row in student_jobs.iterrows():
        page_numbers_str = str(row['page_numbers']).strip()
        if page_numbers_str and page_numbers_str != 'nan':
            # Handle comma-separated values
            pages = [p.strip() for p in page_numbers_str.split(',')]
            for page in pages:
                try:
                    page_numbers_set.add(int(page))
                except ValueError:
                    continue
    
    return sorted(list(page_numbers_set))


def get_student_grader_id(student_id: str, df_merged_jobs: pd.DataFrame) -> Optional[str]:
    """Get the grader ID for a specific student from merged grading jobs.
    
    Args:
        student_id: The student's ID
        df_merged_jobs: DataFrame containing grading jobs with grader_id column
        
    Returns:
        The grader ID for this student, or None if not found
    """
    student_jobs = df_merged_jobs[df_merged_jobs['student_id'] == student_id]
    
    if student_jobs.empty:
        return None
    
    # Get the first non-null grader_id
    grader_ids = student_jobs['grader_id'].dropna().unique()
    return grader_ids[0] if len(grader_ids) > 0 else None


def find_annotated_pdf_pages(
    student_id: str, 
    page_numbers: List[int], 
    grader_id: Optional[str], 
    annotated_pdfs_dir: Path
) -> List[Path]:
    """Find annotated PDF pages for a student, with fallback to student work.
    
    Args:
        student_id: The student's ID
        page_numbers: List of page numbers to find
        grader_id: The grader's ID (can be None)
        annotated_pdfs_dir: Base directory containing annotated PDFs
        
    Returns:
        List of PDF file paths (annotated or student work)
    """
    pdf_files = []
    
    for page_num in page_numbers:
        pdf_file = None
        
        # First try annotated version if grader_id is available
        if grader_id:
            annotated_path = annotated_pdfs_dir / "grading" / "annotated" / grader_id / f"{student_id}_{page_num}_annotated.pdf"
            if annotated_path.exists():
                pdf_file = annotated_path
        
        # Fallback to student work if annotated version doesn't exist
        if pdf_file is None:
            student_work_path = annotated_pdfs_dir / "grading" / "student_work" / f"{student_id}_{page_num}.pdf"
            if student_work_path.exists():
                pdf_file = student_work_path
        
        # Only add if file was found
        if pdf_file is not None:
            pdf_files.append(pdf_file)
    
    return pdf_files


def create_scan_mapping_for_student(
    student_id: str,
    questiondb,
    df_merged_jobs: pd.DataFrame,
    annotated_pdfs_dir: Optional[Path]
) -> Optional[dict]:
    """Create a scan mapping dictionary for a specific student.
    
    Args:
        student_id: The student's ID
        questiondb: The question database
        df_merged_jobs: DataFrame with merged grading jobs
        annotated_pdfs_dir: Directory containing annotated PDFs
        
    Returns:
        Dictionary mapping subquestion identifiers (e.g., "1.i", "2.ii") to scan file patterns, or None if no PDFs directory
    """
    if annotated_pdfs_dir is None:
        return None
    
    scan_mapping = {}
    grader_id = get_student_grader_id(student_id, df_merged_jobs)
    
    # Get all unique problem.subquestion combinations for this student
    student_jobs = df_merged_jobs[df_merged_jobs['student_id'] == student_id]
    
    for _, row in student_jobs.iterrows():
        problem_name = str(row['problem'])
        subquestion_name = str(row['subquestion'])
        subquestion_key = f"{problem_name}.{subquestion_name}"
        
        # Get page numbers for this specific subquestion
        page_numbers = get_subquestion_page_numbers(problem_name, subquestion_name, student_id, df_merged_jobs)
        
        if page_numbers:
            pdf_files = find_annotated_pdf_pages(student_id, page_numbers, grader_id, annotated_pdfs_dir)
            if pdf_files:
                # Convert PDF paths to relative paths that can be used as scan patterns
                scan_patterns = [str(pdf_file) for pdf_file in pdf_files]
                scan_mapping[subquestion_key] = scan_patterns
    
    return scan_mapping if scan_mapping else None


def create_multiindex_dataframe_from_merged_jobs(merged_jobs_df: pd.DataFrame, students_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a multi-index DataFrame from merged grading jobs.
    
    Args:
        merged_jobs_df: DataFrame with merged grading jobs
        students_df: DataFrame with student information (studentID, first_name, last_name, email)
        
    Returns:
        DataFrame with multi-index columns for all problem.subquestion combinations
    """
    # Get all unique problem.subquestion combinations
    problem_subquestion_pairs = []
    for _, row in merged_jobs_df.iterrows():
        pair = (row['problem'], str(row['subquestion']))
        if pair not in problem_subquestion_pairs:
            problem_subquestion_pairs.append(pair)
    
    # Sort the pairs
    problem_subquestion_pairs.sort()
    
    # Create multi-index columns
    column_labels = ["Answer", "Score", "Standard Error", "Ind. Feedback"]
    multi_columns = []
    
    # Add the student info columns first
    multi_columns.extend([
        ("", "studentID"),
        ("", "first_name"), 
        ("", "last_name"),
        ("", "email")
    ])
    
    # Add columns for each problem.subquestion
    for problem, subquestion in problem_subquestion_pairs:
        for label in column_labels:
            multi_columns.append((f"{problem}.{subquestion}", label))
    
    # Get all unique students
    students = merged_jobs_df['student_id'].unique()
    
    # Create the DataFrame
    df = pd.DataFrame(index=students, columns=pd.MultiIndex.from_tuples(multi_columns))
    df.index.name = "studentID"
    
    # Create student info lookup from students_df
    student_info = {}
    for _, row in students_df.iterrows():
        student_info[row['studentID']] = {
            "first_name": row['first_name'],
            "last_name": row['last_name'],
            "email": row['email']
        }
    
    # Fill in the data
    for student_id in students:
        # Set student info
        df.loc[student_id, ("", "studentID")] = student_id
        
        if student_id in student_info:
            df.loc[student_id, ("", "first_name")] = student_info[student_id]["first_name"]
            df.loc[student_id, ("", "last_name")] = student_info[student_id]["last_name"]
            df.loc[student_id, ("", "email")] = student_info[student_id]["email"]
        else:
            # Default values for unknown students
            df.loc[student_id, ("", "first_name")] = "Unknown"
            df.loc[student_id, ("", "last_name")] = "Student"
            df.loc[student_id, ("", "email")] = f"unknown@yale.edu"
        
        # Get student's answers
        student_rows = merged_jobs_df[merged_jobs_df['student_id'] == student_id]

        # Fill in answers for each problem.subquestion
        for problem, subquestion in problem_subquestion_pairs:
            col_prefix = f"{problem}.{subquestion}"
            
            # Find the row for this problem.subquestion
            matching_rows = student_rows[
                (student_rows['problem'] == problem) & 
                (student_rows['subquestion'] == subquestion)
            ]
            
            if len(matching_rows) > 0:
                row = matching_rows.iloc[0]
                
                # Fill in the data
                df.loc[student_id, (col_prefix, "Answer")] = row.get('answer', '')
                df.loc[student_id, (col_prefix, "Score")] = row.get('adjusted_score', 0)
                
                # Standard error handling
                standard_error = row.get('standard_error', row.get('general_error', ''))
                if pd.isna(standard_error):
                    standard_error = ''
                df.loc[student_id, (col_prefix, "Standard Error")] = standard_error
                
                df.loc[student_id, (col_prefix, "Ind. Feedback")] = row.get('feedback', '')
            else:
                # Student didn't answer this question
                df.loc[student_id, (col_prefix, "Answer")] = ''
                df.loc[student_id, (col_prefix, "Score")] = 0
                df.loc[student_id, (col_prefix, "Standard Error")] = ''
                df.loc[student_id, (col_prefix, "Ind. Feedback")] = "It looks like you did not submit your exam"
    
    return df


def generate_feedback_for_one_student(
    student_row: pd.Series,
    questiondb: QuestionDB,
    df_round_one: pd.DataFrame,
    output_dir: Path,
    scan_mapping: Optional[dict] = None
) -> Path:
    """
    Generate personalized feedback for one student.
    
    Args:
        student_row: Series with student data
        questiondb: The question database
        df_round_one: Multi-index DataFrame with all student data
        output_dir: Directory to save feedback PDFs
        
    Returns:
        Path to the generated PDF file
    """
    question_names = [q.name for q in questiondb]
    
    # Generate the LaTeX feedback
    latex = generate_student_feedback(
        COURSE_NAME, 
        student_row, 
        question_names, 
        questiondb, 
        df_round_one, 
        None,
        scan_mapping=scan_mapping
    )
    
    # Save the PDF
    file_path = output_dir / f"{student_row.name}_feedback.pdf"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    latex.generate_pdf(file_path.with_suffix(''))
    # latex.generate_tex(file_path.with_suffix(''))
    
    return file_path


def generate_feedback_for_all_students(
        merged_grading_jobs_path: str,
        questiondb_path: str,
        students_csv_path: str,
        annotated_pdfs_dir: Optional[str] = None
) -> List[Path]:
    """
    Generate personalized feedback for all students based on their exam performance.
    
    Args:
        merged_grading_jobs_path (str): Path to the CSV file with merged grading results.
        questiondb_path (str): Path to the question database (questiondb.json).
        students_csv_path (str): Path to the students CSV file with columns: studentID, first_name, last_name, email

    Returns:
        List of paths to generated feedback PDFs
    """
    merged_grading_jobs_path = Path(merged_grading_jobs_path)
    questiondb_path = Path(questiondb_path)
    students_csv_path = Path(students_csv_path)
    annotated_pdfs_path = Path(annotated_pdfs_dir) if annotated_pdfs_dir else None
    
    # Validate inputs
    validate_csv_file(merged_grading_jobs_path, "Merged grading jobs file")
    validate_file(questiondb_path, "Question database file")
    validate_csv_file(students_csv_path, "Students CSV file")
    
    # Load question database
    ta = TypeAdapter(QuestionDB)
    questiondb = ta.validate_json(questiondb_path.read_bytes())
    
    # Load merged grading jobs
    merged_jobs_df = pd.read_csv(merged_grading_jobs_path)
    
    # Load students data
    students_df = pd.read_csv(students_csv_path)
    
    # Verify required columns in students CSV
    required_cols = ['studentID', 'first_name', 'last_name', 'email']
    missing_cols = [col for col in required_cols if col not in students_df.columns]
    if missing_cols:
        raise ValueError(f"Students CSV is missing required columns: {missing_cols}")
    
    # Create multi-index DataFrame
    print("\nCreating multi-index feedback DataFrame...")
    df_round_one = create_multiindex_dataframe_from_merged_jobs(merged_jobs_df, students_df)
    
    # Get unique students
    students = df_round_one.index.tolist()
    print(f"Found {len(students)} students to generate feedback for")
    
    # Output directory
    output_dir = merged_grading_jobs_path.parent / "student_feedback"
    output_dir.mkdir(parents=True, exist_ok=True)

    latex_dir = output_dir / "LaTeXclass"
    shutil.rmtree(latex_dir, ignore_errors=True)
    shutil.copytree("../problems/LaTeXclass", latex_dir, dirs_exist_ok=True)

    # Generate feedback for each student
    feedback_files = []
    progress = ProgressPrinter("Generating student feedback", len(students))
    
    for i, student_id in enumerate(students):
        progress.update(i + 1)
        
        try:
            student_cols = ["first_name", "last_name", "email"]
            student_row = df_round_one.loc[student_id, (slice(None), student_cols)]
            student_row.index = pd.Index(student_cols)
            
            # Create scan mapping for this student if annotated PDFs are available
            scan_mapping = None
            if annotated_pdfs_path:
                scan_mapping = create_scan_mapping_for_student(
                    student_id, 
                    questiondb, 
                    merged_jobs_df, 
                    annotated_pdfs_path
                )
            
            pdf_path = generate_feedback_for_one_student(
                student_row, 
                questiondb, 
                df_round_one,
                output_dir,
                scan_mapping
            )
            feedback_files.append(pdf_path)
        except Exception as e:
            print(f"\nError generating feedback for {student_id}: {e}")
    
    progress.done()
    
    return feedback_files
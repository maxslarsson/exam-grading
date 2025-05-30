# Feedback System Documentation

## Overview

The feedback system generates personalized PDF reports for each student and distributes them via email. It combines grading results with scanned work to create comprehensive feedback documents using LaTeX.

## Module: `generate_student_feedback.py`

### Purpose
Generates individualized PDF feedback for students using LaTeX templates and the FUF library.

### Main Functions

#### generate_feedback_for_all_students()

Creates feedback PDFs for all students in the grading results.

**Parameters**:
- `merged_grading_jobs_path`: Path to CSV with consolidated grading data
- `questiondb_path`: Path to question database JSON
- `students_csv_path`: Path to student information CSV
- `annotated_pdfs_dir`: Optional directory with annotated PDFs

**Returns**: List of generated PDF file paths

**Process Flow**:
1. Load and validate input data
2. Create multi-index DataFrame structure
3. Generate feedback for each student
4. Copy LaTeX templates to output directory
5. Return list of created PDFs

**Example Usage**:
```python
pdf_files = generate_feedback_for_all_students(
    merged_grading_jobs_path="./merged_grading_jobs.csv",
    questiondb_path="./questiondb.json",
    students_csv_path="./students.csv",
    annotated_pdfs_dir="./annotated_pdfs"
)
```

### Data Transformation

#### Multi-index DataFrame Structure

The system transforms flat grading data into a structured format:

**Input** (merged_grading_jobs.csv):
```csv
student_id,problem,subquestion,answer,adjusted_score,standard_error,feedback
abc123,1,i,a,5.0,,"Good work"
abc123,1,ii,b,3.5,"Missing steps",
```

**Output** (Multi-index DataFrame):
```
Columns: [('1.i', 'Answer'), ('1.i', 'Score'), ('1.i', 'Standard Error'), ('1.i', 'Ind. Feedback'),
          ('1.ii', 'Answer'), ('1.ii', 'Score'), ...]
```

### PDF Generation Process

#### 1. Scan Mapping Creation

Maps each subquestion to its corresponding PDF files:

```python
scan_mapping = {
    "1.i": ["./graded/abc123_1_annotated.pdf"],
    "1.ii": ["./graded/abc123_1_annotated.pdf"],
    "2.i": ["./student_work/abc123_2.pdf"]
}
```

**Priority Order**:
1. Annotated PDFs (if grader exists)
2. Original student work PDFs

#### 2. LaTeX Generation

Uses FUF library to create LaTeX content:

```python
latex_path = fuf.latex.create_homework_feedback.generate_student_feedback(
    course_name="KYPA321 Summer 2025",
    student_id="abc123",
    student_first_name="Alice",
    student_last_name="Smith",
    question_names=["Problem 1", "Problem 2"],
    df_question_scores=multi_index_df.loc["abc123"],
    LaTeXclass_path="./LaTeXclass",
    output_dir="./student_feedback",
    scan_mapping=scan_mapping
)
```

#### 3. PDF Compilation

LaTeX is automatically compiled to PDF using the system's LaTeX installation.

### LaTeX Templates

The system uses custom LaTeX class files:

#### problems.cls

Main document class with options:
- `problemfeedback`: For problem-based feedback
- `homeworkfeedback`: For homework feedback
- `exam`: For exam formatting
- `author`: Show author information
- `replacement`: For replacement pages

#### Supporting Files
- `NRcolors.sty`: Color definitions
- `NRcustom.sty`: Custom commands and formatting
- `YaleLogo.png`, `YaleText.png`: Branding elements

### Error Handling

- **Missing Students**: Use default values (empty name, "Unknown")
- **LaTeX Errors**: Log and continue with next student
- **Missing PDFs**: Skip unavailable scan files
- **Invalid Data**: Handle gracefully with warnings

## Module: `email_feedback_to_students.py`

### Purpose
Distributes generated feedback PDFs to students via Microsoft Outlook.

### Main Function

#### email_feedback_to_students()

Sends feedback PDFs as email attachments.

**Parameters**:
- `feedback_folder`: Directory containing `*_feedback.pdf` files
- `students_csv`: Path to CSV with student emails

**Process**:
1. Load student contact information
2. Find all feedback PDFs
3. Confirm before sending
4. Send emails with attachments
5. Report success/failure statistics

**Example Usage**:
```python
email_feedback_to_students(
    feedback_folder="./student_feedback",
    students_csv="./students.csv"
)
```

### Email Details

**Email Structure**:
- **Subject**: "Your Exam Feedback"
- **Body**: 
  ```
  Dear {first_name},

  Please find attached your exam feedback.

  Best regards,
  Course Team
  ```
- **Attachment**: Student's feedback PDF

### Authentication

Uses Microsoft Graph API via FUF library:
1. OAuth authentication flow
2. Token stored for session
3. Secure API communication

### Safety Features

- **Confirmation Prompt**: Requires "yes" to proceed
- **Dry Run Info**: Shows what will be sent
- **Progress Tracking**: Real-time updates
- **Error Isolation**: Individual failures don't stop batch

## Data Requirements

### Students CSV Format

```csv
studentID,first_name,last_name,email
abc123,Alice,Smith,alice.smith@example.edu
def456,Bob,Jones,bob.jones@example.edu
```

### Merged Grading Jobs Format

Required columns:
- `student_id`: Student identifier
- `problem`: Problem number
- `subquestion`: Subquestion identifier
- `answer`: Student's answer
- `adjusted_score` or `suggested_score`: Numerical score
- `standard_error`: Optional error message
- `general_error`: Optional general feedback
- `feedback`: Optional individual feedback
- `page_numbers`: Comma-separated page numbers
- `grader_id`: Optional grader identifier

### Question Database Format

JSON file with problem definitions:
```json
{
  "problems": [
    {
      "name": "Problem 1",
      "number": 1,
      "subquestions": [...]
    }
  ]
}
```

## Output Structure

### Feedback Directory
```
student_feedback/
├── LaTeXclass/           # LaTeX templates
│   ├── problems.cls
│   ├── NRcolors.sty
│   └── ...
├── abc123_feedback.pdf   # Generated PDFs
├── def456_feedback.pdf
└── ...
```

### PDF Content

Each feedback PDF includes:
1. **Header**: Student name, ID, course information
2. **Problem Sections**: 
   - Question text
   - Student's answer
   - Score and feedback
   - Scanned work (if available)
3. **Summary**: Overall performance metrics

## Dependencies

### External Libraries
- **FUF**: LaTeX generation and email functionality
- **pandas**: Data manipulation
- **pydantic**: Data validation
- **LaTeX**: PDF compilation (system requirement)

### FUF Integration

Key FUF modules used:
- `fuf.latex.create_homework_feedback`: LaTeX generation
- `fuf.outlook.email_feedback_to_students`: Email functionality
- `fuf_service.questiondb`: Question database handling

## Best Practices

### Feedback Generation
1. Validate all input files before processing
2. Use progress tracking for large batches
3. Handle missing data gracefully
4. Preserve original scan quality

### Email Distribution
1. Always confirm before sending
2. Verify email addresses in advance
3. Test with small batch first
4. Monitor delivery failures

### Error Recovery
1. Log all errors with context
2. Continue processing other students
3. Provide summary of failures
4. Allow re-running for failed items

## Example Workflow

```python
# 1. Generate feedback PDFs
pdfs = generate_feedback_for_all_students(
    merged_grading_jobs_path="./merged_jobs.csv",
    questiondb_path="./questiondb.json",
    students_csv_path="./students.csv",
    annotated_pdfs_dir="./annotated_pdfs"
)

# 2. Review generated PDFs
print(f"Generated {len(pdfs)} feedback PDFs")

# 3. Email to students
email_feedback_to_students(
    feedback_folder="./student_feedback",
    students_csv="./students.csv"
)
```

## Troubleshooting

### Common Issues

1. **LaTeX Compilation Errors**
   - Ensure LaTeX is installed
   - Check for special characters in student names
   - Verify template files are present

2. **Missing Scans**
   - Check PDF file naming convention
   - Verify annotated_pdfs_dir path
   - Ensure proper page numbering

3. **Email Failures**
   - Verify Microsoft authentication
   - Check email addresses format
   - Ensure network connectivity

4. **Memory Issues**
   - Process students in batches
   - Clear temporary files
   - Monitor system resources
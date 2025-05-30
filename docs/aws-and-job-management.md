# AWS Integration and Job Management Documentation

## Overview

The exam grading system integrates with AWS S3 for PDF storage and the prprpr grading service for job management. All external interactions use student anonymization to protect privacy.

## AWS Integration

### Module: `upload_pdfs_to_aws.py`

Uploads exam PDFs to AWS S3 with anonymized filenames.

#### Function: upload_pdfs_to_aws(parsed_folder_path: str, students_csv_path: str)

**Purpose**: Upload all PDFs from local folder to S3 bucket

**Parameters**:
- `parsed_folder_path`: Directory containing PDFs to upload
- `students_csv_path`: CSV file with student ID mappings for anonymization

**Process**:
1. Initialize student anonymizer
2. Find all PDF files recursively
3. Anonymize each filename
4. Upload to S3 with structure: `grading/student_work/{anonymized_filename}`
5. Track progress and report failures

**Example Usage**:
```python
upload_pdfs_to_aws(
    "./scans_parsed_OMR/page_1",
    "./students.csv"
)
```

**S3 Structure**:
```
prprpr-s3/
└── grading/
    └── student_work/
        ├── anonymous001_1.pdf
        ├── anonymous001_2.pdf
        └── ...
```

### Module: `get_annotated_pdfs_from_aws.py`

Downloads graded PDFs from AWS S3 with de-anonymization.

#### Function: get_annotated_pdfs_from_aws(destination_folder_path: str, students_csv_path: str)

**Purpose**: Download all graded PDFs and restore original student IDs

**Parameters**:
- `destination_folder_path`: Local directory for downloaded files
- `students_csv_path`: CSV file for de-anonymization

**Process**:
1. List all objects with prefix `grading/`
2. Handle pagination for large result sets
3. Download each PDF
4. De-anonymize filename
5. Preserve directory structure locally

**Error Handling**:
- Separates anonymization errors from download errors
- Collects all failures before reporting
- Provides detailed error messages

## Job Management

### Module: `split_everything_job.py`

Splits master grading job into individual assignments.

#### Function: split_everything_job(everything_job_csv: str, csv_jobs_folder: str) -> list[str]

**Purpose**: Divide master CSV by job_number column

**Parameters**:
- `everything_job_csv`: Path to master job CSV
- `csv_jobs_folder`: Output directory for split jobs

**Returns**: List of created job file paths

**Output Format**:
- Files named: `Job_{number}.csv`
- `job_number` column removed from output
- Empty job numbers filtered out

**Example**:
```python
# Input: everything_job.csv with job_number column
# Output: Job_1.csv, Job_2.csv, Job_3.csv, etc.
job_files = split_everything_job(
    "./everything_job.csv",
    "./csv_jobs"
)
```

### Module: `upload_jobs_to_prprpr.py`

Uploads grading jobs to prprpr API with anonymization.

#### Function: upload_jobs_to_prprpr(csv_folder_path: str, students_csv_path: str)

**Purpose**: Send grading jobs to prprpr service

**Parameters**:
- `csv_folder_path`: Directory containing job CSV files
- `students_csv_path`: CSV for anonymization

**CSV Format**:
```csv
student_id,problem,subquestion,answer,suggested_score
abc123,1,a,correct,5.0
abc123,1,b,partial,2.5
```

**API Request Structure**:
```json
{
  "name": "Job_1",
  "assignee": "grader1",
  "items": [
    {
      "student_id": "anonymous001",
      "problem": 1,
      "subquestion": 1,
      "answer": "correct",
      "suggested_score": 5.0
    }
  ]
}
```

**File Naming Convention**:
- Input: `{assignee}_{job_name}.csv`
- Assignee extracted from filename prefix

**Safety Features**:
- Production confirmation prompt
- OAuth2 authentication
- Progress tracking

### Module: `download_jobs_from_prprpr.py`

Downloads completed grading jobs from prprpr API.

#### Function: download_jobs_from_prprpr(output_folder_path: str, students_csv_path: str)

**Purpose**: Retrieve graded jobs and de-anonymize

**Parameters**:
- `output_folder_path`: Directory for downloaded jobs
- `students_csv_path`: CSV for de-anonymization

**Process**:
1. Authenticate with OAuth2
2. List all available jobs
3. Download job items for each job
4. De-anonymize student IDs
5. Convert to CSV format

**Output Columns**:
- `student_id` (de-anonymized)
- `problem`
- `subquestion` (as Roman numerals)
- `answer`
- `suggested_score`
- `adjusted_score`
- `feedback`
- `is_flagged_for_follow_up`
- `is_submitted`

### Module: `merge_downloaded_jobs.py`

Merges multiple grading jobs with conflict resolution.

#### Function: merge_downloaded_jobs(downloaded_jobs_folder: str, output_file: Optional[str]) -> str

**Purpose**: Combine jobs and resolve grading conflicts

**Parameters**:
- `downloaded_jobs_folder`: Directory with downloaded job CSVs
- `output_file`: Optional output path (defaults to `merged_grading_jobs.csv`)

**Returns**: Path to merged file

**Conflict Resolution**:
1. Detects duplicate grading (same student/problem/subquestion)
2. Shows all graders' scores and feedback
3. Prompts user to choose which grader to keep
4. Adds `grader_id` and `source_file` columns

**Interactive Prompt Example**:
```
Conflict for student abc123, problem 1, subquestion i:
  1. Grader: ta1, Score: 4.5, Feedback: Good work
  2. Grader: ta2, Score: 5.0, Feedback: Excellent
Choose which grader's work to keep (1-2):
```

## Data Transformations

### Anonymization/De-anonymization

**Student CSV Format**:
```csv
student_id,anonymous_id
abc123,student_001
def456,student_002
```

**Filename Transformations**:
- Upload: `abc123_1.pdf` → `student_001_1.pdf`
- Download: `student_001_1.pdf` → `abc123_1.pdf`

### Subquestion Conversion

**Upload (Letter to Number)**:
- a → 1, b → 2, c → 3, etc.

**Download (Number to Roman)**:
- 1 → i, 2 → ii, 3 → iii, etc.

## Authentication

### OAuth2 with PKCE

The system uses OAuth2 with Proof Key for Code Exchange:

1. Generate code verifier and challenge
2. Open browser for user authorization
3. Start local server for callback
4. Exchange authorization code for access token
5. Use token for API requests

### Configuration

**Environment-based Settings**:
```python
# Debug mode (localhost)
PRPRPR_DEBUG = True
PRPRPR_BASE_URL = "http://127.0.0.1:8000"

# Production mode
PRPRPR_DEBUG = False
PRPRPR_BASE_URL = "https://clrify.it"
```

## Error Handling

### Validation Errors
- Missing required files
- Invalid CSV formats
- Unknown student IDs

### Network Errors
- S3 connection failures
- API timeouts
- Authentication failures

### Data Errors
- Anonymization lookup failures
- Missing required fields
- Invalid data types

## Best Practices

### AWS Operations
1. Always use anonymization for uploads
2. Validate all paths before processing
3. Handle pagination for large datasets
4. Report all failures after batch operations

### Job Management
1. Split jobs logically by grader workload
2. Include suggested scores for efficiency
3. Always de-anonymize downloaded data
4. Resolve conflicts interactively

### Security
1. Never store credentials in code
2. Use OAuth2 for API access
3. Anonymize all external data
4. Confirm production operations

## Example Workflow

```python
# 1. Upload PDFs to AWS
upload_pdfs_to_aws("./parsed_pdfs", "./students.csv")

# 2. Create and split jobs
create_everything_job(...)
job_files = split_everything_job("./everything_job.csv", "./jobs")

# 3. Upload jobs to prprpr
upload_jobs_to_prprpr("./jobs", "./students.csv")

# 4. Wait for grading...

# 5. Download completed jobs
download_jobs_from_prprpr("./completed_jobs", "./students.csv")

# 6. Merge results
merged_file = merge_downloaded_jobs("./completed_jobs")

# 7. Download annotated PDFs
get_annotated_pdfs_from_aws("./graded_pdfs", "./students.csv")
```
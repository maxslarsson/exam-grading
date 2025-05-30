# API Reference

## Core Modules

### exam_grading.read_qr_codes

#### Functions

##### read_qr_codes_and_move(exam_scans_folder_path: str) -> str

Reads QR codes from exam scans and organizes images by page number.

**Parameters:**
- `exam_scans_folder_path` (str): Path to folder containing JPEG exam scans

**Returns:**
- str: Path to output folder containing organized images

**Raises:**
- `ValueError`: If input folder doesn't exist
- `RuntimeError`: If QR code reading fails

**Example:**
```python
from exam_grading.read_qr_codes import read_qr_codes_and_move

output_folder = read_qr_codes_and_move("./scans")
print(f"Organized images saved to: {output_folder}")
```

### exam_grading.run_omr

#### Functions

##### run_omr(omr_marker_path: str, bubbles_csv_path: str, parsed_folder_path: str) -> str

Performs optical mark recognition on exam images.

**Parameters:**
- `omr_marker_path` (str): Path to alignment marker image
- `bubbles_csv_path` (str): Path to CSV with bubble coordinates
- `parsed_folder_path` (str): Path to folder with organized images

**Returns:**
- str: Path to output folder containing OMR results

**Raises:**
- `ValueError`: If input files/folders don't exist
- `RuntimeError`: If OMR processing fails

**Example:**
```python
from exam_grading.run_omr import run_omr

output_folder = run_omr(
    "./omr_marker.jpg",
    "./bubbles.csv",
    "./scans_parsed"
)
```

### exam_grading.create_everything_job

#### Functions

##### create_everything_job(bubbles_csv_path: str, consolidated_answers_csv_path: str, questiondb_path: str, output_path: str) -> str

Creates master grading job CSV file.

**Parameters:**
- `bubbles_csv_path` (str): Path to bubble definitions
- `consolidated_answers_csv_path` (str): Path to OMR results
- `questiondb_path` (str): Path to question database JSON
- `output_path` (str): Path for output CSV file

**Returns:**
- str: Path to created job file

**Raises:**
- `ValueError`: If input files don't exist
- `KeyError`: If required columns are missing

**Example:**
```python
from exam_grading.create_everything_job import create_everything_job

job_file = create_everything_job(
    "./bubbles.csv",
    "./consolidated_answers.csv",
    "./questiondb.json",
    "./everything_job.csv"
)
```

### exam_grading.split_everything_job

#### Functions

##### split_everything_job(everything_job_csv: str, csv_jobs_folder: str) -> list[str]

Splits master job into individual grading assignments.

**Parameters:**
- `everything_job_csv` (str): Path to master job CSV
- `csv_jobs_folder` (str): Output directory for split jobs

**Returns:**
- list[str]: List of created job file paths

**Raises:**
- `ValueError`: If input file doesn't exist
- `KeyError`: If job_number column is missing

**Example:**
```python
from exam_grading.split_everything_job import split_everything_job

job_files = split_everything_job(
    "./everything_job.csv",
    "./csv_jobs"
)
print(f"Created {len(job_files)} job files")
```

### exam_grading.upload_pdfs_to_aws

#### Functions

##### upload_pdfs_to_aws(parsed_folder_path: str, students_csv_path: str) -> None

Uploads PDFs to AWS S3 with anonymization.

**Parameters:**
- `parsed_folder_path` (str): Directory containing PDFs
- `students_csv_path` (str): Path to student anonymization CSV

**Raises:**
- `ValueError`: If paths don't exist
- `RuntimeError`: If any uploads fail

**Example:**
```python
from exam_grading.upload_pdfs_to_aws import upload_pdfs_to_aws

upload_pdfs_to_aws(
    "./scans_parsed_OMR",
    "./students.csv"
)
```

### exam_grading.get_annotated_pdfs_from_aws

#### Functions

##### get_annotated_pdfs_from_aws(destination_folder_path: str, students_csv_path: str) -> None

Downloads PDFs from AWS S3 with de-anonymization.

**Parameters:**
- `destination_folder_path` (str): Local directory for downloads
- `students_csv_path` (str): Path to student anonymization CSV

**Raises:**
- `ValueError`: If paths are invalid
- `RuntimeError`: If downloads fail

**Example:**
```python
from exam_grading.get_annotated_pdfs_from_aws import get_annotated_pdfs_from_aws

get_annotated_pdfs_from_aws(
    "./annotated_pdfs",
    "./students.csv"
)
```

### exam_grading.upload_jobs_to_prprpr

#### Functions

##### upload_jobs_to_prprpr(csv_folder_path: str, students_csv_path: str) -> None

Uploads grading jobs to prprpr API.

**Parameters:**
- `csv_folder_path` (str): Directory containing job CSVs
- `students_csv_path` (str): Path to student anonymization CSV

**Raises:**
- `ValueError`: If paths don't exist
- `HTTPError`: If API requests fail

**Example:**
```python
from exam_grading.upload_jobs_to_prprpr import upload_jobs_to_prprpr

upload_jobs_to_prprpr(
    "./csv_jobs",
    "./students.csv"
)
```

### exam_grading.download_jobs_from_prprpr

#### Functions

##### download_jobs_from_prprpr(output_folder_path: str, students_csv_path: str) -> None

Downloads completed jobs from prprpr API.

**Parameters:**
- `output_folder_path` (str): Directory for downloaded jobs
- `students_csv_path` (str): Path to student anonymization CSV

**Raises:**
- `ValueError`: If paths are invalid
- `HTTPError`: If API requests fail

**Example:**
```python
from exam_grading.download_jobs_from_prprpr import download_jobs_from_prprpr

download_jobs_from_prprpr(
    "./downloaded_jobs",
    "./students.csv"
)
```

### exam_grading.merge_downloaded_jobs

#### Functions

##### merge_downloaded_jobs(downloaded_jobs_folder: str, output_file: Optional[str] = None) -> str

Merges multiple grading jobs with conflict resolution.

**Parameters:**
- `downloaded_jobs_folder` (str): Directory with job CSVs
- `output_file` (Optional[str]): Output path (default: "merged_grading_jobs.csv")

**Returns:**
- str: Path to merged file

**Raises:**
- `ValueError`: If folder doesn't exist

**Example:**
```python
from exam_grading.merge_downloaded_jobs import merge_downloaded_jobs

merged_file = merge_downloaded_jobs(
    "./downloaded_jobs",
    "./merged_results.csv"
)
```

### exam_grading.generate_student_feedback

#### Functions

##### generate_feedback_for_all_students(merged_grading_jobs_path: str, questiondb_path: str, students_csv_path: str, annotated_pdfs_dir: Optional[str] = None) -> list[str]

Generates PDF feedback for all students.

**Parameters:**
- `merged_grading_jobs_path` (str): Path to merged grading results
- `questiondb_path` (str): Path to question database
- `students_csv_path` (str): Path to student information
- `annotated_pdfs_dir` (Optional[str]): Directory with annotated PDFs

**Returns:**
- list[str]: List of generated PDF paths

**Raises:**
- `ValueError`: If required files don't exist

**Example:**
```python
from exam_grading.generate_student_feedback import generate_feedback_for_all_students

pdfs = generate_feedback_for_all_students(
    "./merged_grading_jobs.csv",
    "./questiondb.json",
    "./students.csv",
    "./annotated_pdfs"
)
```

### exam_grading.email_feedback_to_students

#### Functions

##### email_feedback_to_students(feedback_folder: str, students_csv: str) -> None

Emails feedback PDFs to students.

**Parameters:**
- `feedback_folder` (str): Directory containing feedback PDFs
- `students_csv` (str): Path to student information with emails

**Raises:**
- `ValueError`: If paths don't exist
- `RuntimeError`: If email sending fails

**Example:**
```python
from exam_grading.email_feedback_to_students import email_feedback_to_students

email_feedback_to_students(
    "./student_feedback",
    "./students.csv"
)
```

## Common Utilities

### exam_grading.common.auth

#### Functions

##### get_prprpr_access_token() -> str

Obtains OAuth2 access token for prprpr API.

**Returns:**
- str: Access token

**Raises:**
- `RuntimeError`: If authentication fails

**Example:**
```python
from exam_grading.common.auth import get_prprpr_access_token

token = get_prprpr_access_token()
headers = {"Authorization": f"Bearer {token}"}
```

### exam_grading.common.validators

#### Functions

##### validate_directory(path: Path, name: str) -> None

Validates that a path exists and is a directory.

**Parameters:**
- `path` (Path): Path to validate
- `name` (str): Description for error messages

**Raises:**
- `ValueError`: If validation fails

##### validate_file(path: Path, name: str) -> None

Validates that a path exists and is a file.

**Parameters:**
- `path` (Path): Path to validate
- `name` (str): Description for error messages

**Raises:**
- `ValueError`: If validation fails

##### validate_csv_file(path: Path, name: str) -> None

Validates that a path exists, is a file, and has .csv extension.

**Parameters:**
- `path` (Path): Path to validate
- `name` (str): Description for error messages

**Raises:**
- `ValueError`: If validation fails

### exam_grading.common.progress

#### Classes

##### ProgressPrinter

Simple progress reporting for console output.

**Constructor:**
```python
ProgressPrinter(task_name: str, total: int)
```

**Methods:**

###### update(current: int) -> None
Updates progress display.

**Parameters:**
- `current` (int): Current item number

###### done() -> None
Marks task as complete.

**Example:**
```python
from exam_grading.common.progress import ProgressPrinter

progress = ProgressPrinter("Processing files", 100)
for i in range(100):
    # Do work...
    progress.update(i + 1)
progress.done()
```

### exam_grading.common.roman_numerals

#### Functions

##### convert_roman_to_int(roman: str) -> int

Converts Roman numeral to integer.

**Parameters:**
- `roman` (str): Roman numeral string

**Returns:**
- int: Integer value

**Example:**
```python
from exam_grading.common.roman_numerals import convert_roman_to_int

value = convert_roman_to_int("XIV")  # Returns 14
```

##### convert_int_to_roman(num: int) -> str

Converts integer to lowercase Roman numeral.

**Parameters:**
- `num` (int): Integer to convert

**Returns:**
- str: Lowercase Roman numeral

**Example:**
```python
from exam_grading.common.roman_numerals import convert_int_to_roman

roman = convert_int_to_roman(42)  # Returns "xlii"
```

### exam_grading.common.anonymization

#### Classes

##### StudentAnonymizer

Manages student ID anonymization.

**Constructor:**
```python
StudentAnonymizer(student_csv_path: str)
```

**Methods:**

###### anonymize(student_id: str) -> str
Converts real ID to anonymous ID.

**Parameters:**
- `student_id` (str): Real student ID

**Returns:**
- str: Anonymous ID

**Raises:**
- `ValueError`: If student ID not found

###### deanonymize(anon_id: str) -> str
Converts anonymous ID to real ID.

**Parameters:**
- `anon_id` (str): Anonymous ID

**Returns:**
- str: Real student ID

**Raises:**
- `ValueError`: If anonymous ID not found

###### anonymize_filename(filename: str) -> str
Anonymizes student IDs in filename.

**Parameters:**
- `filename` (str): Original filename

**Returns:**
- str: Anonymized filename

###### deanonymize_filename(filename: str) -> str
De-anonymizes student IDs in filename.

**Parameters:**
- `filename` (str): Anonymized filename

**Returns:**
- str: Original filename

## Configuration

### exam_grading.common.config

#### Constants

##### PRPRPR_DEBUG
- Type: bool
- Description: Debug mode flag

##### PRPRPR_CLIENT_ID
- Type: str
- Description: OAuth2 client ID

##### PRPRPR_CLIENT_SECRET
- Type: str
- Description: OAuth2 client secret

##### PRPRPR_BASE_URL
- Type: str
- Description: API base URL

##### AWS_BUCKET_NAME
- Type: str
- Description: S3 bucket name

##### GOOGLE_SHEETS_SCOPES
- Type: List[str]
- Description: Google API scopes

##### GOOGLE_CLIENT_CONFIG
- Type: Dict
- Description: Google OAuth2 configuration

## Data Types

### CSV Formats

#### students.csv
```python
@dataclass
class Student:
    student_id: str
    anonymous_id: str
    first_name: str
    last_name: str
    email: str
```

#### bubbles.csv
```python
@dataclass
class Bubble:
    page: int
    question: int
    subquestion: str
    choice: str
    Xpos: float
    Ypos: float
```

#### consolidated_answers.csv
```python
# Wide format with columns:
# student_id, 1.i, 1.ii, 2.i, 2.ii, ...
```

#### grading_job.csv
```python
@dataclass
class GradingItem:
    student_id: str
    problem: int
    subquestion: str
    answer: str
    suggested_score: Optional[float]
    adjusted_score: Optional[float]
    standard_error: Optional[str]
    general_error: Optional[str]
    feedback: Optional[str]
    page_numbers: str
    grader_id: Optional[str]
```

## Error Handling

### Common Exceptions

- `ValueError`: Invalid input parameters
- `FileNotFoundError`: Missing required files
- `RuntimeError`: Processing failures
- `HTTPError`: API communication errors
- `KeyError`: Missing required data fields

### Error Patterns

```python
# Input validation
try:
    validate_file(path, "configuration")
except ValueError as e:
    print(f"Configuration error: {e}")
    sys.exit(1)

# API requests
try:
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
except requests.HTTPError as e:
    print(f"API error: {e}")
    raise

# Batch processing
errors = []
for item in items:
    try:
        process_item(item)
    except Exception as e:
        errors.append((item, str(e)))

if errors:
    print(f"Failed to process {len(errors)} items")
    for item, error in errors:
        print(f"  {item}: {error}")
```
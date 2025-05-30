# Common Utilities Documentation

## Overview

The `common` package provides shared utilities used throughout the exam grading system. These modules handle cross-cutting concerns like authentication, configuration, validation, and progress tracking.

## Modules

### config.py - Configuration Management

Centralized configuration for external services and API credentials.

#### Constants

**prprpr API Configuration**
```python
PRPRPR_DEBUG: bool  # Environment-based debug flag
PRPRPR_CLIENT_ID: str  # OAuth2 client ID
PRPRPR_CLIENT_SECRET: str  # OAuth2 client secret
PRPRPR_BASE_URL: str  # API base URL
```

**AWS Configuration**
```python
AWS_BUCKET_NAME: str = "clrify-gradescope-integration"
```

**Google Sheets Configuration**
```python
GOOGLE_SHEETS_SCOPES: List[str]  # API permission scopes
GOOGLE_CLIENT_CONFIG: Dict  # OAuth2 client configuration
```

#### Usage Example
```python
from exam_grading.common.config import PRPRPR_BASE_URL, AWS_BUCKET_NAME

# Use configuration in your module
api_endpoint = f"{PRPRPR_BASE_URL}/api/v1/jobs"
s3_path = f"s3://{AWS_BUCKET_NAME}/exams/"
```

### auth.py - Authentication

Handles OAuth2 authentication for the prprpr API using PKCE flow.

#### Functions

##### get_prprpr_access_token() -> str
Performs OAuth2 PKCE authentication flow.

**Returns**: Access token for API requests

**Process**:
1. Generates code verifier and challenge
2. Starts local web server for callback
3. Opens browser for user authorization
4. Exchanges authorization code for token

**Example**:
```python
from exam_grading.common.auth import get_prprpr_access_token

token = get_prprpr_access_token()
headers = {"Authorization": f"Bearer {token}"}
```

### validators.py - Input Validation

Provides consistent validation for file system paths.

#### Functions

##### validate_directory(path: Path, name: str) -> None
Validates that a path exists and is a directory.

**Parameters**:
- `path`: Path to validate
- `name`: Description for error messages

**Raises**: `ValueError` if validation fails

##### validate_file(path: Path, name: str) -> None
Validates that a path exists and is a file.

**Parameters**:
- `path`: Path to validate
- `name`: Description for error messages

**Raises**: `ValueError` if validation fails

##### validate_csv_file(path: Path, name: str) -> None
Validates that a path exists, is a file, and has .csv extension.

**Parameters**:
- `path`: Path to validate
- `name`: Description for error messages

**Raises**: `ValueError` if validation fails

**Example**:
```python
from pathlib import Path
from exam_grading.common.validators import validate_directory, validate_csv_file

input_dir = Path("./scans")
validate_directory(input_dir, "scan directory")

bubble_file = Path("./bubbles.csv")
validate_csv_file(bubble_file, "bubble configuration")
```

### progress.py - Progress Tracking

Simple progress reporting for console applications.

#### Classes

##### ProgressPrinter
Displays progress for long-running operations.

**Constructor**:
```python
ProgressPrinter(task_name: str, total: int)
```

**Methods**:
- `update(current: int)`: Update progress display
- `done()`: Mark task complete

**Example**:
```python
from exam_grading.common.progress import ProgressPrinter

progress = ProgressPrinter("Processing files", len(files))
for i, file in enumerate(files):
    process_file(file)
    progress.update(i + 1)
progress.done()
```

### roman_numerals.py - Roman Numeral Conversion

Bidirectional conversion between Roman numerals and integers.

#### Functions

##### convert_roman_to_int(roman: str) -> int
Converts Roman numeral string to integer.

**Parameters**:
- `roman`: Roman numeral string (case-insensitive)

**Returns**: Integer value

**Example**:
```python
from exam_grading.common.roman_numerals import convert_roman_to_int

value = convert_roman_to_int("XIV")  # Returns 14
value = convert_roman_to_int("iv")   # Returns 4 (case-insensitive)
```

##### convert_int_to_roman(num: int) -> str
Converts integer to lowercase Roman numeral.

**Parameters**:
- `num`: Integer to convert (1-3999)

**Returns**: Lowercase Roman numeral string

**Example**:
```python
from exam_grading.common.roman_numerals import convert_int_to_roman

roman = convert_int_to_roman(42)  # Returns "xlii"
```

### anonymization.py - Student ID Management

Manages bidirectional mapping between real and anonymous student IDs.

#### Classes

##### StudentAnonymizer
Handles student ID anonymization for privacy protection.

**Constructor**:
```python
StudentAnonymizer(student_csv_path: str)
```

**Parameters**:
- `student_csv_path`: Path to CSV with columns: student_id, anonymous_id

**Methods**:

###### anonymize(student_id: str) -> str
Convert real student ID to anonymous ID.

**Parameters**:
- `student_id`: Real student ID

**Returns**: Anonymous ID

**Raises**: `ValueError` if student ID not found

###### deanonymize(anon_id: str) -> str
Convert anonymous ID back to real student ID.

**Parameters**:
- `anon_id`: Anonymous ID

**Returns**: Real student ID

**Raises**: `ValueError` if anonymous ID not found

###### anonymize_filename(filename: str) -> str
Replace student IDs in filename with anonymous IDs.

**Parameters**:
- `filename`: Filename potentially containing student IDs

**Returns**: Filename with anonymous IDs

###### deanonymize_filename(filename: str) -> str
Replace anonymous IDs in filename with real student IDs.

**Parameters**:
- `filename`: Filename potentially containing anonymous IDs

**Returns**: Filename with real student IDs

**Example**:
```python
from exam_grading.common.anonymization import StudentAnonymizer

anonymizer = StudentAnonymizer("students.csv")

# Anonymize student ID
anon_id = anonymizer.anonymize("abc123")  # Returns "student_001"

# Anonymize filename
anon_file = anonymizer.anonymize_filename("abc123_exam.pdf")  
# Returns "student_001_exam.pdf"

# Restore original
real_id = anonymizer.deanonymize("student_001")  # Returns "abc123"
```

## Best Practices

### Error Handling
All common utilities use descriptive error messages:
```python
try:
    validate_file(path, "configuration file")
except ValueError as e:
    print(f"Configuration error: {e}")
    sys.exit(1)
```

### Type Safety
Use type hints for better code clarity:
```python
from pathlib import Path
from exam_grading.common.validators import validate_directory

def process_scans(scan_dir: Path) -> None:
    validate_directory(scan_dir, "scan directory")
    # Process files...
```

### Progress Reporting
Always use ProgressPrinter for operations on multiple items:
```python
progress = ProgressPrinter("Uploading PDFs", len(pdf_files))
for i, pdf in enumerate(pdf_files):
    upload_to_s3(pdf)
    progress.update(i + 1)
progress.done()
```

### Configuration Access
Import only needed configuration values:
```python
from exam_grading.common.config import AWS_BUCKET_NAME
# Not: from exam_grading.common.config import *
```

### Privacy Protection
Always anonymize when sending data to external services:
```python
anonymizer = StudentAnonymizer("students.csv")
for file in student_files:
    anon_name = anonymizer.anonymize_filename(file.name)
    upload_file(file, anon_name)
```
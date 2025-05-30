# Configuration Guide

## Overview

The Exam Grading System uses JSON configuration files to manage paths, credentials, and settings. This guide explains all configuration options and how to customize them for your environment.

## Main Configuration File

### Structure

The main configuration file (e.g., `config.json`) contains all path settings:

```json
{
  "paths": {
    "scans_folder": "./presentation/scans",
    "parsed_folder": "./presentation/scans_parsed",
    "omr_output_folder": "./presentation/scans_parsed_OMR",
    "omr_marker": "./omr_marker.jpg",
    "bubbles_csv": "./presentation/bubbles.csv",
    "consolidated_answers": "./presentation/scans_parsed_OMR/consolidated_answers.csv",
    "students_csv": "./presentation/students.csv",
    "questiondb": "./questiondb.json",
    "everything_job": "./presentation/everything_job.csv",
    "csv_jobs_folder": "./presentation/csv_jobs",
    "downloaded_jobs_folder": "./presentation/downloaded_jobs",
    "merged_job": "./presentation/merged_grading_jobs.csv",
    "annotated_pdfs_folder": "./presentation/annotated_pdfs",
    "student_feedback_folder": "./presentation/student_feedback"
  }
}
```

### Path Descriptions

| Path | Description | Required |
|------|-------------|----------|
| `scans_folder` | Input directory for scanned exam images | Yes |
| `parsed_folder` | Output for QR-organized images | Yes |
| `omr_output_folder` | Output for OMR results and PDFs | Yes |
| `omr_marker` | Corner marker image for alignment | Yes |
| `bubbles_csv` | Bubble position definitions | Yes |
| `consolidated_answers` | OMR output CSV path | Yes |
| `students_csv` | Student information and anonymization | Yes |
| `questiondb` | Question database JSON | Yes |
| `everything_job` | Master grading job CSV | Yes |
| `csv_jobs_folder` | Split job files directory | Yes |
| `downloaded_jobs_folder` | Downloaded grading results | Yes |
| `merged_job` | Merged grading output | Yes |
| `annotated_pdfs_folder` | Graded PDFs from AWS | Yes |
| `student_feedback_folder` | Generated feedback PDFs | Yes |

## Data File Formats

### students.csv

Contains student information and anonymization mappings:

```csv
student_id,anonymous_id,first_name,last_name,email
abc123,student_001,Alice,Smith,alice.smith@yale.edu
def456,student_002,Bob,Jones,bob.jones@yale.edu
ghi789,student_003,Carol,Brown,carol.brown@yale.edu
```

**Columns**:
- `student_id`: Unique identifier (required)
- `anonymous_id`: Anonymous ID for external services (required)
- `first_name`: Student's first name (required for feedback)
- `last_name`: Student's last name (required for feedback)
- `email`: Email address (required for email delivery)

### bubbles.csv

Defines bubble positions on answer sheets:

```csv
page,question,subquestion,choice,Xpos,Ypos
1,1,i,a,120.5,234.5
1,1,i,b,145.5,234.5
1,1,i,c,170.5,234.5
1,1,i,d,195.5,234.5
1,1,ii,a,120.5,259.5
```

**Columns**:
- `page`: Page number (1-based)
- `question`: Question number
- `subquestion`: Subquestion identifier (i, ii, iii, etc.)
- `choice`: Answer choice (a, b, c, etc., or 0-9 for numeric)
- `Xpos`: X-coordinate in LaTeX points
- `Ypos`: Y-coordinate in LaTeX points

**Special Choices**:
- `0-9`: Numeric digits
- `D`: Decimal point
- `S`: Slash separator
- `Other`: Alternative option

### questiondb.json

Contains question definitions and metadata:

```json
{
  "problems": [
    {
      "number": 1,
      "name": "Problem 1: Integration",
      "path": "problems/problem1.tex",
      "points": 10,
      "subquestions": [
        {
          "label": "i",
          "points": 5,
          "answer_values": [
            {
              "label": "a",
              "value": "2π",
              "default": 5.0
            },
            {
              "label": "b",
              "value": "π",
              "default": 2.5
            },
            {
              "label": "c",
              "value": "0",
              "default": 0.0
            }
          ]
        },
        {
          "label": "ii",
          "points": 5,
          "answer_values": [
            {
              "label": "a",
              "default": 5.0
            }
          ]
        }
      ]
    }
  ]
}
```

**Structure**:
- `problems`: Array of problem definitions
- `number`: Problem number
- `name`: Display name
- `path`: Path to LaTeX source (relative to questiondb)
- `points`: Total points (optional)
- `subquestions`: Array of subquestion definitions
  - `label`: Subquestion identifier
  - `points`: Points for subquestion
  - `answer_values`: Possible answers with scores

## Application Configuration

### config.py Settings

Located in `src/exam_grading/common/config.py`:

```python
# Debug mode toggle
PRPRPR_DEBUG = os.getenv("PRPRPR_DEBUG", "False").lower() == "true"

# prprpr API configuration
if PRPRPR_DEBUG:
    PRPRPR_CLIENT_ID = "debug_client_id"
    PRPRPR_CLIENT_SECRET = "debug_client_secret"
    PRPRPR_BASE_URL = "http://127.0.0.1:8000"
else:
    PRPRPR_CLIENT_ID = "production_client_id"
    PRPRPR_CLIENT_SECRET = "production_client_secret"
    PRPRPR_BASE_URL = "https://clrify.it"

# AWS configuration
AWS_BUCKET_NAME = "clrify-gradescope-integration"

# Google Sheets configuration
GOOGLE_SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
```

### Environment Variables

Recommended for sensitive data:

```bash
# prprpr credentials
export PRPRPR_CLIENT_ID="your_client_id"
export PRPRPR_CLIENT_SECRET="your_client_secret"
export PRPRPR_DEBUG="true"  # or "false" for production

# AWS credentials
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"

# Google credentials (if using service account)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

## OMR Configuration

### Marker Image

The OMR marker (`omr_marker.jpg`) should be:
- High contrast image
- Unique pattern not found elsewhere
- Placed at all four corners of answer sheets
- Consistent size across all pages

### Bubble Positioning

When creating `bubbles.csv`:

1. **Coordinate System**: LaTeX points (72 points = 1 inch)
2. **Origin**: Bottom-left corner of page
3. **Precision**: Use decimal values for accuracy
4. **Testing**: Verify with sample scans

### Threshold Settings

OMR uses adaptive thresholding, but you can adjust in the code:

```python
# In run_omr.py
THRESHOLD_CAP = 210  # Maximum threshold (0-255 scale)
CONFIDENCE_THRESHOLD = 0.6  # Marker detection confidence
```

## Multiple Configurations

### Managing Different Environments

Create separate config files:

```bash
# Development
dev_config.json

# Testing
test_config.json

# Production
prod_config.json
```

Run with specific configuration:

```bash
python -m exam_grading --config prod_config.json
```

### Configuration Templates

Create a template for new courses:

```json
{
  "course": "MATH101",
  "term": "Fall 2025",
  "paths": {
    "scans_folder": "./courses/math101/scans",
    "students_csv": "./courses/math101/students.csv",
    "questiondb": "./courses/math101/questiondb.json"
    // ... other paths
  }
}
```

## Validation and Testing

### Configuration Validator

Create a validation script:

```python
import json
from pathlib import Path

def validate_config(config_path):
    with open(config_path) as f:
        config = json.load(f)
    
    # Check required paths exist
    for key, path in config["paths"].items():
        if key.endswith("_folder"):
            # Folders will be created if needed
            continue
        if not Path(path).exists():
            print(f"Warning: {key} path does not exist: {path}")
    
    return config

# Usage
validate_config("config.json")
```

### Test Configuration

Minimal configuration for testing:

```json
{
  "paths": {
    "scans_folder": "./test_data/scans",
    "parsed_folder": "./test_output/parsed",
    "omr_output_folder": "./test_output/omr",
    "omr_marker": "./test_data/marker.jpg",
    "bubbles_csv": "./test_data/bubbles.csv",
    "consolidated_answers": "./test_output/answers.csv",
    "students_csv": "./test_data/students.csv",
    "questiondb": "./test_data/questiondb.json",
    "everything_job": "./test_output/everything.csv",
    "csv_jobs_folder": "./test_output/jobs",
    "downloaded_jobs_folder": "./test_output/downloaded",
    "merged_job": "./test_output/merged.csv",
    "annotated_pdfs_folder": "./test_output/annotated",
    "student_feedback_folder": "./test_output/feedback"
  }
}
```

## Security Best Practices

### Credential Management

1. **Never commit credentials** to version control
2. **Use environment variables** for sensitive data
3. **Rotate credentials** regularly
4. **Limit access scope** to minimum required

### File Permissions

```bash
# Restrict config file access
chmod 600 config.json
chmod 600 students.csv
```

### Data Privacy

1. **Anonymize early**: Use anonymous IDs for external services
2. **Separate concerns**: Keep real IDs only where necessary
3. **Audit access**: Log who accesses student data
4. **Encrypt sensitive**: Consider encrypting student CSV

## Troubleshooting Configuration

### Common Issues

1. **Path not found**:
   - Use absolute paths for reliability
   - Check working directory
   - Verify file extensions

2. **Permission denied**:
   - Check file ownership
   - Verify directory permissions
   - Run with appropriate user

3. **Invalid JSON**:
   - Validate with JSON linter
   - Check for trailing commas
   - Ensure proper escaping

### Debug Mode

Enable debug output:

```python
# In your code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Configuration Backup

Always backup configurations:

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
cp config.json backups/config_$DATE.json
cp students.csv backups/students_$DATE.csv
```
# User Guide

## Overview

This guide walks you through using the Exam Grading System to process exams from scanning to student feedback delivery.

## Quick Start

### 1. Prepare Your Environment

```bash
# Navigate to project directory
cd 2025_exam_grading_presentation

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Run the main program
python -m exam_grading
```

### 2. Main Menu

When you run the program, you'll see:

```
===== Exam Grading System =====
1. Read QR codes from scans
2. Run OMR
3. Upload PDFs to AWS
4. Create everything job
5. Split everything job
6. Upload jobs to prprpr
7. Download jobs from prprpr
8. Get annotated PDFs from AWS
9. Merge downloaded jobs
10. Generate student feedback
11. Email feedback to students
0. Exit

Enter your choice:
```

## Workflow Steps

### Step 1: Read QR Codes from Scans

**Purpose**: Extract QR codes from scanned exam pages and organize by page number.

**Prerequisites**:
- Scanned exam images in JPEG format
- QR codes on each page containing student ID and page number

**Process**:
1. Select option `1` from the menu
2. The system will:
   - Read QR codes from all images in the scans folder
   - Create organized folders by page number
   - Move images to appropriate folders
   - Place unreadable images in `noQRcode` folder

**Output**: `scans_parsed/` directory with subfolders:
```
scans_parsed/
├── 1/         # Page 1 images
├── 2/         # Page 2 images
├── ...
└── noQRcode/  # Failed QR reads
```

### Step 2: Run OMR (Optical Mark Recognition)

**Purpose**: Detect filled bubbles on answer sheets.

**Prerequisites**:
- Parsed images from Step 1
- OMR marker image for alignment
- Bubble position CSV file

**Process**:
1. Select option `2` from the menu
2. The system will:
   - Align each page using corner markers
   - Detect filled bubbles
   - Generate answer CSV
   - Create PDFs with bubble overlays

**Output**: 
- `consolidated_answers.csv` with all student answers
- Individual PDFs for each student/page

### Step 3: Upload PDFs to AWS

**Purpose**: Store processed PDFs in cloud storage.

**Prerequisites**:
- PDFs from OMR processing
- AWS credentials configured
- Student anonymization CSV

**Process**:
1. Select option `3` from the menu
2. The system will:
   - Anonymize student IDs
   - Upload PDFs to S3 bucket
   - Show progress for batch upload

**Note**: Files are anonymized for privacy during grading.

### Step 4: Create Everything Job

**Purpose**: Generate master grading CSV combining answers with question metadata.

**Prerequisites**:
- Consolidated answers from OMR
- Question database JSON
- Bubble position CSV

**Process**:
1. Select option `4` from the menu
2. The system will:
   - Load question definitions
   - Match answers to questions
   - Add suggested scores
   - Include page number references

**Output**: `everything_job.csv` with complete grading data

### Step 5: Split Everything Job

**Purpose**: Divide master job into individual grader assignments.

**Prerequisites**:
- Everything job CSV with `job_number` column

**Process**:
1. Select option `5` from the menu
2. The system will:
   - Group rows by job number
   - Create separate CSV files
   - Name files as `Job_1.csv`, `Job_2.csv`, etc.

**Output**: Multiple job files in `csv_jobs/` directory

### Step 6: Upload Jobs to prprpr

**Purpose**: Send grading jobs to the prprpr grading service.

**Prerequisites**:
- Job CSV files from Step 5
- prprpr account and credentials
- Internet connection

**Process**:
1. Select option `6` from the menu
2. Authenticate via browser (OAuth flow)
3. Confirm production upload if applicable
4. The system will:
   - Anonymize student IDs
   - Upload each job
   - Track progress

**Important**: Double-check before uploading to production!

### Step 7: Download Jobs from prprpr

**Purpose**: Retrieve completed grading from prprpr.

**Prerequisites**:
- Jobs uploaded and graded in prprpr
- prprpr credentials

**Process**:
1. Select option `7` from the menu
2. Authenticate if needed
3. The system will:
   - List all available jobs
   - Download grading data
   - De-anonymize student IDs
   - Save as CSV files

**Output**: Graded job files in `downloaded_jobs/` directory

### Step 8: Get Annotated PDFs from AWS

**Purpose**: Download PDFs with grader annotations.

**Prerequisites**:
- Graders have annotated PDFs in prprpr
- AWS credentials

**Process**:
1. Select option `8` from the menu
2. The system will:
   - List all PDFs in S3
   - Download with directory structure
   - De-anonymize filenames
   - Show progress

**Output**: Annotated PDFs in `annotated_pdfs/` directory

### Step 9: Merge Downloaded Jobs

**Purpose**: Combine multiple grading jobs and resolve conflicts.

**Prerequisites**:
- Downloaded job CSV files

**Process**:
1. Select option `9` from the menu
2. For any conflicts (multiple graders), you'll see:
   ```
   Conflict for student abc123, problem 1, subquestion i:
     1. Grader: ta1, Score: 4.5, Feedback: Good work
     2. Grader: ta2, Score: 5.0, Feedback: Excellent
   Choose which grader's work to keep (1-2):
   ```
3. Select the preferred grading

**Output**: `merged_grading_jobs.csv` with consolidated results

### Step 10: Generate Student Feedback

**Purpose**: Create personalized PDF feedback for each student.

**Prerequisites**:
- Merged grading jobs CSV
- Question database
- Student information CSV
- LaTeX installed
- Optional: Annotated PDFs

**Process**:
1. Select option `10` from the menu
2. The system will:
   - Load grading data
   - Generate LaTeX for each student
   - Include scanned work
   - Compile to PDF
   - Show progress

**Output**: Individual feedback PDFs in `student_feedback/` directory

### Step 11: Email Feedback to Students

**Purpose**: Send feedback PDFs to students via email.

**Prerequisites**:
- Generated feedback PDFs
- Student CSV with email addresses
- Microsoft account access

**Process**:
1. Select option `11` from the menu
2. Review what will be sent
3. Confirm with "yes"
4. Authenticate with Microsoft
5. The system will:
   - Send personalized emails
   - Attach feedback PDFs
   - Track success/failures

## Best Practices

### Before Starting

1. **Backup Your Data**: Keep copies of original scans
2. **Test First**: Use a small subset to verify workflow
3. **Check Configuration**: Ensure all paths are correct
4. **Verify Credentials**: Test AWS and prprpr access

### During Processing

1. **Monitor Progress**: Watch for errors at each step
2. **Verify Outputs**: Check intermediate results
3. **Document Issues**: Note any problematic scans
4. **Save Logs**: Keep terminal output for debugging

### Quality Checks

1. **After OMR**: Review `consolidated_answers.csv` for accuracy
2. **Before Upload**: Verify job assignments are correct
3. **After Download**: Check grading completeness
4. **Before Email**: Review sample feedback PDFs

## Common Workflows

### Full Workflow (First Time)

```bash
# Process all steps in order
1 → 2 → 3 → 4 → 5 → 6 → (wait for grading) → 7 → 8 → 9 → 10 → 11
```

### Re-running Failed Steps

If a step fails, you can often re-run just that step:

```bash
# Example: OMR failed for some pages
# Fix the issues, then:
2 → 3 → 4 (continue from there)
```

### Updating Grades Only

If grades change but scans remain the same:

```bash
# Download new grades and regenerate feedback
7 → 9 → 10 → 11
```

## Tips and Tricks

### Handling Special Cases

1. **Replacement Pages**: 
   - Use QR codes with `/replacement` suffix
   - System automatically handles duplicates

2. **Missing QR Codes**:
   - Check `noQRcode` folder
   - Manually rename and move files

3. **Multiple Graders**:
   - Assign different job numbers
   - Resolve conflicts during merge

### Performance Optimization

1. **Batch Processing**:
   - Process all students together
   - Avoid running steps for individual students

2. **Parallel Operations**:
   - AWS uploads/downloads are batched
   - OMR processes pages concurrently

3. **Resource Management**:
   - Close other applications during OMR
   - Ensure sufficient disk space

### Troubleshooting Quick Fixes

1. **QR Code Reading Failures**:
   - Check image quality and orientation
   - Ensure QR codes are clearly visible

2. **OMR Accuracy Issues**:
   - Verify marker alignment
   - Check bubble CSV coordinates
   - Adjust threshold if needed

3. **Upload/Download Errors**:
   - Check internet connection
   - Verify credentials
   - Retry failed operations

## Getting Help

If you encounter issues:

1. Check error messages for specific problems
2. Review the [Troubleshooting Guide](troubleshooting.md)
3. Verify prerequisites for each step
4. Consult system logs for details
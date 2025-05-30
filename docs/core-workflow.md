# Core Workflow Modules Documentation

## Overview

The exam grading system consists of several core workflow modules that process exams from initial scanning through final feedback generation. This document details the main processing modules.

## Module 1: QR Code Reading (`read_qr_codes.py`)

### Purpose
Processes scanned exam images to extract QR codes containing student IDs and page numbers, organizing images into a structured folder hierarchy.

### Main Function

#### read_qr_codes_and_move(exam_scans_folder_path: str) -> str

Reads QR codes from exam scans and organizes images by page number.

**Parameters**:
- `exam_scans_folder_path`: Path to folder containing JPEG exam scans

**Returns**: Path to output folder with organized images

**Process Flow**:
1. Creates output folder: `{input_folder}_parsed`
2. Initializes QReader for QR detection
3. Processes each JPEG image:
   - Extracts QR code data
   - Parses student ID and page number
   - Moves image to appropriate subfolder
   - Handles replacement pages

### QR Code Format

Expected URL pattern:
```
https://clrify.it/replacement/{student_id}/{page_number}/[replacement]
```

- `student_id`: Student's network ID
- `page_number`: Page number (1-6)
- `replacement`: Optional flag for replacement pages

### Output Structure
```
input_folder_parsed/
├── 1/
│   ├── student1_1.jpeg
│   ├── student2_1.jpeg
│   └── ...
├── 2/
│   ├── student1_2.jpeg
│   └── ...
├── ...
└── noQRcode/
    └── unreadable_images.jpeg
```

### Error Handling
- Images without readable QR codes → `noQRcode` folder
- Invalid QR format → Error message and skip
- Duplicate pages → Numbered suffixes (_1, _2, etc.)
- Replacement pages → Overwrite existing

## Module 2: Optical Mark Recognition (`run_omr.py`)

### Purpose
Detects filled bubbles on answer sheets using computer vision techniques and generates consolidated answer data.

### Main Function

#### run_omr(omr_marker_path: str, bubbles_csv_path: str, parsed_folder_path: str) -> str

Performs OMR on organized exam images.

**Parameters**:
- `omr_marker_path`: Path to alignment marker image
- `bubbles_csv_path`: CSV file with bubble coordinates
- `parsed_folder_path`: Folder from QR code processing

**Returns**: Path to output folder with OMR results

### Key Components

#### Image Alignment
1. **Marker Detection**: Finds 4 corner markers using template matching
2. **Perspective Transform**: Aligns image based on marker positions
3. **Confidence Threshold**: Minimum 0.6 correlation required

#### Bubble Detection
1. **Position Calculation**: Converts LaTeX points to pixels
2. **Region Extraction**: Uses inscribed square within bubble circle
3. **Intensity Measurement**: Mean grayscale value in region
4. **Threshold Application**: Adaptive thresholding based on intensity gaps

#### Answer Processing
- **Multiple Choice**: Single letter selection (a, b, c, etc.)
- **Numeric Answers**: Multi-digit numbers with decimals
- **Special Characters**: 'D' for decimal, 'S' for slash

### Bubble CSV Format
```csv
page,question,subquestion,choice,Xpos,Ypos
1,1,i,a,123.45,234.56
1,1,i,b,145.67,234.56
```

### Output Files

#### consolidated_answers.csv
```csv
student_id,1.i,1.ii,2.i,2.ii,...
abc123,a,b,12.5,c,...
def456,c,a,8,d,...
```

#### PDF Files
- Individual PDFs per student per page
- Overlay showing detected bubbles
- Multi-page PDFs for replacement pages

### Algorithm Details

#### Adaptive Thresholding
```python
1. Calculate intensity for all bubbles
2. Find largest gap between consecutive intensities
3. Set threshold at midpoint of largest gap
4. Fallback: mean of all intensities
5. Cap at maximum 210 (out of 255)
```

#### Numeric Answer Assembly
```python
1. Identify numeric format questions (e.g., "1-1-0")
2. Extract digit bubbles in sequence
3. Replace 'D' with decimal point
4. Filter out "Other" if numeric answer exists
```

## Module 3: Job Creation (`create_everything_job.py`)

### Purpose
Creates a comprehensive CSV job file that combines OMR results with question metadata for the grading service.

### Main Function

#### create_everything_job(bubbles_csv_path, consolidated_answers_csv_path, questiondb_path, output_path) -> str

Creates master grading job CSV.

**Parameters**:
- `bubbles_csv_path`: Bubble position definitions
- `consolidated_answers_csv_path`: Student answers from OMR
- `questiondb_path`: Question database JSON file
- `output_path`: Output CSV file path

**Returns**: Path to created job file

### Data Transformation Process

1. **Load Data Sources**:
   - Bubble positions (page mapping)
   - Student answers (wide format)
   - Question database (scoring info)

2. **Transform to Long Format**:
   ```python
   # From: student_id, 1.i, 1.ii, 2.i, ...
   # To:   student_id, problem, subquestion, answer
   ```

3. **Add Metadata**:
   - Page numbers from bubble positions
   - Problem statement page references
   - Suggested scores from question DB

### Output Format

#### everything_job.csv
```csv
student_id,problem,subquestion,answer,page_numbers,suggested_score,job_number
abc123,1,i,a,"0,1",1.0,
abc123,1,ii,b,"0,1",0.5,
abc123,2,i,12.5,"0,2",2.0,
```

### Scoring Logic

#### Suggested Score Calculation
1. Load problem definitions from QuestionDB
2. Match student answer to defined values
3. Use default score if specified
4. Return None if no match

Example QuestionDB entry:
```json
{
  "problem_number": 1,
  "subquestions": [
    {
      "label": "i",
      "answer_values": [
        {"label": "a", "default": 1.0},
        {"label": "b", "default": 0.5},
        {"label": "c", "default": 0.0}
      ]
    }
  ]
}
```

## Module 4: Main Entry Point (`__main__.py`)

### Purpose
Provides an interactive CLI menu for executing the complete exam grading workflow.

### Menu Options

1. **Read QR codes from scans** - Process raw scans
2. **Run OMR** - Detect bubble answers
3. **Upload PDFs to AWS** - Store in S3
4. **Create everything job** - Generate master CSV
5. **Split everything job** - Create individual jobs
6. **Upload jobs to prprpr** - Send for grading
7. **Download jobs from prprpr** - Get results
8. **Get annotated PDFs from AWS** - Download graded PDFs
9. **Merge downloaded jobs** - Combine results
10. **Generate student feedback** - Create reports
11. **Email feedback to students** - Send reports

### Configuration File Format

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

### Usage Example

```bash
# Run with default config
python -m exam_grading

# Run with custom config
python -m exam_grading --config custom_config.json
```

### Workflow Best Practices

1. **Sequential Execution**: Run steps in order (1-11)
2. **Verify Outputs**: Check intermediate results
3. **Error Recovery**: Re-run failed steps
4. **Batch Processing**: Process all students together
5. **Configuration Management**: Use separate configs for testing

## Integration Points

### File System Flow
```
Scans → QR Reader → Parsed Folders → OMR → CSVs → Jobs
```

### External Services
- **AWS S3**: PDF storage
- **prprpr**: Grading service
- **Google Sheets**: Optional grading interface
- **Email**: Student communication

### Data Dependencies
- QR Reader → OMR (folder structure)
- OMR → Job Creation (answer CSV)
- Job Creation → Upload (job CSV)
- Download → Feedback (grading results)
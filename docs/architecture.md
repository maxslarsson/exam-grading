# Architecture Overview

## System Architecture

The Exam Grading System follows a modular, pipeline-based architecture designed for scalability and maintainability.

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ Scanned Images  │────▶│  QR Reader   │────▶│ Organized   │
│    (JPEG)       │     │              │     │   Pages     │
└─────────────────┘     └──────────────┘     └─────────────┘
                                                     │
                                                     ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   AWS S3        │◀────│ PDF Generator│◀────│    OMR      │
│   Storage       │     │              │     │  Processor  │
└─────────────────┘     └──────────────┘     └─────────────┘
                                                     │
                                                     ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ Google Sheets   │◀────│   Grading    │◀────│ Job Creator │
│                 │     │   Service    │     │             │
└─────────────────┘     └──────────────┘     └─────────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │   Feedback   │
                        │  Generator   │
                        └──────────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │    Email     │
                        │ Distribution │
                        └──────────────┘
```

## Core Components

### 1. Input Processing Layer

#### QR Code Reader (`read_qr_codes.py`)
- **Purpose**: Extract student IDs and page numbers from QR codes
- **Input**: Scanned JPEG images
- **Output**: Organized images in folders by page number
- **Key Features**:
  - Handles replacement pages via special QR URLs
  - Validates student IDs against roster
  - Supports batch processing

#### OMR Processor (`run_omr.py`)
- **Purpose**: Detect marked bubbles on answer sheets
- **Input**: Organized page images
- **Output**: CSV files with answers, aligned PDFs
- **Technology**: OpenCV for computer vision
- **Key Features**:
  - Marker-based page alignment
  - Configurable bubble positions
  - Error detection and reporting

### 2. Storage Layer

#### AWS Integration (`upload_pdfs_to_aws.py`, `get_annotated_pdfs_from_aws.py`)
- **Purpose**: Cloud storage for processed and annotated PDFs
- **Service**: AWS S3
- **Organization**: By student ID and page number
- **Features**:
  - Batch upload/download
  - Progress tracking
  - Error handling

### 3. Grading Layer

#### Job Management
- **Create Jobs** (`create_everything_job.py`): Combines OMR data with question database
- **Split Jobs** (`split_everything_job.py`): Divides master job by student
- **Upload Jobs** (`upload_jobs_to_prprpr.py`): Sends to grading service
- **Download Jobs** (`download_jobs_from_prprpr.py`): Retrieves completed grades
- **Merge Jobs** (`merge_downloaded_jobs.py`): Consolidates results

#### Integration Points
- **prprpr Service**: External grading platform
- **Google Sheets API**: Grading spreadsheet creation
- **FUF Service**: Problem database and utilities

### 4. Output Layer

#### Feedback Generator (`generate_student_feedback.py`)
- **Purpose**: Create personalized PDF feedback
- **Technology**: LaTeX for document generation
- **Features**:
  - Problem-specific feedback
  - Score summaries
  - Custom formatting

#### Email Distribution (`email_feedback_to_students.py`)
- **Purpose**: Deliver feedback to students
- **Features**:
  - Batch email sending
  - Attachment handling
  - Delivery tracking

## Data Flow

### 1. Exam Processing Flow
```
Scanned Images → QR Reading → Page Organization → OMR Processing → PDF Generation
```

### 2. Grading Flow
```
OMR Data + Question DB → Job Creation → prprpr Upload → Grading → Download Results
```

### 3. Feedback Flow
```
Grading Results + Student Data → LaTeX Generation → PDF Creation → Email Distribution
```

## Common Utilities

### Authentication (`common/auth.py`)
- OAuth2 for prprpr service
- Google API authentication
- Token management

### Configuration (`common/config.py`)
- Centralized settings
- Environment variables
- API endpoints

### Validation (`common/validators.py`)
- Input validation
- Data integrity checks
- Error reporting

### Progress Tracking (`common/progress.py`)
- Long operation monitoring
- User feedback
- Batch processing support

## External Dependencies

### Services
- **AWS S3**: Cloud storage
- **prprpr**: Grading platform (https://clrify.it)
- **Google Sheets**: Grading spreadsheets
- **FUF Service**: Utility framework

### Libraries
- **qreader**: QR code processing
- **opencv-python**: Computer vision
- **pandas**: Data manipulation
- **boto3**: AWS SDK
- **google-api-python-client**: Google integration

## Security Considerations

### Authentication
- OAuth2 for external services
- AWS IAM for S3 access
- Google service accounts

### Data Protection
- Optional student ID anonymization
- Secure credential storage
- HTTPS for all API calls

## Scalability

### Batch Processing
- Parallel page processing
- Concurrent S3 operations
- Bulk email sending

### Error Handling
- Retry mechanisms
- Partial failure recovery
- Detailed logging

## Extensibility

### Plugin Architecture
- Modular design
- Clear interfaces
- Configuration-driven behavior

### Custom Integrations
- Alternative storage backends
- Different grading services
- Custom feedback formats
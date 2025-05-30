# Installation Guide

## Prerequisites

Before installing the Exam Grading System, ensure you have the following:

### System Requirements

- **Python**: Version 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **LaTeX**: Full LaTeX distribution (for PDF generation)
  - macOS: MacTeX or BasicTeX
  - Linux: TeX Live
  - Windows: MiKTeX or TeX Live
- **Memory**: At least 4GB RAM (8GB recommended for large batches)
- **Storage**: Sufficient space for PDFs and temporary files

### External Service Requirements

1. **AWS Account**
   - S3 bucket access
   - IAM credentials configured
   - AWS CLI installed (optional)

2. **prprpr Service Access**
   - Account on https://clrify.it
   - OAuth client credentials
   - API access permissions

3. **Microsoft Account** (for email functionality)
   - Microsoft 365 or Outlook account
   - Azure app registration (handled by FUF)

4. **Google Cloud** (optional, for Google Sheets)
   - Google Cloud project
   - Sheets API enabled
   - Service account credentials

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd 2025_exam_grading_presentation
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

#### Using pip (Development Mode)

```bash
pip install -e .
```

This installs the package in development mode, allowing you to modify the code without reinstalling.

#### Install Additional Dependencies

If you need development tools:

```bash
pip install mypy pytest black
```

### 4. Configure AWS Credentials

#### Option A: AWS CLI

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region
- Default output format

#### Option B: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

#### Option C: IAM Role (EC2)

If running on EC2, use IAM roles for automatic authentication.

### 5. Configure prprpr Credentials

Edit `src/exam_grading/common/config.py`:

```python
# For development
PRPRPR_DEBUG = True
PRPRPR_CLIENT_ID = "your_dev_client_id"
PRPRPR_CLIENT_SECRET = "your_dev_client_secret"

# For production
PRPRPR_CLIENT_ID_PROD = "your_prod_client_id"
PRPRPR_CLIENT_SECRET_PROD = "your_prod_client_secret"
```

**Security Note**: Consider using environment variables instead:

```bash
export PRPRPR_CLIENT_ID=your_client_id
export PRPRPR_CLIENT_SECRET=your_client_secret
```

### 6. Install LaTeX

#### macOS

```bash
# Using Homebrew
brew install --cask mactex

# Or BasicTeX (smaller)
brew install --cask basictex
```

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install texlive-full
```

#### Windows

Download and install MiKTeX from https://miktex.org/

### 7. Verify Installation

Run the test command:

```bash
python -m exam_grading --help
```

You should see the CLI menu options.

## Configuration Files

### 1. Create Configuration JSON

Create a configuration file (e.g., `config.json`):

```json
{
  "paths": {
    "scans_folder": "./scans",
    "parsed_folder": "./scans_parsed",
    "omr_output_folder": "./scans_parsed_OMR",
    "omr_marker": "./omr_marker.jpg",
    "bubbles_csv": "./bubbles.csv",
    "consolidated_answers": "./scans_parsed_OMR/consolidated_answers.csv",
    "students_csv": "./students.csv",
    "questiondb": "./questiondb.json",
    "everything_job": "./everything_job.csv",
    "csv_jobs_folder": "./csv_jobs",
    "downloaded_jobs_folder": "./downloaded_jobs",
    "merged_job": "./merged_grading_jobs.csv",
    "annotated_pdfs_folder": "./annotated_pdfs",
    "student_feedback_folder": "./student_feedback"
  }
}
```

### 2. Prepare Data Files

#### students.csv

```csv
student_id,anonymous_id,first_name,last_name,email
abc123,student_001,Alice,Smith,alice.smith@yale.edu
def456,student_002,Bob,Jones,bob.jones@yale.edu
```

#### bubbles.csv

```csv
page,question,subquestion,choice,Xpos,Ypos
1,1,i,a,120.5,234.5
1,1,i,b,145.5,234.5
```

#### questiondb.json

```json
{
  "problems": [
    {
      "number": 1,
      "name": "Problem 1",
      "path": "problems/problem1.tex",
      "subquestions": [
        {
          "label": "i",
          "answer_values": [
            {"label": "a", "default": 1.0},
            {"label": "b", "default": 0.5}
          ]
        }
      ]
    }
  ]
}
```

### 3. Prepare OMR Marker

Create or obtain an OMR marker image (JPEG) for page alignment. This should be a distinctive pattern placed at the corners of your answer sheets.

## Testing the Installation

### 1. Test Individual Components

```bash
# Test configuration loading
python -c "from exam_grading.common.config import PRPRPR_BASE_URL; print(PRPRPR_BASE_URL)"

# Test AWS connection
aws s3 ls s3://your-bucket-name/

# Test LaTeX
pdflatex --version
```

### 2. Run Sample Workflow

Use the provided test data:

```bash
# Copy test configuration
cp testing_config.json config.json

# Run QR code reading
python -m exam_grading
# Select option 1
```

## Troubleshooting

### Common Installation Issues

#### Python Version Error

```
Error: Python 3.8 or higher required
```

**Solution**: Install Python 3.8+ or use pyenv to manage versions.

#### Missing Dependencies

```
ModuleNotFoundError: No module named 'cv2'
```

**Solution**: Ensure all dependencies are installed:
```bash
pip install -e . --force-reinstall
```

#### LaTeX Not Found

```
LaTeX Error: pdflatex not found
```

**Solution**: 
1. Install LaTeX as described above
2. Add LaTeX to PATH
3. Restart terminal

#### AWS Authentication Error

```
NoCredentialsError: Unable to locate credentials
```

**Solution**:
1. Run `aws configure`
2. Check ~/.aws/credentials file
3. Verify IAM permissions

### Platform-Specific Issues

#### macOS
- If using M1/M2 Mac, some dependencies may need Rosetta
- Homebrew Python recommended over system Python

#### Windows
- Use PowerShell or WSL for better compatibility
- Path separators: use forward slashes in config files

#### Linux
- May need to install additional system libraries:
  ```bash
  sudo apt-get install python3-dev libgl1-mesa-glx
  ```

## Next Steps

After successful installation:

1. Review the [User Guide](user-guide.md) for usage instructions
2. Check [Configuration Guide](configuration.md) for detailed setup
3. See [Architecture](architecture.md) to understand the system
4. Run through the tutorial workflow

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review error messages carefully
3. Ensure all prerequisites are met
4. Check GitHub issues for similar problems
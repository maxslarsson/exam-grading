# Exam Grading System Documentation

## Overview

The Exam Grading System is an automated solution for processing, grading, and providing feedback on scanned exams. It handles QR code recognition, optical mark recognition (OMR), cloud storage integration, and automated feedback generation.

## Table of Contents

1. [Architecture Overview](architecture.md)
2. [Installation Guide](installation.md)
3. [User Guide](user-guide.md)
4. [API Reference](api-reference.md)
5. [Configuration Guide](configuration.md)
6. [Development Guide](development.md)

## Quick Start

### Prerequisites

- Python 3.8+
- AWS credentials (for S3 integration)
- Google Cloud credentials (for Sheets API)
- Access to prprpr grading service

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd 2025_exam_grading_presentation

# Install dependencies
pip install -e .
```

### Basic Usage

Run the main CLI interface:

```bash
python -m exam_grading
```

Or use the installed script:

```bash
exam-grading
```

## System Components

### Core Workflow

1. **Scan Processing**: Read QR codes and organize scanned images
2. **OMR Processing**: Detect marked bubbles on answer sheets
3. **Cloud Upload**: Store PDFs in AWS S3
4. **Grading**: Create and manage grading jobs via prprpr
5. **Feedback**: Generate personalized student feedback

### Key Features

- **Automated QR Code Reading**: Identifies students and page numbers
- **Optical Mark Recognition**: Detects bubble sheet answers
- **Cloud Integration**: AWS S3 for storage, Google Sheets for grading
- **Batch Processing**: Handle multiple exams efficiently
- **Feedback Generation**: LaTeX-based personalized feedback PDFs

## Configuration

The system uses JSON configuration files to specify:
- Input/output directories
- OMR marker images
- Question databases
- Student information
- API credentials

See [Configuration Guide](configuration.md) for details.

## Support

For issues or questions, please refer to the [troubleshooting guide](troubleshooting.md) or contact the development team.
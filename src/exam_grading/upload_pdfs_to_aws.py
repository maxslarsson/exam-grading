"""Upload PDFs to AWS S3 bucket.

This module handles uploading exam PDFs to AWS S3 for storage and access by
the grading service. All student IDs are anonymized before upload to protect
student privacy. The module requires AWS credentials to be configured via
AWS CLI or environment variables.
"""
import boto3
from pathlib import Path

from .common.validators import validate_directory
from .common.progress import ProgressPrinter
from .common.config import AWS_BUCKET_NAME
from .common.anonymization import StudentAnonymizer


def upload_pdfs_to_aws(parsed_folder_path: str, students_csv_path: str = None) -> None:
    """Upload PDFs from parsed folder to AWS S3 bucket with anonymized filenames.
    
    This function recursively finds all PDF files in the parsed folder and uploads
    them to S3 with anonymized student IDs. Files are organized in S3 under the
    'grading/student_work/' prefix. Anonymization is mandatory to protect privacy.
    
    Args:
        parsed_folder_path: Path to the parsed folder containing PDFs from OMR processing
        students_csv_path: Path to students CSV with anonymization mappings (required)
        
    Raises:
        ValueError: If students_csv_path is not provided or anonymization fails
        RuntimeError: If any files fail to upload
        
    S3 Structure:
        s3://bucket/grading/student_work/anonymous001_1.pdf
        s3://bucket/grading/student_work/anonymous001_2.pdf
        ...
        
    Note:
        - AWS credentials must be configured (via AWS CLI or environment variables)
        - All uploads fail if any file cannot be anonymized (fail-safe for privacy)
        - Progress is displayed during upload
    """
    parsed_folder_path = Path(parsed_folder_path)
    validate_directory(parsed_folder_path, "Parsed folder")
    
    # Initialize anonymizer (required)
    if not students_csv_path:
        raise ValueError("students_csv_path is required for anonymization")
    
    try:
        anonymizer = StudentAnonymizer(students_csv_path)
        print(f"Loaded anonymization mappings from {students_csv_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to load anonymization mappings: {e}")
    
    all_pdfs = list(parsed_folder_path.glob("**/*.pdf"))
    s3 = boto3.client('s3')
    
    progress = ProgressPrinter("Uploading PDF files to S3", len(all_pdfs))
    
    successful = 0
    failed = 0
    
    for i, pdf_path in enumerate(all_pdfs):
        progress.update(i + 1)
        
        try:
            # Anonymize filename (required)
            filename = anonymizer.anonymize_filename(pdf_path.name)
            
            object_name = f"grading/student_work/{filename}"
            s3.upload_file(str(pdf_path), AWS_BUCKET_NAME, object_name)
            successful += 1
        except ValueError as e:
            print(f"\n  ✗ Anonymization error for {pdf_path.name}: {e}")
            failed += 1
        except Exception as e:
            print(f"\n  ✗ Failed to upload {pdf_path}: {e}")
            failed += 1
    
    progress.done()
    
    # Summary and error if any files failed
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(all_pdfs)}")
    
    if failed > 0:
        raise RuntimeError(f"Failed to upload {failed} files. No files should be uploaded without proper anonymization.")
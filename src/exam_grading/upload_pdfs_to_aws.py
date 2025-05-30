"""Upload PDFs to AWS S3 bucket."""
import boto3
from pathlib import Path

from .common.validators import validate_directory
from .common.progress import ProgressPrinter
from .common.config import AWS_BUCKET_NAME
from .common.anonymization import StudentAnonymizer


def upload_pdfs_to_aws(parsed_folder_path: str, students_csv_path: str = None) -> None:
    """
    Upload PDFs from parsed folder to AWS S3 bucket with anonymized filenames.
    
    Args:
        parsed_folder_path: Path to the parsed folder containing PDFs
        students_csv_path: Optional path to students CSV for anonymization
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
"""Upload PDFs to AWS S3 bucket."""
import boto3
from pathlib import Path

from .common.validators import validate_directory
from .common.progress import ProgressPrinter
from .common.config import AWS_BUCKET_NAME


def upload_pdfs_to_aws(parsed_folder_path: str) -> None:
    """
    Upload PDFs from parsed folder to AWS S3 bucket.
    
    Args:
        parsed_folder_path: Path to the parsed folder containing PDFs
    """
    parsed_folder_path = Path(parsed_folder_path)
    validate_directory(parsed_folder_path, "Parsed folder")
    
    all_pdfs = list(parsed_folder_path.glob("**/*.pdf"))
    s3 = boto3.client('s3')
    
    progress = ProgressPrinter("Uploading PDF files to S3", len(all_pdfs))
    
    for i, pdf_path in enumerate(all_pdfs):
        progress.update(i + 1)
        object_name = f"grading/student_work/{pdf_path.name}"
        try:
            s3.upload_file(str(pdf_path), AWS_BUCKET_NAME, object_name)
            print(f"Successfully uploaded {pdf_path}")
        except Exception as e:
            print(f"Failed to upload {pdf_path}: {e}")
    
    progress.done()
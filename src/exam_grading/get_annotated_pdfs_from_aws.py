"""Download annotated PDFs from AWS S3 bucket to local folder.

This module retrieves graded PDFs from AWS S3 after they have been annotated
by graders. It handles de-anonymization to restore original student IDs and
preserves the directory structure from S3. The module supports pagination for
large numbers of files.
"""
import boto3
from pathlib import Path

from .common.config import AWS_BUCKET_NAME
from .common.anonymization import StudentAnonymizer
from .common.progress import ProgressPrinter


def get_annotated_pdfs_from_aws(destination_folder_path: str, students_csv_path: str = None) -> None:
    """Download annotated PDFs from AWS S3 bucket to local folder with de-anonymization.
    
    This function downloads all PDFs from the 'grading/' prefix in S3, which includes
    both student work and annotated versions. Student IDs are de-anonymized during
    download to restore original identities. The S3 directory structure is preserved
    locally.
    
    Args:
        destination_folder_path: Path to destination folder for downloaded PDFs
        students_csv_path: Path to students CSV for de-anonymization (required)
        
    Raises:
        ValueError: If students_csv_path is not provided
        RuntimeError: If de-anonymization fails or files cannot be downloaded
        
    Directory Structure:
        The function preserves the S3 structure:
        - grading/student_work/studentID_page.pdf
        - grading/annotated/graderID/studentID_page_annotated.pdf
        
    Note:
        - Handles S3 pagination for buckets with many files
        - Shows progress during download
        - All files must be successfully de-anonymized (fail-safe)
    """
    destination_folder = Path(destination_folder_path)
    
    # Initialize anonymizer (required for de-anonymization)
    if not students_csv_path:
        raise ValueError("students_csv_path is required for de-anonymization")
    
    try:
        anonymizer = StudentAnonymizer(students_csv_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load de-anonymization mappings: {e}")
    
    s3 = boto3.client("s3")
    
    response = s3.list_objects_v2(Bucket=AWS_BUCKET_NAME, Prefix="grading/")
    
    # Check if any objects were found
    if "Contents" not in response:
        print("No files found in grading/annotated/ prefix")
        return
    
    # Count total PDFs first
    total_pdfs = 0
    temp_response = response
    while True:
        total_pdfs += sum(1 for obj in temp_response["Contents"] if obj["Key"].endswith(".pdf"))
        if temp_response.get("IsTruncated", False):
            continuation_token = temp_response.get("NextContinuationToken")
            temp_response = s3.list_objects_v2(Bucket=AWS_BUCKET_NAME, ContinuationToken=continuation_token, Prefix="grading/")
        else:
            break
    
    progress = ProgressPrinter("Downloading PDFs", total_pdfs)
    
    downloaded_count = 0
    failed_count = 0
    failed_files = []
    
    # Reset to start downloading
    response = s3.list_objects_v2(Bucket=AWS_BUCKET_NAME, Prefix="grading/")
    
    i = 0
    while True:
        for obj in response["Contents"]:
            progress.update(i + 1)
            key = obj["Key"]
            if key.endswith(".pdf"):
                try:
                    # De-anonymize filename (required)
                    filename = anonymizer.deanonymize_filename(Path(key).name)
                    
                    # Preserve directory structure but with de-anonymized filename
                    key_parts = Path(key).parts[:-1]  # All parts except filename
                    local_file_path = destination_folder / Path(*key_parts) / filename
                    
                    local_file_path.parent.mkdir(parents=True, exist_ok=True)
                    s3.download_file(AWS_BUCKET_NAME, key, str(local_file_path))
                    downloaded_count += 1
                except ValueError as e:
                    failed_count += 1
                    failed_files.append(f"{key}: De-anonymization error - {e}")
                except Exception as e:
                    failed_count += 1
                    failed_files.append(f"{key}: Download error - {e}")
            i += 1
        
        if response.get("IsTruncated", False):
            continuation_token = response.get("NextContinuationToken")
            response = s3.list_objects_v2(Bucket=AWS_BUCKET_NAME, ContinuationToken=continuation_token, Prefix="grading/")
        else:
            break
    
    progress.done()
    
    # Summary and error if any files failed
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Successful: {downloaded_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {downloaded_count + failed_count}")
    
    if failed_count > 0:
        print(f"\nFailed files:")
        for failure in failed_files:
            print(f"  • {failure}")
        raise RuntimeError(f"Failed to download {failed_count} files. All files must be properly de-anonymized.")
"""Download annotated PDFs from AWS S3 bucket to local folder."""
import boto3
from pathlib import Path

from .common.config import AWS_BUCKET_NAME
from .common.anonymization import StudentAnonymizer


def get_annotated_pdfs_from_aws(destination_folder_path: str, students_csv_path: str = None) -> None:
    """
    Download annotated PDFs from AWS S3 bucket to local folder with de-anonymization.
    
    Args:
        destination_folder_path: Path to destination folder for downloaded PDFs
        students_csv_path: Optional path to students CSV for de-anonymization
    """
    destination_folder = Path(destination_folder_path)
    
    # Initialize anonymizer (required for de-anonymization)
    if not students_csv_path:
        raise ValueError("students_csv_path is required for de-anonymization")
    
    try:
        anonymizer = StudentAnonymizer(students_csv_path)
        print(f"Loaded de-anonymization mappings from {students_csv_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to load de-anonymization mappings: {e}")
    
    s3 = boto3.client("s3")
    
    response = s3.list_objects_v2(Bucket=AWS_BUCKET_NAME, Prefix="grading/")
    
    # Check if any objects were found
    if "Contents" not in response:
        print("No files found in grading/annotated/ prefix")
        return
    
    downloaded_count = 0
    failed_count = 0
    
    while True:
        for obj in response["Contents"]:
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
                    
                    if filename != Path(key).name:
                        print(f"Downloaded {key} as {local_file_path}")
                    else:
                        print(f"Downloaded {key}")
                    downloaded_count += 1
                except ValueError as e:
                    print(f"\n  ✗ De-anonymization error for {key}: {e}")
                    failed_count += 1
                except Exception as e:
                    print(f"\n  ✗ Failed to download {key}: {e}")
                    failed_count += 1
        
        if response.get("IsTruncated", False):
            continuation_token = response.get("NextContinuationToken")
            response = s3.list_objects_v2(Bucket=AWS_BUCKET_NAME, ContinuationToken=continuation_token, Prefix="grading/")
        else:
            break
    
    # Summary and error if any files failed
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Successful: {downloaded_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {downloaded_count + failed_count}")
    
    if failed_count > 0:
        raise RuntimeError(f"Failed to download {failed_count} files. All files must be properly de-anonymized.")
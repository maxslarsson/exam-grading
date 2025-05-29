"""Download annotated PDFs from AWS S3 bucket to local folder."""
import boto3
from pathlib import Path

from .common.config import AWS_BUCKET_NAME


def get_annotated_pdfs_from_aws(destination_folder_path: str) -> None:
    """
    Download annotated PDFs from AWS S3 bucket to local folder.
    
    Args:
        destination_folder_path: Path to destination folder for downloaded PDFs
    """
    destination_folder = Path(destination_folder_path)
    
    s3 = boto3.client("s3")
    
    response = s3.list_objects_v2(Bucket=AWS_BUCKET_NAME, Prefix="grading/")
    
    # Check if any objects were found
    if "Contents" not in response:
        print("No files found in grading/annotated/ prefix")
        return
    
    downloaded_count = 0
    while True:
        for obj in response["Contents"]:
            key = obj["Key"]
            if key.endswith(".pdf"):
                local_file_path = destination_folder / key
                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                s3.download_file(AWS_BUCKET_NAME, key, str(local_file_path))
                print(f"Downloaded {key} to {local_file_path}")
                downloaded_count += 1
        
        if response.get("IsTruncated", False):
            continuation_token = response.get("NextContinuationToken")
            response = s3.list_objects_v2(Bucket=AWS_BUCKET_NAME, ContinuationToken=continuation_token, Prefix="grading/")
        else:
            break
    
    print(f"\nTotal files downloaded: {downloaded_count}")
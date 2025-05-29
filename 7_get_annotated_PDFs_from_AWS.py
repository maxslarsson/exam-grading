"""
Download annotated PDFs from AWS S3 bucket to local folder.
Usage: python 6_2_get_annotated_PDFs_from_AWS.py <destination_folder>
"""
import sys
import boto3
from pathlib import Path


def main():
    # Get the arguments that were passed to the script
    _, script_args = sys.argv[0], sys.argv[1:]

    # If less than one argument was given to the script, we need the destination folder
    if len(script_args) < 1:
        print("Error: not enough arguments were given to the script")
        print("Usage: python 6_2_get_annotated_PDFs_from_AWS.py <destination_folder>")
        sys.exit(1)

    destination_folder = Path(script_args[0])

    s3 = boto3.client("s3")
    bucket_name = "prprpr-s3"

    response = s3.list_objects_v2(Bucket=bucket_name, Prefix="grading/")
    
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
                s3.download_file(bucket_name, key, str(local_file_path))
                print(f"Downloaded {key} to {local_file_path}")
                downloaded_count += 1

        if response.get("IsTruncated", False):
            continuation_token = response.get("NextContinuationToken")
            response = s3.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuation_token, Prefix="grading/")
        else:
            break
    
    print(f"\nTotal files downloaded: {downloaded_count}")


if __name__ == "__main__":
    main()
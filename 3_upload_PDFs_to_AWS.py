import sys
import boto3
from pathlib import Path


def main():
    # Get the arguments that were passed to the script
    _, script_args = sys.argv[0], sys.argv[1:]

    # If less than two arguments were given to the script, we do not have the CSV files we need
    if len(script_args) < 1:
        print("Error: not enough arguments were given to the script")
        sys.exit(1)

    # We expect the first argument to be the path to the parsed folder that has one subfolder per page
    parsed_folder_path = Path(script_args[0])

    if not parsed_folder_path.is_dir():
        print("Error: first argument is not a directory")
        sys.exit(1)

    all_pdfs = list(parsed_folder_path.glob("**/*.pdf"))
    s3 = boto3.client('s3')
    bucket_name = "prprpr-s3"
    for i, pdf_path in enumerate(all_pdfs):
        print(f"Uploading PDF files to S3...{i+1}/{len(all_pdfs)}", end='\r', flush=True)
        object_name = f"grading/student_work/{pdf_path.name}"
        try:
            s3.upload_file(pdf_path, bucket_name, object_name)
            print(f"Successfully uploaded {pdf_path}")
        except Exception as e:
            print(f"Failed to upload {pdf_path}: {e}")

    print(f"Uploading PDF files to S3...Done!             ")


if __name__ == "__main__":
    main()

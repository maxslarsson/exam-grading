"""Main entry point for the exam grading package."""
import sys
import json
import argparse
from pathlib import Path

from .read_qr_codes import read_qr_codes_and_move
from .run_omr import run_omr
from .upload_pdfs_to_aws import upload_pdfs_to_aws
from .create_everything_job import create_everything_job
from .upload_jobs_to_prprpr import upload_jobs_to_prprpr
from .download_jobs_from_prprpr import download_jobs_from_prprpr
from .get_annotated_pdfs_from_aws import get_annotated_pdfs_from_aws
from .merge_downloaded_jobs import merge_downloaded_jobs
from .split_everything_job import split_everything_job
from .generate_student_feedback import generate_feedback_for_all_students
from .email_feedback_to_students import email_feedback_to_students


def print_menu():
    """Print the main menu."""
    print("\n=== Exam Grading Tool ===\n")
    print("1. Read QR codes and move images")
    print("2. Run OMR on images")
    print("3. Upload PDFs to AWS")
    print("4. Create everything job")
    print("5. Split everything job into individual jobs")
    print("6. Upload jobs to prprpr")
    print("7. Download jobs from prprpr")
    print("8. Get annotated PDFs from AWS")
    print("9. Merge downloaded jobs")
    print("10. Generate student feedback")
    print("11. Email feedback to students")
    print("0. Exit")


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Main menu for exam grading functions."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Exam Grading Tool')
    parser.add_argument('config', help='Path to configuration JSON file')
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
        print(f"Loaded configuration from: {args.config}")
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)
    
    while True:
        print_menu()
        try:
            choice = input("\nEnter your choice (0-11): ").strip()
        except KeyboardInterrupt:
            sys.exit(0)
        
        if choice == "0":
            sys.exit(0)
        elif choice == "1":
            run_read_qr_codes(config)
        elif choice == "2":
            run_omr_function(config)
        elif choice == "3":
            run_upload_pdfs(config)
        elif choice == "4":
            run_create_everything_job(config)
        elif choice == "5":
            run_split_everything_job(config)
        elif choice == "6":
            run_upload_jobs(config)
        elif choice == "7":
            run_download_jobs(config)
        elif choice == "8":
            run_get_annotated_pdfs(config)
        elif choice == "9":
            run_merge_downloaded_jobs(config)
        elif choice == "10":
            run_generate_student_feedback(config)
        elif choice == "11":
            run_email_feedback(config)
        else:
            print("Invalid choice. Please try again.")


def run_read_qr_codes(config):
    """Run the read QR codes function."""
    print("\n--- Read QR codes and move images ---")
    
    try:
        scans_folder = config['paths']['scans_folder']
        output_folder = read_qr_codes_and_move(scans_folder)
        print(f"Success! Output folder: {output_folder}")
    except Exception as e:
        print(f"Error: {e}")


def run_omr_function(config):
    """Run the OMR function."""
    print("\n--- Run OMR on images ---")
    
    try:
        marker_path = config['paths']['omr_marker']
        bubbles_csv = config['paths']['bubbles_csv']
        parsed_folder = config['paths']['parsed_folder']
        output_folder = run_omr(marker_path, bubbles_csv, parsed_folder)
        print(f"Success! Output folder: {output_folder}")
    except Exception as e:
        print(f"Error: {e}")


def run_upload_pdfs(config):
    """Run the upload PDFs to AWS function."""
    print("\n--- Upload PDFs to AWS ---")
    try:
        parsed_omr_folder = config['paths']['parsed_omr_folder']
        students_csv = config['paths']['students_csv']
        upload_pdfs_to_aws(parsed_omr_folder, students_csv)
        print("Success! PDFs uploaded to AWS")
    except Exception as e:
        print(f"Error: {e}")


def run_create_everything_job(config):
    """Run the create everything job function."""
    print("\n--- Create everything job ---")
    
    try:
        bubbles_csv = config['paths']['bubbles_csv']
        answers_csv = config['paths']['consolidated_answers_csv']
        questiondb_path = config['paths']['questiondb']
        output_path = config['paths']['everything_job_csv']
        output_file = create_everything_job(bubbles_csv, answers_csv, questiondb_path, output_path)
        print(f"Success! Created: {output_file}")
    except Exception as e:
        print(f"Error: {e}")


def run_split_everything_job(config):
    """Run the split everything job function."""
    print("\n--- Split everything job into individual jobs ---")
    
    try:
        everything_job_csv = config['paths']['everything_job_csv']
        csv_jobs_folder = config['paths']['csv_jobs_folder']
        job_files = split_everything_job(everything_job_csv, csv_jobs_folder)
        print(f"Success! Created {len(job_files)} job files")
    except Exception as e:
        print(f"Error: {e}")


def run_upload_jobs(config):
    """Run the upload jobs to prprpr function."""
    print("\n--- Upload jobs to prprpr ---")
    
    try:
        csv_folder = config['paths']['csv_jobs_folder']
        students_csv = config['paths']['students_csv']
        upload_jobs_to_prprpr(csv_folder, students_csv)
        print("Success! Jobs uploaded to prprpr")
    except Exception as e:
        print(f"Error: {e}")


def run_download_jobs(config):
    """Run the download jobs from prprpr function."""
    print("\n--- Download jobs from prprpr ---")

    try:
        download_jobs_folder = config['paths']['downloaded_jobs_folder']
        students_csv = config['paths']['students_csv']
        download_jobs_from_prprpr(download_jobs_folder, students_csv)
        print("Success! Jobs downloaded from prprpr")
    except Exception as e:
        print(f"Error: {e}")


def run_get_annotated_pdfs(config):
    """Run the get annotated PDFs from AWS function."""
    print("\n--- Get annotated PDFs from AWS ---")
    
    try:
        destination_folder = config['paths']['annotated_pdfs_folder']
        students_csv = config['paths']['students_csv']
        get_annotated_pdfs_from_aws(destination_folder, students_csv)
        print("Success! PDFs downloaded from AWS")
    except Exception as e:
        print(f"Error: {e}")

def run_merge_downloaded_jobs(config):
    """Run the merge downloaded jobs function."""
    print("\n--- Merge downloaded jobs ---")
    
    try:
        downloaded_jobs_folder = config['paths']['downloaded_jobs_folder']
        output_file = config['paths']['merged_grading_jobs_csv']
        merged_file = merge_downloaded_jobs(downloaded_jobs_folder, output_file)
        print(f"Success! Merged file: {merged_file}")
    except Exception as e:
        print(f"Error: {e}")


def run_generate_student_feedback(config):
    """Run the generate student feedback function."""
    print("\n--- Generate student feedback ---")
    
    try:
        merged_jobs_path = config['paths']['merged_grading_jobs_csv']
        questiondb_path = config['paths']['questiondb']
        students_csv_path = config['paths']['students_csv']
        annotated_pdfs_folder_path = config['paths']['annotated_pdfs_folder']
        feedback_files = generate_feedback_for_all_students(merged_jobs_path, questiondb_path, students_csv_path, annotated_pdfs_folder_path)
        if feedback_files:
            output_dir = feedback_files[0].parent
            print(f"Success! Generated {len(feedback_files)} feedback files in {output_dir}")
        else:
            print("No feedback files were generated")
    except Exception as e:
        print(f"Error: {e}")


def run_email_feedback(config):
    """Run the email feedback to students function."""
    print("\n--- Email feedback to students ---")
    
    try:
        feedback_folder = config['paths']['student_feedback_folder']
        students_csv = config['paths']['students_csv']
        email_feedback_to_students(feedback_folder, students_csv)
        print("Success! Emails sent to students")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
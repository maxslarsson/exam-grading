"""Main entry point for the exam grading package."""
import sys
from pathlib import Path

from .read_qr_codes import read_qr_codes_and_move
from .run_omr import run_omr
from .upload_pdfs_to_aws import upload_pdfs_to_aws
from .create_everything_job import create_everything_job
from .upload_jobs_to_prprpr import upload_jobs_to_prprpr
from .download_jobs_from_prprpr import download_jobs_from_prprpr
from .get_annotated_pdfs_from_aws import get_annotated_pdfs_from_aws
from .create_grading_spreadsheet import create_grading_spreadsheet


def print_menu():
    """Print the main menu."""
    print("\n=== Exam Grading Tool ===\n")
    print("1. Read QR codes and move images")
    print("2. Run OMR on images")
    print("3. Upload PDFs to AWS")
    print("4. Create everything job")
    print("5. Upload jobs to prprpr")
    print("6. Download jobs from prprpr")
    print("7. Get annotated PDFs from AWS")
    print("8. Create grading spreadsheet")
    print("0. Exit")


def main():
    """Main menu for exam grading functions."""
    
    while True:
        print_menu()
        choice = input("\nEnter your choice (0-8): ").strip()
        
        if choice == "0":
            print("Goodbye!")
            sys.exit(0)
        elif choice == "1":
            run_read_qr_codes()
        elif choice == "2":
            run_omr_function()
        elif choice == "3":
            run_upload_pdfs()
        elif choice == "4":
            run_create_everything_job()
        elif choice == "5":
            run_upload_jobs()
        elif choice == "6":
            run_download_jobs()
        elif choice == "7":
            run_get_annotated_pdfs()
        elif choice == "8":
            run_create_spreadsheet()
        else:
            print("Invalid choice. Please try again.")


def run_read_qr_codes():
    """Run the read QR codes function."""
    print("\n--- Read QR codes and move images ---")
    scans_folder = input("Enter path to scans folder: ").strip()
    
    try:
        output_folder = read_qr_codes_and_move(scans_folder)
        print(f"Success! Output folder: {output_folder}")
    except Exception as e:
        print(f"Error: {e}")


def run_omr_function():
    """Run the OMR function."""
    print("\n--- Run OMR on images ---")
    marker_path = input("Enter path to OMR marker image (omr_marker.jpg): ").strip()
    bubbles_csv = input("Enter path to bubbles CSV file: ").strip()
    parsed_folder = input("Enter path to parsed folder: ").strip()
    
    try:
        output_folder = run_omr(marker_path, bubbles_csv, parsed_folder)
        print(f"Success! Output folder: {output_folder}")
    except Exception as e:
        print(f"Error: {e}")


def run_upload_pdfs():
    """Run the upload PDFs to AWS function."""
    print("\n--- Upload PDFs to AWS ---")
    parsed_folder = input("Enter path to parsed OMR folder: ").strip()
    
    try:
        upload_pdfs_to_aws(parsed_folder)
        print("Success! PDFs uploaded to AWS")
    except Exception as e:
        print(f"Error: {e}")


def run_create_everything_job():
    """Run the create everything job function."""
    print("\n--- Create everything job ---")
    bubbles_csv = input("Enter path to bubbles CSV file: ").strip()
    answers_csv = input("Enter path to consolidated answers CSV file: ").strip()
    
    try:
        output_file = create_everything_job(bubbles_csv, answers_csv)
        print(f"Success! Created: {output_file}")
    except Exception as e:
        print(f"Error: {e}")


def run_upload_jobs():
    """Run the upload jobs to prprpr function."""
    print("\n--- Upload jobs to prprpr ---")
    csv_folder = input("Enter path to CSV jobs folder: ").strip()
    
    try:
        upload_jobs_to_prprpr(csv_folder)
        print("Success! Jobs uploaded to prprpr")
    except Exception as e:
        print(f"Error: {e}")


def run_download_jobs():
    """Run the download jobs from prprpr function."""
    print("\n--- Download jobs from prprpr ---")
    output_folder = input("Enter path to output folder: ").strip()
    
    try:
        download_jobs_from_prprpr(output_folder)
        print("Success! Jobs downloaded from prprpr")
    except Exception as e:
        print(f"Error: {e}")


def run_get_annotated_pdfs():
    """Run the get annotated PDFs from AWS function."""
    print("\n--- Get annotated PDFs from AWS ---")
    destination_folder = input("Enter path to destination folder: ").strip()
    
    try:
        get_annotated_pdfs_from_aws(destination_folder)
        print("Success! PDFs downloaded from AWS")
    except Exception as e:
        print(f"Error: {e}")


def run_create_spreadsheet():
    """Run the create grading spreadsheet function."""
    print("\n--- Create grading spreadsheet ---")
    ps_csv = input("Enter path to problem set CSV: ").strip()
    students_csv = input("Enter path to students CSV: ").strip()
    individual_csv = input("Enter path to individual answers CSV: ").strip()
    team_csv = input("Enter path to learning team answers CSV: ").strip()
    
    try:
        url = create_grading_spreadsheet(ps_csv, students_csv, individual_csv, team_csv)
        print(f"Success! Spreadsheet URL: {url}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
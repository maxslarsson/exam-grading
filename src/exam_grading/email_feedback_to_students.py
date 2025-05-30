"""Email feedback PDFs to students using Microsoft Outlook.

This module handles the distribution of generated feedback PDFs to students
via email using the Microsoft Graph API. It integrates with Outlook to send
personalized emails with PDF attachments containing exam feedback.

Key Features:
- Batch email sending with progress tracking
- Student information lookup from CSV file
- Automatic attachment handling
- Error reporting and summary statistics
- Confirmation prompt before sending

Requirements:
- Microsoft Graph API access (OAuth2 authentication)
- Valid Outlook account with send permissions
- FUF library for Graph API integration
"""
from pathlib import Path
import pandas as pd
from fuf.outlook.email_feedback_to_students import send_email_via_outlook, get_graph_client

from .common.progress import ProgressPrinter
from .common.validators import validate_directory, validate_csv_file


def email_feedback_to_students(
    feedback_folder: str,
    students_csv: str
) -> None:
    """
    Email feedback PDFs to students using Microsoft Outlook.
    
    This function sends personalized feedback PDFs to students via email.
    It matches PDF files with student information from a CSV file and
    sends individual emails with the feedback attached.
    
    Args:
        feedback_folder: Path to folder containing student feedback PDFs.
                        Expected filename format: {studentID}_feedback.pdf
        students_csv: Path to students CSV file with required columns:
                     - studentID: Unique student identifier
                     - first_name: Student's first name
                     - last_name: Student's last name  
                     - email: Student's email address
    
    Process:
        1. Validates input paths and CSV format
        2. Loads student information into memory
        3. Finds all feedback PDF files
        4. Prompts for confirmation before sending
        5. Sends emails with progress tracking
        6. Reports summary statistics
        
    Raises:
        ValueError: If required CSV columns are missing or no PDFs found
        
    Note:
        - OAuth2 authentication handled by FUF library
        - Failed emails are logged but don't stop the batch
        - Each student receives only their own feedback
    """
    feedback_folder = Path(feedback_folder)
    students_csv = Path(students_csv)
    
    # Validate inputs - ensure paths exist and are accessible
    validate_directory(feedback_folder, "Feedback folder")
    validate_csv_file(students_csv, "Students CSV")
    
    # Load the students CSV to get student emails and names
    students_df = pd.read_csv(students_csv)
    
    # Verify required columns exist in the CSV
    required_cols = ['studentID', 'first_name', 'last_name', 'email']
    missing_cols = [col for col in required_cols if col not in students_df.columns]
    if missing_cols:
        raise ValueError(f"Students CSV is missing required columns: {missing_cols}")
    
    # Create a mapping of student_id to email and name for quick lookup
    student_info = {}
    for _, row in students_df.iterrows():
        student_info[row['studentID']] = {
            'email': row['email'],
            'first_name': row['first_name'],
            'last_name': row['last_name']
        }
    
    # Find all PDF files in the feedback folder matching the expected pattern
    pdf_files = list(feedback_folder.glob("*_feedback.pdf"))
    
    if not pdf_files:
        print("No feedback PDF files found in the specified folder.")
        return
    
    print(f"\nFound {len(pdf_files)} feedback files to email")
    
    # Confirm before sending - important safety check
    response = input("\nAre you sure you want to send emails to all students? (yes/no): ").strip().lower()
    if response != "yes":
        print("Email sending cancelled.")
        return
    
    # Initialize Microsoft Graph API client for Outlook access
    graph_client = get_graph_client()
    
    # Send emails with progress tracking
    successful = 0
    failed = 0
    progress = ProgressPrinter("Sending emails", len(pdf_files))
    
    for i, pdf_path in enumerate(pdf_files):
        progress.update(i + 1)
        
        try:
            # Extract student ID from filename by removing the _feedback suffix
            # Example: ml2843_feedback.pdf -> ml2843
            student_id = pdf_path.stem.replace("_feedback", "")
            
            # Get student info from our mapping
            if student_id not in student_info:
                print(f"\n  Warning: No info found for student {student_id}, skipping")
                failed += 1
                continue
            
            student = student_info[student_id]
            recipient_email = student['email']

            # Compose personalized email content
            email_subject = "Your Exam Feedback"
            email_body = f"""Dear {student['first_name']},

Please find attached your personalized exam feedback.

If you have any questions about your exam or the feedback provided, please don't hesitate to reach out during office hours.

Best regards,
Nils and Max"""
            
            # Prepare attachment - use filename as key and path as value
            attachments = {
                pdf_path.name: pdf_path
            }
            
            # Send email via Microsoft Graph API
            send_email_via_outlook(
                graph_client=graph_client,
                recipient_email=recipient_email,
                subject=email_subject,
                body=email_body,
                attachments=attachments
            )
            
            successful += 1
            
        except Exception as e:
            # Log error but continue with remaining emails
            print(f"\n  Error sending email for {pdf_path.name}: {str(e)}")
            failed += 1
    
    progress.done()
    
    # Display summary statistics
    print(f"\n{'='*50}")
    print(f"Email Summary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(pdf_files)}")
    
    if failed > 0:
        print(f"\nWarning: Failed to send {failed} emails")

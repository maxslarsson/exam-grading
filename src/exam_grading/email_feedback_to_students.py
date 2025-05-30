"""Email feedback PDFs to students using Outlook."""
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
    Email feedback PDFs to students using Outlook.
    
    Args:
        feedback_folder: Path to folder containing student feedback PDFs
        students_csv: Path to students CSV file with columns: studentID, first_name, last_name, email
    """
    feedback_folder = Path(feedback_folder)
    students_csv = Path(students_csv)
    
    # Validate inputs
    validate_directory(feedback_folder, "Feedback folder")
    validate_csv_file(students_csv, "Students CSV")
    
    # Load the students CSV to get student emails
    students_df = pd.read_csv(students_csv)
    
    # Verify required columns exist
    required_cols = ['studentID', 'first_name', 'last_name', 'email']
    missing_cols = [col for col in required_cols if col not in students_df.columns]
    if missing_cols:
        raise ValueError(f"Students CSV is missing required columns: {missing_cols}")
    
    # Create a mapping of student_id to email and name
    student_info = {}
    for _, row in students_df.iterrows():
        student_info[row['studentID']] = {
            'email': row['email'],
            'first_name': row['first_name'],
            'last_name': row['last_name']
        }
    
    # Find all PDF files in the feedback folder
    pdf_files = list(feedback_folder.glob("*_feedback.pdf"))
    
    if not pdf_files:
        print("No feedback PDF files found in the specified folder.")
        return
    
    print(f"\nFound {len(pdf_files)} feedback files to email")
    
    # Confirm before sending
    response = input("\nAre you sure you want to send emails to all students? (yes/no): ").strip().lower()
    if response != "yes":
        print("Email sending cancelled.")
        return
    
    graph_client = get_graph_client()
    
    # Send emails
    successful = 0
    failed = 0
    progress = ProgressPrinter("Sending emails", len(pdf_files))
    
    for i, pdf_path in enumerate(pdf_files):
        progress.update(i + 1)
        
        try:
            # Extract student ID from filename (assumes format: studentid_feedback.pdf)
            student_id = pdf_path.stem.replace("_feedback", "")
            
            # Get student info
            if student_id not in student_info:
                print(f"\n  Warning: No info found for student {student_id}, skipping")
                failed += 1
                continue
            
            student = student_info[student_id]
            recipient_email = student['email']

            email_subject = "Your Exam Feedback"
            email_body = f"""Dear {student['first_name']},

Please find attached your personalized exam feedback.

If you have any questions about your exam or the feedback provided, please don't hesitate to reach out during office hours.

Best regards,
Nils and Max"""
            
            # Prepare attachment
            attachments = {
                pdf_path.name: pdf_path
            }
            
            # Send email
            send_email_via_outlook(
                graph_client=graph_client,
                recipient_email=recipient_email,
                subject=email_subject,
                body=email_body,
                attachments=attachments
            )
            
            successful += 1
            
        except Exception as e:
            print(f"\n  Error sending email for {pdf_path.name}: {str(e)}")
            failed += 1
    
    progress.done()
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Email Summary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(pdf_files)}")
    
    if failed > 0:
        print(f"\nWarning: Failed to send {failed} emails")

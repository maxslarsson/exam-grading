"""Read QR codes from scanned images and organize them by page.

This module processes scanned exam images to extract QR codes containing student
IDs and page numbers. It organizes the images into a structured folder hierarchy
by page number, handling replacement pages and unreadable QR codes.

The expected QR code format is:
    https://clrify.it/replacement/{student_id}/{page_number}/[replacement]
"""
import re
import shutil
from pathlib import Path
import cv2
from qreader import QReader

from .common.validators import validate_directory
from .common.progress import ProgressPrinter


# Regular expression pattern to parse QR code URLs
# Matches: https://clrify.it/replacement/{net_id}/{page}/[optional_extra]
REPLACEMENT_PAGE_URL_PATTERN = re.compile(
    r'^https?://(www\.)?clrify\.it/replacement/'
    r'(?P<net_id>[^/]+)/'      # capture net_id (student ID - anything except a slash)
    r'(?P<page>[^/]+)/?'       # capture page number (anything except a slash)
    r'(?P<extra>.*)?'          # optional extra part (e.g., "replacement" flag)
    r'$'
)


def read_qr_codes_and_move(exam_scans_folder_path: str) -> str:
    """Read QR codes from scanned exam images and organize them by page.
    
    This function processes all JPEG images in the input folder, reads QR codes
    to extract student IDs and page numbers, and organizes them into subfolders
    by page. It handles replacement pages and images with unreadable QR codes.
    
    Args:
        exam_scans_folder_path: Path to the folder containing scanned exam images
                              (JPEG format expected)
        
    Returns:
        str: Path to the output folder containing organized images
        
    Raises:
        ValueError: If the input folder doesn't exist or isn't a directory
        
    Output Structure:
        input_folder_parsed/
        ├── 1/              # Page 1 images
        │   ├── student1_1.jpeg
        │   └── student2_1.jpeg
        ├── 2/              # Page 2 images
        │   └── student1_2.jpeg
        └── noQRcode/       # Images with unreadable QR codes
            └── unreadable.jpeg
            
    Note:
        - Replacement pages (with "replacement" in QR code) overwrite existing files
        - Duplicate pages get numbered suffixes (_1, _2, etc.)
        - Images without readable QR codes are moved to the "noQRcode" folder
    """
    # Convert to Path object and validate input
    exam_scans_folder_path = Path(exam_scans_folder_path)
    validate_directory(exam_scans_folder_path, "Exam scans folder")
    
    # Create output folder name by appending "_parsed" to input folder name
    output_folder_path = exam_scans_folder_path.parent / (exam_scans_folder_path.name + "_parsed")

    # Clean up any existing output folder to ensure fresh results
    if output_folder_path.exists():
        shutil.rmtree(output_folder_path)

    # Initialize QR code reader
    qreader = QReader()
    
    # Find all JPEG files in the input folder (including subdirectories)
    files = list(exam_scans_folder_path.glob("**/*.jpeg"))
    
    # Initialize progress tracking
    progress = ProgressPrinter("Reading QR Codes", len(files))
    
    # Process each image file
    for i, file in enumerate(files):
        progress.update(i + 1)
        
        # Read image using OpenCV
        img = cv2.imread(str(file), cv2.IMREAD_COLOR)
        
        # Detect and decode all QR codes in the image
        decoded_texts = qreader.detect_and_decode(image=img)
        
        # Look for a QR code matching our expected URL format
        decoded_text = None
        for text in decoded_texts:
            if text is not None and isinstance(text, str) and text.startswith("https://clrify.it/replacement/"):
                decoded_text = text
                break
        
        # Handle cases where no valid QR code was found
        if decoded_text is None:
            # Use filename as student ID and mark as "noQRcode"
            net_id, page, extra = file.stem, "noQRcode", None
        else:
            # Parse the QR code URL using our regex pattern
            m = REPLACEMENT_PAGE_URL_PATTERN.match(decoded_text)
            if m is None:
                print(f"Error: QR code '{decoded_text}' does not match expected format.")
                continue
            
            # Extract student ID, page number, and any extra info
            net_id, page, extra = m.group("net_id"), m.group("page"), m.group("extra")

        # Construct output filename: studentID_pageNumber
        filename = f"{net_id}_{page}"
        output_file_path = output_folder_path / page / f"{filename}.jpeg"

        # Handle duplicate pages
        if output_file_path.is_file():
            # Count existing files with the same base name
            existing_files = list(output_file_path.parent.glob(f"{filename}*.jpeg"))
            
            # Create a numbered filename for the additional page
            additional_output_path = output_file_path.parent / f"{filename}_{len(existing_files)}.jpeg"
            
            # If this is a replacement page, move the existing file and use the original name
            if extra == "replacement":
                output_file_path.rename(additional_output_path)
            else:
                # Otherwise, use the numbered filename for this new file
                output_file_path = additional_output_path
        
        # Create output directory if needed and copy the file
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        output_file_path.write_bytes(file.read_bytes())
    
    progress.done()
    return str(output_folder_path)
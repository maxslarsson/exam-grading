"""Run OMR (Optical Mark Recognition) on parsed exam images.

This module performs optical mark recognition on scanned exam answer sheets. It:
1. Aligns pages using corner markers for accurate bubble detection
2. Detects filled bubbles using computer vision techniques
3. Applies adaptive thresholding to distinguish marked from unmarked bubbles
4. Handles both multiple choice and numeric answer formats
5. Generates annotated PDFs showing detected marks
6. Produces consolidated CSV files with all student answers

The system supports:
- Multiple choice questions (a, b, c, d, etc.)
- Numeric answers with decimal points and fractions
- Multi-page exams with replacement pages
- Adaptive thresholding for varying scan quality
"""
import math
from pathlib import Path
from glob import glob
import cv2
import numpy as np
import pandas as pd
from PIL import Image

from .common.validators import validate_file, validate_csv_file, validate_directory


# OMR Configuration Constants
MIN_JUMP = 25  # Minimum intensity jump between marked/unmarked bubbles to consider a gap
OVERLAY_COLOR = (130, 130, 130)  # Color for unmarked bubble boxes on overlay (gray)
MARKED_COLOR = (255, 0, 0)  # Color for marked bubbles on overlay (red in BGR format)
BUBBLE_RADIUS = 7  # Bubble radius in LaTeX points (1 point = 1/72.27 inch)
THRESHOLD_CIRCLE = 0.6  # Minimum correlation confidence for marker detection (0-1)
ANCHOR_RADIUS = 10  # Corner alignment marker radius in LaTeX points
ANCHOR_DISTANCE = 30  # Distance of markers from page edges in LaTeX points
GLOBAL_THRESHOLD = 210  # Maximum intensity value for a bubble to be considered marked (0-255)
TOP_CROP_PERCENTAGE = 0.09  # Percentage of page height to crop from top when saving PDFs


def run_omr(omr_marker_path: str, bubbles_csv_path: str, parsed_folder_path: str) -> str:
    """Run OMR on parsed exam images to detect marked bubbles.
    
    This is the main entry point for the OMR system. It processes all exam images
    in the parsed folder (organized by page), detects filled bubbles, and generates
    both annotated PDFs and CSV files with the results.
    
    Args:
        omr_marker_path: Path to the marker image used for page alignment.
                        This should be a distinctive pattern placed at all
                        four corners of the answer sheet.
        bubbles_csv_path: CSV file containing bubble position definitions with
                         columns: page, question, subquestion, choice, Xpos, Ypos
        parsed_folder_path: Folder containing parsed exam pages organized by
                           page number (output from read_qr_codes module)
        
    Returns:
        str: Path to the output folder containing OMR results including:
             - page_X/ folders with per-page CSVs and annotated PDFs
             - consolidated_answers.csv with all student answers
             
    Raises:
        ValueError: If input files/folders don't exist or are invalid
        
    Example:
        >>> output_dir = run_omr(
        ...     "./omr_marker.jpg",
        ...     "./bubbles.csv",
        ...     "./scans_parsed"
        ... )
        >>> print(f"OMR results saved to: {output_dir}")
    """
    # Convert to Path objects for consistent path handling
    omr_marker_path = Path(omr_marker_path)
    bubbles_csv_path = Path(bubbles_csv_path)
    parsed_folder_path = Path(parsed_folder_path)
    
    # Validate all inputs exist and are correct type
    validate_file(omr_marker_path, "OMR marker file")
    validate_csv_file(bubbles_csv_path, "Bubbles CSV file")
    validate_directory(parsed_folder_path, "Parsed folder")
    
    # Load marker image and bubble definitions
    omr_marker = cv2.imread(str(omr_marker_path), cv2.IMREAD_GRAYSCALE)
    df_bubbles = pd.read_csv(bubbles_csv_path)
    
    # Create output directory with "_OMR" suffix
    output_dir = parsed_folder_path.parent / (parsed_folder_path.name + "_OMR")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all images recursively
    all_student_answers = {}  # Dictionary to store all student answers for consolidation
    process_directory(parsed_folder_path, omr_marker, df_bubbles, output_dir, all_student_answers)
    
    # Create final consolidated CSV with all student answers
    create_consolidated_output(all_student_answers, output_dir)
    
    return str(output_dir)


def process_directory(directory, omr_marker, df_bubbles, output_dir, all_student_answers):
    """Process all images in a directory and its subdirectories.
    
    This function recursively processes exam images, handling multiple pages per
    student and creating annotated PDFs. It groups files by student ID to handle
    replacement pages correctly.
    
    Args:
        directory: Path object for the directory to process
        omr_marker: Loaded marker image for alignment (grayscale numpy array)
        df_bubbles: DataFrame with bubble position definitions
        output_dir: Path object for output directory
        all_student_answers: Dictionary to accumulate all student answers
                           (modified in-place)
    """
    # Find all image files in current directory
    image_extensions = ("*.png", "*.jpg", "*.jpeg")
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob(str(directory / ext)))
    image_files = sorted(image_files)
    
    # Get list of subdirectories to process recursively
    subdirs = [d for d in directory.iterdir() if d.is_dir()]
    
    if image_files:
        print(f"\nProcessing {len(image_files)} images in {directory}")
        results_df = pd.DataFrame()
        
        # Group files by student_id and page, handling multiple files per student
        student_files = {}
        for image_path in image_files:
            path_obj = Path(image_path)
            filename = path_obj.stem
            
            # Parse filename to get student_id and page
            parts = filename.split("_")
            if len(parts) >= 2:
                student_id = parts[0]
                page_part = parts[1]
                
                # Create a key for grouping
                student_page_key = f"{student_id}_{page_part}"
                
                if student_page_key not in student_files:
                    student_files[student_page_key] = []
                
                student_files[student_page_key].append(image_path)
        
        # Process each student's files
        overlay_images = {}  # Store all pages for each student
        for student_page_key, file_list in student_files.items():
            # Sort files to ensure main file comes first
            file_list.sort()
            
            student_id = student_page_key.split("_")[0]
            
            # Process the main file (first one) for OMR
            main_file = file_list[0]
            overlay = process_single_image(main_file, omr_marker, df_bubbles, results_df, all_student_answers)
            
            if overlay is not None:
                # Crop the main overlay
                height, width = overlay.shape[:2]
                crop_height = int(height * TOP_CROP_PERCENTAGE)
                cropped_main = overlay[crop_height:, :]
                
                # Start with the main overlay
                all_pages = [Image.fromarray(cropped_main)]
                
                # Process additional files (no OMR, just crop and add)
                for additional_file in file_list[1:]:
                    # print(f"Adding additional page: {additional_file}")
                    additional_image = cv2.imread(str(additional_file), cv2.IMREAD_GRAYSCALE)
                    if additional_image is not None:
                        # Convert to BGR for consistency
                        additional_bgr = cv2.cvtColor(additional_image, cv2.COLOR_GRAY2BGR)
                        
                        # Crop the additional page
                        add_height, add_width = additional_bgr.shape[:2]
                        add_crop_height = int(add_height * TOP_CROP_PERCENTAGE)
                        cropped_additional = additional_bgr[add_crop_height:, :]
                        
                        # Add to pages list
                        all_pages.append(Image.fromarray(cropped_additional))
                
                overlay_images[student_id] = all_pages
        
        # Save per-page results in page-specific folder
        page = directory.name
        page_dir = output_dir / f"page_{page}"
        page_dir.mkdir(parents=True, exist_ok=True)
        
        csv_path = page_dir / f"{page}_OMR.csv"
        results_df.to_csv(csv_path, index_label="student_id")
        # print(f"Saved per-page results to: {csv_path}")
        
        # Save overlay PDFs for this page (with all pages concatenated)
        for student_id, pages in overlay_images.items():
            pdf_path = page_dir / f"{student_id}_{page}.pdf"
            
            # Save as multi-page PDF
            if len(pages) > 1:
                pages[0].save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=pages[1:])
                # print(f"Saved multi-page overlay PDF: {pdf_path} ({len(pages)} pages)")
            else:
                pages[0].save(pdf_path, "PDF", resolution=100.0)
                # print(f"Saved overlay PDF: {pdf_path}")
    
    # Process subdirectories recursively
    for subdir in subdirs:
        process_directory(subdir, omr_marker, df_bubbles, output_dir, all_student_answers)


def process_single_image(image_path, omr_marker, df_bubbles, results_df, all_student_answers):
    """Process a single image and detect marked bubbles.
    
    This function performs the core OMR processing on a single exam page:
    1. Loads and preprocesses the image
    2. Aligns it using corner markers
    3. Detects bubble values using adaptive thresholding
    4. Distinguishes between multiple choice and numeric answers
    5. Creates an annotated overlay showing detected marks
    
    Args:
        image_path: Path to the image file to process
        omr_marker: Marker template for alignment (numpy array)
        df_bubbles: DataFrame with bubble positions for current page
        results_df: DataFrame to store per-page results (modified in-place)
        all_student_answers: Dictionary to store consolidated answers (modified in-place)
        
    Returns:
        numpy.ndarray: BGR overlay image with marked bubbles highlighted, or None if error
    """
    image_path = Path(image_path)
    # print(f"Processing: {image_path}")
    
    # Extract student ID from filename (format: studentID_pageNumber.jpeg)
    student_id = image_path.stem.split("_")[0]
    
    # Load and preprocess image
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return None
    
    # Get image DPI (default to 200 if not available)
    try:
        pil_image = Image.open(str(image_path))
        dpi = pil_image.info.get('dpi', (200, 200))
        if isinstance(dpi, (int, float)):
            dpi = (dpi, dpi)
    except:
        dpi = (200, 200)
    
    # Preprocess image
    image = cv2.GaussianBlur(image, (3, 3), 0)
    image = cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    
    # Align image using markers
    image = align_image_with_markers(image, omr_marker, dpi)
    
    # Get page number from directory name
    page_number = int(image_path.parent.name) if image_path.parent.name.isdigit() else 1
    
    # Filter bubbles for current page
    page_bubbles = df_bubbles[df_bubbles['page'] == page_number]
    
    if page_bubbles.empty:
        print(f"Warning: No bubbles defined for page {page_number}")
        return image
    
    # Detect bubble values first
    bubble_values, bubble_positions = detect_bubble_values(image, page_bubbles, dpi)
    
    # Calculate threshold (excluding decimal/slash positions)
    if bubble_values:
        # Filter out decimal/slash positions for threshold calculation
        values_for_threshold = []
        for key, value in bubble_values.items():
            if '_' in key:
                choice_part = key.split('_')[1]
                if '-' in choice_part and len(choice_part.split('-')) >= 3:
                    parts = choice_part.split('-')
                    if parts[2] not in ['D', 'S']:
                        values_for_threshold.append(value)
                else:
                    values_for_threshold.append(value)
            else:
                values_for_threshold.append(value)
        
        if values_for_threshold:
            threshold = calculate_threshold(values_for_threshold)
            # print(f"Threshold: {threshold:.2f}")
        else:
            threshold = GLOBAL_THRESHOLD
            # print(f"Using global threshold: {threshold}")
        
        # Create overlay with colored boxes based on marking status
        overlay = create_overlay_with_marks(image, bubble_values, bubble_positions, threshold)
        
        # Initialize student entry if not exists
        if student_id not in all_student_answers:
            all_student_answers[student_id] = {}
        
        # Separate numeric and regular bubbles
        numeric_bubbles = {}  # Store numeric bubble values by question and position
        regular_bubbles = {}  # Store regular multiple choice bubbles
        
        # Process bubbles for consolidated output and per-page results
        for key, value in bubble_values.items():
            # Check if this is a decimal/slash position
            is_decimal_slash = False
            if '_' in key:
                choice_part = key.split('_')[1]
                if '-' in choice_part and len(choice_part.split('-')) >= 3:
                    parts = choice_part.split('-')
                    if parts[2] in ['D', 'S']:
                        is_decimal_slash = True
            
            # Only store non-decimal/slash bubbles in per-page results
            if not is_decimal_slash:
                results_df.loc[student_id, key] = value
            
            # Check if marked for consolidated output
            is_marked = (value < threshold and value < GLOBAL_THRESHOLD)
            
            # Parse the key to determine bubble type
            parts = key.split('_')
            if len(parts) == 2:
                question_subquestion = parts[0]  # e.g., "1.i"
                choice = parts[1]  # e.g., "a" or "1-1-0"
                
                # Check if this is a numeric bubble
                if '-' in choice and len(choice.split('-')) >= 3:
                    # This is a numeric bubble (e.g., "1-1-0")
                    choice_parts = choice.split('-')
                    question_prefix = choice_parts[0]  # The question number prefix
                    position = int(choice_parts[1])
                    digit_value = choice_parts[2]  # Could be 0-9, D, or S
                    
                    # For decimal/slash, include them regardless of threshold
                    # For digits, check if marked
                    if digit_value in ['D', 'S'] or is_marked:
                        # Use the base question without the numeric prefix
                        base_question = question_subquestion
                        if base_question not in numeric_bubbles:
                            numeric_bubbles[base_question] = {}
                        # Only store if no digit is already selected for this position
                        if position not in numeric_bubbles[base_question]:
                            numeric_bubbles[base_question][position] = digit_value
                else:
                    # This is a regular multiple choice bubble
                    if is_marked:
                        if question_subquestion not in regular_bubbles:
                            regular_bubbles[question_subquestion] = []
                        regular_bubbles[question_subquestion].append(choice)
        
        # Convert numeric bubbles to final numeric answers
        for question, positions in numeric_bubbles.items():
            if positions:
                # First check if there are any actual digits (not just D or S)
                has_digits = any(digit not in ['D', 'S'] for digit in positions.values())
                
                if has_digits:
                    # Sort by position and concatenate
                    sorted_positions = sorted(positions.items())
                    numeric_answer = ""
                    for pos, digit in sorted_positions:
                        if digit == 'D':
                            numeric_answer += '.'
                        elif digit == 'S':
                            numeric_answer += '/'
                        else:
                            numeric_answer += digit
                    
                    # Store the numeric answer
                    if question not in all_student_answers[student_id]:
                        all_student_answers[student_id][question] = []
                    all_student_answers[student_id][question].append(numeric_answer)
        
        # Store regular multiple choice answers
        for question, choices in regular_bubbles.items():
            if question not in all_student_answers[student_id]:
                all_student_answers[student_id][question] = []
            
            # Check if this question has a numeric answer
            has_numeric_answer = question in all_student_answers[student_id] and all_student_answers[student_id][question]
            
            # Filter out "Other" choice if there's a numeric answer
            # The "Other" choice is the one associated with numeric bubbles in the CSV
            filtered_choices = []
            for choice in choices:
                # Check if this choice is associated with numeric bubbles by looking for
                # any numeric bubble entries in the CSV for this question/subquestion/choice combination
                is_other_choice = False
                question_num = question.split('.')[0]
                subquestion = question.split('.')[1]
                
                # Look for numeric bubbles associated with this choice
                for _, bubble in page_bubbles.iterrows():
                    if (str(bubble['question']).startswith(f"{question_num}-") and 
                        bubble['subquestion'] == subquestion and
                        bubble['choice'] == choice):
                        is_other_choice = True
                        break
                
                # Only include this choice if there's no numeric answer or it's not the "Other" choice
                if not has_numeric_answer or not is_other_choice:
                    filtered_choices.append(choice)
            
            all_student_answers[student_id][question].extend(filtered_choices)
        
        # Add threshold to per-page results
        results_df.loc[student_id, f'page{page_number}_threshold'] = threshold
        
        return overlay
    else:
        # No bubbles detected, create a basic overlay
        overlay = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        return overlay


def align_image_with_markers(image, marker_template, dpi):
    """Align image using corner markers for accurate bubble detection.
    
    This function performs perspective correction by:
    1. Detecting four corner markers in the scanned image
    2. Calculating the perspective transform to align them
    3. Applying the transform to correct for scanning distortions
    
    Args:
        image: Grayscale image to align (numpy array)
        marker_template: Template image of the corner marker
        dpi: Tuple of (horizontal_dpi, vertical_dpi) for the image
        
    Returns:
        numpy.ndarray: Aligned grayscale image, or original if alignment fails
        
    Note:
        The function searches for markers only in the corners to improve
        performance and reduce false positives. If any marker has confidence
        below THRESHOLD_CIRCLE, alignment is skipped.
    """
    # Resize marker template to match the expected size based on DPI
    marker_size = point_to_pixel(ANCHOR_RADIUS * 2, dpi[0])
    marker = cv2.resize(marker_template, (marker_size, marker_size))
    
    # Preprocess marker for better matching
    marker = cv2.GaussianBlur(marker, (3, 3), 0)
    marker = cv2.normalize(marker, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    
    h, w = image.shape
    
    # Define search regions for each corner - smaller regions near actual corners
    margin = w // 4  # Search within 1/4 of image dimensions from corners
    search_regions = [
        (0, 0, margin, margin),                      # Top-left
        (w - margin, 0, w, margin),                  # Top-right
        (0, h - margin, margin, h),                  # Bottom-left
        (w - margin, h - margin, w, h)               # Bottom-right
    ]
    
    # Find markers in each quadrant
    marker_centers = []
    for i, (x1, y1, x2, y2) in enumerate(search_regions):
        region = image[y1:y2, x1:x2]
        
        # Template matching
        result = cv2.matchTemplate(region, marker, cv2.TM_CCOEFF_NORMED)
        confidence = result.max()
        
        if confidence < THRESHOLD_CIRCLE:
            print(f"Warning: Marker {i+1} confidence too low ({confidence:.3f})")
            return image  # Return unaligned image
        
        # Find best match location
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        center_x = x1 + max_loc[0] + marker.shape[1] // 2
        center_y = y1 + max_loc[1] + marker.shape[0] // 2
        marker_centers.append([center_x, center_y])
        
        # print(f"Marker {i+1}: ({center_x}, {center_y}) with confidence {confidence:.3f}")
    
    # Convert to numpy array
    marker_centers = np.array(marker_centers, dtype=np.float32)
    
    # Define target positions for markers - where we want them to be
    offset = point_to_pixel(ANCHOR_DISTANCE, dpi[0])
    target_points = np.array([
        [offset, offset],                    # Top-left
        [w - offset, offset],                # Top-right
        [offset, h - offset],                # Bottom-left
        [w - offset, h - offset]            # Bottom-right
    ], dtype=np.float32)
    
    # No need to reorder - markers are already in correct order from search regions
    # Calculate and apply perspective transform
    transform_matrix = cv2.getPerspectiveTransform(marker_centers, target_points)
    aligned = cv2.warpPerspective(image, transform_matrix, (w, h))
    
    return aligned


def detect_bubble_values(image, bubbles_df, dpi):
    """Detect bubble intensity values and positions in the aligned image.
    
    This function extracts the mean grayscale intensity for each bubble region
    defined in the bubbles DataFrame. It handles both regular multiple choice
    bubbles and numeric answer bubbles (including decimal points and slashes).
    
    Args:
        image: Aligned grayscale image (numpy array)
        bubbles_df: DataFrame with bubble definitions including:
                   - Xpos, Ypos: Position in LaTeX points
                   - question, subquestion, choice: Bubble identifiers
        dpi: Tuple of (horizontal_dpi, vertical_dpi) for coordinate conversion
        
    Returns:
        tuple: (bubble_values, bubble_positions) where:
               - bubble_values: Dict mapping bubble keys to intensity values (0-255)
               - bubble_positions: Dict mapping bubble keys to (left, top, right, bottom)
               
    Note:
        Numeric bubbles are identified by question format (e.g., "1-1-0" for first
        digit of question 1). Decimal and slash positions get special handling.
    """
    bubble_values = {}
    bubble_positions = {}
    
    for _, bubble in bubbles_df.iterrows():
        x, y = bubble['Xpos'], bubble['Ypos']
        
        # Convert LaTeX points to pixels
        x_pixel = point_to_pixel(x, dpi[0])
        y_pixel = point_to_pixel(y, dpi[1])
        
        # Calculate bubble bounding box
        # Use inscribed square for more accurate reading
        offset = BUBBLE_RADIUS / math.sqrt(2)
        left = int(point_to_pixel(x - offset, dpi[0]))
        top = int(point_to_pixel(y - offset, dpi[1]))
        right = int(point_to_pixel(x + offset, dpi[0]))
        bottom = int(point_to_pixel(y + offset, dpi[1]))
        
        # Ensure coordinates are within image bounds
        left = max(0, left)
        top = max(0, top)
        right = min(image.shape[1], right)
        bottom = min(image.shape[0], bottom)
        
        # Create key for this bubble
        question = str(bubble['question'])
        subquestion = bubble['subquestion']
        choice = bubble['choice']
        
        # Check if this is a numeric bubble by looking at the question format
        if '-' in question and len(question.split('-')) >= 3:
            # This is a numeric bubble (e.g., "1-1-0")
            # Extract the base question number and use the full question as the choice
            base_question = question.split('-')[0]
            key = f"{base_question}.{subquestion}_{question}"
            
            # Check if this is a decimal point or slash (they don't have actual bubbles)
            parts = question.split('-')
            if len(parts) >= 3 and parts[2] in ['D', 'S']:
                # Store actual intensity value for decimal/slash positions
                # We'll handle them specially during processing
                bubble_values[key] = 100  # Special marker value
            else:
                # Extract bubble region and calculate mean intensity
                bubble_region = image[top:bottom, left:right]
                if bubble_region.size > 0:
                    mean_intensity = cv2.mean(bubble_region)[0]
                else:
                    mean_intensity = 255  # Default to unmarked if region is invalid
                bubble_values[key] = mean_intensity
        else:
            # This is a regular bubble
            key = f"{question}.{subquestion}_{choice}"
            # Extract bubble region and calculate mean intensity
            bubble_region = image[top:bottom, left:right]
            if bubble_region.size > 0:
                mean_intensity = cv2.mean(bubble_region)[0]
            else:
                mean_intensity = 255  # Default to unmarked if region is invalid
            bubble_values[key] = mean_intensity
        
        bubble_positions[key] = (left, top, right, bottom)
    
    return bubble_values, bubble_positions


def create_overlay_with_marks(image, bubble_values, bubble_positions, threshold):
    """Create overlay image with colored boxes based on marking status"""
    overlay = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    for key, value in bubble_values.items():
        left, top, right, bottom = bubble_positions[key]
        
        # Check if this is a decimal point or slash (from the key)
        is_decimal_or_slash = False
        if '_' in key:
            choice_part = key.split('_')[1]
            if '-' in choice_part and len(choice_part.split('-')) >= 3:
                digit_value = choice_part.split('-')[2]
                if digit_value in ['D', 'S']:
                    is_decimal_or_slash = True
        
        if is_decimal_or_slash:
            # Draw decimal points and slashes with a special indicator
            # These are always "selected" for numeric processing
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            # Draw a green circle for decimal/slash positions
            cv2.circle(overlay, (center_x, center_y), 5, (0, 255, 0), 2)  # Green circle outline
            cv2.circle(overlay, (center_x, center_y), 2, (0, 255, 0), -1)  # Green dot center
        else:
            # Determine if bubble is marked
            is_marked = (value < threshold and value < GLOBAL_THRESHOLD)
            
            # Choose color based on marking status
            color = MARKED_COLOR if is_marked else OVERLAY_COLOR
            
            # Draw rectangle
            cv2.rectangle(overlay, (left, top), (right, bottom), color, 2)
    
    return overlay


def calculate_threshold(values):
    """Calculate adaptive threshold for distinguishing marked from unmarked bubbles.
    
    This function uses an adaptive algorithm to find the optimal threshold for
    the current page, accounting for variations in scan quality, darkness, and
    marking style. It looks for the largest gap between consecutive intensity
    values to separate marked and unmarked bubbles.
    
    Args:
        values: List of bubble intensity values (0-255, lower = darker = marked)
        
    Returns:
        float: Threshold value. Bubbles with intensity below this are marked.
        
    Algorithm:
        1. Sort all intensity values
        2. Find the largest gap between consecutive values (> MIN_JUMP)
        3. Place threshold in the middle of this gap
        4. If no clear gap exists, use the mean intensity
        5. Cap at GLOBAL_THRESHOLD to prevent false positives
        
    Example:
        Values: [50, 55, 60, 180, 185, 190]  # Clear gap at 60-180
        Result: 120 (middle of gap)
    """
    if not values:
        return min(200, GLOBAL_THRESHOLD)  # Default threshold, capped by global threshold
    
    # Sort intensity values from darkest to lightest
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    # Find the largest gap in intensities
    max_gap = 0
    threshold = min(200, GLOBAL_THRESHOLD)
    
    # Look for significant jumps in intensity values
    for i in range(1, n):
        gap = sorted_values[i] - sorted_values[i-1]
        if gap > MIN_JUMP and gap > max_gap:
            max_gap = gap
            # Set threshold in the middle of the gap
            threshold = (sorted_values[i] + sorted_values[i-1]) / 2
    
    # If no significant gap found, use statistical approach
    if max_gap == 0:
        # Use mean as threshold (works when all bubbles are similar)
        threshold = np.mean(sorted_values)
    
    # Ensure threshold doesn't exceed global threshold
    threshold = min(threshold, GLOBAL_THRESHOLD)
    
    return threshold


def point_to_pixel(point_value, dpi):
    """Convert LaTeX points to pixels based on image DPI.
    
    Args:
        point_value: Value in LaTeX points
        dpi: Dots per inch of the image
        
    Returns:
        int: Equivalent value in pixels
        
    Note:
        1 LaTeX point = 1/72.27 inch (TeX's definition)
    """
    return int(point_value * dpi / 72.27)


def create_consolidated_output(all_student_answers, output_dir):
    """Create a consolidated CSV with all student answers.
    
    This function creates the final output CSV that combines all detected answers
    across all pages for all students. Multiple selections are joined with commas.
    
    Args:
        all_student_answers: Dict of dicts mapping student_id -> question -> list of answers
        output_dir: Path object for output directory
        
    Output format:
        student_id,1.i,1.ii,2.i,2.ii,...
        abc123,a,b,12.5,c,...
        def456,b,a,8,a,b,...
        
    Note:
        - Questions are sorted numerically then alphabetically by subquestion
        - Multiple answers for a question are comma-separated and sorted
        - Empty cells indicate no answer was detected
    """
    if not all_student_answers:
        print("No student answers to consolidate")
        return
    
    # Get all unique questions across all students
    all_questions = set()
    for student_answers in all_student_answers.values():
        all_questions.update(student_answers.keys())
    
    # Sort questions numerically
    sorted_questions = sorted(all_questions, key=lambda x: (int(x.split('.')[0]), x.split('.')[1]))
    
    # Create output DataFrame
    consolidated_df = pd.DataFrame(index=sorted(all_student_answers.keys()), columns=sorted_questions)
    consolidated_df.index.name = 'student_id'
    
    # Fill in the answers
    for student_id, answers in all_student_answers.items():
        for question, choices in answers.items():
            # Join multiple choices with comma
            consolidated_df.loc[student_id, question] = ','.join(sorted(choices))
    
    # Replace NaN with empty string
    consolidated_df = consolidated_df.fillna('')
    
    # Save consolidated output
    output_path = output_dir / "consolidated_answers.csv"
    consolidated_df.to_csv(output_path)
    print(f"\nSaved consolidated answers to: {output_path}")
    print(f"Total students processed: {len(consolidated_df)}")
    print(f"Total questions: {len(sorted_questions)}")
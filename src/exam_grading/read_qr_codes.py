"""Read QR codes from scanned images and organize them by page."""
import re
from pathlib import Path
import cv2
from qreader import QReader

from .common.validators import validate_directory
from .common.progress import ProgressPrinter


REPLACEMENT_PAGE_URL_PATTERN = re.compile(
    r'^https?://(www\.)?clrify\.it/replacement/'
    r'(?P<net_id>[^/]+)/'      # capture net_id (anything except a slash)
    r'(?P<page>[^/]+)/?'       # capture page (anything except a slash)
    r'$'
)


def read_qr_codes_and_move(exam_scans_folder_path: str) -> str:
    """
    Read QR codes from scanned exam images and organize them by page.
    
    Args:
        exam_scans_folder_path: Path to the folder containing scanned exam images
        
    Returns:
        Path to the output folder containing organized images
    """
    exam_scans_folder_path = Path(exam_scans_folder_path)
    validate_directory(exam_scans_folder_path, "Exam scans folder")
    
    output_folder_path = exam_scans_folder_path.parent / (exam_scans_folder_path.name + "_parsed")
    qreader = QReader()
    files = list(exam_scans_folder_path.glob("**/*.jpeg"))
    
    progress = ProgressPrinter("Reading QR Codes", len(files))
    
    for i, file in enumerate(files):
        progress.update(i + 1)
        
        img = cv2.imread(str(file), cv2.IMREAD_COLOR)
        # https://clrify.it/replacement/<net_id:str>/<page:int>
        decoded_texts = qreader.detect_and_decode(image=img)
        decoded_text = None
        for text in decoded_texts:
            if text is not None and isinstance(text, str) and text.startswith("https://clrify.it/replacement/"):
                decoded_text = text
                break
        
        if decoded_text is None:  # No QR code found
            net_id, page = file.stem, "noQRcode"
        else:
            m = REPLACEMENT_PAGE_URL_PATTERN.match(decoded_text)
            if m is None:
                print(f"Error: QR code '{decoded_text}' does not match expected format.")
                continue
            net_id, page = m.group("net_id"), m.group("page")
        
        filename = f"{net_id}_{page}"
        output_file_path = output_folder_path / page / f"{filename}.jpeg"
        
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        output_file_path.write_bytes(file.read_bytes())
    
    progress.done()
    return str(output_folder_path)
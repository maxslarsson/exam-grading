import re
import sys
import cv2
from pathlib import Path

from qreader import QReader


REPLACEMENT_PAGE_URL_PATTERN = re.compile(
    r'^https?://(www\.)?clrify\.it/replacement/'
    r'(?P<net_id>[^/]+)/'      # capture net_id (anything except a slash)
    r'(?P<page>[^/]+)/?'       # capture page (anything except a slash)
    r'$'
)


def main():
    # Get the arguments that were passed to the script
    _, script_args = sys.argv[0], sys.argv[1:]

    # If less than one argument were given to the script, we do not have the CSV files we need
    if len(script_args) < 1:
        print("Error: not enough arguments were given to the script")
        sys.exit(1)

    # We expect the first argument to be the path to the 2022_MGT403_scans/ folder
    exam_scans_folder_path = Path(script_args[0])

    if not exam_scans_folder_path.is_dir():
        print("Error: first argument is not a directory")
        sys.exit(1)

    output_folder_path = exam_scans_folder_path.parent / (exam_scans_folder_path.name + "_parsed")
    qreader = QReader()
    files = list(exam_scans_folder_path.glob("**/*.jpeg"))

    for i, file in enumerate(files):
        print(f"Reading QR Codes...{i+1}/{len(files)}", end='\r', flush=True)

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

        # if output_file_path.is_file():
        #     existing_files = list(output_file_path.parent.glob(f"{filename}*.jpeg"))
        #     output_file_path = output_file_path.parent / f"{filename}_{len(existing_files)}.jpeg"

        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        output_file_path.write_bytes(file.read_bytes())

    print(f"Reading QR Codes...Done!    ")


if __name__ == '__main__':
    main()

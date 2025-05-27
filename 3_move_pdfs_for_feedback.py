import sys
from pathlib import Path
from PIL import Image


# Question to pages mapping
SUBQUESTIONS = {
    "1.i": [1, 2],
    "1.ii": [1, 3],
    "1.iii": [1, 4],
    "1.iv": [1, 5],
    "1.v": [1, 6],
    "2.i": [7, 8],
    "2.ii": [7, 9, 10],
    "2.iii": [7, 9, 11],
    "2.iv": [7, 9, 12],
    "2.v": [7, 9, 13],
    "2.vi": [7, 9, 14],
    "3.i": [15, 16],
    "3.ii": [15, 17],
}


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

    net_ids = list(parsed_folder_path.glob("**/*.jpeg"))
    net_ids = set([i.name.split("_")[0] for i in net_ids])
    output_dir = parsed_folder_path.parent.parent / (parsed_folder_path.parent.name + "_student_work_PDFs")

    for i, net_id in enumerate(net_ids):
        print(f"Creating work PDFs...{i+1}/{len(net_ids)}", end="\r")
        for subquestion, pages in SUBQUESTIONS.items():
            imgs = []
            for page in pages:
                img_folder = parsed_folder_path / str(page) / str(page)
                img_paths = sorted(list(img_folder.glob(f"{net_id}_{page}*.jpeg")))
                for img_path in img_paths:
                    img = Image.open(img_path)
                    width, height = img.size
                    # img = img.crop((0, height // 12, width, height))
                    imgs.append(img)
            if len(imgs) > 0:
                pdf_path = output_dir / subquestion
                pdf_path.mkdir(parents=True, exist_ok=True)
                imgs[0].save(pdf_path / f"{net_id}_{subquestion}.pdf", "PDF", resolution=100.0, save_all=True, append_images=imgs[1:])

    print(f"Creating work PDFs...Done!     ")


if __name__ == '__main__':
    main()

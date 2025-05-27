import sys
from pathlib import Path
from PIL import Image
import pandas as pd


# Question to pages mapping
SUBQUESTIONS = {
    "1.i": [2],
    "1.ii": [3],
    "1.iii": [4],
    "1.iv": [5],
    "1.v": [6],
    "2.i": [8],
    "2.ii": [10],
    "2.iii": [11],
    "2.iv": [12],
    "2.v": [13],
    "2.vi": [14],
    "3.i": [16],
    "3.ii": [17],
}


def main():
    # Get the arguments that were passed to the script
    _, script_args = sys.argv[0], sys.argv[1:]

    # If less than two arguments were given to the script, we do not have the CSV files we need
    if len(script_args) < 2:
        print("Error: not enough arguments were given to the script")
        sys.exit(1)

    df_bubbles_path = Path(script_args[0])

    # We expect the second argument to be the path to the parsed folder that has one subfolder per page
    parsed_folder_path = Path(script_args[1])

    if not df_bubbles_path.is_file() or df_bubbles_path.suffix != ".csv":
        print("Error: first argument is not a CSV file")
        sys.exit(1)

    if not parsed_folder_path.is_dir():
        print("Error: second argument is not a directory")
        sys.exit(1)

    df_bubbles = pd.read_csv(df_bubbles_path, index_col="net_id")

    net_ids = list(parsed_folder_path.glob("**/*.jpeg"))
    net_ids = set([i.name.split("_")[0] for i in net_ids])
    output_dir = parsed_folder_path.parent.parent / (parsed_folder_path.parent.name + "_student_work_PDFs_by_answer")

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
                answer = df_bubbles.at[net_id, subquestion]
                pdf_path = output_dir / subquestion.replace(".", "_") / str(answer)
                pdf_path.mkdir(parents=True, exist_ok=True)
                imgs[0].save(pdf_path / f"{net_id}_{subquestion.replace('.', '_')}.pdf", "PDF", resolution=100.0, save_all=True, append_images=imgs[1:])

    print(f"Creating work PDFs...Done!     ")


if __name__ == '__main__':
    main()

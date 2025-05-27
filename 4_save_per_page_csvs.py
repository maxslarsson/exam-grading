import sys
import pandas as pd
from collections import defaultdict
from pathlib import Path

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

    dfs = defaultdict(pd.DataFrame)

    csvs = list(parsed_folder_path.glob("*/*_OMR.csv"))

    for csv in csvs:
        page, room = csv.stem.split("_")[:2]
        new_df = pd.read_csv(csv, index_col=0)
        dfs[page] = pd.concat([dfs[page], new_df])

    output_path = parsed_folder_path.parent / (parsed_folder_path.name + "_per_page_OMR_CSVs")
    for page, df in dfs.items():
        path = output_path / f"{page}_OMR.csv"
        path.parent.mkdir(exist_ok=True, parents=True)
        df.to_csv(path)


if __name__ == '__main__':
    main()


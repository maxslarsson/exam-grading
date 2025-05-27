import sys
import pandas as pd
from pathlib import Path

def main():
     # Get the arguments that were passed to the script
    _, script_args = sys.argv[0], sys.argv[1:]

    # If less than two arguments were given to the script, we do not have the CSV files we need
    if len(script_args) < 1:
        print("Error: not enough arguments were given to the script")
        sys.exit(1)

    # We expect the first argument to be the path to the parsed folder that has one subfolder per page
    per_page_csv_folder_path = Path(script_args[0])

    if not per_page_csv_folder_path.is_dir():
        print("Error: second argument is not a directory")
        sys.exit(1)

    df_concat = pd.DataFrame()

    csvs = list(per_page_csv_folder_path.glob("*_OMR.csv"))

    for csv in csvs:
        page, room = csv.stem.split("_")[:2]
        df_bubbles = pd.read_csv(csv, index_col=0)
        df_answers = process_page(df_bubbles, page)
        df_concat = pd.concat([df_concat, df_answers], axis=1)

    output_file_path = per_page_csv_folder_path.parent / (per_page_csv_folder_path.name + "_bubbles.csv")
    df_concat = df_concat.reindex(sorted(df_concat.columns), axis=1)
    df_concat.to_csv(output_file_path)


def process_page(df_bubbles: pd.DataFrame, page: str) -> pd.DataFrame:
    thresh_col_name = f"page{page}_threshold"
    thresh_col = df_bubbles[thresh_col_name]
    thresh_col = thresh_col.replace({255.0: 0.0})
    df_all_other_cols = df_bubbles.loc[:, df_bubbles.columns != thresh_col_name]
    df_selected = df_all_other_cols.le(thresh_col, axis=0)

    questions = ["_".join(c.split("_")[:-1]) for c in df_selected.columns]
    unique_questions = sorted(set(questions))

    df_return = pd.DataFrame("", index=df_selected.index, columns=unique_questions)
    for question in unique_questions:
        question_cols = [c for c in df_selected.columns if "_".join(c.split("_")[:-1]) == question]
        for col in question_cols:
            option = col.split("_")[-1]
            df_return.loc[df_selected[col], question] += option

    return df_return


if __name__ == '__main__':
    main()


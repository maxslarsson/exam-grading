"""Create grading spreadsheet in Google Sheets."""
from pathlib import Path
from typing import Any, Tuple, Union
import pandas as pd
from googleapiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow

from .common.validators import validate_csv_file
from .common.config import GOOGLE_SHEETS_SCOPES, GOOGLE_CLIENT_CONFIG


def create_grading_spreadsheet(csv_ps_path: str, csv_students_path: str, 
                             csv_individual_answers_path: str, csv_learning_team_answers_path: str) -> str:
    """
    Create a grading spreadsheet in Google Sheets.
    
    Args:
        csv_ps_path: Path to problem set info CSV
        csv_students_path: Path to students CSV
        csv_individual_answers_path: Path to individual answers CSV
        csv_learning_team_answers_path: Path to learning team answers CSV
        
    Returns:
        URL of the created spreadsheet
    """
    # Parse CSV paths
    csv_ps_path = Path(csv_ps_path)
    csv_students_path = Path(csv_students_path)
    csv_individual_answers_path = Path(csv_individual_answers_path)
    csv_learning_team_answers_path = Path(csv_learning_team_answers_path)
    
    # Validate paths
    validate_csv_file(csv_ps_path, "Problem set info CSV")
    validate_csv_file(csv_students_path, "Students CSV")
    validate_csv_file(csv_individual_answers_path, "Individual answers CSV")
    validate_csv_file(csv_learning_team_answers_path, "Learning team answers CSV")
    
    # Read CSV files
    df_ps = pd.read_csv(csv_ps_path)
    df_students = pd.read_csv(csv_students_path, index_col="net_id")
    df_individual_answers = pd.read_csv(csv_individual_answers_path, index_col="net_id")
    df_learning_team_answers = pd.read_csv(csv_learning_team_answers_path, index_col=["cohort", "learning_team"])
    
    df_learning_teams = df_students.loc[:, ["cohort", "learning_team"]]
    df_learning_teams = df_learning_teams.sort_values(by=["cohort", "learning_team"])
    df_learning_teams = df_learning_teams.drop_duplicates()
    
    df_individual_questions = list(df_individual_answers.columns)
    df_learning_team_questions = list(df_learning_team_answers.columns)
    
    if df_individual_questions != df_learning_team_questions:
        raise ValueError("Error: There are different questions in df_individual_answers and df_learning_team_answers")
    
    question_cols = []
    
    for question in df_individual_questions:
        for subcolumn in ["Answer", "Score", "Standard Error", "Ind. Feedback"]:
            question_cols.append((question, subcolumn))
    
    snake_case_cols_to_readable = {
        "cohort": "Cohort",
        "learning_team": "Learning Team",
        "last_name": "Last Name",
        "first_name": "First Name"
    }
    
    df_students.columns = pd.MultiIndex.from_tuples([("", c) for c in df_students.columns])
    df_learning_teams.columns = pd.MultiIndex.from_tuples([("", c) for c in df_learning_teams.columns])
    df_individual_answers.columns = pd.MultiIndex.from_tuples([(c, "Answer") for c in df_individual_answers.columns])
    df_learning_team_answers.columns = pd.MultiIndex.from_tuples([(c, "Answer") for c in df_learning_team_answers.columns])
    
    # Create the "Lookup" sheet
    df_lookup = pd.DataFrame(columns=["Question", "Answer", "Score", "Standard Error", "Ind. Feedback"])
    df_lookup["Question"] = df_individual_answers.columns.get_level_values(0)
    df_lookup["Answer"] = ""
    df_lookup["Score"] = 0
    
    # Create the "Individual Portion" sheet
    individual_prefix_cols = [("", c) for c in ["Cohort", "Learning Team", "Last Name", "First Name"]]
    individual_cols = pd.MultiIndex.from_tuples(individual_prefix_cols + question_cols)
    df_individual = pd.DataFrame(index=df_individual_answers.index, columns=individual_cols)
    df_individual.loc[:, individual_prefix_cols] = df_students.rename(columns=snake_case_cols_to_readable)
    df_individual.loc[:, (slice(None), "Answer")] = df_individual_answers
    
    for row_idx, net_id in enumerate(df_individual.index):
        for col_idx, col in enumerate(df_individual):
            if col[1] not in ["Score", "Standard Error", "Ind. Feedback"]:
                continue
            
            cur_col_letter = num_to_excel_letter(col_idx)
            
            if col[1] == "Score":  # Find default score for this question
                error_val = f'QUERY(Questions!A1:C100, "SELECT C WHERE A=\'" & {cur_col_letter}1 & "\'", 0)'
            else:
                error_val = '""'
            
            col_letter_of_answer = num_to_excel_letter(df_individual.columns.get_loc((col[0], "Answer")))
            answer_cell = col_letter_of_answer + str(row_idx + 1 + df_individual.columns.nlevels)
            col_to_get = num_to_excel_letter(df_lookup.columns.get_loc(col[1]))
            formula = f'=IFERROR(QUERY(Lookup!A2:E150, "SELECT {col_to_get} WHERE A=\'" & {cur_col_letter}1 & "\' AND B=\'" & {answer_cell} & "\'", 0), {error_val})'
            df_individual.at[net_id, col] = formula
    
    # Create the "Learning Team Portion" sheet
    learning_team_prefix_cols = [("", c) for c in ["Cohort", "Learning Team"]]
    learning_team_cols = pd.MultiIndex.from_tuples(learning_team_prefix_cols + question_cols)
    df_learning_team = pd.DataFrame(df_learning_teams.rename(columns={"cohort": "Cohort", "learning_team": "Learning Team"}), columns=learning_team_cols)
    df_learning_team = df_learning_team.set_index([("", "Cohort"), ("", "Learning Team")], drop=False)
    df_learning_team.loc[:, (slice(None), "Answer")] = df_learning_team_answers
    
    for row_idx, net_id in enumerate(df_learning_team.index):
        for col_idx, col in enumerate(df_learning_team):
            if col[1] not in ["Score", "Standard Error", "Ind. Feedback"]:
                continue
            
            cur_col_letter = num_to_excel_letter(col_idx)
            
            if col[1] == "Score":  # Find default score for this question
                error_val = f'QUERY(Questions!A2:C100, "SELECT C WHERE A=\'" & {cur_col_letter}1 & "\'", 0)'
            else:
                error_val = '""'
            
            col_letter_of_answer = num_to_excel_letter(df_learning_team.columns.get_loc((col[0], "Answer")))
            answer_cell = col_letter_of_answer + str(row_idx + 1 + df_learning_team.columns.nlevels)
            col_to_get = num_to_excel_letter(df_lookup.columns.get_loc(col[1]))
            formula = f'=IFERROR(QUERY(Lookup!A2:E150, "SELECT {col_to_get} WHERE A=\'" & {cur_col_letter}1 & "\' AND B=\'" & {answer_cell} & "\'", 0), {error_val})'
            df_learning_team.at[net_id, col] = formula
    
    # Create the "Questions" sheet
    df_questions = pd.DataFrame(columns=["Question", "Max Score", "Default Value"])
    df_questions["Question"] = df_individual_answers.columns.get_level_values(0)
    
    # Create the "Complete Feedback" sheet
    df_complete_feedback = df_individual.loc[:, individual_prefix_cols]
    df_complete_feedback.loc[:, ("", "Filename")] = df_complete_feedback.index
    df_complete_feedback = df_complete_feedback.applymap(lambda c: "{" + str(c) + "}")
    
    df_questions_levels = df_questions.columns.nlevels
    df_individual_levels = df_individual.columns.nlevels
    df_learning_team_levels = df_learning_team.columns.nlevels
    
    for question in df_individual_questions:
        for part in ["ind", "team"]:
            for subcolumn in ["Answer", "Score", "Max Score", "Standard Error", "Ind. Feedback"]:
                for net_id in df_complete_feedback.index:
                    if subcolumn == "Max Score":
                        col_in_questions = df_questions.columns.get_loc("Max Score")
                        row_in_questions = df_questions.index[df_questions["Question"] == question].tolist()[0]
                        formula = '="{" & ' + f"Questions!{num_to_excel_letter(col_in_questions)}{row_in_questions+1+df_questions_levels}" + ' & "}"'
                    elif part == "ind":
                        col_in_individual = df_individual.columns.get_loc((question, subcolumn))
                        row_in_individual = df_individual.index.get_loc(net_id)
                        formula = '="{" & ' + f"'Individual Portion'!{num_to_excel_letter(col_in_individual)}{row_in_individual + 1 + df_individual_levels}" + ' & "}"'
                    elif part == "team":
                        cohort, learning_team = df_students.loc[net_id, ("", ["cohort", "learning_team"])]
                        col_in_learning_team = df_learning_team.columns.get_loc((question, subcolumn))
                        row_in_learning_team = df_learning_team.index.get_loc((cohort, learning_team))
                        formula = '="{" & ' + f"'Learning Team Portion'!{num_to_excel_letter(col_in_learning_team)}{row_in_learning_team + 1 + df_learning_team_levels}" + ' & "}"'
                    
                    df_complete_feedback.at[net_id, (f"{question}_{part}", subcolumn)] = formula
    
    # Make all the NAs empty cells
    df_lookup = df_lookup.fillna("")
    df_individual = df_individual.fillna("")
    df_learning_team = df_learning_team.fillna("")
    df_questions = df_questions.fillna("")
    df_complete_feedback = df_complete_feedback.fillna("")
    
    df_complete_feedback = df_complete_feedback.add_prefix("{").add_suffix("}")
    
    lookup_sheet = df_to_sheet("Lookup", df_lookup)
    individual_portion_sheet = df_to_sheet("Individual Portion", df_individual)
    learning_team_portion_sheet = df_to_sheet("Learning Team Portion", df_learning_team)
    questions_sheet = df_to_sheet("Questions", df_questions)
    complete_feedback_sheet = df_to_sheet("Complete Feedback", df_complete_feedback)
    
    flow = InstalledAppFlow.from_client_config(GOOGLE_CLIENT_CONFIG, GOOGLE_SHEETS_SCOPES)
    creds = flow.run_local_server(port=0)
    
    service = discovery.build("sheets", "v4", credentials=creds)
    
    year = df_ps.at[0, "year"]
    course = df_ps.at[0, "course"]
    ps = df_ps.at[0, "problem_set"]
    
    spreadsheet_name = f"{year}_{course}_{ps}_grading"
    
    spreadsheet_body = {
        "properties": {"title": spreadsheet_name},
        "sheets": [
            lookup_sheet,
            individual_portion_sheet,
            learning_team_portion_sheet,
            questions_sheet,
            complete_feedback_sheet,
        ],
    }
    
    request = service.spreadsheets().create(body=spreadsheet_body)
    response = request.execute()
    
    if "spreadsheetUrl" not in response:
        raise RuntimeError("Error: something went wrong with creating the spreadsheet")
    
    print(f"URL for grading spreadsheet: {response['spreadsheetUrl']}")
    return response['spreadsheetUrl']


def df_to_sheet(sheet_name: str, df: pd.DataFrame) -> dict[str, Any]:
    spreadsheet = {
        "properties": {"title": sheet_name},
        "data": df_to_data(df),
        # "merges": df_cols_to_merge(df.columns),
    }
    return spreadsheet


def df_to_data(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    
    # Add the columns to the first row
    for level in range(df.columns.nlevels):
        row = [{"userEnteredValue": encode_value(c)} for c in df.columns.get_level_values(level)]
        rows.append(row)
    
    for _, row in df.iterrows():
        rows.append([{"userEnteredValue": encode_value(el)} for el in row])
    
    row_data = [{"values": row} for row in rows]
    grid_data = {"rowData": row_data}
    data = [grid_data]
    return data


def encode_value(value):
    if isinstance(value, int) or isinstance(value, float):
        return {"numberValue": value}
    elif isinstance(value, str):
        if value.startswith("="):
            return {"formulaValue": value}
        else:
            return {"stringValue": value}
    else:
        raise ValueError("Error: unsupported value to put in cell")


def num_to_excel_letter(num: int) -> str:
    start_index = 0  # it can start either at 0 or at 1
    letter = ""
    while num > 25 + start_index:
        letter += chr(65 + int((num - start_index) / 26) - 1)
        num = num - (int((num - start_index) / 26)) * 26
    letter += chr(65 - start_index + (int(num)))
    return letter
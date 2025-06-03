import pandas as pd
from typing import List

def clean_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]
    df.columns = [c.encode('ascii', 'ignore').decode().strip() for c in df.columns]
    return df


def split_duplicate_ids_by_invariant_columns(df: pd.DataFrame, invariant_columns: List[str]) -> pd.DataFrame:
    if invariant_columns is None:
        raise ValueError("You must provide a list of invariant_columns.")

    unique_ids_before: int = df['ID'].nunique()
    df['Original_ID'] = df['ID']

    def split_id(group: pd.DataFrame) -> pd.DataFrame:
        unique_combos = group[invariant_columns].drop_duplicates()

        if len(unique_combos) == 1:
            group['New_ID'] = group['Original_ID'].iloc[0]
        else:
            for idx, (_, subgroup) in enumerate(group.groupby(invariant_columns, dropna=False)):
                group.loc[subgroup.index, 'New_ID'] = f"{group['Original_ID'].iloc[0]}_{idx + 1}"
        return group

    df = df.groupby('Original_ID', group_keys=False).apply(split_id)
    df['ID'] = df['New_ID'].fillna(df['Original_ID'])

    df = df.drop(columns=['New_ID', 'Original_ID']).reset_index(drop=True)

    unique_ids_after: int = df['ID'].nunique()
    print(f"🔵 Unique IDs before cleaning: {unique_ids_before}")
    print(f"🟢 Unique IDs after cleaning: {unique_ids_after}")
    print(f"🧮 Difference: {unique_ids_after - unique_ids_before} new IDs created")

    return df


def remove_initial_stage_candidates(df: pd.DataFrame) -> pd.DataFrame:
    df['Candidate State'] = df['Candidate State'].str.strip().str.lower()

    ids_to_drop: List[str] = []
    for id_value, group in df.groupby('ID'):
        is_single_row = len(group) == 1
        is_initial_stage_only = group['Candidate State'].isin(['imported', 'first contact', 'in selection']).all()
        has_no_sector_info = group['Sector'].isna().all()

        if is_single_row and is_initial_stage_only and has_no_sector_info:
            ids_to_drop.append(id_value)

    df_cleaned = df[~df['ID'].isin(ids_to_drop)].reset_index(drop=True)
    print(f"🗂️ Removed {len(ids_to_drop)} initial-stage only candidates.")
    return df_cleaned

def sort_group(group: pd.DataFrame, state_order: List[str], event_order: List[str]) -> pd.DataFrame:
    sorted_group = group.sort_values(by=['Candidate State', 'event_type__val'], 
                                     key=lambda col: col.map(
                                         lambda x: (
                                             state_order.index(x) if x in state_order else -1, 
                                             event_order.index(x) if x in event_order else -1
                                         )
                                     )
                                    )
    return sorted_group

def remove_not_hired_valid_candidates(df: pd.DataFrame, state_order: List[str], event_order: List[str], feedbacks_to_remove: List[str]) -> pd.DataFrame:  
    df['Candidate State'] = df['Candidate State'].str.strip().str.lower()
    df['event_type__val'] = df['event_type__val'].str.strip().str.lower()
    df['event_feedback'] = df['event_feedback'].str.strip()

    df['Hired'] = df['Candidate State'].apply(
        lambda x: True if x == 'hired' else False
    )

    df = df.groupby('ID', group_keys=False).apply(sort_group, state_order=state_order, event_order=event_order)

    df = df.reset_index(drop=True)

    last_event = df.groupby('ID').tail(1)

    ids_to_remove_feedback = last_event[
        (last_event['event_feedback'].isin(feedbacks_to_remove)) & (last_event['Hired'] != True)
    ]['ID'].tolist()

    ids_to_remove_event = last_event[
        (last_event['event_type__val'].isin(['economic proposal', 'candidate notification'])) & 
        (last_event['Hired'] != True)
    ]['ID'].tolist()

    all_ids_to_remove = set(ids_to_remove_feedback + ids_to_remove_event)

    print(f"Number of unique IDs to remove: {len(all_ids_to_remove)}")

    total_ids_before = df['ID'].nunique()

    df = df[~df['ID'].isin(all_ids_to_remove)].reset_index(drop=True)

    total_ids_after = df['ID'].nunique()

    print(f"Total IDs before cleaning: {total_ids_before}")
    print(f"Total IDs after cleaning: {total_ids_after}")
    print(f"Total IDs removed: {total_ids_before - total_ids_after}")

    df = df.drop(columns=['state_order', 'event_order'], errors='ignore')

    return df

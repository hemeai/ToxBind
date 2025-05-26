"""
Analyzes and combines results from AlphaFold predictions.

This script merges the initial combined data with IPAE scores,
sorts the results, selects specific columns, and saves the final
dataset. It also generates a FASTA file containing all binder sequences
from the sorted results and copies the final CSV to the parent directory.
"""
import shutil
import pandas as pd

# Load data
try:
    combined_df = pd.read_csv('./combined_data.csv')
except FileNotFoundError:
    print("Error: './combined_data.csv' not found. Please run 'combine_outputs.py' first.")
    # Depending on the workflow, you might want to exit here:
    # import sys
    # sys.exit(1)
    combined_df = pd.DataFrame() # Create empty DataFrame to avoid later errors if script continues

try:
    results_ipae_df = pd.read_csv('./results_ipae.csv')
except FileNotFoundError:
    print("Error: './results_ipae.csv' not found. Please run 'get_ipae_score.py' first.")
    # Depending on the workflow, you might want to exit here:
    # import sys
    # sys.exit(1)
    results_ipae_df = pd.DataFrame() # Create empty DataFrame

# Merge dataframes
if not combined_df.empty and not results_ipae_df.empty:
    # Ensure 'Design' column exists in both dataframes before merging
    if 'Design' not in combined_df.columns or 'Design' not in results_ipae_df.columns:
        print("Error: 'Design' column missing in one of the input CSV files. Cannot merge.")
        # import sys
        # sys.exit(1)
        merged_df = pd.DataFrame() # Or handle as appropriate
    else:
        merged_df = pd.merge(combined_df, results_ipae_df, on='Design', how='left')
else:
    print("One or both input DataFrames are empty. Merging skipped.")
    merged_df = pd.DataFrame() # Ensure merged_df exists even if empty

# merged_df # This line has no effect, commented out

# Define columns for the final output
SPECIFIC_COLUMNS = [
    'Rank', 'Design', 'Length', 'ipae_score', 'Average_i_pTM',
    'Target_Hotspot', 'Sequence', 'TargetSequence', 'TargetSequenceLength',
    'Average_pAE', 'Average_i_pAE', 'Average_pTM', 'Average_pLDDT',
    'Average_i_pLDDT', 'Average_ss_pLDDT', 'Average_Target_RMSD',
    'Average_Hotspot_RMSD', 'Average_Binder_pLDDT', 'Average_Binder_pTM',
    'Average_Binder_pAE', 'Average_Binder_RMSD', 'DesignTime', 'Notes',
    'TargetSettings', 'Folder'
]

# Ensure all SPECIFIC_COLUMNS exist in merged_df, add them with NaN if not
# This prevents KeyErrors if a column is missing after the merge (e.g., if results_ipae_df was empty)
if not merged_df.empty:
    for col in SPECIFIC_COLUMNS:
        if col not in merged_df.columns:
            merged_df[col] = pd.NA # Or np.nan if using numpy

    # Sort and select columns
    # Only sort if 'ipae_score' column exists and is not all NaN
    if 'ipae_score' in merged_df.columns and not merged_df['ipae_score'].isnull().all():
        sorted_merged_df = merged_df.sort_values(by='ipae_score', ascending=True)
    else:
        print("Warning: 'ipae_score' column issues. Sorting by 'ipae_score' skipped.")
        sorted_merged_df = merged_df # Proceed without sorting by ipae_score

    # Filter for existing columns to avoid KeyError if some are missing
    existing_specific_columns = [col for col in SPECIFIC_COLUMNS if col in sorted_merged_df.columns]
    sorted_merged_df = sorted_merged_df[existing_specific_columns]
    # sorted_merged_df # This line has no effect, commented out
else:
    # Create an empty DataFrame with SPECIFIC_COLUMNS if merged_df is empty
    # This ensures final_results.csv is created with headers even if there's no data
    sorted_merged_df = pd.DataFrame(columns=SPECIFIC_COLUMNS)


# Save sorted and selected data
sorted_merged_df.to_csv("final_results.csv", index=False)

# Generate a combined FASTA file for binders
FASTA_FILE_NAME = "all_binder_fastas"
final_fasta_content_str = "" # Renamed variable
# Iterate over each row of the DataFrame
# Check if 'Design', 'Length', 'Sequence' columns exist before iterating
required_fasta_cols = ['Design', 'Length', 'Sequence']
if not sorted_merged_df.empty and all(col in sorted_merged_df.columns for col in required_fasta_cols):
    for _, row in sorted_merged_df.iterrows(): # index is not used
        design = row['Design']
        # binder_seq_len = row['Length'] # Unused variable
        sequence = row['Sequence']

        # Ensure sequence is a string before creating FASTA content
        if pd.isna(sequence):
            print(f"Warning: Sequence for Design {design} is missing. Skipping for FASTA.")
            continue

        current_fasta_content = f">{design}\n{sequence}\n\n"
        final_fasta_content_str += current_fasta_content
else:
    if sorted_merged_df.empty:
        print("DataFrame is empty. Cannot generate FASTA file.")
    else:
        cols_str = ", ".join(required_fasta_cols)
        print(f"Missing required columns for FASTA: {cols_str}")


# Write the FASTA file
FASTA_FILE_PATH = f"{FASTA_FILE_NAME}.fasta"
try:
    with open(FASTA_FILE_PATH, "w", encoding="utf-8") as fasta_file:
        fasta_file.write(final_fasta_content_str)
    print(f"FASTA file '{FASTA_FILE_PATH}' created successfully.")
except IOError as e:
    print(f"Error writing FASTA file '{FASTA_FILE_PATH}': {e}")


# Copy final_results.csv to the parent directory
try:
    shutil.copy('final_results.csv', '../final_results.csv')
    print("Copied 'final_results.csv' to parent directory.")
except FileNotFoundError:
    print("Error: 'final_results.csv' not found for copying.")
except (IOError, OSError) as e: # More specific exceptions for file operations
    print(f"Error copying 'final_results.csv': {type(e).__name__} - {e}")
except Exception as e: # Catch-all for other unexpected errors
    print(f"An unexpected error occurred during copy: {type(e).__name__} - {e}")
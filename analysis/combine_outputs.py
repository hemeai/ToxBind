"""
Combines design statistics with extracted protein sequences from PDB files.

This script reads CSV files containing design statistics from specified folders,
extracts protein sequences from PDB files located in 'Accepted' subfolders
within a given parent directory, and then merges this information based on
sequence identity into a single CSV file named 'combined_data.csv'.
"""
import os
import pandas as pd
from Bio.PDB import PDBParser, PPBuilder

def read_csv_from_folders(base_path_param):
    """
    Reads CSV files named 'final_design_stats.csv' from each subfolder
    of the base_path_param and combines them into a single DataFrame.
    """
    data_frames = []

    # Iterate through each folder in the base path
    for folder_name in os.listdir(base_path_param):
        folder_path = os.path.join(base_path_param, folder_name)

        # Check if it's a directory
        if os.path.isdir(folder_path):
            # Define the path to the CSV file
            csv_path = os.path.join(folder_path, 'final_design_stats.csv')

            # If the CSV file exists, read it
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    # Optionally, add a column for folder name
                    df['Folder'] = folder_name
                    data_frames.append(df)
                except pd.errors.EmptyDataError:
                    print(f"Warning: CSV file {csv_path} is empty and will be skipped.")
                except pd.errors.ParserError as e:
                    print(f"ParserError reading CSV file {csv_path}: {e}")
                except IOError as e:
                    print(f"IOError reading CSV file {csv_path}: {e}")
                except Exception as e:  # Catch other truly unexpected issues
                    print(f"An unexpected error occurred while reading {csv_path}: {e}")

    # Combine all the DataFrames into a single DataFrame (if any)
    if not data_frames:
        return None # Return None if no dataframes were loaded

    combined_df_local = pd.concat(data_frames, ignore_index=True)
    return combined_df_local

def extract_sequences_from_pdb(file_path, parser, ppb):
    """Helper function to extract sequences from a single PDB file."""
    file_sequences = {}
    try:
        structure = parser.get_structure("Protein", file_path)
        for model in structure:
            for chain in model:
                chain_id = chain.id
                peptides = ppb.build_peptides(chain)
                chain_sequences = [
                    str(peptide.get_sequence()) for peptide in peptides
                ]
                if chain_sequences:
                    file_sequences[chain_id] = chain_sequences
                else:
                    file_sequences[chain_id] = ["No sequence found"]
    except RuntimeError as e: # More specific exception for PDB parsing issues
        print(f"Error processing PDB file {file_path}: {e}")
    return file_sequences

def extract_sequences_from_accepted_folders(parent_folder_param):
    """
    Searches for PDB files directly in 'Accepted' folders within the given
    parent folder and extracts sequences.
    Ignores subdirectories inside 'Accepted' folders.

    Args:
        parent_folder_param (str): The path to the parent folder to search for PDB files.

    Returns:
        dict: A dictionary where keys are filenames and values are sequences by chain.
    """
    parser = PDBParser(QUIET=True)
    ppb = PPBuilder()
    sequences_dict = {}

    for root, _, files in os.walk(parent_folder_param): # Removed unused 'dirs'
        if os.path.basename(root) == "Accepted":
            for file in files:
                if file.endswith(".pdb"):
                    file_path = os.path.join(root, file)
                    print(f"Processing file: {file_path}")
                    file_sequences = extract_sequences_from_pdb(file_path, parser, ppb)
                    if file_sequences: # Only add if sequences were found
                        sequences_dict[file_path] = file_sequences
    return sequences_dict

def extract_sequences_to_dataframe(sequences_param):
    """
    Extracts File ID, Sequence 1 (Chain A), and Sequence 2 (Chain B)
    from the sequences dictionary into a DataFrame.

    Args:
        sequences_param (dict): Dictionary with file paths as keys
                                and chain sequences as values.

    Returns:
        pd.DataFrame: DataFrame containing DesignModel, TargetSequence, and Sequence.
    """
    data = []

    for file, chains in sequences_param.items():
        file_id = os.path.splitext(os.path.basename(file))[0]
        sequence1 = None
        sequence2 = None

        for chain_id, seq_list in chains.items():
            if chain_id == "A" and seq_list:
                sequence1 = seq_list[0]
            elif chain_id == "B" and seq_list:
                sequence2 = seq_list[0]

        data.append([file_id, sequence1, sequence2])

    df = pd.DataFrame(data, columns=["DesignModel", "TargetSequence", "Sequence"])
    return df

# Example usage
# Define base path for input CSVs
BASE_PATH = './../out/bindcraft/snake-venom-binder'
# Define parent folder for PDB files
PARENT_FOLDER = "./../out/bindcraft/snake-venom-binder"

# Process CSVs
final_design_stats_df = read_csv_from_folders(BASE_PATH)

if final_design_stats_df is not None:
    print("Successfully read design stats CSVs.")
    # final_design_stats_df.head() # For debugging, can be uncommented
    # print(f"Shape of final_design_stats_df: {final_design_stats_df.shape}") # For debugging

    # Process PDBs
    sequences_result = extract_sequences_from_accepted_folders(PARENT_FOLDER)
    accepted_df = extract_sequences_to_dataframe(sequences_result)
    # accepted_df.head() # For debugging, can be uncommented

    # Merge dataframes
    if not accepted_df.empty:
        combined_df_result = pd.merge(final_design_stats_df, accepted_df, on='Sequence', how='left')
        combined_df_result['TargetSequenceLength'] = combined_df_result['TargetSequence'].apply(
            lambda x: len(x) if pd.notnull(x) else 0
        )
        # combined_df_result.head() # For debugging, can be uncommented
        # combined_df_result.tail() # For debugging, can be uncommented

        # Save the combined DataFrame
        combined_df_result.to_csv('combined_data.csv', index=False)
        print("Combined data saved to combined_data.csv")
        # print(f"Shape of combined_df_result: {combined_df_result.shape}") # For debugging
    else:
        print("No sequences extracted, so no merge performed. Saving original design stats.")
        final_design_stats_df.to_csv('combined_data.csv', index=False)
        print("Original design stats saved to combined_data.csv")
else:
    print("No design statistics CSV files found or loaded. Exiting.")

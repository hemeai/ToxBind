# %%
import os
import pandas as pd

# Function to read CSV files from each folder and combine them into a single DataFrame
def read_csv_from_folders(base_path):
    data_frames = []
    
    # Iterate through each folder in the base path
    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        
        # Check if it's a directory
        if os.path.isdir(folder_path):
            # Define the path to the CSV file
            csv_path = os.path.join(folder_path, 'final_design_stats.csv')
            
            # If the CSV file exists, read it
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                # Optionally, add a column for folder name to track from which folder the data came
                df['Folder'] = folder_name
                data_frames.append(df)
    
    # Combine all the DataFrames into a single DataFrame (if any)
    if data_frames:
        combined_df = pd.concat(data_frames, ignore_index=True)
        return combined_df
    else:
        return None

# Example usage
base_path = './../out/bindcraft/snake-venom-binder'
final_design_stats_df = read_csv_from_folders(base_path)
final_design_stats_df.head()
final_design_stats_df.shape

# %%
import os
from Bio.PDB import PDBParser, PPBuilder

def extract_sequences_from_accepted_folders(parent_folder):
    """
    Searches for PDB files directly in 'Accepted' folders within the given parent folder and extracts sequences.
    Ignores subdirectories inside 'Accepted' folders.
    
    Args:
        parent_folder (str): The path to the parent folder to search for PDB files.
        
    Returns:
        dict: A dictionary where keys are filenames and values are sequences by chain.
    """
    # Initialize the PDB parser
    parser = PDBParser(QUIET=True)
    
    # Dictionary to store sequences by file
    sequences = {}
    
    # Walk through the parent folder and all its subdirectories
    for root, dirs, files in os.walk(parent_folder):
        # Check if the current directory is an 'Accepted' folder
        if os.path.basename(root) == "Accepted":
            for file in files:
                if file.endswith(".pdb"):  # Check if the file is a PDB file
                    file_path = os.path.join(root, file)
                    print(f"Processing file: {file_path}")
                    
                    try:
                        # Parse the PDB structure
                        structure = parser.get_structure("Protein", file_path)
                        
                        # Use the Polypeptide builder to extract sequences for each chain
                        ppb = PPBuilder()
                        file_sequences = {}
                        
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
                        
                        # Add the file's sequences to the result dictionary
                        sequences[file_path] = file_sequences
                    
                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
    
    return sequences


import pandas as pd
def extract_sequences_to_dataframe(sequences):
    """
    Extracts File ID, Sequence 1, and Sequence 2 from the sequences dictionary into a DataFrame.
    
    Args:
        sequences (dict): Dictionary with file paths as keys and chain sequences as values.
        
    Returns:
        pd.DataFrame: DataFrame containing File ID, Sequence 1, and Sequence 2.
    """
    # List to store results
    data = []
    
    for file, chains in sequences.items():
        # Extract the File ID from the file path
        file_id = os.path.splitext(os.path.basename(file))[0]
        
        # Initialize placeholders for Sequence 1 and Sequence 2
        sequence1 = None
        sequence2 = None
        
        # Iterate through chains to get sequences
        for chain, seq_list in chains.items():
            if chain == "A" and seq_list:  # Assume Sequence 1 corresponds to Chain A
                sequence1 = seq_list[0]  # Take the first sequence from Chain A
            elif chain == "B" and seq_list:  # Assume Sequence 2 corresponds to Chain B
                sequence2 = seq_list[0]  # Take the first sequence from Chain B
        
        # Append to the results
        data.append([file_id, sequence1, sequence2])
    
    # Create a DataFrame
    df = pd.DataFrame(data, columns=["DesignModel", "TargetSequence", "Sequence"])
    return df

# Example usage
parent_folder = "./../out/bindcraft/snake-venom-binder"  # Replace with your parent folder path
sequences = extract_sequences_from_accepted_folders(parent_folder)
accepted_df = extract_sequences_to_dataframe(sequences)
accepted_df.head()

# %%
final_design_stats_df.head()

# %%
combined_df = pd.merge(final_design_stats_df, accepted_df, on='Sequence')
combined_df['TargetSequenceLength'] = combined_df['TargetSequence'].apply(len)
combined_df.head()

# %%
combined_df.tail()

# %%
combined_df.to_csv('combined_data.csv', index=False)

# %%
combined_df.shape

# %%


# %%




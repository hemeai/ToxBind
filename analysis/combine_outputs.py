import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
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
    return final_design_stats_df, os, pd


@app.cell
def _(os, pd):
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
        parser = PDBParser(QUIET=True)
        sequences = {}  # Initialize the PDB parser
        for root, dirs, files in os.walk(parent_folder):
            if os.path.basename(root) == 'Accepted':
                for file in files:  # Dictionary to store sequences by file
                    if file.endswith('.pdb'):
                        file_path = os.path.join(root, file)
                        print(f'Processing file: {file_path}')  # Walk through the parent folder and all its subdirectories
                        try:
                            structure = parser.get_structure('Protein', file_path)  # Check if the current directory is an 'Accepted' folder
                            ppb = PPBuilder()
                            file_sequences = {}
                            for model in structure:  # Check if the file is a PDB file
                                for chain in model:
                                    chain_id = chain.id
                                    peptides = ppb.build_peptides(chain)
                                    chain_sequences = [str(peptide.get_sequence()) for peptide in peptides]
                                    if chain_sequences:  # Parse the PDB structure
                                        file_sequences[chain_id] = chain_sequences
                                    else:
                                        file_sequences[chain_id] = ['No sequence found']  # Use the Polypeptide builder to extract sequences for each chain
                            sequences[file_path] = file_sequences
                        except Exception as e:
                            print(f'Error processing file {file_path}: {e}')
        return sequences

    def extract_sequences_to_dataframe(sequences):
        """
        Extracts File ID, Sequence 1, and Sequence 2 from the sequences dictionary into a DataFrame.
    
        Args:
            sequences (dict): Dictionary with file paths as keys and chain sequences as values.
        
        Returns:
            pd.DataFrame: DataFrame containing File ID, Sequence 1, and Sequence 2.
        """
        data = []  # Add the file's sequences to the result dictionary
        for file, chains in sequences.items():
            file_id = os.path.splitext(os.path.basename(file))[0]
            sequence1 = None
            sequence2 = None
            for chain, seq_list in chains.items():
                if chain == 'A' and seq_list:
                    sequence1 = seq_list[0]
                elif chain == 'B' and seq_list:
                    sequence2 = seq_list[0]
            data.append([file_id, sequence1, sequence2])
        df = pd.DataFrame(data, columns=['DesignModel', 'TargetSequence', 'Sequence'])
        return df
    parent_folder = './../out/bindcraft/snake-venom-binder'
    sequences = extract_sequences_from_accepted_folders(parent_folder)
    accepted_df = extract_sequences_to_dataframe(sequences)
    # Example usage
    accepted_df.head()  # List to store results  # Extract the File ID from the file path  # Initialize placeholders for Sequence 1 and Sequence 2  # Iterate through chains to get sequences  # Assume Sequence 1 corresponds to Chain A  # Take the first sequence from Chain A  # Assume Sequence 2 corresponds to Chain B  # Take the first sequence from Chain B  # Append to the results  # Create a DataFrame  # Replace with your parent folder path
    return (accepted_df,)


@app.cell
def _(final_design_stats_df):
    final_design_stats_df.head()
    return


@app.cell
def _(accepted_df, final_design_stats_df, pd):
    combined_df = pd.merge(final_design_stats_df, accepted_df, on='Sequence')
    combined_df['TargetSequenceLength'] = combined_df['TargetSequence'].apply(len)
    combined_df.head()
    return (combined_df,)


@app.cell
def _(combined_df):
    combined_df.tail()
    return


@app.cell
def _(combined_df):
    combined_df.to_csv('combined_data.csv', index=False)
    return


@app.cell
def _(combined_df):
    combined_df.shape
    return


if __name__ == "__main__":
    app.run()


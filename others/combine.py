import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
    import os
    import pandas as pd

    # Function to get paths of PDB files from the 'Accepted' folder
    def get_pdb_paths_from_accepted(base_path):
        pdb_paths = []
    
        # Iterate through each folder in the base path
        for folder_name in os.listdir(base_path):
            folder_path = os.path.join(base_path, folder_name)
        
            # Check if it's a directory
            if os.path.isdir(folder_path):
                # Define the path to the 'Accepted' folder
                accepted_folder_path = os.path.join(folder_path, 'Accepted')
            
                # Check if the 'Accepted' folder exists
                if os.path.exists(accepted_folder_path):
                    # Iterate through files in the 'Accepted' folder
                    for file_name in os.listdir(accepted_folder_path):
                        if file_name.endswith('.pdb'):
                            pdb_paths.append(os.path.join(accepted_folder_path, file_name))
    
        return pdb_paths

    # Example usage
    base_path = './../out/bindcraft/snake-venom-binder'
    pdb_file_paths = get_pdb_paths_from_accepted(base_path)
    print(pdb_file_paths)

    # Example usage
    # base_path = './../out/bindcraft/'
    # final_design_stats_df = read_csv_from_folders(base_path)
    # final_design_stats_df.head()
    # final_design_stats_df.shape
    return (pdb_file_paths,)


@app.cell
def _(pdb_file_paths):
    import subprocess
    for input_pdb in pdb_file_paths: 
        command = f'modal run modal_pdb2png.py --input-pdb {input_pdb} --render-style flat --protein-rotate 0,45,0 --run-name cover'
        subprocess.run(command, shell=True)
    return


if __name__ == "__main__":
    app.run()


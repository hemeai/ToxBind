"""
This script processes a CSV file ('combined_data.csv'), generates FASTA files
for each entry, runs AlphaFold (via Modal) if results don't already exist,
and then extracts the Interface Predicted Aligned Error (ipae) score from
the AlphaFold results. Finally, it saves these scores into 'results_ipae.csv'.
"""
import os
import glob
import subprocess
import sys # For sys.exit
import pandas as pd

# Ensure the script is run from the 'analysis' directory or adjust paths accordingly
# Assuming 'combined_data.csv' and 'modal_alphafold.py' are in the same directory
# or paths are adjusted.

try:
    combined_df = pd.read_csv("./combined_data.csv")
except FileNotFoundError:
    print("Error: 'combined_data.csv' not found. Make sure it's in the correct directory.")
    sys.exit(1) # Exit if the crucial input file is missing


def check_existing_result(fasta_file_name_param):
    """
    Checks if an AlphaFold result file already exists for the given FASTA file name.

    Args:
        fasta_file_name_param (str): The base name of the FASTA file (without .fasta).

    Returns:
        bool: True if a result file exists, False otherwise.
    """
    # Adjusted glob pattern to be more specific if results are in a subdir of fasta_file_name
    pattern = f"./alphafold_results/**/{fasta_file_name_param}.result.zip"
    existing_files = glob.glob(pattern, recursive=True)
    return bool(existing_files)

# Define a directory for FASTA files
FASTA_OUTPUT_DIR = "./fasta_files_for_alphafold"
os.makedirs(FASTA_OUTPUT_DIR, exist_ok=True)

# Initialize a dictionary to store the results
results = {}
# Iterate over each row of the DataFrame
for _, row in combined_df.iterrows(): # index is not used
    fasta_file_name = row["Design"]
    binder_sequence = row["Sequence"]
    target_seq = row["TargetSequence"]
    print(f"Processing: {fasta_file_name}")

    # Create the FASTA file content
    COMBINED_SEQ_STR = f"{target_seq}:{binder_sequence}" # Renamed variable
    FASTA_CONTENT_STR = f">{fasta_file_name}\n{COMBINED_SEQ_STR}\n" # Renamed variable

    # Write the FASTA file
    fasta_file_path = os.path.join(FASTA_OUTPUT_DIR, f"{fasta_file_name}.fasta")
    try:
        with open(fasta_file_path, "w", encoding='utf-8') as fasta_file:
            fasta_file.write(FASTA_CONTENT_STR)
    except IOError as e:
        print(f"Error writing FASTA file {fasta_file_path}: {e}")
        continue # Skip to the next design

    # Before running command, check if result exists
    if check_existing_result(fasta_file_name):
        print(f"Result for {fasta_file_name} already exists, skipping computation.")
    else:
        # Ensure paths are correctly specified for modal run
        MODAL_SCRIPT_PATH_LOCAL = "./modal_alphafold.py" # Renamed variable
        ALPHAFOLD_RESULTS_DIR_LOCAL = "./alphafold_results" # Renamed variable
        # Breaking down the command string for readability
        COMMAND_RUN_ALPHAFOLD_STR = (
            f'GPU="H100" modal run {MODAL_SCRIPT_PATH_LOCAL} '
            f'--input-fasta "{fasta_file_path}" --out-dir "{ALPHAFOLD_RESULTS_DIR_LOCAL}"'
        )
        try:
            subprocess.run(COMMAND_RUN_ALPHAFOLD_STR, shell=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running AlphaFold for {fasta_file_name}: {e}")
            continue # Skip to the next design if AlphaFold fails
        except FileNotFoundError:
            print("Error: 'modal' command not found. Is Modal installed and in PATH?")
            continue

    # Capture the ipae score from the result
    result_zip_files = glob.glob(
        f"./alphafold_results/**/{fasta_file_name}.result.zip", recursive=True
    )
    if not result_zip_files:
        print(f"No result zip file found for {fasta_file_name}. "
              "Skipping IPAE extraction.")
        results[fasta_file_name] = None
        continue
    result_zip = result_zip_files[0]

    # Command to unzip and filter JSON using jq
    COMMAND_EXTRACT_IPAE_STR = ( # Renamed variable
        f'unzip -p "{result_zip}" "*.json" | '
        f'jq -r \'select(.ipae != null) | .ipae."0"\''
    )

    IPAE_SCORE_VAL = None # Renamed variable
    try:
        process_result = subprocess.run(
            COMMAND_EXTRACT_IPAE_STR,
            shell=True, # shell=True is needed here because of the pipe |
            text=True,
            capture_output=True,
            check=False
        )
        if process_result.returncode == 0:
            output = process_result.stdout.strip()
            if output:
                try:
                    IPAE_SCORE_VAL = float(output)
                    print(f"Extracted IPAE score for {fasta_file_name}: {IPAE_SCORE_VAL}")
                except ValueError:
                    print(f"Could not convert IPAE score to float for "
                          f"{fasta_file_name}: '{output}'")
            else:
                print(f"No IPAE score found in JSON for {fasta_file_name} "
                      "(jq output was empty).")
        elif process_result.returncode == 4:
            print(f"No IPAE score found (jq code 4) for {fasta_file_name}.")
        else:
            print(f"Error extracting IPAE for {fasta_file_name} "
                  f"(return code {process_result.returncode}): "
                  f"{process_result.stderr.strip()}")

    except subprocess.CalledProcessError as e:
        print(f"Subprocess error during IPAE extraction for {fasta_file_name}: {e}")
    except FileNotFoundError:
        print("Error: 'unzip' or 'jq' command not found. "
              "Please ensure they are installed and in PATH.")
    except Exception as e: # Catch any other unexpected error during this block
        print(f"An unexpected error occurred during IPAE extraction for "
              f"{fasta_file_name}: {type(e).__name__} - {e}")

    results[fasta_file_name] = IPAE_SCORE_VAL

print("Final IPAE results:", results)
results_df = pd.DataFrame(list(results.items()), columns=["Design", "ipae_score"])
results_df.to_csv("results_ipae.csv", index=False)
print(results_df)

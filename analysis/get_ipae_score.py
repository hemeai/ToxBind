import pandas as pd
import subprocess
import re
import glob

combined_df = pd.read_csv("./combined_data.csv")

# Initialize a dictionary to store the results
results = {}
target_seq = "LKCNKLVPIAYKTCPEGKNLCYKMFMMSDLTIPVKRGCIDVCPKNSLLVKYVCCNTDRCN"

# Iterate over each row of the DataFrame
for index, row in combined_df.iterrows():
    fasta_file_name = row["Design"]
    binder_seq_len = row["Length"]
    binder_sequence = row["Sequence"]
    print("fasta file name: ", fasta_file_name)
    print("binder sequence: ", binder_sequence)
    print("binder sequence length: ", binder_seq_len)

    # Create the FASTA file content
    # Add a colon at the end of the sequence
    comined_seq = target_seq + ":" + binder_sequence

    # Create the FASTA file content
    fasta_content = f">{fasta_file_name}\n{comined_seq}\n"

    # Write the FASTA file
    fasta_file_path = f"{fasta_file_name}.fasta"
    with open(fasta_file_path, "w") as fasta_file:
        fasta_file.write(fasta_content)

    # Run the shell script with the appropriate parameters
    command = f'GPU="H100" modal run modal_alphafold.py --input-fasta {fasta_file_path} --out-dir ./alphafold_results'
    subprocess.run(command, shell=True)

    # Capture the ipae score from the result
    result_zip = glob.glob(f"./alphafold_results/**/{fasta_file_name}.result.zip", recursive=True)[0]
    # Command to unzip and filter JSON using jq
    command = f'unzip -p "{result_zip}" "*.json" | jq -r \'select(.ipae != null) | .ipae."0"\''
    ipae_score = None
    try:
        # Run the subprocess and capture the output
        result = subprocess.run(
            command,
            shell=True,          # Enables use of the full pipeline
            text=True,           # Outputs results as text, not bytes
            capture_output=True  # Captures stdout and stderr
        )
        # Check for errors
        if result.returncode == 0:
            # Print or process the output
            output = result.stdout.strip()
            if output:  # Ensure there is valid output
                print(f"Extracted value: {output}")
                ipae_score = float(output)
            else:
                print("No valid value found.")
        else:
            print(f"Error: {result.stderr}")

    except Exception as e:
        print(f"An error occurred: {e}")

    # Store the result in the dictionary
    if ipae_score is not None:
        results[fasta_file_name] = ipae_score

print(results)
# Convert the dictionary to a DataFrame
results_df = pd.DataFrame(list(results.items()), columns=["Design", "ipae_score"])

# Save the DataFrame to a CSV file
results_df.to_csv("results_ipae.csv", index=False)

# Print the DataFrame
print(results_df)

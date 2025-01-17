import pandas as pd
import subprocess
import re

combined_df = pd.read_csv("./combined_data.csv")

# Initialize a dictionary to store the results
results = {}
target_seq = "LKCNKLVPIAYKTCPEGKNLCYKMFMMSDLTIPVKRGCIDVCPKNSLLVKYVCCNTDRCN"

# Iterate over each row of the DataFrame
for index, row in combined_df.iterrows():
    fasta_file_name = row["Design"]
    binder_seq_len = row["Length"]
    sequence = row["Sequence"]
    print("fasta file name: ", fasta_file_name)
    print("sequence: ", sequence)
    print("sequence length: ", binder_seq_len)

    # Create the FASTA file content
    # Add a colon at the end of the sequence
    comined_seq = sequence + ":" + target_seq

    # Create the FASTA file content
    fasta_content = f">{fasta_file_name}\n{comined_seq}\n"

    # Write the FASTA file
    fasta_file_path = f"{fasta_file_name}.fasta"
    with open(fasta_file_path, "w") as fasta_file:
        fasta_file.write(fasta_content)

    # Run the shell script with the appropriate parameters
    # command = f'GPU="H100" modal run modal_alphafold.py --input-fasta {fasta_file_path}'
    # subprocess.run(command, shell=True)

    # Capture the ipae score from the result
    result_zip = f"./alphafold_results/**/{fasta_file_name}.result.zip"
    result = subprocess.run(
        ["zipgrep", "ipae", result_zip], capture_output=True, text=True
    )
    ipae_score = None
    if result.stdout:
        match = re.search(r'"ipae":\s*([\d.]+)', result.stdout)
        if match:
            ipae_score = float(match.group(1))

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

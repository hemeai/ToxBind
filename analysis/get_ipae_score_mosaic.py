"""
This script processes Mosaic output files ('designs.txt'), generates FASTA files
for each entry, runs AlphaFold (via Modal) if results don't already exist,
and then extracts the Interface Predicted Aligned Error (ipae) score from
the AlphaFold results. Finally, it saves these scores into 'results_ipae_mosaic.csv'.

Key differences from BindCraft pipeline:
- Mosaic outputs designs.txt in FASTA format with only binder sequences
- Target sequence needs to be added (from modal_mosaic.py)
- Design names include loss values: >design{idx}_{loss_value}
"""
import os
import glob
import subprocess
import sys
import pandas as pd
import argparse
from pathlib import Path

# Target sequence from modal_mosaic.py (line 34)
DEFAULT_TARGET_SEQUENCE = "MICYNQQSSQPPTTKTCSETSCYKKTWRDHRGTIIERGCGCPKVKPGIKLHCCRTDKCNN"


def parse_designs_txt(designs_file_path, target_sequence):
    """
    Parses a designs.txt file from Mosaic output.

    Args:
        designs_file_path (str): Path to the designs.txt file
        target_sequence (str): The target protein sequence

    Returns:
        pd.DataFrame: DataFrame with columns: Design, Sequence, TargetSequence, LossValue
    """
    designs = []

    with open(designs_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Parse FASTA format
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('>'):
            # Parse header: >design{idx}_{loss_value}
            header = line[1:]  # Remove '>'

            # Extract loss value if present
            if '_' in header:
                design_name, loss_value = header.rsplit('_', 1)
                try:
                    loss_value = float(loss_value)
                except ValueError:
                    # If parsing fails, use the whole header as name
                    design_name = header
                    loss_value = None
            else:
                design_name = header
                loss_value = None

            # Get sequence from next line
            i += 1
            if i < len(lines):
                sequence = lines[i].strip()
                designs.append({
                    'Design': design_name,
                    'Sequence': sequence,
                    'TargetSequence': target_sequence,
                    'LossValue': loss_value
                })
        i += 1

    return pd.DataFrame(designs)


def check_existing_result(fasta_file_name_param, alphafold_results_dir):
    """
    Checks if an AlphaFold result file already exists for the given FASTA file name.

    Args:
        fasta_file_name_param (str): The base name of the FASTA file (without .fasta).
        alphafold_results_dir (str): Directory where AlphaFold results are stored.

    Returns:
        bool: True if a result file exists, False otherwise.
    """
    pattern = f"{alphafold_results_dir}/**/{fasta_file_name_param}.result.zip"
    existing_files = glob.glob(pattern, recursive=True)
    return bool(existing_files)


def extract_ipae_score(result_zip, fasta_file_name):
    """
    Extracts iPAE score from AlphaFold result ZIP file.

    Args:
        result_zip (str): Path to the result ZIP file
        fasta_file_name (str): Name of the design for logging

    Returns:
        float or None: iPAE score if found, None otherwise
    """
    command_extract_ipae = (
        f'unzip -p "{result_zip}" "*.json" | '
        f'jq -r \'select(.ipae != null) | .ipae."0"\''
    )

    ipae_score = None
    try:
        process_result = subprocess.run(
            command_extract_ipae,
            shell=True,
            text=True,
            capture_output=True,
            check=False
        )
        if process_result.returncode == 0:
            output = process_result.stdout.strip()
            if output:
                try:
                    ipae_score = float(output)
                    print(f"Extracted iPAE score for {fasta_file_name}: {ipae_score}")
                except ValueError:
                    print(f"Could not convert iPAE score to float for "
                          f"{fasta_file_name}: '{output}'")
            else:
                print(f"No iPAE score found in JSON for {fasta_file_name} "
                      "(jq output was empty).")
        elif process_result.returncode == 4:
            print(f"No iPAE score found (jq code 4) for {fasta_file_name}.")
        else:
            print(f"Error extracting iPAE for {fasta_file_name} "
                  f"(return code {process_result.returncode}): "
                  f"{process_result.stderr.strip()}")
    except Exception as e:
        print(f"An unexpected error occurred during iPAE extraction for "
              f"{fasta_file_name}: {type(e).__name__} - {e}")

    return ipae_score


def main():
    parser = argparse.ArgumentParser(
        description='Process Mosaic designs.txt and calculate iPAE scores using AlphaFold'
    )
    parser.add_argument(
        '--input-designs',
        type=str,
        default='../out/mosaic/latest/designs.txt',
        help='Path to designs.txt file from Mosaic (default: ../out/mosaic/latest/designs.txt)'
    )
    parser.add_argument(
        '--target-sequence',
        type=str,
        default=DEFAULT_TARGET_SEQUENCE,
        help='Target protein sequence (default: sequence from modal_mosaic.py)'
    )
    parser.add_argument(
        '--output-csv',
        type=str,
        default='./results_ipae_mosaic.csv',
        help='Output CSV file path (default: ./results_ipae_mosaic.csv)'
    )
    parser.add_argument(
        '--fasta-dir',
        type=str,
        default='./fasta_files_mosaic',
        help='Directory for FASTA files (default: ./fasta_files_mosaic)'
    )
    parser.add_argument(
        '--alphafold-results-dir',
        type=str,
        default='./alphafold_results',
        help='Directory for AlphaFold results (default: ./alphafold_results)'
    )
    parser.add_argument(
        '--modal-script',
        type=str,
        default='./modal_alphafold.py',
        help='Path to modal_alphafold.py script (default: ./modal_alphafold.py)'
    )
    parser.add_argument(
        '--gpu',
        type=str,
        default='H100',
        help='GPU type for Modal (default: H100)'
    )
    parser.add_argument(
        '--skip-alphafold',
        action='store_true',
        help='Skip running AlphaFold and only extract scores from existing results'
    )

    args = parser.parse_args()

    # Check if designs.txt exists
    if not os.path.exists(args.input_designs):
        print(f"Error: designs.txt not found at '{args.input_designs}'")
        print("\nTo find your designs.txt file, look in: ../out/mosaic/")
        print("Folders are organized by date (YYMMDD format)")
        sys.exit(1)

    print(f"Reading designs from: {args.input_designs}")

    # Parse designs.txt
    designs_df = parse_designs_txt(args.input_designs, args.target_sequence)
    print(f"Found {len(designs_df)} designs")
    print(f"\nFirst few designs:")
    print(designs_df.head())

    # Create FASTA output directory
    os.makedirs(args.fasta_dir, exist_ok=True)

    # Initialize results dictionary
    results = {}

    # Process each design
    for _, row in designs_df.iterrows():
        design_name = row["Design"]
        binder_sequence = row["Sequence"]
        target_seq = row["TargetSequence"]
        loss_value = row.get("LossValue", None)

        print(f"\nProcessing: {design_name} (loss: {loss_value})")

        # Create FASTA file content (format required by AlphaFold)
        combined_seq = f"{target_seq}:{binder_sequence}"
        fasta_content = f">{design_name}\n{combined_seq}\n"

        # Write FASTA file
        fasta_file_path = os.path.join(args.fasta_dir, f"{design_name}.fasta")
        try:
            with open(fasta_file_path, "w", encoding='utf-8') as fasta_file:
                fasta_file.write(fasta_content)
        except IOError as e:
            print(f"Error writing FASTA file {fasta_file_path}: {e}")
            continue

        # Check if result already exists
        if check_existing_result(design_name, args.alphafold_results_dir):
            print(f"Result for {design_name} already exists, skipping AlphaFold run.")
        elif not args.skip_alphafold:
            # Run AlphaFold via Modal
            command_run_alphafold = (
                f'GPU="{args.gpu}" modal run {args.modal_script} '
                f'--input-fasta "{fasta_file_path}" --out-dir "{args.alphafold_results_dir}"'
            )
            try:
                print(f"Running AlphaFold for {design_name}...")
                subprocess.run(command_run_alphafold, shell=True, check=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running AlphaFold for {design_name}: {e}")
                continue
            except FileNotFoundError:
                print("Error: 'modal' command not found. Is Modal installed and in PATH?")
                continue

        # Extract iPAE score
        result_zip_files = glob.glob(
            f"{args.alphafold_results_dir}/**/{design_name}.result.zip",
            recursive=True
        )
        if not result_zip_files:
            print(f"No result zip file found for {design_name}. Skipping iPAE extraction.")
            results[design_name] = {'ipae_score': None, 'loss_value': loss_value}
            continue

        result_zip = result_zip_files[0]
        ipae_score = extract_ipae_score(result_zip, design_name)
        results[design_name] = {'ipae_score': ipae_score, 'loss_value': loss_value}

    # Create results DataFrame
    results_data = [
        {
            'Design': design_name,
            'ipae_score': data['ipae_score'],
            'loss_value': data['loss_value']
        }
        for design_name, data in results.items()
    ]
    results_df = pd.DataFrame(results_data)

    # Sort by iPAE score (lower is better)
    results_df = results_df.sort_values('ipae_score', na_position='last')

    # Save to CSV
    results_df.to_csv(args.output_csv, index=False)
    print(f"\n{'='*60}")
    print(f"Results saved to: {args.output_csv}")
    print(f"{'='*60}")
    print("\nTop 10 designs by iPAE score (lower is better):")
    print(results_df.head(10).to_string(index=False))

    # Merge with original designs DataFrame for complete information
    complete_results = pd.merge(
        designs_df,
        results_df[['Design', 'ipae_score']],
        on='Design',
        how='left'
    )
    complete_output = args.output_csv.replace('.csv', '_complete.csv')
    complete_results.to_csv(complete_output, index=False)
    print(f"\nComplete results (with sequences) saved to: {complete_output}")


if __name__ == "__main__":
    main()

import csv
import json

def create_alphafold_complex_json_from_csv(csv_filepath, json_output_filepath):
    """
    Reads a CSV file containing protein design results (binder and target sequences)
    and creates a JSON file formatted for an AlphaFold server to predict complexes.

    Args:
        csv_filepath (str): Path to the input CSV file.
        json_output_filepath (str): Path to save the generated JSON file.
    """
    all_jobs = []

    try:
        with open(csv_filepath, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            required_columns = ['Design', 'Sequence', 'TargetSequence']
            if not all(col in reader.fieldnames for col in required_columns):
                missing_cols = [col for col in required_columns if col not in reader.fieldnames]
                print(f"Error: CSV file must contain {', '.join(required_columns)} columns. Missing: {', '.join(missing_cols)}")
                return

            for row_number, row in enumerate(reader, 1):
                design_name = row.get('Design')
                binder_sequence = row.get('Sequence')
                target_sequence = row.get('TargetSequence')

                if not design_name or not binder_sequence or not target_sequence:
                    print(f"Warning: Skipping row {row_number} due to missing Design, Sequence, or TargetSequence.")
                    # print(f"Details: Design='{design_name}', Binder='{binder_sequence}', Target='{target_sequence}'")
                    continue
                
                # Basic validation for protein sequences (can be expanded)
                if not all(c.isalpha() and c.isupper() for c in binder_sequence):
                    print(f"Warning: Skipping row {row_number} (Design: {design_name}) due to invalid characters in binder Sequence: {binder_sequence[:30]}...")
                    continue
                if not all(c.isalpha() and c.isupper() for c in target_sequence):
                    print(f"Warning: Skipping row {row_number} (Design: {design_name}) due to invalid characters in TargetSequence: {target_sequence[:30]}...")
                    continue


                job_definition = {
                    "name": f"{design_name}", # Appending _complex to distinguish
                    "modelSeeds": [],
                    "sequences": [
                        {
                            "proteinChain": {
                                "sequence": binder_sequence,
                                "count": 1
                            }
                        },
                        {
                            "proteinChain": {
                                "sequence": target_sequence,
                                "count": 1
                            }
                        }
                    ],
                    "dialect": "alphafoldserver",
                    "version": 1
                }
                all_jobs.append(job_definition)

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_filepath}")
        return
    except Exception as e:
        print(f"An error occurred while processing the CSV file: {e}")
        return

    if not all_jobs:
        print("No valid jobs were created. Output JSON file will not be generated.")
        return

    try:
        with open(json_output_filepath, mode='w', encoding='utf-8') as jsonfile:
            json.dump(all_jobs, jsonfile, indent=2)
        print(f"Successfully created JSON file for complex predictions: {json_output_filepath}")
        print(f"Total jobs created: {len(all_jobs)}")
    except Exception as e:
        print(f"An error occurred while writing the JSON file: {e}")

if __name__ == '__main__':
    # --- Configuration ---
    csv_input_path = '/Users/satishgaurav/Documents/extra/Hemeai/ToxBind/final_results.csv'
    # New output file name to reflect complex predictions
    json_output_path = 'alphafold_complex_jobs_from_csv.json'
    # --- End Configuration ---

    create_alphafold_complex_json_from_csv(csv_input_path, json_output_path)

import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import subprocess
    import re
    import pandas as pd
    from IPython.display import display, Markdown

    return Markdown, display, pd, subprocess


@app.cell
def _(pd):
    combined_df = pd.read_csv("./combined_data.csv")
    combined_df.head()
    return (combined_df,)


@app.cell
def _(combined_df):
    combined_df.iterrows()
    return


@app.cell
def _(pd):
    combined_df_1 = pd.read_csv("./combined_data.csv")
    results_ipae_df = pd.read_csv("./results_ipae.csv")
    return combined_df_1, results_ipae_df


@app.cell
def _(combined_df_1, pd, results_ipae_df):
    merged_df = pd.merge(
        combined_df_1, results_ipae_df, left_on="Design", right_on="Design"
    )
    merged_df
    return (merged_df,)


@app.cell
def _(merged_df):
    for value in merged_df.columns.to_list():
        print(value)
    return


@app.cell
def _():
    specific_columns = [
        "Rank",
        "Design",
        "Length",
        "ipae_score",
        "Average_i_pTM",
        "Target_Hotspot",
        "Sequence",
        "TargetSequence",
        "TargetSequenceLength",
        "Average_pAE",
        "Average_i_pAE",
        "Average_pTM",
        "Average_pLDDT",
        "Average_i_pLDDT",
        "Average_ss_pLDDT",
        "Average_Target_RMSD",
        "Average_Hotspot_RMSD",
        "Average_Binder_pLDDT",
        "Average_Binder_pTM",
        "Average_Binder_pAE",
        "Average_Binder_RMSD",
        "DesignTime",
        "Notes",
        "TargetSettings",
        "Folder",
    ]
    return (specific_columns,)


@app.cell
def _(merged_df, specific_columns):
    sorted_merged_df = merged_df.sort_values(by="ipae_score", ascending=True)
    sorted_merged_df = sorted_merged_df[specific_columns]
    sorted_merged_df
    return (sorted_merged_df,)


@app.cell
def _(Markdown, display, sorted_merged_df):
    sorted_merged_df_1 = sorted_merged_df.sort_values(
        by=["Average_i_pTM", "ipae_score"], ascending=[False, False]
    )
    display(Markdown(sorted_merged_df_1.to_markdown(index=False)))
    return (sorted_merged_df_1,)


@app.cell
def _(sorted_merged_df_1):
    sorted_merged_df_1.to_csv("final_results.csv", index=False)
    return


@app.cell
def _(sorted_merged_df_1):
    _fasta_file_name = "all_binder_fastas"
    final_fasta_content = ""
    for index, _row in sorted_merged_df_1.iterrows():
        design = _row["Design"]
        binder_seq_len = _row["Length"]
        sequence = _row["Sequence"]
        fasta_content = f">{design}\n{sequence}\n\n"
        final_fasta_content = final_fasta_content + fasta_content
    _fasta_file_path = f"{_fasta_file_name}.fasta"
    with open(_fasta_file_path, "w") as _fasta_file:
        _fasta_file.write(final_fasta_content)
    return


@app.cell
def _(merged_df):
    filtered_df = merged_df[merged_df["Notes"].isna()]
    filtered_df
    return


@app.cell
def _(merged_df):
    merged_df["Notes"].to_list()
    return


@app.cell
def _():
    # !cp final_results.csv ./../final_results.csv
    return


@app.cell
def _(pd):
    final_result_df = pd.read_csv("./../final_results.csv")
    final_result_df
    return (final_result_df,)


@app.cell
def _(final_result_df):
    final_result_df_1yi5 = final_result_df.sort_values(
        by=["Average_i_pTM", "ipae_score"], ascending=[False, False]
    )
    final_result_df_1yi5 = final_result_df_1yi5[
        final_result_df_1yi5["TargetSettings"] == "1yi5"
    ]
    # display(Markdown(final_result_df_1yi5.to_markdown(index=True)))
    return


@app.cell
def _(Markdown, display, final_result_df):
    final_result_df_7z14 = final_result_df.sort_values(
        by=["Average_i_pTM", "ipae_score"], ascending=[False, False]
    )
    final_result_df_7z14 = final_result_df_7z14[
        final_result_df_7z14["TargetSettings"] == "7z14"
    ]
    display(Markdown(final_result_df_7z14.to_markdown(index=True)))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Get IPAE score for Binder from Paper
    """)
    return


@app.cell
def _(Markdown, display, pd):
    import os
    from Bio.PDB import PDBParser, PPBuilder

    def extract_chain_sequences(pdb_path):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure("design", pdb_path)
        model = structure[0]
        chains = list(model.get_chains())
        if len(chains) < 2:  # Assuming only one model
            return (None, None)
        ppb = PPBuilder()

        def get_chain_sequence(chain):
            peptides = ppb.build_peptides(chain)  # Not enough chains
            if peptides:
                return "".join([str(p.get_sequence()) for p in peptides])
            else:
                return ""

        seq1 = get_chain_sequence(chains[0])
        seq2 = get_chain_sequence(chains[1])
        return (seq1, seq2)

    def process_folder(folder_path):
        data = []
        for file in os.listdir(folder_path):
            if file.endswith(".pdb"):
                pdb_path = os.path.join(folder_path, file)
                seq1, seq2 = extract_chain_sequences(pdb_path)
                if seq1 is not None and seq2 is not None:
                    data.append(
                        {
                            "Design": os.path.splitext(file)[0],
                            "Sequence": seq1,
                            "TargetSequence": seq2,
                        }
                    )
        df = pd.DataFrame(data)
        return df

    folder_path = "./../target"
    df = process_folder(folder_path)
    # Example usage
    display(Markdown(df.to_markdown(index=True)))  # change this to your folder path
    return (os,)


@app.cell
def _(Markdown, display, pd):
    target_dict = {
        "Design": ["9KB5", "9KB6", "9KB7"],
        "Sequence": [
            "MSGGSPAEREAGRIVVRGDVAIAEAVVRKVGEVAGKEVILLISYRKNGEWITYQRNLEATPEDVERTIAVIREIYEESGGDFILAIFSDPEVGAAGRAVAAAAAGGSGSHHWGSTHHHHHH",
            "MSGGTPEERLAQLEKEIQALYDAADEVVDEVEEKDGKMTVTRTLTIGDGTVTLVETLKIVDGAPVKDGEIEVICNPECEELGKRLKALAKEYEKAQEEVEKAKA",
            "MSGGPKTVVVRLSPSMNEEQAAEIGREAGKAALAAGDRLVFVGPADQSYAAMKAAMEAGLPEVTMYALDFSDAESALKAAEVAEDEGDEEVAEVAREIAEEIKAGGSGSHHWGSTHHHHHH",
        ],
        "TargetSequence": [
            "IRCFITPDITSKDCPNGHVCYTKTWCDAFCSIRGKRVDLGCAATCPTVKTGVDIQCCSTDNCNPFPTRKRP",
            "LKCNQLIPPFWKTCPKGKNLCYKMTMRAAPMVPVKRGCIDVCPKSSLLIKYMCCNTDKCN",
            "MICYNQQSSQPPTTKTCSETSCYKKTWRDHRGTIIERGCGCPKVKPGIKLHCCRTDKCNN",
        ],
    }
    target_df = pd.DataFrame(target_dict)
    display(Markdown(target_df.to_markdown(index=True)))
    combined_df_2 = target_df  # alpha-cobratoxin long chain  # cytotoxin  # short chain consensus toxin (ScNtx)
    return (combined_df_2,)


@app.cell
def _(combined_df_2, os, pd, subprocess):
    """
    This script processes a CSV file ('combined_data.csv'), generates FASTA files
    for each entry, runs AlphaFold (via Modal) if results don't already exist,
    and then extracts the Interface Predicted Aligned Error (ipae) score from
    the AlphaFold results. Finally, it saves these scores into 'results_ipae.csv'.
    """
    import glob
    import sys

    def check_existing_result(fasta_file_name_param):
        """
        Checks if an AlphaFold result file already exists for the given FASTA file name.

        Args:
            fasta_file_name_param (str): The base name of the FASTA file (without .fasta).

        Returns:
            bool: True if a result file exists, False otherwise.
        """
        pattern = f"./../target/alphafold_results/**/{fasta_file_name_param}.result.zip"
        existing_files = glob.glob(pattern, recursive=True)
        return bool(existing_files)

    FASTA_OUTPUT_DIR = "./../target/fasta_files_for_alphafold"
    os.makedirs(FASTA_OUTPUT_DIR, exist_ok=True)
    results = {}
    for _, _row in combined_df_2.iterrows():
        _fasta_file_name = _row["Design"]
        binder_sequence = _row["Sequence"]
        target_seq = _row["TargetSequence"]
        print(f"Processing: {_fasta_file_name}")
        COMBINED_SEQ_STR = f"{target_seq}:{binder_sequence}"
        FASTA_CONTENT_STR = f">{_fasta_file_name}\n{COMBINED_SEQ_STR}\n"
        _fasta_file_path = os.path.join(FASTA_OUTPUT_DIR, f"{_fasta_file_name}.fasta")
        try:
            with open(_fasta_file_path, "w", encoding="utf-8") as _fasta_file:
                _fasta_file.write(FASTA_CONTENT_STR)
        except IOError as e:
            print(f"Error writing FASTA file {_fasta_file_path}: {e}")
            continue
        if check_existing_result(_fasta_file_name):
            print(
                f"Result for {_fasta_file_name} already exists, skipping computation."
            )
        else:
            MODAL_SCRIPT_PATH_LOCAL = "./modal_alphafold.py"
            ALPHAFOLD_RESULTS_DIR_LOCAL = "./../target/alphafold_results"
            COMMAND_RUN_ALPHAFOLD_STR = f'GPU="H100" modal run {MODAL_SCRIPT_PATH_LOCAL} --input-fasta "{_fasta_file_path}" --out-dir "{ALPHAFOLD_RESULTS_DIR_LOCAL}"'
            try:
                subprocess.run(
                    COMMAND_RUN_ALPHAFOLD_STR, shell=True, check=True, text=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Error running AlphaFold for {_fasta_file_name}: {e}")
                continue
            except FileNotFoundError:
                print(
                    "Error: 'modal' command not found. Is Modal installed and in PATH?"
                )
                continue
        result_zip_files = glob.glob(
            f"./../target/alphafold_results/**/{_fasta_file_name}.result.zip",
            recursive=True,
        )
        if not result_zip_files:
            print(
                f"No result zip file found for {_fasta_file_name}. Skipping IPAE extraction."
            )
            results[_fasta_file_name] = None
            continue
        result_zip = result_zip_files[0]
        COMMAND_EXTRACT_IPAE_STR = f"""unzip -p "{result_zip}" "*.json" | jq -r 'select(.ipae != null) | .ipae."0"'"""
        IPAE_SCORE_VAL = None
        try:
            process_result = subprocess.run(
                COMMAND_EXTRACT_IPAE_STR,
                shell=True,
                text=True,
                capture_output=True,
                check=False,
            )
            if process_result.returncode == 0:
                output = process_result.stdout.strip()
                if output:
                    try:
                        IPAE_SCORE_VAL = float(output)
                        print(
                            f"Extracted IPAE score for {_fasta_file_name}: {IPAE_SCORE_VAL}"
                        )
                    except ValueError:
                        print(
                            f"Could not convert IPAE score to float for {_fasta_file_name}: '{output}'"
                        )
                else:
                    print(
                        f"No IPAE score found in JSON for {_fasta_file_name} (jq output was empty)."
                    )
            elif process_result.returncode == 4:
                print(f"No IPAE score found (jq code 4) for {_fasta_file_name}.")
            else:
                print(
                    f"Error extracting IPAE for {_fasta_file_name} (return code {process_result.returncode}): {process_result.stderr.strip()}"
                )
        except subprocess.CalledProcessError as e:
            print(
                f"Subprocess error during IPAE extraction for {_fasta_file_name}: {e}"
            )
        except FileNotFoundError:
            print(
                "Error: 'unzip' or 'jq' command not found. Please ensure they are installed and in PATH."
            )
        except Exception as e:
            print(
                f"An unexpected error occurred during IPAE extraction for {_fasta_file_name}: {type(e).__name__} - {e}"
            )
        results[_fasta_file_name] = IPAE_SCORE_VAL
    print("Final IPAE results:", results)
    results_df = pd.DataFrame(list(results.items()), columns=["Design", "ipae_score"])
    results_df.to_csv("./../target/results_ipae.csv", index=False)
    print(results_df)
    return


if __name__ == "__main__":
    app.run()

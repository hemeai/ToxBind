"""
Run AlphaFold2 / AF2-multimer using Modal.

This script defines Modal functions to run AlphaFold2 predictions,
including support for multimer predictions (e.g., binder-target complexes).
It also includes functions to score the binding interface using iPAE values
from the AlphaFold output.
"""
import os
import json
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime

import numpy as np
from modal import App, Image # type: ignore
# colabfold and Bio will be available in the Modal environment
from colabfold.batch import get_queries, run as colabfold_run # type: ignore
from colabfold.download import default_data_dir # type: ignore


GPU_CONFIG = os.environ.get("MODAL_GPU", "A10G")
# Ensure TIMEOUT is an int; default to 20 minutes (1200 seconds)
MODAL_TIMEOUT = int(os.environ.get("MODAL_TIMEOUT", 20 * 60))
LOCAL_MSA_DIR = Path("msas") # Use Path object directly
if not LOCAL_MSA_DIR.exists():
    LOCAL_MSA_DIR.mkdir(exist_ok=True)

# Define the Modal image
# Break long lines for readability and to pass linting
image = (
    Image.debian_slim(python_version="3.11")
    .micromamba()
    .apt_install("wget", "git")
    .pip_install(
        "colabfold[alphafold-minus-jax]@git+https://github.com/sokrypton/ColabFold",
        "numpy",
        "pandas" # Added pandas as it's used by other scripts, good to have
    )
    .micromamba_install(
        "kalign2=2.04", "hhsuite=3.3.0", channels=["conda-forge", "bioconda"]
    )
    .run_commands(
        'pip install --upgrade "jax[cuda12_pip]" '
        '-f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html',
        gpu=GPU_CONFIG, # Use the defined GPU_CONFIG
    )
    .run_commands("python -m colabfold.download")
)

app = App("alphafold", image=image)


# pylint: disable=too-many-locals
def score_af2m_binding(af2m_dict: dict, target_len: int,
                       binders_len: list[int]) -> dict:
    """
    Calculate binding scores from AlphaFold2 multimer prediction results.
    The target is assumed to be the first part of the sequence up to `target_len`,
    followed by one or more binders.

    Parameters:
        af2m_dict (dict): Dictionary from AlphaFold2 multimer JSON output.
        target_len (int): Length of the target protein sequence.
        binders_len (list[int]): List of lengths for each binder sequence.

    Returns:
        dict: A dictionary containing various pLDDT and PAE scores.
    """
    plddt_array = np.array(af2m_dict["plddt"])
    pae_array = np.array(af2m_dict["pae"])

    total_expected_len = target_len + sum(binders_len)
    if not len(plddt_array) == len(pae_array) == total_expected_len:
        # Consider logging this error as well or raising a more specific error
        raise ValueError(
            f"Mismatch in array lengths. Expected {total_expected_len}, "
            f"got pLDDT: {len(plddt_array)}, PAE: {len(pae_array)}"
        )

    plddt_target = np.mean(plddt_array[:target_len])
    pae_target = np.mean(pae_array[:target_len, :target_len])

    plddt_binder_scores = {}
    pae_binder_scores = {}
    ipae_scores = {}
    ipae_binder_scores_detailed = {} # Renamed from ipae_binder

    current_pos = target_len
    for binder_idx, binder_len_val in enumerate(binders_len):
        binder_start, binder_end = current_pos, current_pos + binder_len_val

        plddt_binder_scores[binder_idx] = np.mean(plddt_array[binder_start:binder_end])

        pae_binder_scores[binder_idx] = np.mean(
            pae_array[binder_start:binder_end, binder_start:binder_end]
        )
        # Interface PAE (iPAE)
        interface_pae_target_binder = pae_array[:target_len, binder_start:binder_end]
        interface_pae_binder_target = pae_array[binder_start:binder_end, :target_len]
        ipae_scores[binder_idx] = np.mean(
            [np.mean(interface_pae_target_binder), np.mean(interface_pae_binder_target)]
        )

        # This calculates the mean PAE for each residue of the current binder
        # against all residues of the target.
        # The result is an array of PAE values, one for each residue in the binder.
        per_residue_ipae_binder_vs_target = np.mean(
            pae_array[binder_start:binder_end, :target_len], axis=1
        )
        ipae_binder_scores_detailed[binder_idx] = per_residue_ipae_binder_vs_target

        current_pos += binder_len_val

    return {
        "plddt_binder": {k: float(v) for k, v in plddt_binder_scores.items()},
        "plddt_target": float(plddt_target),
        "pae_binder": {k: float(v) for k, v in pae_binder_scores.items()},
        "pae_target": float(pae_target),
        "ipae": {k: float(v) for k, v in ipae_scores.items()},
        "ipae_binder": {
            k: [float(score) for score in val_array] # val_array is ipae_binder_scores_detailed[k]
            for k, val_array in ipae_binder_scores_detailed.items()
        },
    }


@app.function(
    image=image.add_local_dir(LOCAL_MSA_DIR, remote_path="/msas"), # type: ignore
    gpu=GPU_CONFIG,
    timeout=MODAL_TIMEOUT,
)
# pylint: disable=too-many-arguments,too-many-locals,too-many-statements,too-many-branches,too-many-positional-arguments
def alphafold(
    fasta_name: str,
    fasta_str: str,
    models: list[int] = None, # type: ignore
    num_recycles: int = 3,
    num_relax: int = 0,
    use_templates: bool = False,
    use_precomputed_msas: bool = False,
    return_all_files: bool = False,
):
    """
    Runs AlphaFold2 or AF2-multimer prediction using ColabFold.

    This function is decorated to run as a Modal function, leveraging cloud compute.
    It takes a FASTA string, processes it, runs the ColabFold pipeline, and
    optionally scores multimer predictions for interface PAE.

    Args:
        fasta_name: Name for the input FASTA file (e.g., "input.fasta").
        fasta_str: The string content of the FASTA file.
                   For multimers, sequences should be separated by ':'.
        models: A list of model numbers (1-5) to use for prediction.
                Defaults to [1].
        num_recycles: Number of recycles for the model. Defaults to 3.
        num_relax: Number of relaxation steps (0 for None, 1 for Amber). Defaults to 0.
        use_templates: Whether to use templates. Defaults to False.
        use_precomputed_msas: If True, attempts to copy MSAs from a predefined
                              local path in the Modal container. Defaults to False.
        return_all_files: If True, returns all generated files; otherwise, only
                          returns the primary result zip file. Defaults to False.

    Returns:
        A list of tuples, where each tuple contains the relative path
        of an output file and its content in bytes.
    """
    if models is None:
        models = [1]

    tmp_in_dir = Path("/tmp/in_af")
    tmp_out_dir = Path("/tmp/out_af")
    tmp_in_dir.mkdir(parents=True, exist_ok=True)
    tmp_out_dir.mkdir(parents=True, exist_ok=True)

    if use_precomputed_msas:
        msas_source_path = Path("/msas")
        if msas_source_path.exists() and msas_source_path.is_dir():
            try:
                subprocess.run(
                    f"cp -r {msas_source_path}/* {tmp_out_dir}",
                    shell=True, check=True, text=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Error copying MSAs: {e}")
                # Decide if this is a fatal error or just a warning
        else:
            print(f"Warning: MSA source directory {msas_source_path} not found. Skipping copy.")

    fasta_file_path = tmp_in_dir / fasta_name
    with open(fasta_file_path, "w", encoding="utf-8") as f:
        f.write(fasta_str)

    header = fasta_str.splitlines()[0]
    # "".join on a list of stripped lines is safer
    fasta_seq = "".join(s.strip() for s in fasta_str.splitlines()[1:])

    # Validate FASTA format (basic check)
    valid_chars = "ACDEFGHIKLMNPQRSTVWY:"
    if not header.startswith(">") or any(aa not in valid_chars for aa in fasta_seq.upper()):
        raise ValueError(f"Invalid FASTA format or characters: {fasta_str[:100]}...")

    queries, is_complex = get_queries(str(tmp_in_dir))

    colabfold_run(
        queries=queries,
        result_dir=str(tmp_out_dir),
        use_templates=use_templates,
        num_relax=num_relax,
        relax_max_iterations=200, # Default in ColabFold
        msa_mode="MMseqs2 (UniRef+Environmental)", # Default in ColabFold
        model_type="auto",
        num_models=len(models),
        num_recycles=str(num_recycles), # ColabFold expects string for num_recycles
        model_order=models,
        is_complex=is_complex,
        data_dir=default_data_dir(),
        keep_existing_results=False,
        rank_by="auto",
        pair_mode="unpaired+paired",
        stop_at_score=100.0, # Default in ColabFold
        zip_results=True,
        user_agent="colabfold/modal-client",
    )

    if ":" in fasta_seq:  # then it is a multimer
        # Correctly parse target and binder lengths for multiple binders
        parts = fasta_seq.split(":")
        target_sequence_str = parts[0]
        target_len_val = len(target_sequence_str)
        binders_len_val = [len(b_seq) for b_seq in parts[1:] if b_seq]


        results_zip_files = list(tmp_out_dir.glob("**/*.zip"))
        if not results_zip_files:
            # This case should ideally be handled, maybe raise an error
            # or return empty if no zip file is produced.
            print(f"Warning: No result zip found in {tmp_out_dir}")
            return []
        results_zip = results_zip_files[0]


        with zipfile.ZipFile(results_zip, "a") as zip_ref: # Open in append mode
            # Filter for .json files that are not af2m_scores.json
            json_file_names = [
                f_name for f_name in zip_ref.namelist()
                if f_name.endswith(".json") and "af2m_scores" not in f_name
            ]

            for json_file_name in json_file_names:
                try:
                    json_content = zip_ref.read(json_file_name)
                    json_data = json.loads(json_content.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Error decoding JSON from {json_file_name} in zip: {e}")
                    continue

                if "plddt" in json_data and "pae" in json_data:
                    prefix = Path(json_file_name).with_suffix("")
                    af2m_scores = score_af2m_binding(json_data, target_len_val, binders_len_val)
                    scores_json = json.dumps(af2m_scores, indent=2)
                    # Add the scores JSON to the zip file
                    zip_ref.writestr(f"{prefix}.af2m_scores.json", scores_json)
                    break # Process only the first relevant JSON file

    output_files_data = []
    for out_file_path in tmp_out_dir.glob("**/*"):
        if out_file_path.is_file():
            if return_all_files or out_file_path.suffix == ".zip":
                with open(out_file_path, "rb") as f_rb: # Read in binary mode
                    output_files_data.append(
                        (out_file_path.relative_to(tmp_out_dir), f_rb.read())
                    )
    return output_files_data


@app.local_entrypoint()
# pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments
def main(
    input_fasta: str,
    models: str = "1", # Comma-separated string
    num_recycles: int = 1,
    num_relax: int = 0,
    out_dir: str = ".",
    use_templates: bool = False,
    use_precomputed_msas: bool = False,
    return_all_files: bool = False,
):
    """
    Local entry point to run AlphaFold prediction using Modal.

    Args:
        input_fasta (str): Path to the input FASTA file.
        models (str, optional): Comma-separated string of model numbers (1-5).
                                Defaults to "1".
        num_recycles (int, optional): Number of recycles. Defaults to 1.
        num_relax (int, optional): Number of relaxations (0=None, 1=Amber).
                                   Defaults to 0.
        out_dir (str, optional): Directory to save output files.
                                 Defaults to current directory (".").
        use_templates (bool, optional): Whether to use templates. Defaults to False.
        use_precomputed_msas (bool, optional): Whether to use precomputed MSAs.
                                              Defaults to False.
        return_all_files (bool, optional): Whether to return all output files or just the zip.
                                           Defaults to False.
    """
    try:
        with open(input_fasta, "r", encoding="utf-8") as f:
            fasta_str_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input FASTA file not found at {input_fasta}")
        return # Or sys.exit(1)

    model_list = [int(model.strip()) for model in models.split(",") if model.strip()]

    outputs = alphafold.remote(
        fasta_name=Path(input_fasta).name,
        fasta_str=fasta_str_content,
        models=model_list,
        num_recycles=num_recycles,
        num_relax=num_relax,
        use_templates=use_templates,
        use_precomputed_msas=use_precomputed_msas,
        return_all_files=return_all_files,
    )

    today_str = datetime.now().strftime("%Y%m%d%H%M")[2:]
    out_dir_full = Path(out_dir) / today_str
    out_dir_full.mkdir(parents=True, exist_ok=True) # Ensure out_dir_full is created

    for out_file_rel_path, out_content in outputs:
        full_path = out_dir_full / out_file_rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if out_content: # Ensure content is not None (though bytes shouldn't be None)
            with open(full_path, "wb") as out:
                out.write(out_content)
    print(f"Outputs saved to {out_dir_full.resolve()}")
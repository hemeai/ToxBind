"""
This script converts protein sequences from a FASTA file to DNA sequences,
optimizing them for a specified species (e.g., E. coli) using DNA Chisel.
It avoids specified patterns like BsaI restriction sites.
"""
import os
from dnachisel import ( # type: ignore
    reverse_translate, DnaOptimizationProblem, CodonOptimize, AvoidPattern
)
from Bio import SeqIO # type: ignore

def convert_and_optimize( # pylint: disable=line-too-long
    input_fasta="data/protein.fasta",
    output_fasta="output/optimized_dna.fasta",
    species="e_coli"
):
    """
    Converts a protein sequence to an optimized DNA sequence.

    Args:
        input_fasta (str): Path to the input FASTA file containing the protein sequence.
        output_fasta (str): Path to save the optimized DNA sequence in FASTA format.
        species (str): Species for codon optimization (e.g., 'e_coli', 'h_sapiens').
    """
    # Read the protein sequence from FASTA
    record = next(SeqIO.parse(input_fasta, "fasta"))
    protein_seq = str(record.seq)

    # Reverse translate with species codon usage
    dna_seq = reverse_translate(protein_seq)

    # Set up DNA Chisel optimization problem
    problem = DnaOptimizationProblem(
        sequence=dna_seq,
        constraints=[
            AvoidPattern("BsaI_site"),  # Example: avoid BsaI restriction sites
        ],
        objectives=[
            CodonOptimize(species=species)
        ]
    )

    # Perform optimization
    problem.optimize()

    # Ensure output folder exists
    output_dir = os.path.dirname(output_fasta)
    if output_dir: # Ensure output_dir is not an empty string (e.g. if output_fasta is just a filename)
        os.makedirs(output_dir, exist_ok=True)

    # Save optimized sequence
    with open(output_fasta, "w", encoding="utf-8") as f:
        f.write(f">optimized_gene\n{problem.sequence}\n") # Use f-string

    print(f"[✓] Optimized DNA saved: {output_fasta}")

# Run it
if __name__ == "__main__":
    convert_and_optimize()

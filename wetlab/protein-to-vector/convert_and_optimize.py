from dnachisel import reverse_translate, DnaOptimizationProblem, CodonOptimize, AvoidPattern
from Bio import SeqIO
import os

def convert_and_optimize(
    input_fasta="data/protein.fasta",
    output_fasta="output/optimized_dna.fasta",
    species="e_coli"
):
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
    os.makedirs(os.path.dirname(output_fasta), exist_ok=True)

    # Save optimized sequence
    with open(output_fasta, "w") as f:
        f.write(">optimized_gene\n" + problem.sequence + "\n")

    print(f"[✓] Optimized DNA written to {output_fasta}")

# Run it
if __name__ == "__main__":
    convert_and_optimize()

"""
This script reads a DNA sequence from a FASTA file, translates it into
amino acids codon by codon, and prints a mapping of codon index,
codon, and corresponding amino acid.
"""
from Bio import SeqIO # type: ignore
from Bio.Seq import Seq # type: ignore

def map_codons_to_amino_acids_from_fasta(fasta_path):
    """
    Reads a DNA sequence from a FASTA file, translates it codon by codon,
    and prints the mapping.

    Args:
        fasta_path (str): The path to the input FASTA file containing
                          a single DNA sequence.
    """
    # Read the first DNA sequence from FASTA
    record = next(SeqIO.parse(fasta_path, "fasta"))
    dna_seq = str(record.seq)

    # Split into codons
    codons = [dna_seq[i:i+3] for i in range(0, len(dna_seq), 3)]
    amino_acids = [Seq(codon).translate() if len(codon) == 3 else '-' for codon in codons]

    # Print mapping
    print(f"{'Index':<5} {'Codon':<6} {'Amino Acid'}")
    print("-" * 25)
    for i, (codon, aa) in enumerate(zip(codons, amino_acids)):
        print(f"{i+1:<5} {codon:<6} {aa}")

# Run the function on your output file
if __name__ == "__main__":
    DEFAULT_FASTA_FILE = "output/optimized_dna.fasta"
    map_codons_to_amino_acids_from_fasta(DEFAULT_FASTA_FILE)

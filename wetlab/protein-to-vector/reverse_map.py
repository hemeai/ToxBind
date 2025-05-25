from Bio.Seq import Seq

def map_codons_to_amino_acids(dna_seq):
    dna = Seq(dna_seq)
    codons = [str(dna[i:i+3]) for i in range(0, len(dna), 3)]
    amino_acids = [str(Seq(c).translate()) if len(c) == 3 else '-' for c in codons]

    print(f"{'Index':<5} {'Codon':<6} {'Amino Acid'}")
    print("-" * 25)
    for i, (codon, aa) in enumerate(zip(codons, amino_acids)):
        print(f"{i+1:<5} {codon:<6} {aa}")

# Example sequence (your optimized_gene)
optimized_dna = (
    "ATGAAAACCGCGTATATTGCGAAACAGCGCCAGATTTATTTTGTGAAATATCATTTTTATCGCCAGGATATTTTTGATTTTTGGATTTATCATACCCAGGGCTATTTTCCGGATTGGCAGAACTAT"
)

map_codons_to_amino_acids(optimized_dna)

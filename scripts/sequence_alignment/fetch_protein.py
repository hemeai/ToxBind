from Bio import Entrez, SeqIO
import os

Entrez.email = "satish@hemeai.com"


def fetch_protein(query, out_file):
    handle = Entrez.esearch(db="protein", term=query, retmax=20)
    record = Entrez.read(handle)
    handle.close()

    ids = record["IdList"]

    if not ids:
        print("No results for:", query)
        return

    handle = Entrez.efetch(db="protein", id=ids, rettype="fasta", retmode="text")
    sequences = handle.read()
    handle.close()

    with open(out_file, "a") as f:
        f.write(sequences)


# Example
fetch_protein("PLA2 Austrelaps labialis", "pla2_sequences.fasta")

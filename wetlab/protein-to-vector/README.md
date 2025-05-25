# 1. Place your protein sequence in data/protein.fasta
#    Format:
#    >my_protein
#    MKTAYIAKQRQISFVKSHFSRQDILDLWIYHTQGYFPDWQNY

# 2. Reverse translate
bash scripts/reverse_translate.sh

# 3. Codon optimize
python scripts/codon_optimize.py

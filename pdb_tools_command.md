
https://www.bonvinlab.org/pdb-tools/

pdb_merge 6aru_final_chain_A_domain_3.pdb hu_nano2_4_85252b_B.pdb | pdb_tidy > input.pdb

pdb_fetch 5nq4 > 5nq4.pdb
pdb_wc 7z14.pdb

pdb_tofasta -multi 7z14.pdb 


/Users/satishgaurav/Documents/extra/HemeAI/ToxBind/analysis/fasta_files_for_alphafold/1yi5_l102_s209387_mpnn3.fasta

GPU="H100" modal run modal_alphafold.py --input-fasta ./fasta_files_for_alphafold/1yi5_l102_s209387_mpnn3.fasta  --out-dir output-test

GPU="H100" modal run modal_alphafold.py --input-fasta ./fasta_files_for_alphafold/1yi5_l102_s209387_mpnn3.fasta  


pip install modal
python3 -m modal setup


https://www.rcsb.org/3d-view/8D9Y
pdb_fetch 8d9y > 8d9y.pdb

wget https://files.rcsb.org/download/8d9y.pdb
pdb_tofasta -multi 8d9y.pdb 

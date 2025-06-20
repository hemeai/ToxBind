
https://www.bonvinlab.org/pdb-tools/

pdb_merge 6aru_final_chain_A_domain_3.pdb hu_nano2_4_85252b_B.pdb | pdb_tidy > input.pdb

pdb_fetch 5nq4 > 5nq4.pdb
pdb_wc 7z14.pdb

pdb_tofasta -multi 7z14.pdb 

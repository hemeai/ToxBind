TIMEOUT=1400 GPU=A100 modal run --detach modal_bindcraft.py --input-pdb 5nq4.pdb --lengths 72,96 --number-of-final-designs 1

TIMEOUT=1400 GPU=A100 modal run --detach modal_bindcraft.py --input-pdb 5nq4.pdb --lengths 120,120 --number-of-final-designs 1

TIMEOUT=1400 GPU=A100 modal run --detach modal_bindcraft.py --input-pdb 1yi5_chain_I.pdb --lengths 96,96 --number-of-final-designs 1

TIMEOUT=1400 GPU=A100 modal run --detach modal_bindcraft.py --input-pdb 1yi5.pdb --chains H --target-hotspot-residues H26-H37 --lengths 96,96 --number-of-final-designs 1

TIMEOUT=1400 GPU=A100 modal run --detach modal_bindcraft.py --input-pdb 1yi5.pdb --chains H --target-hotspot-residues H6,H7,H26-H37,H50,H51 --lengths 96,96 --number-of-final-designs 1

TIMEOUT=1400 GPU=A100 modal run --detach modal_bindcraft.py --input-pdb 1yi5.pdb --chains H --target-hotspot-residues H26-H37,H50,H51 --lengths 144,160 --number-of-final-designs 1

TIMEOUT=1400 GPU=A100 modal run --detach modal_bindcraft.py --input-pdb 1yi5.pdb --chains H --target-hotspot-residues H7,H8,H27,H28,H31,H32,H33,H37 --lengths 96,96 --number-of-final-designs 3

TIMEOUT=1400 GPU=A100 modal run --detach modal_bindcraft.py --input-pdb 1yi5.pdb --chains H --lengths 72,96 --number-of-final-designs 1

TIMEOUT=1400 GPU=A100 modal run --detach modal_bindcraft.py --input-pdb ./target/7z14.pdb --chains F --lengths 72,96 --number-of-final-designs 1

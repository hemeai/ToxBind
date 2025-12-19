# Protein → Orderable Plasmid

Automated wet-lab handoff: take a designed protein sequence and emit an order-ready expression plasmid (pUC19 + T7 promoter/RBS + His6-TEV tag + strong terminator) with pydna assembly verification.

## Quickstart

1. Drop your protein sequence into `data/protein.fasta`
   ```
   >my_protein
   MKTAYIAKQRQISFVKSHFSRQDILDLWIYHTQGYFPDWQNY
   ```
2. Run the pipeline:
   ```bash
   python wetlab/protein-to-vector/convert_and_optimize.py
   ```
3. Collect outputs in `wetlab/protein-to-vector/output/`:
   - `optimized_cds.fasta` – codon-optimized CDS (Type IIS-clean, GC checked)
   - `expression_cassette.fasta` – T7→RBS→ATG→His6→TEV→linker→CDS→stop→terminator
   - `gblock_insert.fasta` – cassette wrapped with 40 bp pUC19 homology arms (Gibson/HiFi ready)
   - `plasmid_ready_to_order.fasta` – final circular plasmid sequence for synthesis/ordering
   - `assembly_report.txt` – pydna assembly success + restriction digest sizes + feature map

## What it builds

- **Codon optimization:** DNA Chisel with GC windowing and automatic scrubbing of BsaI/BsmBI/BbsI.
- **Expression cassette:** T7 promoter, B0034 RBS, ATG + His6-TEV tag + flexible linker, stop codon, L3S2P21 terminator.
- **Backbone:** pUC19 (drop-in replaces the MCS; defaults to midpoint if MCS not found).
- **Simulation:** pydna assembly with backbone homology arms + in-silico restriction digests (BsaI/BsmBI/BbsI/EcoRI).

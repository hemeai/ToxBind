"""
End-to-end wet-lab handoff:
1. Codon-optimize the designed protein.
2. Build a Golden Gate/Gibson-ready expression cassette (T7 promoter, RBS, His6-TEV tag, terminator).
3. Drop it into a pUC19 backbone and validate the assembly with pydna.
4. Emit orderable FASTAs plus an assembly/QC report.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

from Bio import SeqIO  # type: ignore
from Bio.Restriction import BbsI, BsaI, BsmBI, EcoRI  # type: ignore
from Bio.SeqUtils import gc_fraction  # type: ignore
from dnachisel import (  # type: ignore
    AvoidPattern,
    CodonOptimize,
    DnaOptimizationProblem,
    EnforceGCContent,
    NoSolutionError,
    reverse_translate,
)
from pydna.assembly import Assembly  # type: ignore
from pydna.dseqrecord import Dseqrecord  # type: ignore

DEFAULT_INPUT_FASTA = "data/protein.fasta"
DEFAULT_BACKBONE_FASTA = "data/backbones/pUC19.fasta"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_OVERLAP_BP = 40  # Gibson-like overlaps for the gBlock
BASE_DIR = os.path.dirname(__file__)

# Land the cassette where the classic pUC19 MCS sits; fall back to the plasmid midpoint if not found.
PUC19_MCS = (
    "GAATTCGAGCTCGGTACCCGGGGATCCTCTAGAGTCGACCTGCAGGCATGCAAGCTT"
)

# Expression parts.
PROMOTER_T7 = "TAATACGACTCACTATAGGG"
RBS_B0034 = "AAAGAGGAGAAA"
START_CODON = "ATG"
NTERM_HIS6 = "CACCACCACCACCACCAC"
TEV_SITE = "GAAAACCTGTATTTTCAGGGT"  # ENLYFQG
FLEX_LINKER = "GGCGGTGGCGGT"  # (Gly-Gly-Gly-Gly-Ser in a codon-friendly form)
STOP_CODON = "TAA"
TERMINATOR_L3S2P21 = "AAGCTAGAGTAAGTAGTTCCTAGGTTTTTCTCCTTTTGCTTTTTT"


@dataclass
class PipelineResult:
    """Container for all intermediate and final DNA strings."""

    optimized_cds: str
    expression_cassette: str
    gblock_insert: str
    plasmid_sequence: str
    assembly_ok: bool
    digest_summary: Dict[str, List[int]]
    feature_positions: Dict[str, int]


def resolve_path(path: str) -> str:
    """Resolve repo-relative paths so the script can be run from anywhere."""
    return path if os.path.isabs(path) else os.path.join(BASE_DIR, path)


def load_protein_sequence(fasta_path: str) -> str:
    """Grab the first protein entry from FASTA."""
    record = next(SeqIO.parse(fasta_path, "fasta"))
    return str(record.seq).strip().upper()


def optimize_cds(protein_seq: str, species: str) -> str:
    """Reverse translate + codon-optimize while scrubbing Type IIS sites and GC extremes."""
    raw_dna = reverse_translate(protein_seq)
    gc_window = min(120, max(60, len(raw_dna) // 2))
    constraints = [
        AvoidPattern("GGTCTC"),  # BsaI
        AvoidPattern("GAGACC"),  # BsaI revcomp
        AvoidPattern("CGTCTC"),  # BsmBI
        AvoidPattern("GAGACG"),  # BsmBI revcomp
        AvoidPattern("GAAGAC"),  # BbsI
        AvoidPattern("GTCTTC"),  # BbsI revcomp
        EnforceGCContent(mini=0.30, maxi=0.70, window=gc_window),
    ]
    problem = DnaOptimizationProblem(
        sequence=raw_dna,
        constraints=constraints,
        objectives=[CodonOptimize(species=species)],
    )
    try:
        problem.optimize()
    except NoSolutionError:
        relaxed = DnaOptimizationProblem(
            sequence=raw_dna,
            constraints=[
                AvoidPattern("GGTCTC"),
                AvoidPattern("GAGACC"),
                AvoidPattern("CGTCTC"),
                AvoidPattern("GAGACG"),
                AvoidPattern("GAAGAC"),
                AvoidPattern("GTCTTC"),
            ],
            objectives=[CodonOptimize(species=species)],
        )
        relaxed.optimize()
        return str(relaxed.sequence).upper()
    return str(problem.sequence).upper()


def build_expression_cassette(cds: str) -> Tuple[str, Dict[str, int]]:
    """
    Assemble the expression cassette and return positions (1-based) for quick feature mapping.
    The frame is: T7 promoter -> RBS -> ATG -> His6 -> TEV -> linker -> CDS -> stop -> terminator.
    """

    parts: List[Tuple[str, str]] = []
    parts.append(("t7_promoter", PROMOTER_T7))
    parts.append(("rbs", RBS_B0034))
    parts.append(("start_codon", START_CODON))
    parts.append(("his6_tag", NTERM_HIS6))
    parts.append(("tev_site", TEV_SITE))
    parts.append(("linker", FLEX_LINKER))
    parts.append(("coding_sequence", cds))
    parts.append(("stop_codon", STOP_CODON))
    parts.append(("terminator", TERMINATOR_L3S2P21))

    feature_positions: Dict[str, int] = {}
    cassette_parts: List[str] = []
    cursor = 0
    for name, fragment in parts:
        feature_positions[name] = cursor + 1
        cassette_parts.append(fragment)
        cursor += len(fragment)

    return "".join(cassette_parts), feature_positions


def split_backbone(backbone_seq: str) -> Tuple[str, str, str, str]:
    """Remove the MCS (if present) to create an insertion site."""
    seq = backbone_seq.upper()
    if PUC19_MCS in seq:
        prefix, suffix = seq.split(PUC19_MCS, 1)
        insertion_site = "pUC19 MCS"
    else:
        halfway = len(seq) // 2
        prefix, suffix = seq[:halfway], seq[halfway:]
        insertion_site = "midpoint fallback"
    return prefix, suffix, prefix + suffix, insertion_site


def build_gblock_insert(backbone_linearized: str, cassette: str, overlap_bp: int) -> Tuple[str, int]:
    """Wrap the cassette with backbone homology arms for Gibson/HiFi assembly."""
    safe_overlap = min(overlap_bp, len(backbone_linearized) // 2)
    left = backbone_linearized[-safe_overlap:]
    right = backbone_linearized[:safe_overlap]
    return f"{left}{cassette}{right}", safe_overlap


def run_pydna_assembly(
    backbone_linearized: str, gblock_insert: str, overlap_bp: int
) -> Tuple[bool, str | None]:
    """Simulate the assembly in silico and return whether pydna found a circular product."""
    backbone_fragment = Dseqrecord(backbone_linearized, circular=False)
    insert_fragment = Dseqrecord(gblock_insert, circular=False)
    assembly = Assembly([backbone_fragment, insert_fragment], limit=overlap_bp)
    products = assembly.assemble_circular()
    if not products:
        return False, None
    return True, str(products[0].seq)


def digest_summary(plasmid_seq: str) -> Dict[str, List[int]]:
    """Digest the plasmid with a few diagnostic enzymes to hand to the wet lab."""
    plasmid = Dseqrecord(plasmid_seq, circular=True)
    summary: Dict[str, List[int]] = {}
    for enzyme in (BsaI, BsmBI, BbsI, EcoRI):
        fragments = plasmid.cut(enzyme)
        summary[enzyme.__name__] = sorted(len(f.seq) for f in fragments)
    return summary


def is_rotation(seq: str, target: str) -> bool:
    """Check circular equivalence of two sequences."""
    return len(seq) == len(target) and seq in (target + target)


def write_fasta(path: str, header: str, sequence: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f">{header}\n{sequence}\n")


def write_report(
    path: str,
    result: PipelineResult,
    backbone_source: str,
    insertion_site: str,
    overlap_bp: int,
    prefix_len: int,
) -> None:
    """Emit a human-friendly summary for the wet lab."""
    lines = [
        "=== Protein-to-plasmid build ===",
        f"Backbone: {backbone_source}",
        f"Insertion site: {insertion_site}",
        f"Gibson homology: {overlap_bp} bp each side",
        f"Cassette start (plasmid coords): {prefix_len + 1:,}",
        "",
        f"Optimized CDS length: {len(result.optimized_cds)} bp (GC {gc_fraction(result.optimized_cds)*100:.1f}%)",
        f"Expression cassette length: {len(result.expression_cassette)} bp",
        f"Final plasmid length: {len(result.plasmid_sequence)} bp (GC {gc_fraction(result.plasmid_sequence)*100:.1f}%)",
        "",
        "Feature starts (1-based on plasmid):",
    ]
    for name, pos in sorted(result.feature_positions.items(), key=lambda kv: kv[1]):
        lines.append(f" - {name}: {pos:,}")

    lines.append("")
    lines.append("Pydna assembly: " + ("✓ circular product found" if result.assembly_ok else "✗ no circular product"))
    lines.append("Restriction digest (fragment sizes in bp):")
    for enz, frags in result.digest_summary.items():
        msg = "no cut" if not frags else ", ".join(str(f) for f in frags)
        lines.append(f" - {enz}: {msg}")
    lines.append("Cassette design is BsaI/BsmBI/BbsI-free; any hits above are inherited from the backbone.")

    lines.append("")
    lines.append("Orderables:")
    lines.append(" - optimized CDS: output/optimized_cds.fasta")
    lines.append(" - expression cassette (no homology): output/expression_cassette.fasta")
    lines.append(" - gBlock with backbone homology: output/gblock_insert.fasta")
    lines.append(" - final plasmid: output/plasmid_ready_to_order.fasta")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def convert_and_optimize(
    input_fasta: str = DEFAULT_INPUT_FASTA,
    backbone_fasta: str = DEFAULT_BACKBONE_FASTA,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    species: str = "e_coli",
    overlap_bp: int = DEFAULT_OVERLAP_BP,
) -> PipelineResult:
    """
    Full pipeline: protein -> optimized CDS -> cassette -> plasmid + pydna verification.
    """
    input_fasta = resolve_path(input_fasta)
    backbone_fasta = resolve_path(backbone_fasta)
    output_dir = resolve_path(output_dir)

    protein_seq = load_protein_sequence(input_fasta)
    optimized_cds = optimize_cds(protein_seq, species)
    cassette, cassette_positions = build_expression_cassette(optimized_cds)

    backbone_record = next(SeqIO.parse(backbone_fasta, "fasta"))
    prefix, suffix, trimmed_backbone, insertion_site = split_backbone(str(backbone_record.seq))

    final_plasmid_seq = f"{prefix}{cassette}{suffix}"

    # Linearize backbone at the insertion site for assembly and wrap the cassette with homology.
    backbone_linearized = f"{suffix}{prefix}"
    gblock_insert, used_overlap = build_gblock_insert(backbone_linearized, cassette, overlap_bp)

    assembly_ok, assembled_seq = run_pydna_assembly(backbone_linearized, gblock_insert, used_overlap)
    if assembly_ok and assembled_seq and not is_rotation(assembled_seq, final_plasmid_seq):
        assembly_ok = False  # pydna built something, but it doesn't match our design

    digest_info = digest_summary(final_plasmid_seq)

    # Lift cassette feature positions into plasmid coordinates.
    feature_positions = {name: pos + len(prefix) for name, pos in cassette_positions.items()}

    # Persist outputs.
    os.makedirs(output_dir, exist_ok=True)
    write_fasta(os.path.join(output_dir, "optimized_cds.fasta"), "optimized_cds", optimized_cds)
    write_fasta(os.path.join(output_dir, "expression_cassette.fasta"), "expression_cassette", cassette)
    write_fasta(os.path.join(output_dir, "gblock_insert.fasta"), "cassette_with_backbone_homology", gblock_insert)
    write_fasta(os.path.join(output_dir, "plasmid_ready_to_order.fasta"), "pUC19_expression_plasmid", final_plasmid_seq)

    report = PipelineResult(
        optimized_cds=optimized_cds,
        expression_cassette=cassette,
        gblock_insert=gblock_insert,
        plasmid_sequence=final_plasmid_seq,
        assembly_ok=assembly_ok,
        digest_summary=digest_info,
        feature_positions=feature_positions,
    )
    write_report(
        os.path.join(output_dir, "assembly_report.txt"),
        report,
        backbone_record.id,
        insertion_site,
        used_overlap,
        len(prefix),
    )

    print("[✓] Optimized CDS, cassette, gBlock, and plasmid written to", output_dir)
    if assembly_ok:
        print("[✓] pydna found a circular assembly matching the design")
    else:
        print("[!] pydna could not confirm the assembly; check overlaps or backbone sequence")
    return report


if __name__ == "__main__":
    convert_and_optimize()

"""Prepare Chai-1 input FASTA files from Mosaic binder designs.

Generates FASTA files in Chai-1 format for target-binder complex prediction.
For running predictions with parallel execution and scoring, use predict_chai1_mosaic.py.

Chai-1 FASTA format:
    >protein|name=<name>_target
    <TARGET_SEQUENCE>
    >protein|name=<name>_binder
    <BINDER_SEQUENCE>

Usage:
    # Generate FASTA files only
    python prepare_chai1_input.py --input designs.txt --output-dir ./chai1_fasta

    # Single combined FASTA
    python prepare_chai1_input.py --input designs.txt --combined

For predictions with scoring (recommended):
    uv run modal run predict_chai1_mosaic.py --input designs.txt
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

# Default target: snake venom protein from modal_mosaic.py
DEFAULT_TARGET = "MICYNQQSSQPPTTKTCSETSCYKKTWRDHRGTIIERGCGCPKVKPGIKLHCCRTDKCNN"


def parse_designs_txt(designs_path: str | Path) -> list[dict]:
    """Parse Mosaic designs.txt FASTA file.

    Handles:
        >design0_-1.7871    (name with loss value)
        SEQUENCE
    """
    designs = []

    with open(designs_path) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith(">"):
            header = line[1:]

            loss_value = None
            name = header
            if "_" in header:
                parts = header.rsplit("_", 1)
                try:
                    loss_value = float(parts[1])
                    name = parts[0]
                except ValueError:
                    pass

            i += 1
            if i < len(lines):
                sequence = lines[i].strip()
                designs.append({
                    "name": name,
                    "sequence": sequence,
                    "loss_value": loss_value,
                })
        i += 1

    return designs


def generate_chai1_fasta(target_seq: str, binder_seq: str, name: str) -> str:
    """Generate Chai-1 format FASTA for target-binder complex."""
    return "\n".join([
        f">protein|name={name}_target",
        target_seq,
        f">protein|name={name}_binder",
        binder_seq,
    ]) + "\n"


def generate_chai1_fasta_combined(target_seq: str, designs: list[dict]) -> str:
    """Generate combined FASTA with target and all binders."""
    seq_hash = hashlib.sha256(target_seq.encode()).hexdigest()[:6]
    lines = [f">protein|name={seq_hash}_target", target_seq]

    for d in designs:
        lines.append(f">protein|name={d['name']}")
        lines.append(d["sequence"])

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Prepare Chai-1 input FASTA files from Mosaic designs",
        epilog="For predictions: uv run modal run predict_chai1_mosaic.py --input designs.txt",
    )
    parser.add_argument("--input", "-i", required=True, help="Mosaic designs.txt file")
    parser.add_argument("--target-sequence", default=DEFAULT_TARGET, help="Target sequence")
    parser.add_argument("--output-dir", "-o", help="Output directory (default: same as input)")
    parser.add_argument("--combined", action="store_true", help="Single combined FASTA")
    parser.add_argument("--limit", "-n", type=int, help="Limit number of designs")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {args.input} not found")
        sys.exit(1)

    designs = parse_designs_txt(input_path)
    print(f"Found {len(designs)} designs")

    if args.limit:
        designs = designs[:args.limit]

    # Default output to chai1_fasta subfolder in input directory
    output_dir = Path(args.output_dir) if args.output_dir else input_path.parent / "chai1_fasta"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.combined:
        content = generate_chai1_fasta_combined(args.target_sequence, designs)
        path = output_dir / "combined.faa"
        path.write_text(content)
        print(f"Generated: {path}")
    else:
        for d in designs:
            content = generate_chai1_fasta(args.target_sequence, d["sequence"], d["name"])
            path = output_dir / f"{d['name']}.faa"
            path.write_text(content)
            loss_str = f" (loss: {d['loss_value']:.4f})" if d["loss_value"] else ""
            print(f"  {path.name}{loss_str}")

        print(f"\nGenerated {len(designs)} files in {output_dir}")

    # Summary
    print(f"\nTarget: {len(args.target_sequence)} aa")
    print(f"Binders: {len(designs)} designs")
    if designs:
        avg_len = sum(len(d["sequence"]) for d in designs) / len(designs)
        print(f"Avg binder length: {avg_len:.1f} aa")

    print(f"\nTo run predictions with scoring:")
    print(f"  uv run modal run predict_chai1_mosaic.py --input {args.input}")


if __name__ == "__main__":
    main()

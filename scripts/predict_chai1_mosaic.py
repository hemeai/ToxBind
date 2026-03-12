"""Chai-1 structure prediction for Mosaic binder designs via foldism.

Generates FASTA files from Mosaic designs and runs predictions using foldism.py.
Extracts confidence scores and generates results CSV.

Usage:
    # Predict all designs
    python predict_chai1_mosaic.py --input designs.txt

    # Limit to first N designs
    python predict_chai1_mosaic.py --input designs.txt --limit 5

    # Custom target sequence
    python predict_chai1_mosaic.py --input designs.txt --target "SEQUENCE"

    # Use different algorithm
    python predict_chai1_mosaic.py --input designs.txt --algorithm boltz2
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Default target: snake venom protein (from modal_mosaic.py)
DEFAULT_TARGET = "MICYNQQSSQPPTTKTCSETSCYKKTWRDHRGTIIERGCGCPKVKPGIKLHCCRTDKCNN"

# Path to foldism script
FOLDISM_SCRIPT = Path(__file__).parent / "foldism" / "foldism.py"


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class Design:
    """A binder design from Mosaic output."""
    name: str
    sequence: str
    loss_value: float | None = None


# =============================================================================
# Input Parsing
# =============================================================================


def parse_designs_txt(designs_path: str | Path) -> list[Design]:
    """Parse Mosaic designs.txt FASTA file."""
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
                designs.append(Design(name=name, sequence=sequence, loss_value=loss_value))
        i += 1

    return designs


def generate_fasta(target_seq: str, binder_seq: str, name: str) -> str:
    """Generate standard FASTA for target-binder complex.

    Foldism handles conversion to Chai-1/Boltz-2 format internally.
    """
    return "\n".join([
        f">{name}_target",
        target_seq,
        f">{name}_binder",
        binder_seq,
    ]) + "\n"


# =============================================================================
# Score Extraction
# =============================================================================


def check_cached_results(results_dir: Path, design_name: str, algorithm: str) -> bool:
    """Check if results already exist locally."""
    if algorithm == "chai1":
        # Check for score file
        score_file = results_dir / design_name / f"{design_name}.chai1.scores.json"
        if score_file.exists():
            return True
        # Check alternate locations
        for f in results_dir.rglob(f"{design_name}.chai1.scores.json"):
            return True
    elif algorithm == "boltz2":
        for f in results_dir.rglob(f"confidence_*{design_name}*.json"):
            return True
        # Check by directory
        if (results_dir / design_name).exists():
            for f in (results_dir / design_name).rglob("confidence_*.json"):
                return True
    elif algorithm in ("protenix", "protenix-mini"):
        for f in results_dir.rglob(f"summary_confidence_*{design_name}*.json"):
            return True
    return False


def extract_scores_from_results(results_dir: Path, design_name: str, algorithm: str) -> dict:
    """Extract scores from foldism output."""
    scores = {}

    # Look for score files based on algorithm
    if algorithm == "chai1":
        score_file = results_dir / design_name / f"{design_name}.chai1.scores.json"
        if not score_file.exists():
            # Try alternate locations
            for f in results_dir.rglob(f"{design_name}.chai1.scores.json"):
                score_file = f
                break
            # Try any chai1 scores.json
            if not score_file.exists():
                for f in results_dir.rglob("*.chai1.scores.json"):
                    if design_name in str(f):
                        score_file = f
                        break

        if score_file.exists():
            data = json.loads(score_file.read_text())
            scores["aggregate_score"] = data.get("aggregate_score", [None])[0] if isinstance(data.get("aggregate_score"), list) else data.get("aggregate_score")
            scores["ptm"] = data.get("ptm", [None])[0] if isinstance(data.get("ptm"), list) else data.get("ptm")
            scores["iptm"] = data.get("iptm", [None])[0] if isinstance(data.get("iptm"), list) else data.get("iptm")

    elif algorithm == "boltz2":
        for f in results_dir.rglob("confidence_*.json"):
            if design_name in str(f):
                data = json.loads(f.read_text())
                scores["confidence_score"] = data.get("confidence_score")
                scores["ptm"] = data.get("ptm")
                scores["iptm"] = data.get("iptm")
                break

    elif algorithm in ("protenix", "protenix-mini"):
        for f in results_dir.rglob("summary_confidence_*.json"):
            if design_name in str(f):
                data = json.loads(f.read_text())
                scores["ranking_score"] = data.get("ranking_score")
                scores["ptm"] = data.get("ptm")
                scores["iptm"] = data.get("iptm")
                break

    return scores


# =============================================================================
# Foldism Runner
# =============================================================================


def run_foldism(fasta_path: Path, output_dir: Path, algorithm: str, use_msa: bool = True) -> bool:
    """Run foldism.py on a FASTA file."""
    foldism_script = FOLDISM_SCRIPT.resolve()
    foldism_dir = foldism_script.parent

    if not foldism_script.exists():
        print(f"Error: foldism.py not found at {foldism_script}")
        return False

    # Use absolute paths for Modal
    fasta_abs = fasta_path.resolve()
    output_abs = output_dir.resolve()

    cmd = [
        "uv", "run", "modal", "run", "foldism.py",
        "--input-faa", str(fasta_abs),
        "--algorithms", algorithm,
        "--out-dir", str(output_abs),
    ]

    if not use_msa:
        cmd.append("--use-msa=false")

    print(f"  Running: {' '.join(cmd[-6:])}")

    try:
        # Run from foldism directory so it can find index.html
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=foldism_dir)
        if result.returncode != 0:
            print(f"  Error: {result.stderr[:200] if result.stderr else 'Unknown error'}")
            return False
        return True
    except FileNotFoundError:
        print("Error: 'uv' or 'modal' command not found")
        return False


# =============================================================================
# Main Pipeline
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Run structure predictions on Mosaic binder designs via foldism",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python predict_chai1_mosaic.py --input out/mosaic/20260201/designs.txt
    python predict_chai1_mosaic.py --input designs.txt --algorithm boltz2
    python predict_chai1_mosaic.py --input designs.txt --limit 5 --no-msa
        """,
    )
    parser.add_argument("--input", "-i", required=True, help="Mosaic designs.txt file")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="Target protein sequence")
    parser.add_argument("--output-dir", "-o", help="Output directory (default: <input_dir>/predictions)")
    parser.add_argument("--algorithm", "-a", default="chai1",
                        choices=["chai1", "boltz2", "protenix", "protenix-mini", "alphafold2"],
                        help="Folding algorithm (default: chai1)")
    parser.add_argument("--limit", "-n", type=int, help="Limit number of designs")
    parser.add_argument("--no-msa", action="store_true", help="Disable MSA (faster but less accurate)")

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {args.input} not found")
        sys.exit(1)

    # Parse designs
    designs = parse_designs_txt(input_path)
    print(f"Found {len(designs)} designs in {input_path.name}")

    if args.limit:
        designs = designs[:args.limit]
        print(f"Processing first {args.limit} designs")

    # Setup directories
    base_dir = Path(args.output_dir) if args.output_dir else input_path.parent / "predictions"
    fasta_dir = base_dir / "fasta"
    results_dir = base_dir / "results"
    fasta_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Generate FASTA files
    print(f"\nGenerating FASTA files in {fasta_dir}")
    fasta_files = []
    for d in designs:
        content = generate_fasta(args.target, d.sequence, d.name)
        fasta_path = fasta_dir / f"{d.name}.faa"
        fasta_path.write_text(content)
        fasta_files.append((d, fasta_path))
        print(f"  {fasta_path.name}")

    # Run predictions
    print(f"\nRunning {args.algorithm} predictions via foldism")
    print(f"{'='*60}")

    all_results = []
    cached_count = 0
    for design, fasta_path in fasta_files:
        print(f"\n[{design.name}]")

        # Check if results already cached locally
        if check_cached_results(results_dir, design.name, args.algorithm):
            print(f"  Using cached results")
            success = True
            cached_count += 1
        else:
            success = run_foldism(fasta_path, results_dir, args.algorithm, use_msa=not args.no_msa)

        # Extract scores
        scores = {}
        if success:
            scores = extract_scores_from_results(results_dir, design.name, args.algorithm)

        result = {
            "design_name": design.name,
            "binder_sequence": design.sequence,
            "loss_value": design.loss_value,
            "binder_length": len(design.sequence),
            "algorithm": args.algorithm,
            "success": success,
            **scores,
        }
        all_results.append(result)

        # Print score summary
        if scores:
            score_key = "aggregate_score" if args.algorithm == "chai1" else "confidence_score" if args.algorithm == "boltz2" else "ranking_score"
            score_val = scores.get(score_key)
            if score_val is not None:
                print(f"  {score_key}: {score_val:.4f}")

    # Write results CSV
    csv_path = base_dir / f"results_{args.algorithm}.csv"

    # Determine fieldnames based on algorithm
    base_fields = ["design_name", "loss_value", "binder_length", "success"]
    if args.algorithm == "chai1":
        score_fields = ["aggregate_score", "ptm", "iptm"]
    elif args.algorithm == "boltz2":
        score_fields = ["confidence_score", "ptm", "iptm"]
    else:
        score_fields = ["ranking_score", "ptm", "iptm"]

    fieldnames = base_fields + score_fields

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_results)

    # Write full results JSON
    json_path = base_dir / f"results_{args.algorithm}_full.json"
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"Algorithm: {args.algorithm}")
    print(f"Total designs: {len(designs)}")
    print(f"Successful: {sum(1 for r in all_results if r.get('success'))}")
    if cached_count > 0:
        print(f"From cache: {cached_count}")
    print(f"Results CSV: {csv_path}")
    print(f"Full results: {json_path}")

    # Print top designs
    score_key = "aggregate_score" if args.algorithm == "chai1" else "confidence_score" if args.algorithm == "boltz2" else "ranking_score"
    successful = [r for r in all_results if r.get(score_key) is not None]
    if successful:
        successful.sort(key=lambda x: x[score_key], reverse=True)
        print(f"\nTop 5 designs by {score_key} (higher is better):")
        for r in successful[:5]:
            loss_str = f", loss={r['loss_value']:.4f}" if r.get("loss_value") else ""
            print(f"  {r['design_name']}: {r[score_key]:.4f}{loss_str}")


if __name__ == "__main__":
    main()

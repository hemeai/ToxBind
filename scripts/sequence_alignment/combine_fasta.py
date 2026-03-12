import argparse
from pathlib import Path
from Bio import SeqIO


def combine_fastas(input_folder, output_file, recursive=False, remove_duplicates=False):
    input_folder = Path(input_folder)

    if not input_folder.exists():
        raise FileNotFoundError(f"Input folder '{input_folder}' does not exist.")

    # Choose search method
    if recursive:
        fasta_files = (
            list(input_folder.rglob("*.fa"))
            + list(input_folder.rglob("*.fasta"))
            + list(input_folder.rglob("*.fna"))
        )
    else:
        fasta_files = (
            list(input_folder.glob("*.fa"))
            + list(input_folder.glob("*.fasta"))
            + list(input_folder.glob("*.fna"))
        )

    print(f"Found {len(fasta_files)} FASTA files")

    seen_ids = set()
    total_written = 0

    with open(output_file, "w") as out_handle:
        for file in fasta_files:
            print(f"Reading {file.name}")
            for record in SeqIO.parse(file, "fasta"):
                if remove_duplicates:
                    if record.id in seen_ids:
                        continue
                    seen_ids.add(record.id)

                SeqIO.write(record, out_handle, "fasta")
                total_written += 1

    print(f"\nTotal sequences written: {total_written}")
    print(f"Combined FASTA written to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Combine multiple FASTA files into one using Biopython."
    )

    parser.add_argument(
        "-i", "--input", required=True, help="Path to folder containing FASTA files"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="combined.fasta",
        help="Output FASTA file name (default: combined.fasta)",
    )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search subdirectories recursively",
    )

    parser.add_argument(
        "-d", "--deduplicate", action="store_true", help="Remove duplicate sequence IDs"
    )

    args = parser.parse_args()

    combine_fastas(
        args.input,
        args.output,
        recursive=args.recursive,
        remove_duplicates=args.deduplicate,
    )

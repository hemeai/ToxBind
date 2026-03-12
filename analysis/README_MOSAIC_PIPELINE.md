# Mosaic iPAE Scoring Pipeline

This document explains how to calculate iPAE scores for Mosaic-generated binder designs.

## Background

### BindCraft vs Mosaic Output Differences

| Aspect | BindCraft | Mosaic |
|--------|-----------|--------|
| **Output Format** | `final_design_stats.csv` | `designs.txt` (FASTA) |
| **Sequences Included** | Target + Binder (separate columns) | Binder only |
| **Metadata** | Multiple metrics (pTM, pAE, RMSD, etc.) | Loss value only |
| **Processing Pipeline** | `combine_outputs.py` → `get_ipae_score.py` | `get_ipae_score_mosaic.py` |

### Key Incompatibility

- **BindCraft**: Outputs comprehensive CSV with both target and binder sequences
- **Mosaic**: Outputs minimal FASTA file with only binder sequences and loss values
- **Solution**: `get_ipae_score_mosaic.py` adds the target sequence from `modal_mosaic.py`

## Files

### New Scripts

1. **`get_ipae_score_mosaic.py`**: Main pipeline script
   - Reads `designs.txt` from Mosaic output
   - Adds target sequence (from `modal_mosaic.py`)
   - Generates FASTA files for AlphaFold
   - Runs AlphaFold predictions via Modal
   - Extracts iPAE scores
   - Saves results to CSV

2. **`process_latest_mosaic.sh`**: Helper script
   - Automatically finds the latest Mosaic output
   - Runs the iPAE scoring pipeline
   - Simplifies the workflow

## Usage

### Quick Start (Recommended)

Process the most recent Mosaic designs:

```bash
cd analysis
./process_latest_mosaic.sh
```

### Advanced Usage

#### 1. Process a Specific designs.txt File

```bash
python get_ipae_score_mosaic.py \
    --input-designs ../out/mosaic/2602011430/designs.txt
```

#### 2. Use a Different Target Sequence

```bash
python get_ipae_score_mosaic.py \
    --input-designs ../out/mosaic/2602011430/designs.txt \
    --target-sequence "YOUR_CUSTOM_TARGET_SEQUENCE"
```

#### 3. Skip AlphaFold (Extract from Existing Results)

```bash
python get_ipae_score_mosaic.py \
    --input-designs ../out/mosaic/2602011430/designs.txt \
    --skip-alphafold
```

#### 4. Change GPU Type

```bash
python get_ipae_score_mosaic.py \
    --input-designs ../out/mosaic/2602011430/designs.txt \
    --gpu A100
```

#### 5. Custom Output Location

```bash
python get_ipae_score_mosaic.py \
    --input-designs ../out/mosaic/2602011430/designs.txt \
    --output-csv ./my_results.csv \
    --fasta-dir ./my_fasta_files \
    --alphafold-results-dir ./my_alphafold_results
```

### Using the Helper Script

The helper script automatically finds the latest Mosaic output:

```bash
# Basic usage
./process_latest_mosaic.sh

# Skip AlphaFold runs
./process_latest_mosaic.sh --skip-alphafold

# Use different GPU
./process_latest_mosaic.sh --gpu A100

# Custom target sequence
./process_latest_mosaic.sh --target-seq "MICYNQQSSQPPTTKTCSETSCYKKTWRDHRGTIIERGCGCPKVKPGIKLHCCRTDKCNN"
```

## Command-Line Options

### `get_ipae_score_mosaic.py`

| Option | Default | Description |
|--------|---------|-------------|
| `--input-designs` | `../out/mosaic/latest/designs.txt` | Path to designs.txt from Mosaic |
| `--target-sequence` | From `modal_mosaic.py` | Target protein sequence |
| `--output-csv` | `./results_ipae_mosaic.csv` | Output CSV file path |
| `--fasta-dir` | `./fasta_files_mosaic` | Directory for FASTA files |
| `--alphafold-results-dir` | `./alphafold_results` | Directory for AlphaFold results |
| `--modal-script` | `./modal_alphafold.py` | Path to modal_alphafold.py |
| `--gpu` | `H100` | GPU type for Modal (H100, A100, etc.) |
| `--skip-alphafold` | False | Skip AlphaFold, only extract scores |

## Output Files

### Primary Outputs

1. **`results_ipae_mosaic.csv`**: iPAE scores summary
   - Columns: `Design`, `ipae_score`, `loss_value`
   - Sorted by iPAE score (lower is better)

2. **`results_ipae_mosaic_complete.csv`**: Full results
   - Includes all sequences and metadata
   - Columns: `Design`, `Sequence`, `TargetSequence`, `LossValue`, `ipae_score`

### Intermediate Files

- **`fasta_files_mosaic/`**: Generated FASTA files for AlphaFold
- **`alphafold_results/`**: AlphaFold prediction results (ZIP files)

## Workflow Example

```bash
# 1. Run Mosaic to generate designs
cd scripts
uvx modal run modal_mosaic.py --workers 4 --max-time-hours 2.0

# 2. Process the results to calculate iPAE scores
cd ../analysis
./process_latest_mosaic.sh

# 3. View the top designs
head -20 results_ipae_mosaic.csv
```

## Understanding the Results

### iPAE Score

- **Lower is better**: Indicates more confident binding prediction
- Measured in Ångströms (Å)
- Typical good values: < 5 Å
- Represents expected position error at the target-binder interface

### Loss Value (from Mosaic)

- **More negative is better**: Indicates better optimization
- Combines multiple objectives:
  - Binder-target contact
  - Within-binder contact
  - Inverse folding sequence recovery
  - PAE metrics
  - pTM and pLDDT

### Interpreting Both Metrics

- **Best designs**: Low iPAE score + low (negative) loss value
- **Loss value** = optimization objective during design
- **iPAE score** = validation via AlphaFold prediction

## Troubleshooting

### "designs.txt not found"

```bash
# List available Mosaic outputs
ls -la ../out/mosaic/

# Manually specify the correct path
python get_ipae_score_mosaic.py \
    --input-designs ../out/mosaic/YOUR_DATE_FOLDER/designs.txt
```

### "modal command not found"

```bash
# Install Modal
pip install modal

# Or use uv
uv pip install modal
```

### "No result zip file found"

This means AlphaFold hasn't run yet or failed:

```bash
# Check AlphaFold results directory
ls -la ./alphafold_results/

# Run without --skip-alphafold flag
python get_ipae_score_mosaic.py --input-designs YOUR_FILE.txt
```

### Custom Target Sequence

If you modified the target in `modal_mosaic.py`, update it:

```bash
python get_ipae_score_mosaic.py \
    --target-sequence "YOUR_NEW_TARGET_SEQUENCE"
```

## Comparison with BindCraft Pipeline

### BindCraft Workflow

```bash
cd analysis
python combine_outputs.py      # Combines CSV + extracts PDB sequences
python get_ipae_score.py        # Calculates iPAE scores
python result_analysis.py       # Final analysis
```

### Mosaic Workflow

```bash
cd analysis
python get_ipae_score_mosaic.py # All-in-one: parse FASTA, add target, calculate iPAE
# Or use the helper:
./process_latest_mosaic.sh
```

## Target Sequence

The default target sequence (from `modal_mosaic.py:34`):

```
MICYNQQSSQPPTTKTCSETSCYKKTWRDHRGTIIERGCGCPKVKPGIKLHCCRTDKCNN
```

This is a snake venom protein sequence. If you're targeting a different protein, use `--target-sequence`.

## Notes

- AlphaFold results are cached - rerunning won't recompute existing results
- FASTA files are kept for debugging and manual inspection
- The script is compatible with the same `modal_alphafold.py` used by BindCraft
- Results are automatically sorted by iPAE score for easy review

## Integration with Existing Analysis

To merge Mosaic results with BindCraft results:

```python
import pandas as pd

# Load both results
bindcraft_results = pd.read_csv('results_ipae.csv')
mosaic_results = pd.read_csv('results_ipae_mosaic.csv')

# Add method column
bindcraft_results['Method'] = 'BindCraft'
mosaic_results['Method'] = 'Mosaic'

# Combine
combined = pd.concat([bindcraft_results, mosaic_results], ignore_index=True)
combined.to_csv('results_combined_all_methods.csv', index=False)
```

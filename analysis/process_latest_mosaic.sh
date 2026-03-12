#!/bin/bash
# Helper script to process the latest Mosaic designs with iPAE scoring
#
# Usage:
#   ./process_latest_mosaic.sh [OPTIONS]
#
# Options:
#   --skip-alphafold    Skip running AlphaFold (only extract from existing results)
#   --gpu TYPE          GPU type for Modal (default: H100)
#   --target-seq SEQ    Custom target sequence (default: from modal_mosaic.py)

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Mosaic iPAE Score Processing Pipeline${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Find the latest mosaic output directory
MOSAIC_OUT_DIR="../out/mosaic"

if [ ! -d "$MOSAIC_OUT_DIR" ]; then
    echo -e "${RED}Error: Mosaic output directory not found: $MOSAIC_OUT_DIR${NC}"
    exit 1
fi

# Find the most recent subdirectory (sorted by name, which corresponds to timestamp)
LATEST_DIR=$(find "$MOSAIC_OUT_DIR" -mindepth 1 -maxdepth 1 -type d | sort -r | head -n 1)

if [ -z "$LATEST_DIR" ]; then
    echo -e "${RED}Error: No mosaic output directories found in $MOSAIC_OUT_DIR${NC}"
    exit 1
fi

DESIGNS_FILE="$LATEST_DIR/designs.txt"

if [ ! -f "$DESIGNS_FILE" ]; then
    echo -e "${RED}Error: designs.txt not found in $LATEST_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}Found latest designs:${NC} $DESIGNS_FILE"
echo -e "${GREEN}Number of designs:${NC} $(grep -c '^>' $DESIGNS_FILE)\n"

# Run the iPAE scoring pipeline
echo -e "${BLUE}Running iPAE scoring pipeline...${NC}\n"

python get_ipae_score_mosaic.py \
    --input-designs "$DESIGNS_FILE" \
    "$@"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Processing complete!${NC}"
echo -e "${GREEN}========================================${NC}"

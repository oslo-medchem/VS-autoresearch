#!/usr/bin/env bash
# Reproduce the full VS-autoresearch pipeline from scratch.
#
# Prerequisites:
#   conda env create -f environment.yml
#   conda activate vs_autoresearch
#   Uni-Dock installed and on PATH (or set UNIDOCK_BIN)
#
# Usage:
#   bash prepare_all.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "  VS-autoresearch: Full pipeline reproduction"
echo "============================================"
echo

# --- Stage 1: Fetch and curate actives ---
echo ">>> Stage 1: Active compound curation"
cd "$REPO_ROOT/01_active_curation"
python fetch_fpr2_actives.py
python curate_actives.py
echo

# --- Stage 2: Generate decoys ---
echo ">>> Stage 2: Property-matched decoy generation"
cd "$REPO_ROOT/02_decoy_generation"
python generate_decoys.py
echo

# --- Stage 3: Library preparation ---
echo ">>> Stage 3: Ligand library preparation"
cd "$REPO_ROOT/03_library_preparation"
python prepare_combined_library.py

echo "  Preparing naive library (OpenBabel)..."
cd "$REPO_ROOT/03_library_preparation/naive"
python prepare_naive.py

echo "  Preparing skill library (Meeko + RDKit)..."
cd "$REPO_ROOT/03_library_preparation/skill"
python prepare_skill.py
echo

# --- Stage 4: Receptor preparation ---
echo ">>> Stage 4: Receptor preparation"
cd "$REPO_ROOT/04_receptor_preparation"
python prepare_structures.py
echo

echo "============================================"
echo "  Pipeline complete. Ready for docking."
echo "  Next: cd 05_autoresearch && python prepare.py"
echo "============================================"

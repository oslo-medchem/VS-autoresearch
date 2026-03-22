# VS-autoresearch

**Autonomous Optimisation of Structure-Based Virtual Screening Protocols Using an LLM Coding Agent**

An LLM coding agent (Claude Code, Anthropic) autonomously executed 26 docking experiments across two structurally diverse targets—FPR2 (GPCR) and CDK2 (kinase)—systematically varying scoring functions, ligand and receptor preparation protocols, search exhaustiveness, box size, and post-docking transforms. On FPR2, Vinardo scoring improved AUC from 0.736 to 0.748 (+0.012). On CDK2, switching to an unfiltered ligand library improved AUC from 0.677 to 0.735 (+0.058). Optimal parameters were target-dependent: the preferred scoring function and library preparation reversed between targets.

## Results Summary

### FPR2 (GPCR, PDB 7T6S, 3.0 Å cryo-EM) — 10 experiments, ~55 GPU-hours

| # | Experiment | AUC | Delta AUC | Decision |
|---|-----------|-----|----------|----------|
| 0 | Baseline (Vina) | 0.736 | -- | baseline |
| 1 | Vinardo scoring | **0.748** | **+0.012** | **kept** |
| 2 | Box 20 Å | 0.745 | -0.003 | reverted |
| 3 | Naive library | n/a | n/a | reverted |
| 4 | Rank transform | 0.744 | 0.000 | reverted |
| 5 | Exhaustiveness 16 | 0.744 | -0.004 | reverted |
| 6 | Naive receptor | 0.732 | -0.016 | reverted |
| 7 | MW correction | 0.702 | -0.046 | reverted |
| 8 | Multi-pose top-3 | 0.715 | -0.033 | reverted |
| 9 | Multi-pose Boltzmann | 0.730 | -0.018 | reverted |

### CDK2 (kinase, PDB 6INL, 1.74 Å X-ray) — 16 experiments, ~6 GPU-hours

| # | Experiment | AUC | Delta AUC | Decision |
|---|-----------|-----|----------|----------|
| 0 | Baseline (Vinardo, skill) | 0.677 | -- | baseline |
| 1 | Naive library | **0.716** | **+0.039** | **kept** |
| 2 | Vina scoring | **0.735** | **+0.019** | **kept** |
| 3 | Exhaustiveness 16 | 0.730 | -0.005 | reverted |
| 4 | Box 30 Å | 0.728 | -0.007 | reverted |
| 5 | Box 20 Å | 0.725 | -0.010 | reverted |
| 6 | Naive receptor | 0.732 | -0.003 | reverted |
| 7 | Rank normalisation | 0.735 | 0.000 | reverted |
| 8 | Exhaustiveness 32 | 0.724 | -0.011 | reverted |
| 9 | MW correction | 0.720 | -0.015 | reverted |
| 10 | Vinardo (re-test) | 0.716 | -0.019 | reverted |
| 11 | Skill library (swap) | 0.680 | -0.055 | reverted |
| 12 | Batch size 50 | **0.735** | **0.000** | **kept** |
| 13 | Multi-pose top-3 | 0.729 | -0.006 | reverted |
| 14 | Exhaustiveness 4 | 0.729 | -0.006 | reverted |
| 15 | Log transform | 0.735 | 0.000 | reverted |

## Repository Structure

```
VS-autoresearch/
├── 01_active_curation/       # ChEMBL FPR2 active compound curation
├── 02_decoy_generation/      # Property-matched decoy generation
├── 03_library_preparation/   # FPR2 ligand preparation (naive + skill protocols)
├── 04_receptor_preparation/  # FPR2 receptor structure preparation
├── 05_autoresearch/          # FPR2 autoresearch loop (agent code + logs)
├── 06_manuscript/            # Publication materials (figures, DOCX)
├── 07_cdk2_autoresearch/     # CDK2 autoresearch loop (agent code + logs)
├── skill/                    # Virtual screening pipeline skill file
├── prepare_all.sh            # Regenerate all data from scratch
├── environment.yml           # Conda environment specification
└── LICENSE                   # MIT
```

## Quick Start

### 1. Create the environment

```bash
conda env create -f environment.yml
conda activate vs_autoresearch
```

[Uni-Dock](https://github.com/dptech-corp/Uni-Dock) must be installed separately (requires NVIDIA GPU + CUDA).

### 2. Regenerate PDBQT libraries (optional)

PDBQT files are excluded from the repository. Regenerate from SMILES:

```bash
bash prepare_all.sh
```

### 3. Run the autoresearch loop

```bash
# FPR2
cd 05_autoresearch
python prepare.py && python experiment.py

# CDK2
cd 07_cdk2_autoresearch
python prepare.py && python experiment.py
```

## Targets

| Target | Protein | PDB | Resolution | Method | Library |
|--------|---------|-----|-----------|--------|---------|
| FPR2 | Formyl peptide receptor 2 (GPCR) | 7T6S | 3.0 Å | cryo-EM | 573 actives + ~4,600 decoys |
| CDK2 | Cyclin-dependent kinase 2 | 6INL | 1.74 Å | X-ray | 474 actives + 2,000 decoys |

## Computational Setup

- **Docking engine**: Uni-Dock (GPU-accelerated AutoDock Vina)
- **GPU**: NVIDIA RTX 4500 Ada (24 GB VRAM), single (FPR2) or dual (CDK2)
- **Agent**: Claude Code (Anthropic, claude-opus-4-6)
- **Total compute**: ~61 GPU-hours across 26 experiments

## Citation

If you use this work, please cite:

> Gani, O. Autonomous Optimisation of Structure-Based Virtual Screening Protocols Using an LLM Coding Agent. *Digital Discovery*, 2026, submitted.

## Licence

MIT. See [LICENSE](LICENSE).

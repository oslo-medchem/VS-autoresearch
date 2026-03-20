# Stage 3: Ligand Library Preparation

Combines actives and decoys into a shuffled library and prepares 3D structures as PDBQT files using two protocols.

## Scripts

- **prepare_combined_library.py** -- Merges actives + decoys, shuffles, creates ground truth labels
- **naive/prepare_naive.py** -- OpenBabel: gen3d + PDBQT conversion (baseline protocol)
- **skill/prepare_skill.py** -- RDKit ETKDGv3 conformer generation + Meeko PDBQT preparation + PAINS/Brenk filtering (optimised protocol)

## Output

- **library_combined.smi** -- Shuffled combined library (actives + decoys)
- **library_labels.csv** -- Ground truth labels (compound_id, label, smiles)
- **naive/pdbqt/** -- PDBQT files from OpenBabel (10,752 compounds; gitignored)
- **skill/pdbqt/** -- PDBQT files from Meeko (5,223 compounds after filtering; gitignored)

## Regenerating PDBQT files

PDBQT directories are excluded from git. Regenerate with:

```bash
conda activate vs_autoresearch
cd naive && python prepare_naive.py
cd ../skill && python prepare_skill.py
```

The skill protocol produces fewer files because PAINS/Brenk filters remove problematic compounds.

# Stage 4: Receptor Preparation

Prepares the FPR2 receptor structure for docking.

## Files

- **7T6S.pdb** -- Original cryo-EM structure (3.0 A resolution)
- **receptor_chainR.pdb** -- Extracted chain R (FPR2)
- **ligand_FUI_crystal.sdf** -- Co-crystallised ligand (Compound C43 / FUI)
- **ligand_center.txt** -- Binding site centre coordinates (81.893, 115.414, 96.832)
- **receptor_skill.pdbqt** -- Meeko mk_prepare_receptor output
- **receptor_naive.pdbqt** -- OpenBabel PDBQT conversion output

## Script

- **prepare_structures.py** -- Extracts chain R from 7T6S, isolates the co-crystallised ligand, and computes the binding site centre

## Usage

```bash
conda activate vs_autoresearch
python prepare_structures.py
```

The pre-prepared PDBQT files are included in the repository. Regenerate with Meeko or OpenBabel if needed.

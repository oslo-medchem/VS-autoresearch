# Stage 2: Property-Matched Decoy Generation

Generates property-matched decoys for the virtual screening benchmark following the DUD-E methodology.

## Script

- **generate_decoys.py** -- Downloads drug-like molecules from ChEMBL, matches against actives on five physicochemical properties (MW, LogP, HBD, HBA, RotBond), and selects 10 decoys per active

## Output

- **decoys_10000.smi** -- 10,000 property-matched decoy SMILES

## Usage

```bash
conda activate vs_autoresearch
python generate_decoys.py
```

Requires `chembl-webresource-client`, `rdkit`, and `numpy`.

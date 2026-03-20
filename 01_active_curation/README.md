# Stage 1: Active Compound Curation

Fetches FPR2 (CHEMBL4227) active compounds from ChEMBL 34 and curates them into a diverse, drug-like set.

## Scripts

- **fetch_fpr2_actives.py** -- Queries ChEMBL for FPR2 bioactivity data (pChEMBL >= 5.0)
- **curate_actives.py** -- Standardises structures, removes duplicates, applies drug-likeness filters, clusters by Tanimoto similarity, and diversity-selects 1,000 compounds

## Output

- **actives_1000.smi** -- 1,000 diverse active SMILES (used in library preparation)
- **actives_curated.csv** -- Full curated dataset with molecular properties

## Usage

```bash
conda activate vs_autoresearch
python fetch_fpr2_actives.py    # Downloads from ChEMBL API
python curate_actives.py        # Produces actives_1000.smi
```

Requires `chembl-webresource-client` and `rdkit`.

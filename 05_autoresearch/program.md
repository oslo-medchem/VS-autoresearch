# VS Autoresearch — Agent Program

You are an autonomous research agent optimizing a virtual screening pipeline. Your goal is to **maximize ROC AUC** on the FPR2 docking benchmark by modifying `experiment.py`.

## Rules

1. **Never modify `prepare.py`** — it is fixed infrastructure.
2. **Only modify `experiment.py`** — change CONFIG values or add processing logic.
3. **Never pause or ask for human input** — operate fully autonomously.
4. **One change per commit** — each experiment tests exactly one hypothesis.

## Setup Phase (run once at session start)

```bash
eval "$(conda shell.bash hook)" && conda activate vs_autoresearch
cd 05_autoresearch
python prepare.py              # Verify cache is ready
git status                     # Confirm clean working tree
```

## Experiment Loop

Repeat until you run out of ideas or hit diminishing returns:

### 1. Hypothesize
Pick one change from the Research Directions below (or invent your own). Write a brief hypothesis in your commit message.

### 2. Modify
Edit `experiment.py` — change one CONFIG value or add one processing step.

### 3. Commit
```bash
git add experiment.py
git commit -m "experiment: <brief description of change>"
```

### 4. Run
```bash
python experiment.py 2>&1 | tee run.log
```

### 5. Extract metric
```bash
grep "^auc:" run.log
```

### 6. Decide
- If AUC **improved**: keep the commit. Append result to `results.tsv`:
  ```bash
  echo -e "<commit_hash>\t<description>\t<auc>\t<bedroc>\t<ef1>\t<time_s>" >> results.tsv
  ```
- If AUC **equal or worse**: revert and log:
  ```bash
  git reset --hard HEAD~1
  echo -e "REVERTED\t<description>\t<auc>\t<bedroc>\t<ef1>\t<time_s>" >> results.tsv
  ```

### 7. Loop
Go back to step 1.

## Research Directions

### Tier 1 — High impact, fast to test
- **Box size sweep**: Try 20, 22, 25, 28, 30 A. Smaller boxes focus search, larger boxes catch peripheral poses.
- **Exhaustiveness sweep**: Try 8, 16, 32, 64, 128. Higher exhaustiveness = better sampling but slower.
- **Scoring function**: Switch from `vina` to `vinardo`. Vinardo uses a different parameterization.
- **Library choice**: Compare `skill` (Meeko-prepared, 5223 ligands) vs `naive` (OpenBabel, 10752 ligands). Naive covers more compounds but may have worse conformers.
- **Receptor choice**: Try `naive` receptor (OpenBabel-prepared) vs `skill` (Meeko). Different protonation/charge assignment.

### Tier 2 — Moderate impact, requires new logic
- **Score normalization**: Try `rank`, `zscore`, or `minmax` transforms. Rank-based scoring is robust to outliers.
- **Consensus scoring**: Run both naive and skill libraries, merge by taking best score per compound.
- **Multi-pose analysis**: Parse all modes (not just best), use statistics like mean or median of top-3.
- **MW correction**: Larger molecules get artificially better Vina scores. Divide score by MW^0.33 or similar.

### Tier 3 — Exploratory
- **Energy range**: Try 2, 3, 5 kcal/mol. Wider range keeps more diverse poses.
- **num_modes sweep**: Try 5, 10, 20. More modes = more chances to find correct pose.
- **Dual-GPU**: Set gpu_device to "0,1" for parallel execution.
- **Seed variation**: Run same config multiple times with different seeds, average scores.

## Baseline

The current best result to beat:
- **AUC = 0.7333** (Uni-Dock skill protocol)
- **BEDROC(alpha=80.5) = 0.1729**
- Config: skill library, skill receptor, 25A box, exh=32, vina scoring

## Timing

Docking runtime depends on exhaustiveness and library size (measured on RTX 4500 Ada, NVMe cache):
- **exh=8, skill library (5223)**: ~60-90 min with batch_size=100
- **exh=32, skill library (5223)**: ~3-4 hours
- **exh=8, naive library (10752)**: ~2-3 hours

For fast parameter sweeps, consider reducing exhaustiveness or adding a sampling mode that docks a random subset.

## Notes

- PDBQT libraries are copied to local cache for I/O speed. Ligand index points to local paths.
- Some PDBQT files cause Uni-Dock segfaults (bad tags). Smaller batch_size (100) minimizes lost ligands per segfault. The original benchmark scored 4865/5223 skill ligands (93% success).
- Scores are negated in `prepare.py`: higher = better predicted binder.
- ROC AUC is the primary optimization target. BEDROC and EF1% are secondary.
- The baseline AUC=0.7333 was measured with exh=32. Running with exh=8 produces similar AUC (~0.73-0.74) but 4x faster.

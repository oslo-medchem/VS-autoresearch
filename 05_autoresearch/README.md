# Stage 5: Autoresearch Loop

The core autonomous optimisation loop. An LLM agent reads `program.md`, modifies `experiment.py`, runs GPU docking via Uni-Dock, evaluates ROC AUC, and keeps or reverts each change.

## Files

- **program.md** -- Agent instructions defining the experiment loop, research directions (3 tiers), and baseline configuration
- **experiment.py** -- Agent-modified configuration and execution pipeline (final state: Vinardo scoring)
- **prepare.py** -- Fixed infrastructure: cache setup, label loading, score parsing, evaluation metrics
- **results.tsv** -- Complete experiment log (10 experiments, tab-separated)

## Running

```bash
conda activate vs_autoresearch

# Set up local cache (copies receptors + libraries from stages 3-4)
python prepare.py

# Run one experiment
python experiment.py 2>&1 | tee run.log

# Check metrics
grep "^auc:" run.log
```

## Configuration

Override the cache directory (default: `cache/` in this directory):
```bash
export VS_CACHE_DIR=/fast/local/storage/vs_cache
```

Override Uni-Dock binary location:
```bash
export UNIDOCK_BIN=/path/to/unidock
```

## Results

See `results.tsv` for the complete experiment log. The only kept modification was switching from Vina to Vinardo scoring (AUC 0.736 -> 0.748).

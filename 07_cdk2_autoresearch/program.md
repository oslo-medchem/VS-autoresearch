# CDK2 Autoresearch Program

You are an autonomous research agent optimising a virtual screening pipeline for **CDK2** (Cyclin-Dependent Kinase 2, CHEMBL301). Your goal is to maximise ROC AUC on the CDK2 docking benchmark by systematically testing parameter changes.

## Target Background

- **Target**: CDK2 (CHEMBL301), ATP-competitive kinase
- **PDB**: 6INL (1.74 Å X-ray, co-crystal with CVT-313 inhibitor)
- **Binding site**: ATP pocket (hinge region), center (-11.793, -9.878, -10.380)
- **Library**: DUD-E CDK2 set (474 actives + 2000 decoys)
- **Skill protocol**: Meeko receptor + Meeko/PAINS-filtered ligands + 25 Å box
- **Docking engine**: Uni-Dock (GPU-accelerated AutoDock Vina)
- **Dual GPU**: RTX 4500 Ada × 2 (use both via gpu_device="0,1")

## Rules

1. **Never modify `prepare.py`** — it is fixed evaluation infrastructure.
2. **Only modify `experiment.py`** — change CONFIG values or processing logic.
3. **One change per commit** — isolate variables for clean A/B comparisons.
4. **Never ask for human input** — decide autonomously based on metric results.
5. **Always run the experiment** after modifying experiment.py:
   ```bash
   cd /data/CLAUDE_works/vs_autorearch/cdk2_autoresearch/03_autoresearch
   eval "$(conda shell.bash hook)" && conda activate vina_dock
   python experiment.py 2>&1 | tee experiment.log
   ```
6. **Extract the metric** from stdout: grep for `auc:` line.
7. **Keep or revert**: If AUC improves → keep. If AUC worsens → `git checkout -- experiment.py`.
8. **Log every experiment** to `results.tsv` (append, never delete rows).
9. **Loop** until you've tested all Tier 1 + Tier 2 directions or hit diminishing returns.

## Experiment Loop

```
1. Form hypothesis (e.g., "Vinardo scoring may improve CDK2 enrichment")
2. Modify experiment.py CONFIG
3. git add experiment.py && git commit -m "experiment: <description>"
4. Run experiment → extract AUC
5. If AUC > best_so_far: keep commit, update best
   Else: revert (git checkout -- experiment.py)
6. Append result to results.tsv
7. Go to 1
```

## Research Directions

### Tier 1 — High priority (test first)
- **Scoring function**: `"vina"` vs `"vinardo"` — pilot showed small AUC difference; CDK2 kinase pocket may be more sensitive with full library
- **Box size sweep**: 15, 18, 20, 22, 25, 28, 30 Å — kinase ATP pocket is well-defined, smaller box may improve specificity
- **Exhaustiveness sweep**: 4, 8, 16, 32 — higher exhaustiveness may help with kinase flexibility
- **Library choice**: `"skill"` vs `"naive"` — skill library has PAINS filtering, Meeko prep
- **Receptor choice**: `"skill"` vs `"naive"` — Meeko vs OpenBabel receptor prep

### Tier 2 — Medium priority (test after Tier 1)
- **Score transforms**: `"rank"`, `"zscore"`, `"minmax"` — may improve discrimination by normalizing score distributions
- **Consensus scoring**: Average rank of Vina + Vinardo scores (requires `reuse_results=True`)
- **Num modes sweep**: 5, 10, 20 — more poses may capture alternative binding modes
- **Energy range**: 2, 3, 5, 8 kcal/mol — wider range keeps more diverse poses

### Tier 3 — Low priority (if time allows)
- **MW correction**: score / MW^0.33 — larger molecules tend to score better, correction may improve ranking
- **Combined best parameters**: after finding individual improvements, combine top settings

## Skill Protocol Guidance

The virtual screening skill recommends:
- **Exhaustiveness 32** for production quality (vs 8 for fast iteration)
- **25 Å box** centered on co-crystal ligand
- **Meeko preparation** (mk_prepare_receptor.py, mk_prepare_ligand.py) with PAINS/Brenk filtering
- **BEDROC α=80.5** for early enrichment assessment
- Quality thresholds: EF1% > 10, ROC AUC > 0.7

## Timing Estimates (dual-GPU, 2474 compounds)
- exh=8: ~15-20 min per experiment
- exh=16: ~25-35 min per experiment
- exh=32: ~45-60 min per experiment

## results.tsv Format

Tab-separated, one header row + one row per experiment:
```
commit	description	auc	bedroc	ef1	time_s
baseline	skill/skill/25A/exh8/vina/none	0.XXXX	0.XXXX	X.XX	XXXX
```

## Current State

- **Baseline**: AUC=0.6767 (skill library / skill receptor / 25A / exh8 / vina / no transform)
- **Best AUC**: 0.7325 (naive library / skill receptor / 25A / exh8 / vina / batch50)
- **Improvement**: +0.0558 AUC (+8.2% relative)
- **Experiments run**: 16 (3 kept, 13 reverted)
- **Library sizes**: Skill=1309, Naive=2471 (PAINS filter removes ~47% from skill)

### Key Findings
1. **Naive library dramatically outperforms skill** (+0.056 AUC): The PAINS/Brenk filter removes too aggressively for CDK2 DUD-E
2. **Vina outperforms Vinardo** for naive library (+0.017 AUC), opposite of skill library result
3. **Skill receptor > naive receptor** regardless of library choice
4. **25Å box is optimal** — both smaller (18-22Å) and larger (30Å) reduce AUC
5. **Exhaustiveness 8 is optimal** — both lower (4) and higher (16, 32) reduce AUC
6. **Score transforms don't help** — AUC is rank-invariant
7. **Smaller batch sizes rescue more compounds** but don't improve AUC (segfault attrition is ~random)
8. **num_modes and energy_range have minimal effect** on best-pose scoring

# Autonomous virtual screening optimisation by an agentic AI research loop: a two-target study

**Osman Gani**

Section for Pharmaceutical Chemistry, Department of Pharmacy, University of Oslo, P.O. Box 1068 Blindern, 0316 Oslo, Norway

ORCID: 0009-0000-0515-2781 | Correspondence: osman.gani@farmasi.uio.no

---

## Abstract

I applied the autoresearch paradigm to structure-based virtual screening (VS) optimisation on two structurally diverse targets: formyl peptide receptor 2 (FPR2, a GPCR with 3.0 Å cryo-EM structure) and cyclin-dependent kinase 2 (CDK2, with 1.74 Å X-ray structure). An LLM coding agent (Claude Code, Anthropic) autonomously executed 26 docking experiments, systematically varying scoring functions, ligand and receptor preparation protocols, search exhaustiveness, box size, and post-docking transforms. On FPR2, the agent identified that Vinardo scoring improves AUC from 0.736 to 0.748 (+0.012), while on CDK2, switching to an unfiltered ligand library dramatically improved AUC from 0.677 to 0.735 (+0.058). Strikingly, optimal parameters were target-dependent: the preferred scoring function and library preparation reversed between targets. These results demonstrate that the autoresearch pattern translates effectively from machine learning to physics-based computational chemistry and that autonomous parameter optimisation can uncover target-specific configurations that manual tuning is unlikely to explore.

## Introduction

The autoresearch paradigm, recently introduced by Karpathy,^1 uses AI coding agents to run autonomous experiment loops: the agent reads its own source code, forms a hypothesis, modifies the code, runs the experiment, evaluates the outcome, and keeps or reverts the change. This pattern has shown striking results in machine learning, where overnight runs of dozens of experiments have yielded substantial performance gains on language model training benchmarks.^1 However, the paradigm has not been applied outside machine learning, and its utility for experimental pipelines in the natural sciences remains unknown.

Structure-based virtual screening (VS) is a natural candidate for autonomous optimisation. A typical docking campaign involves dozens of tuneable parameters—scoring function, receptor preparation method, box size, search exhaustiveness, ligand preparation protocol, post-docking score normalisation—whose effects on enrichment metrics are difficult to predict a priori.^2,3 These parameters are typically set by expert intuition or limited manual sweeps, leaving large regions of the configuration space unexplored.^4 Each docking run produces a single scalar outcome (e.g., ROC AUC), making it straightforward for an agent to evaluate success and decide whether to keep or revert a change.

LLM-based coding agents have matured from simple API wrappers into autonomous systems capable of executing complex scientific workflows. Recent work has demonstrated agents that augment chemistry reasoning with specialised tools,^5 plan and carry out chemical syntheses,^6 and conduct fully automated scientific discovery.^7 However, these studies used agents to execute predefined workflows rather than to iteratively optimise one. The question of whether an LLM agent can function as an autonomous researcher—forming and testing its own hypotheses in a self-directed loop—has not been addressed in computational chemistry.

I applied the autoresearch paradigm to VS optimisation on two structurally diverse targets: formyl peptide receptor 2 (FPR2), a G protein-coupled receptor with a 3.0 Å cryo-EM structure (PDB: 7T6S^8), and cyclin-dependent kinase 2 (CDK2), a well-studied kinase with a 1.74 Å X-ray crystal structure (PDB: 6INL^9). These targets differ in binding site topology (transmembrane pocket vs. ATP-competitive cleft), structure quality (cryo-EM vs. X-ray), and available benchmark data (ChEMBL-curated actives vs. DUD-E decoys). The agent autonomously executed 26 experiments across both targets.

## Results and discussion

### Overview of both autonomous campaigns

The agent completed 26 experiments across two targets (Tables 1 and 2): ten on FPR2 (~55 GPU-hours, single GPU) and sixteen on CDK2 (~6 GPU-hours, dual-GPU). Of these, one experiment was kept for FPR2 (Vinardo scoring) and three for CDK2 (naive library, Vina scoring, batch size adjustment). The agent made all decisions without human intervention.

### FPR2: scoring function is the dominant parameter

On FPR2, the only successful modification was switching from the Vina to the Vinardo^10 scoring function, improving AUC from 0.736 to 0.748 (+0.012; Table 1). Nine other modifications were reverted.

### CDK2: library preparation has the largest impact

The CDK2 campaign yielded a dramatically larger improvement: AUC rose from 0.677 to 0.735 (+0.058, +8.6%; Table 2). The largest single gain came from switching to the naive (OpenBabel-prepared) ligand library (+0.039), followed by switching from Vinardo back to Vina scoring (+0.019). The PAINS/Brenk filter^16,17 removed 47% of compounds including bona fide DUD-E actives.^19

### Optimal parameters are target-dependent

The most striking finding is the reversal of optimal parameters between targets (Fig. 3). Vinardo outperformed Vina on FPR2 but underperformed on CDK2. The skill library was essential for FPR2 but detrimental for CDK2. No universally optimal VS configuration exists.

### Agent behaviour and emergent capabilities

The agent exhibited systematic exploration, infrastructure improvisation (reuse_results mechanism), mathematical reasoning (monotonic transform invariance), and adaptive strategy modification.

### Limitations

Broader validation across diverse target classes is needed. The search space was limited to Uni-Dock CLI parameters. Stochastic noise floor of ~0.004 AUC limits detection of small improvements.

## Conclusions

The autoresearch paradigm can be successfully applied to VS optimisation. An LLM agent autonomously executed 26 experiments across two targets, achieving +0.012 AUC on FPR2 and +0.058 AUC on CDK2 with target-dependent parameter optima.

## Methods

### Autoresearch framework
Claude Code (Anthropic, claude-opus-4-6^21) with strict hypothesise–modify–commit–dock–evaluate–decide loop.^1

### Targets and libraries
FPR2: PDB 7T6S^8, 573 actives, ~4,600 decoys. CDK2: PDB 6INL^9, 474 DUD-E^19 actives, 2,000 decoys.

### Docking engine
Uni-Dock^13 on NVIDIA RTX 4500 Ada GPUs. Vina^11 and Vinardo^10 scoring.

### Evaluation
ROC AUC, BEDROC (α=80.5^20), EF 1%.

## References

1–22: See DOCX manuscript for full reference list.

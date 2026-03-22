# Autonomous Optimisation of Structure-Based Virtual Screening Protocols Using an LLM Coding Agent

**Osman Gani**

Section for Pharmaceutical Chemistry, Department of Pharmacy, University of Oslo, P.O. Box 1068 Blindern, 0316 Oslo, Norway

ORCID: 0009-0000-0515-2781 | Correspondence: osman.gani@farmasi.uio.no

---

## Abstract

I applied the autoresearch paradigm to structure-based virtual screening (VS) optimisation on two structurally diverse targets: formyl peptide receptor 2 (FPR2, a GPCR with 3.0 Å cryo-EM structure) and cyclin-dependent kinase 2 (CDK2, with 1.74 Å X-ray structure). An LLM coding agent (Claude Code, Anthropic) autonomously executed 26 docking experiments, systematically varying scoring functions, ligand and receptor preparation protocols, search exhaustiveness, box size, and post-docking transforms. On FPR2, the agent identified that Vinardo scoring improves ROC AUC from 0.736 to 0.748 (+1.6%), while on CDK2, switching to an unfiltered ligand library improved AUC from 0.677 to 0.735 (+8.6%). Multi-metric analysis revealed that the FPR2 AUC gain came at the cost of early enrichment (BEDROC −13.9%, EF 1% −45.6%), whereas CDK2 showed robust improvement across all metrics (BEDROC +73.0%, EF 1% +104.7%). Optimal parameters were target-dependent, with the preferred scoring function and library preparation reversing between targets. These results demonstrate that the autoresearch pattern translates effectively from machine learning to physics-based computational chemistry, that single-metric optimisation can be misleading, and that autonomous parameter search can uncover target-specific configurations unlikely to emerge from manual tuning.

## Introduction

The autoresearch paradigm, recently introduced by Karpathy,^1 uses AI coding agents to run autonomous experiment loops: the agent reads its own source code, forms a hypothesis, modifies the code, runs the experiment, evaluates the outcome, and keeps or reverts the change. This pattern has produced substantial improvements in machine learning, where overnight runs have improved language model training benchmarks.^1 However, the paradigm has not been applied outside machine learning, and its utility for experimental pipelines in the natural sciences remains unknown.

Structure-based virtual screening (VS) is a natural candidate for autonomous optimisation. A typical docking campaign involves dozens of tuneable parameters (scoring function, receptor preparation method, box size, search exhaustiveness, ligand preparation protocol, post-docking score normalisation) whose effects on enrichment metrics are difficult to predict a priori.^2,3 These parameters are typically set by expert intuition or limited manual sweeps, leaving large regions of the configuration space unexplored.^4 Each docking run produces a single scalar outcome (e.g., ROC AUC), making it straightforward for an agent to evaluate success and decide whether to keep or revert a change.

LLM-based coding agents can now execute multi-step scientific workflows autonomously. Recent work has demonstrated agents that augment chemistry reasoning with specialised tools,^5 plan and carry out chemical syntheses,^6 and conduct fully automated scientific discovery.^7 However, these studies used agents to execute predefined workflows rather than to iteratively optimise one. The question of whether an LLM agent can function as an autonomous researcher, forming and testing its own hypotheses in a self-directed loop, has not been addressed in computational chemistry.

I applied the autoresearch paradigm to VS optimisation on two structurally diverse targets: formyl peptide receptor 2 (FPR2), a G protein-coupled receptor with a 3.0 Å cryo-EM structure (PDB: 7T6S^8), and cyclin-dependent kinase 2 (CDK2), a well-studied kinase with a 1.74 Å X-ray crystal structure (PDB: 6INL^9). These targets differ in binding site topology (transmembrane pocket vs. ATP-competitive cleft), structure quality (cryo-EM vs. X-ray), and available benchmark data (ChEMBL-curated actives vs. DUD-E decoys). The agent autonomously executed 26 experiments across both targets.

## Results and discussion

### Overview of both autonomous campaigns

The agent completed 26 experiments across two targets (Tables 1 and 2): ten on FPR2 (~55 GPU-hours, single GPU) and sixteen on CDK2 (~6 GPU-hours, dual-GPU). Of these, one experiment was kept for FPR2 (Vinardo scoring) and three for CDK2 (naive library, Vina scoring, batch size adjustment). The agent followed a strict experiment loop (Fig. 1) and made all decisions (hypothesis selection, parameter modification, keep/revert) without human intervention. Although ROC AUC was the primary optimisation target, all experiments were evaluated against three metrics (ROC AUC, BEDROC at α = 80.5, and enrichment factor at 1%), enabling post hoc analysis of whether AUC gains translated into improved early enrichment.

### FPR2: scoring function is the dominant parameter

On FPR2, the only successful modification was switching from the Vina to the Vinardo^10 scoring function, improving AUC from 0.736 to 0.748 (+0.012; Table 1, experiment 1). This improvement exceeded the estimated stochastic noise floor of 0.004 by threefold (see ESI, Section S4). Nine other modifications were reverted, including box size reduction (20 Å, −0.003), doubling exhaustiveness (−0.004), switching to OpenBabel-prepared receptor (−0.016), MW correction (−0.046), and multi-pose aggregation (−0.018 to −0.033). The OpenBabel-prepared ligand library caused 100% segfault rate in Uni-Dock, preventing evaluation entirely.

### CDK2: library preparation has the largest impact

The CDK2 campaign yielded a larger improvement: AUC rose from 0.677 (baseline) to 0.735 (+0.058, +8.6%; Table 2). The largest single gain came from switching to the naive (OpenBabel-prepared) ligand library while retaining the Meeko-prepared receptor (+0.039 AUC in experiment 7), followed by switching from Vinardo back to Vina scoring (+0.019 in experiment 9). The PAINS/Brenk filter^16,17 removed 47% of compounds from the skill library, reducing it from 2,471 to 1,309 ligands. The removed compounds included known CDK2 actives from DUD-E,^19 biasing the benchmark against the filtered library.

### Optimal parameters are target-dependent

The key finding is the reversal of optimal parameters between targets (Fig. 3). For FPR2, Vinardo outperformed Vina (+0.012 AUC), while for CDK2, Vina outperformed Vinardo (+0.019) after switching to the naive library. Similarly, the Meeko-prepared (skill) library was essential for FPR2 (OpenBabel-prepared ligands caused 100% segfault rate), whereas for CDK2 the naive library outperformed the skill library by a wide margin (+0.058 AUC). These reversals demonstrate that there is no universally optimal VS configuration: scoring function, preparation protocol, and other parameters interact with target-specific binding site characteristics in ways that are difficult to predict a priori.

### AUC gains do not guarantee improved early enrichment

Multi-metric analysis reveals a limitation of single-metric optimisation (Fig. 2). On FPR2, the Vinardo-driven AUC improvement (+1.6%) was accompanied by a 13.9% decrease in BEDROC and a 45.6% decrease in EF 1%, indicating that the scoring function change reshuffled the ranked list without improving, and in fact worsening, the concentration of actives among the highest-ranked compounds. In a prospective screen where only the top 1% of compounds can be tested experimentally, this AUC gain would translate into fewer confirmed hits. By contrast, the CDK2 optimisation improved all three metrics: AUC +8.6%, BEDROC +73.0%, and EF 1% +104.7%. Concretely, the CDK2 improvement arose from a structural change to the input library (removing a counterproductive PAINS/Brenk filter), whereas the FPR2 improvement relied solely on a scoring function swap that altered the score distribution without fundamentally changing which compounds were evaluated.

These results support multi-metric evaluation in autonomous VS campaigns. An agent optimising BEDROC or EF 1% instead of, or alongside, AUC might reach different and potentially more practically useful configurations. Future implementations should consider multi-objective optimisation frameworks that balance global discrimination (AUC) against early enrichment (BEDROC, EF 1%).

The differing response to library preparation is instructive. For FPR2, the skill library (Meeko-prepared with PAINS^16/Brenk^17 filtering) was the only viable option because OpenBabel-generated PDBQT files contained pervasive structural defects that crashed Uni-Dock. For CDK2, the same PAINS/Brenk filter removed 47% of compounds, including bona fide DUD-E actives, resulting in a substantially smaller library (1,309 vs. 2,471 compounds) and worse enrichment. This finding cautions against blanket application of PAINS filters in retrospective benchmarks where the active set may contain compounds flagged by these heuristic substructure rules.

### Agent behaviour and emergent capabilities

Across both campaigns, the agent exhibited systematic exploration, prioritising high-impact parameters (scoring function, library choice) before lower-impact ones (transforms, exhaustiveness). When the naive library run on FPR2 destroyed cached results, the agent independently devised a "reuse_results" mechanism to skip docking and test post-processing modifications on existing output files, saving approximately 6 GPU-hours per transform test. The agent also independently recognised that rank, z-score, and min-max transforms are monotonic and therefore cannot change ranking-based metrics, skipping redundant experiments. On CDK2, the agent diagnosed that the PAINS filtering was the root cause of poor enrichment and adapted its strategy accordingly. None of these behaviours was explicitly programmed.

### Limitations

Although two targets were studied, broader validation across diverse target classes is needed to establish general guidelines. The search space was limited to parameters exposed by the Uni-Dock command-line interface; more sophisticated modifications (e.g., consensus scoring across multiple docking engines, flexible residue selection) remain unexplored. The stochastic noise floor of approximately 0.004 AUC limits the agent's ability to detect small improvements. The FPR2 result (AUC 0.748) reflects the difficulty of VS on GPCR targets with cryo-EM structures at moderate resolution, while the CDK2 result (AUC 0.735) is influenced by DUD-E benchmark biases.^19

## Conclusions

I have demonstrated that the autoresearch paradigm, previously limited to machine learning hyperparameter tuning, can be successfully applied to structure-based virtual screening optimisation. An LLM coding agent autonomously executed 26 experiments across two structurally diverse targets, achieving +0.012 AUC on FPR2 and +0.058 AUC on CDK2. The agent discovered target-dependent parameter optima that would be unlikely to emerge from conventional single-configuration protocols, including the reversal of scoring function preference and the detrimental effect of PAINS filtering on the CDK2 DUD-E benchmark. Multi-metric evaluation revealed that AUC gains do not necessarily translate into improved early enrichment: on FPR2, BEDROC and EF 1% actually worsened despite improved AUC, highlighting the importance of tracking multiple metrics in autonomous VS campaigns.

The autonomous agent required no human intervention during the optimisation loops and independently devised infrastructure workarounds, reasoned about mathematical properties of score transforms, and adapted its strategy based on accumulated results. Combined with advances in self-driving laboratories^6 and automated scientific discovery,^7 this work suggests that agentic AI can serve as a practical tool for computational drug discovery.

## Methods

### Autoresearch framework
Claude Code (Anthropic, claude-opus-4-6^21) with strict hypothesise, modify, commit, dock, evaluate, decide loop.^1

### Targets and libraries
FPR2: PDB 7T6S^8, 573 actives, ~4,600 decoys. CDK2: PDB 6INL^9, 474 DUD-E^19 actives, 2,000 decoys.

### Docking engine
Uni-Dock^13 on NVIDIA RTX 4500 Ada GPUs. Vina^11 and Vinardo^10 scoring.

### Evaluation
ROC AUC, BEDROC (α=80.5^20), EF 1%.

## References

1-22: See DOCX manuscript for full reference list.

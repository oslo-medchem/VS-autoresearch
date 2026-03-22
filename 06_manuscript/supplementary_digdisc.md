# Electronic Supplementary Information (ESI)

## Autonomous Optimisation of Structure-Based Virtual Screening Protocols Using an LLM Coding Agent

Osman Gani

Section for Pharmaceutical Chemistry, Department of Pharmacy, University of Oslo

---

## S1. Agent program files

The agent operated under structured protocol files (program.md) for each target. Research directions were organised into three tiers by expected impact.

## S2. FPR2 detailed experiment logs

10 experiments (1 kept, 9 reverted). See DOCX supplementary for full details.

## S3. CDK2 detailed experiment logs

16 experiments (3 kept, 13 reverted). See DOCX supplementary for full details.

## S4. Stochastic variation analysis

FPR2 noise floor: ~0.004 AUC (two identical runs: 0.744 vs 0.748).
CDK2 noise floor: ~0.002–0.005 AUC (batch-dependent segfault variation).

## S5. Segfault analysis

FPR2: ~1,100 ligands lost per run (79% success rate). CDK2 naive library: ~20–40% batch crash rate.

## S6. Git commit histories

See DOCX supplementary for full git logs of both campaigns.

## S7. Final optimised configurations

FPR2: Vinardo scoring, skill library, skill receptor, 25 Å box, exh. 8.
CDK2: Vina scoring, naive library, skill receptor, 25 Å box, exh. 8, dual GPU.

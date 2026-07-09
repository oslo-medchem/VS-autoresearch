# Revision notes

The manuscript associated with this repository underwent a major revision during
peer review. This file records what changed in the science and in the repository;
the campaign data under the numbered stage directories is unchanged.

## Key scientific correction (CDK2 library filtering)

The original draft stated that the PAINS/Brenk filter applied in the "skill"
library preparation "removed known CDK2 actives, biasing the benchmark against the
filtered library." A formal active-versus-decoy count shows the opposite:

- The filter removed 47% of compounds overall (2,471 to 1,309).
- It dropped a **smaller** fraction of actives (37.8%, 179/474) than of decoys
  (49.3%, 984/1,997), so the retained set was **enriched** in actives
  (Fisher exact odds ratio 0.63 for an active being dropped, p = 6.5 × 10⁻⁶).
- The higher AUC of the unfiltered ("naive") library therefore reflects a change
  in benchmark composition (and a larger decoy pool), not a genuine
  docking-protocol improvement. Applying a PAINS/Brenk filter to a DUD-E benchmark
  is methodologically inappropriate because it alters the deliberately
  property-matched active/decoy composition.

The corrected statements are reflected in `06_manuscript/manuscript_digdisc.md`
and its generator `06_manuscript/make_docx.py`. The reanalysis that established
this is `08_revision_analyses/cdk2_filter_lossbias.py`.

## New re-analyses (no new docking)

`08_revision_analyses/` adds deterministic re-analyses of the existing campaign and
pilot data, each addressing a reviewer point: a physicochemical descriptor panel of
the libraries (`library_descriptors.py`, plus `fpr2_actives_descriptors.py` which
regenerates the FPR2 active set from its ChEMBL query because the archived FPR2
library SMILES are null-filled), the CDK2 filter loss-bias analysis
(`cdk2_filter_lossbias.py`), a third-target (HIV-1 protease) scoring comparison from
the pilot data (`pilot_thirdtarget_stats.py`), and a co-crystal self-redock for pose
validation (`redock_cocrystal.py`, FPR2 FUI to 7T6S: 0.37 Å RMSD). See
`08_revision_analyses/README.md`.

## Build artifacts

`06_manuscript/manuscript_digdisc.docx` and `supplementary_digdisc.docx` are build
artifacts of `make_docx.py`; they have been regenerated so they match the current
source, including the correction above. Regenerate with
`python 06_manuscript/make_docx.py`.

## Earlier repository change

The manuscript citation was made journal-neutral while under review (commit
`044b485`); this repository does not name a submission venue.

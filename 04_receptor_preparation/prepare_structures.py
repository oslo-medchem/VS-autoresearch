#!/usr/bin/env python3
"""Extract chain R (FPR2) and ligand FUI from PDB 7T6S."""

import os
import numpy as np
from Bio.PDB import PDBParser, PDBIO, Select
from rdkit import Chem
from rdkit.Chem import AllChem, rdmolfiles

# Paths
PDB_FILE = "7T6S.pdb"
RECEPTOR_PDB = "receptor_chainR.pdb"
LIGAND_PDB = "ligand_FUI.pdb"
LIGAND_SDF = "ligand_FUI_crystal.sdf"
LIGAND_SMILES_SDF = "ligand_FUI_smiles.sdf"

# SMILES for Compound C43 (FUI)
SMILES = "O=C(N)N(C1=CC=C(Cl)C=C1)C2=C(C(C)C)N(C)N(C3=CC=CC=C3)C2=O"


class ChainRProteinSelect(Select):
    """Select only standard amino acid residues from chain R."""
    STANDARD_AA = {
        'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY',
        'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE', 'PRO', 'SER',
        'THR', 'TRP', 'TYR', 'VAL'
    }

    def accept_chain(self, chain):
        return chain.get_id() == 'R'

    def accept_residue(self, residue):
        return residue.get_resname() in self.STANDARD_AA


class LigandSelect(Select):
    """Select only FUI ligand from chain R."""
    def accept_chain(self, chain):
        return chain.get_id() == 'R'

    def accept_residue(self, residue):
        return residue.get_resname() == 'FUI'


# Parse PDB
parser = PDBParser(QUIET=True)
structure = parser.get_structure('7T6S', PDB_FILE)

# Save receptor (chain R, standard residues only)
io = PDBIO()
io.set_structure(structure)
io.save(RECEPTOR_PDB, ChainRProteinSelect())
print(f"Saved receptor (chain R protein only): {RECEPTOR_PDB}")

# Count residues
receptor_struct = parser.get_structure('rec', RECEPTOR_PDB)
n_res = sum(1 for r in receptor_struct.get_residues())
print(f"  Receptor residues: {n_res}")

# Save ligand PDB
io.set_structure(structure)
io.save(LIGAND_PDB, LigandSelect())
print(f"Saved ligand PDB: {LIGAND_PDB}")

# Extract ligand coordinates and compute center of mass
ligand_coords = []
for model in structure:
    for chain in model:
        if chain.get_id() == 'R':
            for residue in chain:
                if residue.get_resname() == 'FUI':
                    for atom in residue:
                        ligand_coords.append(atom.get_vector().get_array())

ligand_coords = np.array(ligand_coords)
center = ligand_coords.mean(axis=0)
print(f"\nLigand FUI center of mass: {center[0]:.3f}, {center[1]:.3f}, {center[2]:.3f}")
print(f"Ligand atoms: {len(ligand_coords)}")

# Save center to file for docking config
with open("ligand_center.txt", "w") as f:
    f.write(f"center_x = {center[0]:.3f}\n")
    f.write(f"center_y = {center[1]:.3f}\n")
    f.write(f"center_z = {center[2]:.3f}\n")
print("Saved ligand center to ligand_center.txt")

# Convert ligand PDB to SDF using RDKit (for crystal coordinates)
# Read the PDB ligand with openbabel for better handling
import subprocess
subprocess.run([
    "obabel", LIGAND_PDB, "-O", LIGAND_SDF, "--gen3d" if False else ""
], capture_output=True)
# Alternative: simple conversion without --gen3d to keep crystal coords
subprocess.run(["obabel", LIGAND_PDB, "-O", LIGAND_SDF], capture_output=True)
print(f"Converted crystal ligand to SDF: {LIGAND_SDF}")

# Generate ligand from SMILES (reference)
mol = Chem.MolFromSmiles(SMILES)
mol = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
AllChem.MMFFOptimizeMolecule(mol)
writer = rdmolfiles.SDWriter(LIGAND_SMILES_SDF)
writer.write(mol)
writer.close()
print(f"Generated ligand from SMILES: {LIGAND_SMILES_SDF}")
print(f"  Heavy atoms: {mol.GetNumHeavyAtoms()}")

print("\n=== Structure preparation complete ===")

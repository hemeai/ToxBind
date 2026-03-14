import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import subprocess

    return (subprocess,)


@app.cell
def _(subprocess):
    # Add execute permissions to binaries
    #! chmod +x dssp
    subprocess.call(['chmod', '+x', 'dssp'])
    #! chmod +x DAlphaBall.gcc
    subprocess.call(['chmod', '+x', 'DAlphaBall.gcc'])

    # Verify permissions
    #! ls -l dssp
    subprocess.call(['ls', '-l', 'dssp'])
    #! ls -l DAlphaBall.gcc
    subprocess.call(['ls', '-l', 'DAlphaBall.gcc'])
    return


@app.cell
def _():
    from IPython.display import display, Markdown

    return Markdown, display


@app.cell
def _():
    ####################################
    ################ BioPython functions
    import os
    ### Import dependencies
    import math
    import numpy as np
    from collections import defaultdict
    from scipy.spatial import cKDTree
    from Bio import BiopythonWarning
    from Bio.PDB import PDBParser, DSSP, Selection, Polypeptide, PDBIO, Select, Chain, Superimposer
    from Bio.SeqUtils.ProtParam import ProteinAnalysis
    from Bio.PDB.Selection import unfold_entities
    from Bio.PDB.Polypeptide import is_aa

    def validate_design_sequence(sequence, num_clashes, advanced_settings):
    # analyze sequence composition of design
        note_array = []
        if num_clashes > 0:
            note_array.append('Relaxed structure contains clashes.')
        if advanced_settings['omit_AAs']:  # Check if protein contains clashes after relaxation
            restricted_AAs = advanced_settings['omit_AAs'].split(',')
            for restricted_AA in restricted_AAs:
                if restricted_AA in sequence:
                    note_array.append('Contains: ' + restricted_AA + '!')  # Check if the sequence contains disallowed amino acids
        analysis = ProteinAnalysis(sequence)
        extinction_coefficient_reduced = analysis.molar_extinction_coefficient()[0]
        molecular_weight = round(analysis.molecular_weight() / 1000, 2)
        extinction_coefficient_reduced_1 = round(extinction_coefficient_reduced / molecular_weight * 0.01, 2)
        if extinction_coefficient_reduced_1 <= 2:
            note_array.append(f'Absorption value is {extinction_coefficient_reduced_1}, consider adding tryptophane to design.')
        notes = ' '.join(note_array)  # Analyze the protein
        return notes

    def target_pdb_rmsd(trajectory_pdb, starting_pdb, chain_ids_string):  # Calculate the reduced extinction coefficient per 1% solution
        parser = PDBParser(QUIET=True)
        structure_trajectory = parser.get_structure('trajectory', trajectory_pdb)
        structure_starting = parser.get_structure('starting', starting_pdb)
        chain_trajectory = structure_trajectory[0]['A']
        chain_ids = chain_ids_string.split(',')  # Check if the absorption is high enough
        residues_starting = []
        for chain_id in chain_ids:
            chain_id = chain_id.strip()
            chain = structure_starting[0][chain_id]  # Join the notes into a single string
            for residue in chain:
                if is_aa(residue, standard=True):
                    residues_starting.append(residue)
        residues_trajectory = [residue for residue in chain_trajectory if is_aa(residue, standard=True)]
    # temporary function, calculate RMSD of input PDB and trajectory target
        min_length = min(len(residues_starting), len(residues_trajectory))
        residues_starting = residues_starting[:min_length]  # Parse the PDB files
        residues_trajectory = residues_trajectory[:min_length]
        atoms_starting = [residue['CA'] for residue in residues_starting if 'CA' in residue]
        atoms_trajectory = [residue['CA'] for residue in residues_trajectory if 'CA' in residue]
        sup = Superimposer()
        sup.set_atoms(atoms_starting, atoms_trajectory)  # Extract chain A from trajectory_pdb
        rmsd = sup.rms
        return round(rmsd, 2)
      # Extract the specified chains from starting_pdb
    def calculate_clash_score(pdb_file, threshold=2.4, only_ca=False):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_file)
        atoms = []
        atom_info = []
        for model in structure:
            for chain in model:
                for residue in chain:
                    for atom in residue:
                        if atom.element == 'H':  # Extract residues from chain A in trajectory_pdb
                            continue
                        if only_ca and atom.get_name() != 'CA':
                            continue  # Ensure that both structures have the same number of residues
                        atoms.append(atom.coord)
                        atom_info.append((chain.id, residue.id[1], atom.get_name(), atom.coord))
        tree = cKDTree(atoms)
        pairs = tree.query_pairs(threshold)
        valid_pairs = set()  # Collect CA atoms from the two sets of residues
        for i, j in pairs:
            chain_i, res_i, name_i, coord_i = atom_info[i]
            chain_j, res_j, name_j, coord_j = atom_info[j]
            if chain_i == chain_j and res_i == res_j:  # Calculate RMSD using structural alignment
                continue
            if chain_i == chain_j and abs(res_i - res_j) == 1:
                continue
            if not only_ca and chain_i == chain_j:
                continue
            valid_pairs.add((i, j))
    # detect C alpha clashes for deformed trajectories
        return len(valid_pairs)
    three_to_one_map = {'ALA': 'A', 'CYS': 'C', 'ASP': 'D', 'GLU': 'E', 'PHE': 'F', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LYS': 'K', 'LEU': 'L', 'MET': 'M', 'ASN': 'N', 'PRO': 'P', 'GLN': 'Q', 'ARG': 'R', 'SER': 'S', 'THR': 'T', 'VAL': 'V', 'TRP': 'W', 'TYR': 'Y'}

    def hotspot_residues(trajectory_pdb, binder_chain='B', atom_distance_cutoff=4.0):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('complex', trajectory_pdb)  # Detailed atom info for debugging and processing
        binder_atoms = Selection.unfold_entities(structure[0][binder_chain], 'A')
        binder_coords = np.array([atom.coord for atom in binder_atoms])
        target_atoms = Selection.unfold_entities(structure[0]['A'], 'A')
        target_coords = np.array([atom.coord for atom in target_atoms])
        binder_tree = cKDTree(binder_coords)
        target_tree = cKDTree(target_coords)  # Skip hydrogen atoms
        interacting_residues = {}
        pairs = binder_tree.query_ball_tree(target_tree, atom_distance_cutoff)
        for binder_idx, close_indices in enumerate(pairs):
            binder_residue = binder_atoms[binder_idx].get_parent()
            binder_resname = binder_residue.get_resname()
            if binder_resname in three_to_one_map:
                aa_single_letter = three_to_one_map[binder_resname]
                for close_idx in close_indices:
                    target_residue = target_atoms[close_idx].get_parent()
                    interacting_residues[binder_residue.id[1]] = aa_single_letter
        return interacting_residues

    def calc_ss_percentage(pdb_file, advanced_settings, chain_id='B', atom_distance_cutoff=4.0):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_file)  # Exclude clashes within the same residue
        model = structure[0]
        dssp = DSSP(model, pdb_file, dssp='mkdssp')
        ss_counts = defaultdict(int)
        ss_interface_counts = defaultdict(int)  # Exclude directly sequential residues in the same chain for all atoms
        plddts_interface = []
        plddts_ss = []
        chain = model[chain_id]
        interacting_residues = set(hotspot_residues(pdb_file, chain_id, atom_distance_cutoff).keys())  # If calculating sidechain clashes, only consider clashes between different chains
        for residue in chain:
            residue_id = residue.id[1]
            if (chain_id, residue_id) in dssp:
                ss = dssp[chain_id, residue_id][2]
                ss_type = 'loop'
                if ss in ['H', 'G', 'I']:
                    ss_type = 'helix'
                elif ss == 'E':
                    ss_type = 'sheet'
                ss_counts[ss_type] = ss_counts[ss_type] + 1
                if ss_type != 'loop':
                    avg_plddt_ss = sum((atom.bfactor for atom in residue)) / len(residue)
                    plddts_ss.append(avg_plddt_ss)
                if residue_id in interacting_residues:
    # identify interacting residues at the binder interface
                    ss_interface_counts[ss_type] = ss_interface_counts[ss_type] + 1
                    avg_plddt_residue = sum((atom.bfactor for atom in residue)) / len(residue)  # Parse the PDB file
                    plddts_interface.append(avg_plddt_residue)
        total_residues = sum(ss_counts.values())
        total_interface_residues = sum(ss_interface_counts.values())
        percentages = calculate_percentages(total_residues, ss_counts['helix'], ss_counts['sheet'])  # Get the specified chain
        interface_percentages = calculate_percentages(total_interface_residues, ss_interface_counts['helix'], ss_interface_counts['sheet'])
        i_plddt = round(sum(plddts_interface) / len(plddts_interface) / 100, 2) if plddts_interface else 0
        ss_plddt = round(sum(plddts_ss) / len(plddts_ss) / 100, 2) if plddts_ss else 0
        return (*percentages, *interface_percentages, i_plddt, ss_plddt)  # Get atoms and coords for the target chain

    def calculate_percentages(total, helix, sheet):
        helix_percentage = round(helix / total * 100, 2) if total > 0 else 0
        sheet_percentage = round(sheet / total * 100, 2) if total > 0 else 0  # Build KD trees for both chains
        loop_percentage = round((total - helix - sheet) / total * 100, 2) if total > 0 else 0
    # calculate secondary structure percentage of design
        return (helix_percentage, sheet_percentage, loop_percentage)  # Prepare to collect interacting residues  # Query the tree for pairs of atoms within the distance cutoff  # Process each binder atom's interactions  # Convert three-letter code to single-letter code using the manual dictionary  # Parse the structure  # Consider only the first model in the structure  # Calculate DSSP for the model  # Prepare to count residues  # Get chain and interacting residues once  # Get the secondary structure  # calculate secondary structure normalised pLDDT  # calculate interface pLDDT  # Calculate percentages

    return (
        DSSP,
        PDBParser,
        ProteinAnalysis,
        calc_ss_percentage,
        hotspot_residues,
        is_aa,
    )


@app.cell
def _(calc_ss_percentage):
    advanced_settings = {
        "dssp_path": "/usr/local/bin/mkdssp",
        "omit_AAs": "C",
    }
    pdb_file = "./../target/8d9y.pdb"
    calc_ss_percentage(pdb_file=pdb_file, advanced_settings=advanced_settings)
    return (advanced_settings,)


@app.cell
def _(DSSP, PDBParser, advanced_settings, hotspot_residues):
    import pandas as pd
    AA_PROPERTIES = {'ALA': 'nonpolar', 'ARG': 'positive', 'ASN': 'polar', 'ASP': 'negative', 'CYS': 'polar', 'GLN': 'polar', 'GLU': 'negative', 'GLY': 'nonpolar', 'HIS': 'positive', 'ILE': 'nonpolar', 'LEU': 'nonpolar', 'LYS': 'positive', 'MET': 'nonpolar', 'PHE': 'nonpolar', 'PRO': 'nonpolar', 'SER': 'polar', 'THR': 'polar', 'TRP': 'nonpolar', 'TYR': 'polar', 'VAL': 'nonpolar', 'SEC': 'polar'}

    def create_structure_df(pdb_file, advanced_settings, chain_id=None, atom_distance_cutoff=4.0):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_file)
        model = structure[0]
        dssp = DSSP(model, pdb_file, dssp='mkdssp')
        data = []
        chains = [model[chain_id]] if chain_id else model.get_chains()
        for chain in chains:
            current_chain_id = chain.id
            interacting_residues = set()
            if current_chain_id:
                interacting_residues = set(hotspot_residues(pdb_file, current_chain_id, atom_distance_cutoff).keys())
            for residue in chain:
                residue_id = residue.id[1]
                res_name = residue.get_resname()
                if (current_chain_id, residue_id) in dssp:
                    dssp_data = dssp[current_chain_id, residue_id]
                    ss = dssp_data[2]
                    acc = dssp_data[3]
                    phi = dssp_data[4]
                    psi = dssp_data[5]
                    ss_type = 'loop'
                    if ss in ['H', 'G', 'I']:
                        ss_type = 'helix'
                    elif ss == 'E':
                        ss_type = 'sheet'
                    avg_plddt = sum((atom.bfactor for atom in residue)) / len(residue) / 100
                    data.append({'chain_id': current_chain_id, 'residue_id': residue_id, 'residue_name': res_name, 'property': AA_PROPERTIES.get(res_name, 'unknown'), 'ss_type': ss_type, 'ss_code': ss, 'accessibility': acc, 'phi': phi, 'psi': psi, 'plddt': round(avg_plddt, 2), 'is_interface': residue_id in interacting_residues if chain_id else None})
        return pd.DataFrame(data)  # Calculate DSSP for the model
    pdb_file_1 = './../target/8d9y.pdb'
    df = create_structure_df(pdb_file_1, advanced_settings)
    # Example usage:
    df.head()  # Prepare data for DataFrame  # Process either specific chain or all chains  # Get interacting residues if chain_id is specified
    return df, pd


@app.cell
def _(df):
    df.tail(10)
    return


@app.cell
def _(df):
    df.head(10)
    return


@app.cell
def _(df):
    df_target = df[df['chain_id'] == 'I']
    df_target = df_target.reset_index(drop=True)
    df_target.index = range(1, len(df_target) + 1)
    return (df_target,)


@app.cell
def _(df_target):
    df_target.to_csv('8d9y_chain_B_secondary_structure_information.csv', index=False)
    return


@app.cell
def _(df_target):
    df_target[df_target['property'] == 'nonpolar']
    return


@app.cell
def _(Markdown, df_target, display):
    display(Markdown(df_target[df_target['property'] == 'nonpolar'].sort_values('accessibility', ascending=False).to_markdown()))
    return


@app.cell
def _(Markdown, df_target, display):
    display(Markdown(df_target.sort_values('accessibility', ascending=False).to_markdown()))
    return


@app.cell
def _(Markdown, df_target, display):
    display(Markdown(df_target.to_markdown()))
    return


@app.cell
def _(PDBParser, ProteinAnalysis):
    from Bio.Data import IUPACData
    from Bio.SeqUtils import ProtParamData
    three_to_one = IUPACData.protein_letters_3to1
    pdb_file_2 = './../target/8d9y.pdb'
    parser = PDBParser()
    # 3-letter to 1-letter code map
    structure = parser.get_structure('8d9y', pdb_file_2)
    residue_list = []
    # Load PDB
    sequence = ''
    for chain in structure[0]:
        if chain.id == 'F':
            for residue in chain:
    # Extract sequence and map residues
                resname = residue.get_resname().strip()
                try:
                    one_letter = three_to_one[resname.capitalize()]
                    sequence = sequence + one_letter  # First model
                    residue_list.append(residue)
                except KeyError:
                    continue
    print('Sequence:', sequence)
    print('Length:', len(sequence))
    window = 9
    pa = ProteinAnalysis(sequence)
    hydropathy_values = pa.protein_scale(param_dict=ProtParamData.kd, window=window)
    offset = window // 2  # Skip non-standard residues
    for i, residue in enumerate(residue_list):
        resname = residue.get_resname()
        resnum = residue.get_id()[1]
        if offset <= i < len(residue_list) - offset:
    # Hydropathy analysis with window
            hydro = hydropathy_values[i - offset]
            print(f'Residue {resname} {resnum:>3}: Hydropathy = {hydro:.2f}')
        else:
    # Align hydropathy values to the residue list
            print(f'Residue {resname} {resnum:>3}: Hydropathy = NA')  # Values are centered in the window
    return IUPACData, ProtParamData


@app.cell
def _(IUPACData, PDBParser, ProtParamData, ProteinAnalysis, pd):
    def calculate_hydropathy_df(pdb_file, chain_id='F', window=9):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('structure', pdb_file)
        three_to_one = IUPACData.protein_letters_3to1
        sequence = ''
        residue_info = []
        for chain in structure[0]:
            if chain.id == chain_id:
                for residue in chain:
                    resname = residue.get_resname().strip()
                    try:
                        one_letter = three_to_one[resname.capitalize()]
                        sequence = sequence + one_letter  # Extract sequence and residues
                        residue_info.append({'residue_name': resname, 'residue_id': residue.get_id()[1], 'chain_id': chain.id, 'one_letter': one_letter})
                    except KeyError:
                        continue
        analysed_seq = ProteinAnalysis(sequence)  # first model
        hydro_values = analysed_seq.protein_scale(param_dict=ProtParamData.kd, window=window)
        offset = window // 2
        for i in range(len(residue_info)):
            if offset <= i < len(residue_info) - offset:
                residue_info[i]['hydropathy'] = round(hydro_values[i - offset], 3)
            else:
                residue_info[i]['hydropathy'] = None
        for i, r in enumerate(residue_info):
            r['index'] = i + 1
        return pd.DataFrame(residue_info)
    df_hydro = calculate_hydropathy_df('./../target/8d9y.pdb', chain_id='I', window=9)
    #  Run this
    print(df_hydro.head())  # skip non-standard residues  # Calculate hydropathy  # Add hydropathy to residue info  # Add index
    return (df_hydro,)


@app.cell
def _(Markdown, df_hydro, df_target, display):
    # Ensure consistent residue name format
    df_hydro_1 = df_hydro[['chain_id', 'residue_id', 'residue_name', 'hydropathy']]
    df_hydro_1['residue_name'] = df_hydro_1['residue_name'].str.upper()
    df_merged = df_target.merge(df_hydro_1, on=['chain_id', 'residue_id', 'residue_name'], how='left')
    # Merge only hydropathy into df_target
    cols = df_merged.columns.tolist()
    access_idx = cols.index('accessibility')
    cols.remove('hydropathy')
    cols.insert(access_idx + 1, 'hydropathy')  # keep all rows from df_target
    df_merged = df_merged[cols]
    # Get list of columns
    # Find the index of 'accessibility' column
    # Remove 'hydropathy' from its current location
    # Insert 'hydropathy' right after 'accessibility'
    # Reorder dataframe
    # df_merged = df_merged.sort_values(by=['accessibility', 'hydropathy'], ascending=[False, False]).reset_index(drop=True)
    # Display result
    display(Markdown(df_merged.to_markdown(index=False)))
    return (df_merged,)


@app.cell
def _(Markdown, df_merged, display):
    df_filtered = df_merged[(df_merged['accessibility'] > 0.7)]
    display(Markdown(df_filtered.to_markdown(index=False)))
    return


@app.cell
def _(Markdown, df_merged, display):
    df_filtered_1 = df_merged[(df_merged['accessibility'] > 0.7) & (df_merged['hydropathy'] > 0.4)]
    display(Markdown(df_filtered_1.to_markdown(index=False)))
    return


@app.cell
def _(Markdown, df_merged, display):
    df_filtered_2 = df_merged[(df_merged['accessibility'] > 0.6) & (df_merged['hydropathy'] > 0.3)]
    display(Markdown(df_filtered_2.to_markdown(index=False)))
    return


@app.cell
def _(Markdown, df_merged, display):
    df_filtered_3 = df_merged[(df_merged['accessibility'] > 0.5) & (df_merged['hydropathy'] > 0.3)]
    display(Markdown(df_filtered_3.to_markdown(index=False)))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Detecting Inter-Chain Contacts
    To determine whether a particular chain (e.g., 'F') makes contact with other chains in a PDB structure, you can check for interatomic distances between residues in chain 'F' and residues in all other chains. If any atoms are closer than a distance threshold (commonly ~5 Å), it's considered a contact.
    """)
    return


@app.cell
def _(PDBParser, is_aa):
    from Bio.PDB import NeighborSearch

    def get_chain_contacts(pdb_file, target_chain_id='F', distance_threshold=3.5):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('structure', pdb_file)
        model = structure[0]
        target_atoms = []  # Use the first model
        other_atoms = []
        for chain in model:  # Collect atoms from chain F and other chains
            for residue in chain:
                if not is_aa(residue):
                    continue
                for atom in residue:
                    if chain.id == target_chain_id:
                        target_atoms.append(atom)
                    else:
                        other_atoms.append(atom)
        ns = NeighborSearch(other_atoms)
        contacts = set()
        for atom in target_atoms:
            neighbors = ns.search(atom.coord, distance_threshold)
            for neighbor in neighbors:
                neighbor_chain = neighbor.get_parent().get_parent().id  # Search for contacts using NeighborSearch
                if neighbor_chain != target_chain_id:
                    contacts.add(neighbor_chain)
        return list(contacts)
    pdb_file_3 = './../target/8d9y.pdb'
    contacting_chains = get_chain_contacts(pdb_file_3, target_chain_id='I')
    print(f"Chain 'I' contacts: {contacting_chains}")
    return (NeighborSearch,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Residue-Level Contact Map
    identify residue-residue contacts between chain 'F' and other chains in a PDB file. This means listing which residue in chain 'F' is close to which residue in other chains, based on a distance cutoff (usually ~5.0 Å).
    """)
    return


@app.cell
def _(NeighborSearch, PDBParser, display, is_aa, pd):
    def get_chain_residue_contacts(pdb_file, target_chain_id='F', distance_threshold=5.0):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('structure', pdb_file)
        model = structure[0]
        target_residues = [res for res in model[target_chain_id] if is_aa(res)]
        other_atoms = []
        atom_to_residue = {}
        for chain in model:
            if chain.id == target_chain_id:
                continue  # Build list of all atoms (excluding the target chain) and map them to residues
            for residue in chain:
                if not is_aa(residue):
                    continue
                for atom in residue:
                    other_atoms.append(atom)
                    atom_to_residue[atom] = residue
        ns = NeighborSearch(other_atoms)
        contacts = []
        for res_f in target_residues:
            for atom in res_f:
                neighbors = ns.search(atom.coord, distance_threshold)
                for neighbor in neighbors:
                    res_other = atom_to_residue[neighbor]  # Build neighbor search index
                    contact = {f'{target_chain_id}_residue_name': res_f.get_resname(), f'{target_chain_id}_residue_id': res_f.get_id()[1], 'contact_chain': res_other.get_parent().id, 'contact_residue_name': res_other.get_resname(), 'contact_residue_id': res_other.get_id()[1]}
                    contacts.append(contact)
        contacts = [dict(t) for t in {tuple(d.items()) for d in contacts}]  # Store residue-residue contacts
        return contacts
    contacts = get_chain_residue_contacts('./../target/8d9y.pdb', target_chain_id='I', distance_threshold=3)
    df_contacts = pd.DataFrame(contacts)
    df_contacts = df_contacts.sort_values(by='I_residue_id')
    display(df_contacts)  # Remove duplicates
    return (df_contacts,)


@app.cell
def _(df_contacts):
    f_residue_string = ",".join(df_contacts["I_residue_id"].apply(lambda x: f"I{x}").drop_duplicates())
    print(f_residue_string)
    return


@app.cell
def _():
    # contacts = get_chain_residue_contacts("./../out/bindcraft/snake-venom-binder/2506192105/Accepted/8d9y_l105_s971412_mpnn2_model2.pdb", target_chain_id='B', distance_threshold=3)
    # df_contacts_target = pd.DataFrame(contacts)
    # display(df_contacts_target)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Detect Disulfide Bonds in a Chain
    """)
    return


@app.cell
def _(PDBParser, is_aa):
    def find_disulfide_bonds(pdb_file, chain_id='F', distance_cutoff=2.2):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('struct', pdb_file)
        model = structure[0]
        chain = model[chain_id]
        sg_atoms = []
        residues = []
        for residue in chain:
            if is_aa(residue) and residue.get_resname() == 'CYS':
                if 'SG' in residue:  # Get all CYS SG atoms
                    sg_atoms.append(residue['SG'])
                    residues.append(residue)
        disulfides = []
        for i in range(len(sg_atoms)):
            for j in range(i + 1, len(sg_atoms)):
                dist = sg_atoms[i] - sg_atoms[j]
                if dist <= distance_cutoff:
                    disulfides.append((residues[i].get_id()[1], residues[j].get_id()[1]))
        return disulfides
    pdb_file_4 = './../target/8d9y.pdb'  # Search for SG-SG pairs within cutoff
    disulfide_bonds = find_disulfide_bonds(pdb_file_4, chain_id='I')
    print('Disulfide bonds (residue ID pairs):', disulfide_bonds)
    return


if __name__ == "__main__":
    app.run()

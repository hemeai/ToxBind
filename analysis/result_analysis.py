# %%
import subprocess
import re
import pandas as pd
import shutil

# %%
combined_df = pd.read_csv('./combined_data.csv')
combined_df.head()

# %%
combined_df.iterrows()

# %%
combined_df = pd.read_csv('./combined_data.csv')
results_ipae_df = pd.read_csv('./results_ipae.csv')

# %%
merged_df = pd.merge(combined_df, results_ipae_df, left_on='Design', right_on='Design')
merged_df

# %%
# for value in merged_df.columns.to_list(): 
#     print(value)

# %%
specific_columns = [
    'Rank',
    'Design',
    'Length',
    'ipae_score',
    'Average_i_pTM',
    'Target_Hotspot',
    'Sequence',
    'TargetSequence', 
    'TargetSequenceLength',
    'Average_pAE',
    'Average_i_pAE',
    'Average_pTM',
    'Average_pLDDT',
    'Average_i_pLDDT',
    'Average_ss_pLDDT',
    'Average_Target_RMSD',
    'Average_Hotspot_RMSD',
    'Average_Binder_pLDDT',
    'Average_Binder_pTM',
    'Average_Binder_pAE',
    'Average_Binder_RMSD',
    'DesignTime',
    'Notes',
    'TargetSettings',
    'Folder'
]

# %%
sorted_merged_df = merged_df.sort_values(by='ipae_score', ascending=True)
sorted_merged_df = sorted_merged_df[specific_columns]
# sorted_merged_df

# %%
sorted_merged_df.to_csv("final_results.csv", index=False)

# %%
fasta_file_name = "all_binder_fastas"
final_fasta_content = ""
# Iterate over each row of the DataFrame
for index, row in sorted_merged_df.iterrows():
    design = row['Design']
    binder_seq_len = row['Length']
    sequence = row['Sequence'] 

    # Create the FASTA file content
    fasta_content = f">{design}\n{sequence}\n\n"
    final_fasta_content += fasta_content

# Write the FASTA file
fasta_file_path = f"{fasta_file_name}.fasta"
with open(fasta_file_path, "w") as fasta_file:
    fasta_file.write(final_fasta_content)


# %%
shutil.copy('final_results.csv', '../final_results.csv')

# %%




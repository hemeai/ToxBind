<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->

# ToxBind: Snake Venom Binder

<div align="center">
  <img src="https://github.com/hemeai/ToxBind/blob/main/others/images/ToxBind.png?raw=true" width="100%"  alt="ToxBind Cover Image" />
</div>

## Table of Contents

1. [Introduction](#1-introduction)
2. [Target Protein Link](#2-target-protein-link)
3. [Designed Binder Results](#3-designed-binder-results)
4. [Choosing Hotspots](#4-choosing-hotspots)
5. [How to RUN](#5-how-to-run)
6. [TODO](#4-todo)
7. [References & Useful Links](#5-references-&-useful-links)

## 1. Introduction

This is a repository for the snake venom binder project using BindCraft. The project is based on the paper "De novo designed proteins neutralize lethal snake venom toxins[^1]" at [Baker lab](https://www.bakerlab.org/) (Awesome work). The paper describes the design of de novo anti-venoms that can neutralize different kinds of snake venom toxins. The approach varies in the methods for generating the binder. The paper used the RFDiffusion-based method. Here, we are using BindCraft, as it can create high-quality binders without using a lot of sampling. It has become my favorite method of choice for binder design. 

[^1]: Vázquez Torres, S., Benard Valle, M., Mackessy, S.P. et al. De-novo designed proteins neutralize lethal snake venom toxins. Nature 639, 225–231 (2025). https://doi.org/10.1038/s41586-024-08393-x

**Abstract from the paper:**

> Snakebite envenoming remains a devastating and neglected tropical disease, claiming over 100,000 lives annually and causing severe complications and long-lasting disabilities for many more. Three-finger toxins (3FTx) are highly toxic components of elapid snake venoms that can cause diverse pathologies, including severe tissue damage3 and inhibition of nicotinic acetylcholine receptors, resulting in life-threatening neurotoxicity4. At present, the only available treatments for snakebites consist of polyclonal antibodies derived from the plasma of immunized animals, which have high cost and limited efficacy against 3FTxs. Here, we used deep learning methods to de novo design proteins to bind short-chain and long-chain α-neurotoxins and cytotoxins from the 3FTx family. With limited experimental screening, we obtained protein designs with remarkable thermal stability, high binding affinity, and near-atomic-level agreement with the computational models. The designed proteins effectively neutralized all three 3FTx subfamilies in vitro and protected mice from a lethal neurotoxin challenge. Such potent, stable, and readily manufacturable toxin-neutralizing proteins could provide the basis for safer, cost-effective, and widely accessible next-generation antivenom therapeutics. Beyond snakebite, our results highlight how computational design could help democratize therapeutic discovery, particularly in resource-limited settings, by substantially reducing costs and resource requirements for the development of therapies for neglected tropical diseases.

It describes a way to 3 types of proteins
1. Short-chain alpha neurotoxin 
2. Long-chain alpha neurotoxin 
3. Cytotoxin 

The target protein for each type of toxin is selected. For cytotoxin, a consensus toxin is derived from many type of cytotoxin. Finally, the structure prediction is performed by AlphaFold2 and this structure is used for designing new anti venom struture. Currently, we will not focus on generating the consensus cytotoxin, instead, we will use the deposited structure (i.e., results from the paper) on the PDB (9BK6). 

"ScNtx" stands for "short-chain consensus alpha-neurotoxin," which is a synthetic protein designed to represent a typical short-chain alpha-neurotoxin found in the venom of various elapid snakes, like cobras; it is created by combining the most common amino acid sequences from multiple short-chain alpha-neurotoxins, essentially acting as a "consensus" toxin used for research and development of antivenoms due to its ability to trigger a broad immune response against similar toxins from different snake species [^2][^3][^4]

[^2]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9352773/ 
[^3]: https://pubmed.ncbi.nlm.nih.gov/29626299/ 
[^4]: https://www.nature.com/articles/s41467-022-32174-7

## 2. Designed Binder Results
Note: Designed binders are NOT yet experimentally validated.

Binder table: [final_results.csv](./final_results.csv)

Large files (Trajectory animations, plots) are not tracked in this repository due to size constraints.
Please download them from:
- [Google Drive Link](https://drive.google.com/drive/folders/1FNKq4x_s7st9nGh1GVHpGyuJaXnNYYe6?usp=sharing)

## 3. Target Toxin/Proteins 
We have the following targets: 
1. 1QKD: https://www.rcsb.org/structure/1QKD Erabutoxin
2. 1YI5: https://www.rcsb.org/structure/1YI5 Long alpha-neurotoxins, alpha-cobratoxin
3. 7Z14: https://www.rcsb.org/structure/7Z14 Short-chain neurotoxin
4. 5NQ4: https://www.rcsb.org/structure/5NQ4 S-type cobra cytotoxin

Overall, all targets can be classified into two categories: cytotoxins and neurotoxins. There are two types of neurotoxins: short-chain and long-chain. For the binder to be effective, it must neutralize all types of toxins present in the snake venom simultaneously. It is important to understand the conserved structural parts, i.e., regions with no mutations in amino acids.  

Let's try to understand the target structure better – what makes it unique and the importance of conserved amino acids for its function. I attempted secondary structure analysis using Biopython.

To create an effective binder, we should focus on three key areas:
  1. Conserved structural parts – Ensuring a single binder can neutralize diverse types of toxins.
  2. Likable amino acids – Better binding affinity leads to higher potency, allowing for a lower dose.
  3. Accessibility of structural parts – Even if certain parts are high affinity/likable amino acids in the target structure, they may be buried inside, making them harder to access. 

Let's explain three in detail: 
1. Conserved structural parts: 
TODO

2. Likable amino acids:
Amino acids that are hydrophobic in nature tend to be more favorable for binding sites. Therefore, we can focus on non-polar amino acids.

3. Accessibility of structural parts:
Using BioPython, we can analyze the [protein structure](./functions/7z14_secondary_structure_information.csv) and know the type of secondary structure of present, which sequence of which type of structure. Along, with that we can calculate the accessibity score, higher score means it is most present on the outside and has less steric hinderence posed by the adjacent residues & vice-versa. 

https://pmc.ncbi.nlm.nih.gov/articles/PMC9352773/

**Abstract from the paper:**
> Bites by elapid snakes (e.g., cobras) can result in life-threatening paralysis caused by venom neurotoxins blocking neuromuscular nicotinic acetylcholine receptors. Here, we determine the cryo-EM structure of the muscle-type Torpedo receptor in complex with ScNtx, a recombinant short-chain α-neurotoxin. ScNtx is pinched between loop C on the principal subunit and a unique hairpin in loop F on the complementary subunit, thereby blocking access to the neurotransmitter binding site. ScNtx adopts a binding mode that is tilted toward the complementary subunit, forming a wider network of interactions than those seen in the long-chain α-Bungarotoxin complex. Certain mutations in ScNtx at the toxin-receptor interface eliminate inhibition of neuronal α7 nAChRs but not of human muscle-type receptors. These observations explain why ScNtx binds more tightly to muscle-type receptors than neuronal receptors. Together, these data offer a framework for understanding subtype-specific actions of short-chain α-neurotoxins and inspire strategies for the  design of new snake antivenoms.

## 4. Choosing Hotspots

If you are a scientist and have experience working with a particular protein, it might be easy to pick the correct hotspots (target amino acids where the binder should try to make the contacts). And if the protein structure is small, then you could look at the 3D structure/any known binder and take a guess which area the model should target. However, guessing might not be the best approach; it might get you a good binder or worse, depending on your luck. So, we will bring some quantifiable metrics from which we can generate an initial target, and depending on the initial success, it can be tuned further. One thing to note is that quantifiable metrics don’t guarantee the generated binders are better. It may be better, or maybe not. Also, Bindcraft has a default way to choose the best binding area; if you cannot decide which side to target, leave the method to default. Based on the outcome, if you could try to co-relate which could be the potential hotspots for binding?

We have picked the 1YI5, a long-chain alpha-neurotoxin. Some metrics to quantify are polarity, loop type, accessibility, and hydropathy.


| Property   | Description |
|:-----------|-------------:|
| Accessibility         | A quantifiable way to check whether the amino acids of the chains are exposed outside or not. A positive value means it is accessible, and a negative value indicates the amino acids are inside the 3D structure. |
| Hydropathy          | This value signifies whether the nature of the amino acids is hydrophobic or hydrophilic; the general trend is to target hydrophobic amino acids/surfaces that do not interact with water. A positive value means it is more hydrophobic. |
| Polarity          | The polarity of amino acids is also important; polar amino acids gravitate more toward the solvent, i.e., water, and are less likely to participate in protein-protein interactions. That being said, it is not always the case. |
| Loop type          | Helix and loops are relatively stable, so targeting the amino acids part should be preferred. A protein's (tails) termini are very dynamic, so binding on the tails would not be easy. |


You can decide which order you want to use your parameters depending on your priority. Here, I have set to
Accessibility > Hydropathy > Polarity > Loop Type. 



The following table shows the properties of all amino acids in a structure. 

| chain_id   |   residue_id | residue_name   | property   | ss_type   | ss_code   |   accessibility |   hydropathy |    phi |    psi |   plddt | is_interface   |
|:-----------|-------------:|:---------------|:-----------|:----------|:----------|----------------:|-------------:|-------:|-------:|--------:|:---------------|
| F          |            1 | ILE            | nonpolar   | loop      | -         |       0.16568   |      nan     |  360   |  135.5 |    0.39 |                |
| F          |            2 | ARG            | positive   | sheet     | E         |       0.41129   |      nan     |  -77.2 |  117.5 |    0.39 |                |
| F          |            3 | CYS            | polar      | sheet     | E         |       0         |      nan     | -126.1 |  150.2 |    0.39 |                |
| F          |            4 | PHE            | nonpolar   | sheet     | E         |       0.258883  |      nan     |  -69.4 |  112.2 |    0.39 |                |
| F          |            5 | ILE            | nonpolar   | loop      | -         |       0.319527  |        0.944 |  -95.9 |  150.5 |    0.39 |                |
| F          |            6 | THR            | polar      | loop      | S         |       0.140845  |        0.367 | -112.8 |  147.8 |    0.39 |                |
| F          |            7 | PRO            | nonpolar   | loop      | S         |       0.294118  |        0.778 |  -93   |   23.6 |    0.39 |                |
| F          |            8 | ASP            | negative   | loop      | S         |       0.466258  |        0.067 |  -89.2 |  152.2 |    0.4  |                |
| F          |            9 | ILE            | nonpolar   | loop      | S         |       0.650888  |       -0.633 |  -79.6 |  -14.2 |    0.4  |                |
| F          |           10 | THR            | polar      | loop      | S         |       0.43662   |       -0.856 | -101.8 |  165.2 |    0.39 |                |
| F          |           11 | SER            | polar      | sheet     | E         |       0.292308  |       -0.956 |  -94   |  143.7 |    0.39 |                |
| F          |           12 | LYS            | positive   | sheet     | E         |       0.458537  |       -1.167 | -140.3 |  161.5 |    0.4  |                |
| F          |           13 | ASP            | negative   | sheet     | E         |       0.656442  |       -0.822 |  -90.2 |  102.3 |    0.4  |                |
| F          |           14 | CYS            | polar      | loop      | -         |       0.118519  |       -1.678 | -106.6 |  100   |    0.4  |                |
| F          |           15 | PRO            | nonpolar   | loop      | S         |       0.794118  |       -1.133 |  -59.1 |  117.1 |    0.4  |                |
| F          |           16 | ASN            | polar      | loop      | S         |       0.675159  |       -0.767 |    8.7 |   70.7 |    0.39 |                |
| F          |           17 | GLY            | nonpolar   | loop      | -         |       0.142857  |       -0.478 |  -83   |  112.5 |    0.4  |                |
| F          |           18 | HIS            | positive   | loop      | -         |       0.63587   |       -0.167 |  -70.6 |   -3.3 |    0.4  |                |
| F          |           19 | VAL            | nonpolar   | sheet     | E         |       0.126761  |       -0.878 | -137   |  141.5 |    0.39 |                |
| F          |           20 | CYS            | polar      | sheet     | E         |       0         |       -0.778 |  -95.5 |  130.2 |    0.39 |                |
| F          |           21 | TYR            | polar      | sheet     | E         |       0.193694  |       -0.489 | -124.1 |  153.5 |    0.39 |                |
| F          |           22 | THR            | polar      | sheet     | E         |       0.140845  |       -0.167 | -135.3 |   84.4 |    0.39 |                |
| F          |           23 | LYS            | positive   | sheet     | E         |       0.321951  |       -0.2   |  -69.2 |  138.9 |    0.4  |                |
| F          |           24 | THR            | polar      | sheet     | E         |       0.190141  |       -0.467 | -149.2 |  124.5 |    0.4  |                |
| F          |           25 | TRP            | nonpolar   | sheet     | E         |       0.14978   |       -0.433 | -147.4 |  149.1 |    0.39 |                |
| F          |           26 | CYS            | polar      | loop      | -         |       0.318519  |       -0.011 |  -93   |  119.6 |    0.4  |                |
| F          |           27 | ASP            | negative   | loop      | -         |       0.0858896 |       -0.022 | -101.9 | -149.4 |    0.39 |                |
| F          |           28 | ALA            | nonpolar   | loop      | S         |       0.0283019 |        0.911 |  -85.5 |  -40.6 |    0.39 |                |
| F          |           29 | PHE            | nonpolar   | loop      | T         |       0.0507614 |        0.489 |  -69.6 |   23.4 |    0.39 |                |
| F          |           30 | CYS            | polar      | helix     | H         |       0.0444444 |        0.544 | -107.2 |  -36.9 |    0.39 |                |
| F          |           31 | SER            | polar      | helix     | H         |       0.415385  |       -0.167 |  -65.1 |  -25.5 |    0.39 |                |
| F          |           32 | ILE            | nonpolar   | helix     | H         |       0.224852  |       -0.278 |  -84.1 |  -73   |    0.39 |                |
| F          |           33 | ARG            | positive   | helix     | H         |       0.0483871 |       -0.011 |  -95.1 |   -2.2 |    0.39 |                |
| F          |           34 | GLY            | nonpolar   | loop      | -         |       0.214286  |       -0.711 |  114.6 | -177.9 |    0.39 |                |
| F          |           35 | LYS            | positive   | loop      | -         |       0.326829  |       -0.567 |  -58.7 |  146.8 |    0.39 |                |
| F          |           36 | ARG            | positive   | sheet     | E         |       0.314516  |       -0.522 |  -73.8 |  146.9 |    0.39 |                |
| F          |           37 | VAL            | nonpolar   | sheet     | E         |       0.0211268 |       -0.744 | -134.8 |  121.2 |    0.39 |                |
| F          |           38 | ASP            | negative   | sheet     | E         |       0.319018  |       -0.044 | -106   |  114.1 |    0.39 |                |
| F          |           39 | LEU            | nonpolar   | sheet     | E         |       0.054878  |        0.2   |  -90   |  166.5 |    0.39 |                |
| F          |           40 | GLY            | nonpolar   | sheet     | E         |       0.047619  |        0.556 |  162.2 | -171.9 |    0.39 |                |
| F          |           41 | CYS            | polar      | sheet     | E         |       0.237037  |        1.333 | -122.4 |  162.8 |    0.4  |                |
| F          |           42 | ALA            | nonpolar   | sheet     | E         |       0.254717  |        0.689 | -163.5 |  168.6 |    0.39 |                |
| F          |           43 | ALA            | nonpolar   | loop      | S         |       0.603774  |        1     |  -63.4 |  -49.8 |    0.39 |                |
| F          |           44 | THR            | polar      | loop      | S         |       0.753521  |        1.044 | -138.3 |  169.9 |    0.4  |                |
| F          |           45 | CYS            | polar      | loop      | P         |       0.503704  |        0.656 |  -65.3 |  135.3 |    0.39 |                |
| F          |           46 | PRO            | nonpolar   | loop      | P         |       0.330882  |        0.3   |  -74.9 |  168.4 |    0.39 |                |
| F          |           47 | THR            | polar      | loop      | P         |       0.978873  |        0.056 |  -69   |  154.8 |    0.39 |                |
| F          |           48 | VAL            | nonpolar   | loop      | -         |       0.619718  |        0.322 | -112.8 |  115.6 |    0.4  |                |
| F          |           49 | LYS            | positive   | loop      | -         |       0.756098  |        0.011 |  -72.8 |  153.3 |    0.4  |                |
| F          |           50 | THR            | polar      | loop      | S         |       1         |        0.233 |  -75   |  122.2 |    0.4  |                |
| F          |           51 | GLY            | nonpolar   | loop      | S         |       0.619048  |        0.022 |   98.2 |  -37   |    0.39 |                |
| F          |           52 | VAL            | nonpolar   | loop      | -         |       0.197183  |        0.378 |  -51.9 |  143.8 |    0.39 |                |
| F          |           53 | ASP            | negative   | loop      | B         |       0.521472  |        0.189 | -123.2 |  126.6 |    0.4  |                |
| F          |           54 | ILE            | nonpolar   | loop      | -         |       0.284024  |        0.533 | -118   |  161.8 |    0.4  |                |
| F          |           55 | GLN            | polar      | loop      | -         |       0.717172  |        0.533 | -157.3 |  103.9 |    0.39 |                |
| F          |           56 | CYS            | polar      | sheet     | E         |       0.325926  |        0.189 |  -93.7 |  162.2 |    0.39 |                |
| F          |           57 | CYS            | polar      | sheet     | E         |       0.244444  |       -0.667 | -173.1 |  177.3 |    0.39 |                |
| F          |           58 | SER            | polar      | loop      | -         |       0.715385  |        0     | -141.9 |   12.9 |    0.39 |                |
| F          |           59 | THR            | polar      | loop      | S         |       0.683099  |       -0.889 |  -88.4 |  133.8 |    0.39 |                |
| F          |           60 | ASP            | negative   | loop      | S         |       0.662577  |       -0.678 |  -50   |  107.9 |    0.4  |                |
| F          |           61 | ASN            | polar      | loop      | S         |       0.33121   |       -0.644 |   63.7 |   81   |    0.39 |                |
| F          |           62 | CYS            | polar      | loop      | -         |       0.281481  |       -1.1   | -125.6 |    6.3 |    0.39 |                |
| F          |           63 | ASN            | polar      | loop      | -         |       0.0382166 |       -1.089 | -126.8 |   31   |    0.39 |                |
| F          |           64 | PRO            | nonpolar   | loop      | -         |       0.492647  |       -1.511 |  -64.6 | -177.9 |    0.39 |                |
| F          |           65 | PHE            | nonpolar   | loop      | -         |       0.365482  |      nan     |  -73   |  133.8 |    0.4  |                |
| F          |           66 | PRO            | nonpolar   | loop      | -         |       0.433824  |      nan     |  -78   |  176.3 |    0.4  |                |
| F          |           67 | THR            | polar      | loop      | -         |       0.901408  |      nan     | -107.5 |  -22.5 |    0.4  |                |
| F          |           68 | ARG            | positive   | loop      | -         |       0.516129  |      nan     | -178.2 |  360   |    0.4  |                |


Here, I have tried to filter based on accessibility > 0.7 and hydropathy > 0.4, after filtering we get two amino acids.

| chain_id   |   residue_id | residue_name   | property   | ss_type   | ss_code   |   accessibility |   hydropathy |    phi |   psi |   plddt | is_interface   |
|:-----------|-------------:|:---------------|:-----------|:----------|:----------|----------------:|-------------:|-------:|------:|--------:|:---------------|
| F          |           44 | THR            | polar      | loop      | S         |        0.753521 |        1.044 | -138.3 | 169.9 |    0.4  |                |
| F          |           55 | GLN            | polar      | loop      | -         |        0.717172 |        0.533 | -157.3 | 103.9 |    0.39 |                |

accessibility > 0.6 and hydropathy > 0.3

| chain_id   |   residue_id | residue_name   | property   | ss_type   | ss_code   |   accessibility |   hydropathy |    phi |   psi |   plddt | is_interface   |
|:-----------|-------------:|:---------------|:-----------|:----------|:----------|----------------:|-------------:|-------:|------:|--------:|:---------------|
| F          |           43 | ALA            | nonpolar   | loop      | S         |        0.603774 |        1     |  -63.4 | -49.8 |    0.39 |                |
| F          |           44 | THR            | polar      | loop      | S         |        0.753521 |        1.044 | -138.3 | 169.9 |    0.4  |                |
| F          |           48 | VAL            | nonpolar   | loop      | -         |        0.619718 |        0.322 | -112.8 | 115.6 |    0.4  |                |
| F          |           55 | GLN            | polar      | loop      | -         |        0.717172 |        0.533 | -157.3 | 103.9 |    0.39 |                |


accessibility > 0.5 and hydropathy > 0.3

| chain_id   |   residue_id | residue_name   | property   | ss_type   | ss_code   |   accessibility |   hydropathy |    phi |   psi |   plddt | is_interface   |
|:-----------|-------------:|:---------------|:-----------|:----------|:----------|----------------:|-------------:|-------:|------:|--------:|:---------------|
| F          |           43 | ALA            | nonpolar   | loop      | S         |        0.603774 |        1     |  -63.4 | -49.8 |    0.39 |                |
| F          |           44 | THR            | polar      | loop      | S         |        0.753521 |        1.044 | -138.3 | 169.9 |    0.4  |                |
| F          |           45 | CYS            | polar      | loop      | P         |        0.503704 |        0.656 |  -65.3 | 135.3 |    0.39 |                |
| F          |           48 | VAL            | nonpolar   | loop      | -         |        0.619718 |        0.322 | -112.8 | 115.6 |    0.4  |                |
| F          |           55 | GLN            | polar      | loop      | -         |        0.717172 |        0.533 | -157.3 | 103.9 |    0.39 |                |


Also, note that setting aggressive filters might leave the good hotspots. I would recommend keeping it at the bottom level and adjusting accordingly based on the outcome. 


## 5. How to RUN 



## 6. TODO
- [x] Combine all workflow into one
- [x] Remove duplicate runs and re-run the same thing again and again 
- [x] Add target sequence, Folder
- [x] PBD ID of the target sequence, Date, and BindCraft version
- [ ] Add GCP backend also
- [ ] Build consensus toxin with AF2
- [ ] Arrange sections for better readability 

## 7. References & Useful Links

Article:
https://www.bakerlab.org/2025/01/15/neutralizing-deadly-snake-toxins/

Crystal structure of the alpha-cobratoxin-AChBP complex
https://www.rcsb.org/3d-view/1YI5

https://en.wikipedia.org/wiki/Snake_venom
https://www.sciencedirect.com/science/article/abs/pii/B9780124158139000143
https://en.wikipedia.org/wiki/Amino_acid

Why This Is the Deadliest Venom in the World
https://www.youtube.com/watch?v=Y43QAqfTIcM

Snakebite venom variation and its impact on the efficacy of polyclonal antibody therapy: 
https://www.youtube.com/watch?v=lIpZC_ZH1Xw

Kurt Wibmer: Monoclonal antibodies neutralizing snake venom long & short chain 3-finger neurotoxins
https://www.youtube.com/watch?v=dYjPe4uWf0s

Evolution and diversification of snake venom toxins and venom glands
https://www.youtube.com/watch?v=mSkgitjnv8I

Characterization of a Novel Three-Finger Toxin in Blue Coral Snakes
https://www.youtube.com/watch?v=AISxPDUbf7k

Venoms and Toxins 2023: Flash talk by Anas Bedraoui (22-24 Aug 2023)
https://www.youtube.com/watch?v=XatqenCd_IU

Beta-neurotoxin
https://en.wikipedia.org/wiki/Inland_taipan#Venom
https://www.sciencedirect.com/science/article/abs/pii/S0028390807000056

How Horses Save Humans From Snakebites
https://www.youtube.com/watch?v=7ziWrneMYss

How Antivenom Is Made During A Global Shortage | Big Business | Business Insider
https://www.youtube.com/watch?v=nWjky1ITYSI

Snakebite capital: What India must get right
https://www.youtube.com/watch?v=7O_CbGipHhY

Universal Vaccines, Universal Anti-venom and Broadly Neutralizing Antibodies
https://www.youtube.com/watch?v=ZR0C_AetTCI&t=2326s

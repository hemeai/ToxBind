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
3. [Designed Snake Venom Binder](#3-designed-snake-venom-binder)
4. [TODO](#4-todo)
5. [References & Useful Links](#5-references-&-useful-links)

## 1. Introduction

This is a repository for the snake venom binder project using BindCraft. The project is based on the paper "De novo designed proteins neutralize lethal snake venom toxins[^1]" at [Baker lab](https://www.bakerlab.org/) (Awesome work). The paper describes the design of de novo anti-venoms that can neutralize different kinds of snake venom toxins. The approach varies in the methods for generating the binder. The paper used the RFDiffusion-based method. Here, we are using BindCraft, as it can create high-quality binders without using a lot of sampling. It has become my favorite method of choice for binder design. 

[^1]: Vázquez Torres, S., Benard Valle, M., Mackessy, S.P. et al. De-novo designed proteins neutralize lethal snake venom toxins. Nature 639, 225–231 (2025). https://doi.org/10.1038/s41586-024-08393-x

**Abstract from the paper:**

> Snakebite envenoming remains a devastating and neglected tropical disease, claiming over 100,000 lives annually and causing severe complications and long-lasting disabilities for many more. Three-finger toxins (3FTx) are highly toxic components of elapid snake venoms that can cause diverse pathologies, including severe tissue damage3 and inhibition of nicotinic acetylcholine receptors, resulting in life-threatening neurotoxicity4. At present, the only available treatments for snakebites consist of polyclonal antibodies derived from the plasma of immunized animals, which have high cost and limited efficacy against 3FTxs. Here, we used deep learning methods to de novo design proteins to bind short-chain and long-chain α-neurotoxins and cytotoxins from the 3FTx family. With limited experimental screening, we obtained protein designs with remarkable thermal stability, high binding affinity, and near-atomic-level agreement with the computational models. The designed proteins effectively neutralized all three 3FTx subfamilies in vitro and protected mice from a lethal neurotoxin challenge. Such potent, stable, and readily manufacturable toxin-neutralizing proteins could provide the basis for safer, cost-effective, and widely accessible next-generation antivenom therapeutics. Beyond snakebite, our results highlight how computational design could help democratize therapeutic discovery, particularly in resource-limited settings, by substantially reducing costs and resource requirements for the development of therapies for neglected tropical diseases.

It describes a way to 3 kinds of proteins
1. Short-chain alpha neurotoxin 
2. Long-chain alpha neurotoxin 
3. Cytotoxin 

The target protein for each type of toxin is selected. For cytotoxin, a consensus toxin is derived from many type of cytotoxin. Finally, the structure prediction is performed by AlphaFold2 and this structure is used for designing new anti venom struture. Currently, we will not focus on generating the consensus cytotoxin, instead, we will use the deposited structure (i.e., results from the paper) on the PDB. 

"ScNtx" stands for "short-chain consensus alpha-neurotoxin," which is a synthetic protein designed to represent a typical short-chain alpha-neurotoxin found in the venom of various elapid snakes, like cobras; it is created by combining the most common amino acid sequences from multiple short-chain alpha-neurotoxins, essentially acting as a "consensus" toxin used for research and development of antivenoms due to its ability to trigger a broad immune response against similar toxins from different snake species [^2][^3][^4]

[^2] https://pmc.ncbi.nlm.nih.gov/articles/PMC9352773/ 
[^3] https://pubmed.ncbi.nlm.nih.gov/29626299/ 
[^4] https://www.nature.com/articles/s41467-022-32174-7

## 2. Designed Snake Venom Binder
Note: Designed binders are not yet validated experimentally.

Binder table: [final_results.csv](./final_results.csv)

Large files (Trajectory animations, plots) are not tracked in this repository due to size constraints.
Please download them from:
- [Google Drive Link](https://drive.google.com/drive/folders/1Gxfo3N9OhU5ZyxvZsio3WGBP6lHr02mt)

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

## 4. TODO
- [x] Combine all workflow into one
- [x] Remove duplicate runs and re-run the same thing again and again 
- [x] Add target sequence, Folder
- [x] PBD ID of the target sequence, Date, and BindCraft version
- [ ] Add GCP backend also
- [ ] Build consensus toxin with AF2
- [ ] Arrange sections for better readability 

## 5. References & Useful Links

Article:
https://www.bakerlab.org/2025/01/15/neutralizing-deadly-snake-toxins/

Crystal structure of the a-cobratoxin-AChBP complex
https://www.rcsb.org/3d-view/1YI5

https://en.wikipedia.org/wiki/Snake_venom
https://www.sciencedirect.com/science/article/abs/pii/B9780124158139000143
https://en.wikipedia.org/wiki/Amino_acid

<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->

# ToxBind: Snake Venom Binder

## Table of Contents

1. [Introduction](#1-introduction)
2. [Target Protein Link](#2-target-protein-link)
3. [Designed Snake Venom Binder](#3-designed-snake-venom-binder)
4. [TODO](#4-todo)
5. [References & Useful Links](#5-references-&-useful-links)

## 1. Introduction

This is a repository for the snake venom binder project using BindCraft. The project is based on the paper "De novo designed proteins neutralize lethal snake venom toxins" by the Baker lab (Awesome work). The paper describes the design of a protein that can neutralize snake venom toxins.

Paper link:
De novo-designed proteins neutralize lethal snake venom toxins
https://www.nature.com/articles/s41586-024-08393-x

**Abstract from the paper:**

> Snakebite envenoming remains a devastating and neglected tropical disease, claiming over 100,000 lives annually and causing severe complications and long-lasting disabilities for many more1,2. Three-finger toxins (3FTx) are highly toxic components of elapid snake venoms that can cause diverse pathologies, including severe tissue damage3 and inhibition of nicotinic acetylcholine receptors, resulting in life-threatening neurotoxicity4. At present, the only available treatments for snakebites consist of polyclonal antibodies derived from the plasma of immunized animals, which have high cost and limited efficacy against 3FTxs5,6,7. Here we used deep learning methods to de novo design proteins to bind short-chain and long-chain α-neurotoxins and cytotoxins from the 3FTx family. With limited experimental screening, we obtained protein designs with remarkable thermal stability, high binding affinity and near-atomic-level agreement with the computational models. The designed proteins effectively neutralized all three 3FTx subfamilies in vitro and protected mice from a lethal neurotoxin challenge. Such potent, stable and readily manufacturable toxin-neutralizing proteins could provide the basis for safer, cost-effective and widely accessible next-generation antivenom therapeutics. Beyond snakebite, our results highlight how computational design could help democratize therapeutic discovery, particularly in resource-limited settings, by substantially reducing costs and resource requirements for the development of therapies for neglected tropical diseases.

"ScNtx" stands for "short-chain consensus alpha-neurotoxin," which is a synthetic protein designed to represent a typical short-chain alpha-neurotoxin found in the venom of various elapid snakes, like cobras; it is created by combining the most common amino acid sequences from multiple short-chain alpha-neurotoxins, essentially acting as a "consensus" toxin used for research and development of antivenoms due to its ability to trigger a broad immune response against similar toxins from different snake species. [1, 2, 3]

[1] https://pmc.ncbi.nlm.nih.gov/articles/PMC9352773/ <br>
[2] https://pubmed.ncbi.nlm.nih.gov/29626299/ <br>
[3] https://www.nature.com/articles/s41467-022-32174-7 <br>

## 2. Designed Snake Venom Binder

One of the binder in cartoon and molecular surface representation.

<img src="./others/images/5nq4_l84_s3585_mpnn4_model2_cartoon.png" width="300" height="350" /> <img src="./others/images/5nq4_l84_s3585_mpnn4_model2.png" width="300" height="350" />

Note: Designed binders are not yet validated experimentally.

Binder table: [final_results.csv](./final_results.csv)

Large files (Trajectory animations, plots) are not tracked in this repository due to size constraints.
Please download them from:

- [Google Drive Link](https://drive.google.com/drive/folders/1Gxfo3N9OhU5ZyxvZsio3WGBP6lHr02mt)

## 3. Target Protein Link

7Z14: https://www.rcsb.org/structure/7Z14

https://pmc.ncbi.nlm.nih.gov/articles/PMC9352773/

**Abstract from the paper:**

> Bites by elapid snakes (e.g. cobras) can result in life-threatening paralysis caused by venom neurotoxins blocking neuromuscular nicotinic acetylcholine receptors. Here, we determine the cryo-EM structure of the muscle-type Torpedo receptor in complex with ScNtx, a recombinant short-chain α-neurotoxin. ScNtx is pinched between loop C on the principal subunit and a unique hairpin in loop F on the complementary subunit, thereby blocking access to the neurotransmitter binding site. ScNtx adopts a binding mode that is tilted toward the complementary subunit, forming a wider network of interactions than those seen in the long-chain α-Bungarotoxin complex. Certain mutations in ScNtx at the toxin-receptor interface eliminate inhibition of neuronal α7 nAChRs, but not of human muscle-type receptors. These observations explain why ScNtx binds more tightly to muscle-type receptors than neuronal receptors. Together, these data offer a framework for understanding subtype-specific actions of short-chain α-neurotoxins and inspire strategies for design of new snake antivenoms.

## 4. TODO

- [ ] Combine all workflow into one
- [ ] Add target sequence, PBD ID of target sequence, Date and BindCraft version
- [ ] Add GCP backend also
- [ ] Build consensus toxin with AF2

## 5. References & Useful Links

Article:
https://www.bakerlab.org/2025/01/15/neutralizing-deadly-snake-toxins/

Crystal structure of the a-cobratoxin-AChBP complex
https://www.rcsb.org/3d-view/1YI5

https://en.wikipedia.org/wiki/Snake_venom
https://www.sciencedirect.com/science/article/abs/pii/B9780124158139000143
https://en.wikipedia.org/wiki/Amino_acid

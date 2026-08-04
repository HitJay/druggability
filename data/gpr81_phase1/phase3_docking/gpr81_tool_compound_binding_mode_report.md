# GPR81 tool-compound binding-mode analysis (Phase 3)

> This is a computational pose comparison. It does not prove agonism, affinity, or selectivity.

Docking receptors: 8Z87, 8Z8A, 9KT9. Apo 8Z8B was excluded because its pocket box was not transferred without structural alignment.

## Pose summary

### 3_5_DHBA
- 8Z87: pose1=-6.443 kcal/mol; score span=0.294; core contact fraction=0.667; core residues=71;75;92;167;168;261;264;268; warning=none
- 8Z8A: pose1=-6.280 kcal/mol; score span=0.340; core contact fraction=0.667; core residues=71;92;95;167;168;261;264;268; warning=none
- 9KT9: pose1=-5.649 kcal/mol; score span=0.264; core contact fraction=0.000; core residues=none; warning=none

### 3_OBA
- 8Z87: pose1=-4.783 kcal/mol; score span=0.460; core contact fraction=0.583; core residues=71;75;167;168;261;264;268; warning=none
- 8Z8A: pose1=-4.638 kcal/mol; score span=0.465; core contact fraction=0.583; core residues=71;75;167;168;261;264;268; warning=none
- 9KT9: pose1=-4.013 kcal/mol; score span=0.357; core contact fraction=0.000; core residues=none; warning=none

### AZ1_GPR81_agonist_2
- 8Z87: pose1=10.134 kcal/mol; score span=0.000; core contact fraction=0.833; core residues=71;75;92;95;165;167;168;261;264;268; warning=positive_or_weak_score
- 8Z8A: pose1=-3.940 kcal/mol; score span=1.846; core contact fraction=0.500; core residues=92;95;96;99;167;168; warning=broad_pose_ensemble
- 9KT9: pose1=-0.843 kcal/mol; score span=0.556; core contact fraction=0.000; core residues=none; warning=positive_or_weak_score

### CHBA
- 8Z87: pose1=-6.300 kcal/mol; score span=0.373; core contact fraction=0.667; core residues=71;75;99;167;168;261;264;268; warning=none
- 8Z8A: pose1=-5.929 kcal/mol; score span=0.093; core contact fraction=0.667; core residues=71;75;92;167;168;261;264;268; warning=none
- 9KT9: pose1=-5.908 kcal/mol; score span=0.468; core contact fraction=0.000; core residues=none; warning=none

### GPR81_agonist_1
- 8Z87: pose1=-4.856 kcal/mol; score span=2.926; core contact fraction=0.000; core residues=none; warning=broad_pose_ensemble
- 8Z8A: pose1=-7.730 kcal/mol; score span=1.563; core contact fraction=0.083; core residues=167; warning=broad_pose_ensemble
- 9KT9: pose1=-4.657 kcal/mol; score span=1.500; core contact fraction=0.000; core residues=none; warning=none

## Interpretation rules

- More negative Vina score is only a local computational ranking signal.
- A credible comparison requires compatible pocket occupancy, reproducible contacts across receptor conformations, and agreement with experimental biology.
- AZ1 and GPR81 agonist 1 should be treated cautiously if pose scores are weak/positive or if the pose ensemble is broad.
- The next report should overlay aligned receptor structures and compare ligand poses in a common coordinate frame.

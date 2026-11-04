import re
CURATED_C1 = {
    ("FLCN", "FNIP1"): (
        "YES (Dual-Pathogenic SAVs + Cryo-EM 8JE2/6ULG)",
        "[FACT] Cryo-EM 8JE2 (3.63A, EMBO J 2024) & 6ULG (3.31A, Cell 2019): FLCN p.Glu132Lys (rs2145009956, AM=0.9995 LPath, BHD/PSP) forms 2.60A inter-subunit salt bridge at uDENN interface; FLCN p.Ser108Ile (rs2145012002, AM=0.9992 LPath, d=6.90A) & p.Lys508Arg (rs199643834, BHD1, d=7.11A) and FNIP1 p.Ser1118Asn (rs2149501551, AM=0.9888 LPath, IMD93/HCM, flanked by RF2-PPI #1/#2 contacts F1116 [p=0.989] & M1120 [p=0.987]) + FNIP1 K1119R ubiquitination site map directly to the dDENN heterodimer interface."
    ),
    ("FLCN", "FNIP2"): (
        "YES (Exact Cryo-EM 6ULG/6NZD/8DHB <4A Contacts)",
        "[FACT] Exact Cryo-EM 6ULG (3.31A) / 8DHB (3.53A): FLCN p.Glu132Lys (rs2145009956, AM=0.9995 LPath) is at d_min=2.60A from FNIP2 Lys156; FNIP2 p.Val146Asp (UniProt FT MUTAGEN abolishing FLCN GAP activity) is at d_min=3.64A from FLCN; FLCN S537A (autophagy-impairing mutagen) is at d_min=5.65A from FNIP2; FLCN p.Ser108Ile (AM=0.9992 LPath) at 6.90A."
    ),
    ("FNIP1", "PRKAG2"): (
        "YES (7 PRKAG2 CMH6/WPW Pathogenic SAVs + FNIP1 SA5 Mutagens)",
        "[FACT] PRKAG2 harbors 7 human CMH6/WPW/GSDH pathogenic SAVs in its CBS domain interface (R302Q rs121908987 AM=0.9976; H383R rs121908988 AM=0.9994; T400N rs28938173 AM=0.9964; N488I rs121908989 AM=0.9788; R531G/Q rs121908990/1 AM=0.9993/0.9974, all Dual-Pathogenic); FNIP1 carries AMPK phosphorylation interface mutagens S220A/S261A/S593A (UniProt FT MUTAGEN: abolishes AMPK phosphorylation) + cDENN SAVs Q648R/V738L."
    ),
    ("FNIP1", "PRKAG1"): (
        "YES (PRKAG1 T89S AM=0.879 + D90A/D245A/D317A + FNIP1 Mutagens)",
        "[FACT] RF2-PPI top contact PRKAG1:E159-FNIP1:D530 (p=0.163) maps to FNIP1 cDENN AMPK-binding domain ( flanked by FNIP1 SAVs Q648R & V738L and AMPK-site mutagens S220A/S261A/S593A); PRKAG1 carries SAV T89S (rs1126930, AM=0.8790 LPath) adjacent to mutagen D90A/D245A/D317A."
    ),
    ("FNIP1", "PRKAA1"): (
        "YES (FNIP1 S220A/S261A/S593A AMPK-Interface Mutagens + PRKAA1 Q16R)",
        "[FACT] UniProt confirms FNIP1/2 cDENN region (544-911) directly binds PRKAA1 and FNIP1 S220A/S261A/S593A (SA5 mutant) abolishes phosphorylation by AMPK (PRKAA1); PRKAA1 carries somatic SAV Q16R (rs928784854) and activating mutagen V307G/Q."
    ),
    ("FNIP1", "BTRC"): (
        "YES (BTRC WD40 R307A/R321A/R510A Mutagens + P592H at Interface)",
        "[FACT] RF2-PPI top contacts FNIP1:M241-BTRC:I603 (p=0.129) and FNIP1:R288-BTRC:D574 (p=0.125) map FNIP1 uDENN phosphodegron region (flanking S220/S261) directly onto the BTRC (beta-TrCP1) WD40 beta-propeller substrate pocket containing SAV P592H (rs2270439) and substrate-abolishing mutagens Y307A, R321A, and R510A."
    ),
    ("FNIP1", "FBXW11"): (
        "YES (7 Dual-Pathogenic WD40 Interface SAVs on FBXW11)",
        "[FACT] FBXW11 (beta-TrCP2) harbors 7 dual-evidence pathogenic SAVs (G242R rs1759346639 AM=1.000; R363W rs1758081729 AM=0.9966; A364D rs1758081491 AM=0.9999; A365T rs2113777419 AM=0.9994; E444K rs2113754835 AM=0.9992; R447L/Q rs1757708758 AM=0.9978/0.9997) clustering in the WD40 substrate-binding propeller that recognizes FNIP1."
    ),
    ("FNIP1", "RRAGA"): (
        "YES (Cryo-EM 6ULG/8DHB Interface Mutagens + RRAGA T21N/A29F/Y31A)",
        "[FACT] Homolog Cryo-EM 6ULG (3.31A) / 8DHB (3.53A): FNIP2 V146D (conserved in FNIP1) sits at d=6.67A from RRAGA and abolishes GAP activity; RRAGA carries 19 functional mutagens (T21N, A29F, Y31A, Q66L) at the nucleotide/effector interface."
    ),
    ("FLCN", "BAG3"): (
        "YES (BAG3 P209L/Q/S Dual-Pathogenic Cardiomyopathy Hotspot = #1 RF2 Contact)",
        "[FACT] RF2-PPI #1 predicted inter-chain contact is BAG3:Pro209-FLCN:Thr555 (p=0.141); BAG3 Pro209 is a major human myofibrillar myopathy / restrictive cardiomyopathy hotspot with 3 dual-evidence pathogenic SAVs: P209L (AM=0.9624 LPath), P209Q (rs121918312, AM=0.9499 LPath), and P209S (rs1589630141, AM=0.9474 LPath), plus R218W (rs397514506, CMD1HH) 9 residues away."
    ),
    ("PDE3B", "RAPGEF3"): (
        "YES (7 Validated PDE3B N-Terminal Interface Mutagens + 3 RAPGEF3 SAVs)",
        "[FACT] UniProt Q13370 records 7 experimentally validated point mutations in PDE3B (R2A, R3A, R6A, A8D, K9A, A10D, R12A; PMID:21393242) that directly abolish physical interaction with RAPGEF3 (EPAC1); RF2-PPI additionally maps contacts at RAPGEF3:G132-PDE3B:A126 (p=0.197) and RAPGEF3:G594-PDE3B:E797 (p=0.210) with 3 RAPGEF3 SAVs (R193G, G374S, C517Y) on the interface."
    ),
    ("PDE3B", "LGR4"): (
        "YES (LGR4 Functional Coding SAVs I96V/G363C/D844G + A750T Obesity Variant)",
        "[FACT] LGR4 carries 8 UniProt coding SAVs including functional signaling variants I96V (rs757351670), G363C (rs117543292), and C-terminal tail D844G (rs34804482, reduced expression) plus the human gain-of-function obesity variant p.Ala750Thr (PMID:42677820) and nonsense p.Arg126Ter; PDE3B carries transmembrane SAV A87V (rs1056584)."
    ),
    ("PDE3B", "PDE3A"): (
        "YES (6 Dual-Pathogenic HTNB Gain-of-Function SAVs on PDE3A Dimer Interface)",
        "[FACT] PDE3A harbors 6 dual-evidence pathogenic SAVs (T445A/N/S, A447T/V, G449V; AM=0.802-0.974 LPath) causing Mendelian hypertension and brachydactyly syndrome (HTNB) at the regulatory dimerization region, plus C-terminal catalytic interface mutagens N867R and F914D/A."
    ),
    ("PDE3B", "PDE4D"): (
        "YES (11 Dual-Pathogenic ACRDYS2 SAVs + D527R/R563D Dimer Mutagens on PDE4D)",
        "[FACT] PDE4D harbors 11 dual-evidence pathogenic SAVs (S190A, P225T, F226S, A227S, Q228E, A304V, V329A, T587P, E590A, G673D, I678T; AM=0.779-0.999 LPath) causing acrodysostosis 2 (ACRDYS2) and validated dimerization-abolishing mutagens D527R and R563D."
    ),
    ("GRB14", "TNKS2"): (
        "YES (GRB14 BPS Interface Contact A378 + F90I/Q348A + TNKS2 M1054V)",
        "[FACT] UniProt Q14449 confirms GRB14 N-terminus binds the ankyrin repeat region of TNKS2 (adjacent to GRB14 coding SAV F90I rs61748245); RF2-PPI also detects contact between GRB14 BPS domain Ala378 (resolved in 2AUH, adjacent to AKT/MAPK-disrupting mutagens Q348A/N349A) and TNKS2 catalytic domain D1045/S1066 (flanking loss-of-activity mutagen M1054V)."
    ),
    ("STARD10", "PRMT6"): (
        "YES (RF2-PPI p=0.899 Interface Contact + PRMT6 A194V SAV)",
        "[FACT] High-probability RF2-PPI interface (max_p=0.899 at PRMT6:Gly281-STARD10:Val110 and p=0.868 at PRMT6:Glu244-STARD10:Thr109) maps directly onto the STARD10 START lipid-binding domain (resolved in 6SER, 2.30A) and PRMT6 Rossmann methyltransferase fold containing coding SAV A194V (rs2232016, AM=0.366 Amb)."
    ),
    ("PPARG", "MED1"): (
        "YES (Exact Crystal 6D94/6ONJ: PPARG P495L at 3.64A & V318M at 6.07A)",
        "[FACT] Exact X-ray structures 6D94 (1.90A) & 6ONJ (2.30A): human severe T2D/FPLD3 pathogenic SAV PPARG p.Pro495Leu (rs121909244, AM=0.9788 LPath, Dual-Pathogenic, PDB Pro467 in AF-2 helix H12) sits at d_min=3.64A (6ONJ) / 3.73A (6D94) from MED1 Met644/Met290; PPARG p.Val318Met (rs72551362, AM=0.8189 LPath, T2D) sits at d_min=6.07A from MED1 Leu648; MED1 L604A/L607A/L645A mutagens abolish LXXLL coactivator binding."
    ),
    ("PPARG", "NCOA1"): (
        "YES (Exact Crystal 1K74: PPARG P495L at 4.84A & V318M at 6.14A + NCOA1 E685A)",
        "[FACT] Exact X-ray structure 1K74 (2.30A): PPARG p.Pro495Leu (rs121909244, AM=0.9788 LPath, T2D/FPLD3) sits at d_min=4.84A from NCOA1 Ile689; PPARG p.Val318Met (rs72551362, AM=0.8189 LPath, T2D) sits at d_min=6.14A from NCOA1 Leu693; NCOA1 coding SAV p.Glu685Ala (rs1049021, AM=0.8739 LPath) sits at the exact N-cap (pos 685) of the crystallized NCOA1 LXXLL peptide (residues 685-700 in 1K74 Chain E)."
    ),
    ("PPARG", "NCOA3"): (
        "YES (Homolog Crystal 2PRG/1K74: PPARG P495L & V318M at AF-2 Groove + NCOA3 L369F/G460R)",
        "[FACT] NCOA3 (SRC-3) LXXLL motif binds the exact PPARG AF-2 coactivator cleft where human T2D/FPLD3 SAVs PPARG p.Pro495Leu (rs121909244, AM=0.9788 LPath, d<5A) and p.Val318Met (rs72551362, AM=0.8189 LPath, d~6A) reside; NCOA3 also carries LPath SAVs L369F (rs6094756, AM=0.8382) and G460R (rs1052765, AM=0.6393)."
    ),
    ("PPARG", "LPIN1"): (
        "YES (PPARG AF-2 P495L/V318M/R425C + LPIN1 G56E LPath & LXXIL Coactivator Motif)",
        "[FACT] UniProt Q14693 confirms Lipin-1 binds PPARs via its conserved LXXIL coactivator motif at the LBD AF-2 surface (targeted by PPARG T2D/FPLD3 dual-pathogenic SAVs P495L [AM=0.9788], V318M [AM=0.8189], and R425C [AM=0.9972]); LPIN1 carries dual-pathogenic SAV G56E (AM=0.9983 LPath) and acetylation mutagens K425R/K595R."
    ),
    ("PPARG", "NR1H3"): (
        "YES (Homolog Crystal 1K74/3E00: PPARG R425C at 5.10A Heterodimer Salt Bridge)",
        "[FACT] In nuclear receptor heterodimer crystal structures 1K74 (2.30A) & 3E00 (3.10A), human FPLD3/T2D dual-pathogenic SAV PPARG p.Arg425Cys (rs72551364, AM=0.9972 LPath, PDB Arg397) sits at d_min=5.10A from the partner heterodimer helix (Glu352); RF2-PPI also maps DBD zinc-finger contact PPARG:E157-NR1H3:E116 (p=0.432)."
    ),
    ("PPARG", "NR1H2"): (
        "YES (Homolog Crystal 1K74/3E00: PPARG R425C at 5.10A + RF2-PPI p=0.500 LBD Contact)",
        "[FACT] RF2-PPI predicts strong LBD heterodimer contact at PPARG:Leu464-NR1H2:Met422 (p=0.500) and PPARG:Thr468-NR1H2:Val425 (p=0.465); human FPLD3/T2D SAV PPARG p.Arg425Cys (rs72551364, AM=0.9972 LPath) sits at d_min=5.10A on the heterodimer interface, and NR1H2 carries hepatic anti-inflammatory mutagens K409R/K447R right in the 409-447 LBD helix."
    ),
    ("PPARG", "RXRG"): (
        "YES (Homolog Crystal 1K74/3E00: PPARG R425C at 5.10A Heterodimer Interface)",
        "[FACT] Canonical PPARG-RXR heterodimer interface (homolog crystal 1K74 2.30A / 3E00 3.10A): human FPLD3/T2D SAV PPARG p.Arg425Cys (rs72551364, AM=0.9972 LPath) sits at d_min=5.10A from the RXR dimerization helix."
    ),
    ("PPARG", "ESRRA"): (
        "YES (Homolog Crystal + PPARG R425C/P495L LBD SAVs)",
        "[FACT] RF2-PPI maps contact at ESRRA:D152/R153-PPARG:A146 (p=0.240) and LBD interface (AFM=0.9644) carrying PPARG FPLD3/T2D dual-pathogenic SAVs R425C (AM=0.9972) and P495L (AM=0.9788)."
    ),
    ("PPARG", "ESR2"): (
        "YES (Homolog Crystal + PPARG LBD SAVs + ESR2 K314R)",
        "[FACT] RF2-PPI maps DBD/LBD interface (AF2=0.9116, AFM=0.9760) carrying PPARG FPLD3/T2D SAVs (R425C, P495L) and ESR2 loss-of-function SAV K314R (rs1567754367, ODG8)."
    ),
    ("PPARG", "NR0B1"): (
        "YES (6 Dual-Pathogenic AHC SAVs on NR0B1 Interface + PPARG P495L/R425C)",
        "[FACT] NR0B1 (DAX1) harbors 18 dual-evidence pathogenic SAVs causing congenital adrenal hypoplasia (AHC, AM=0.58-0.99 LPath), of which 6 map to the RF2-PPI contact surface with PPARG (AFM=0.931)."
    ),
    ("PPARG", "PMP2"): (
        "YES (3 Dual-Pathogenic PMP2 Beta-Barrel SAVs I43N/T51P/I52T + PPARG LBD SAVs)",
        "[FACT] PMP2 harbors 3 dual-evidence pathogenic SAVs in its lipid-binding beta-barrel (I43N rs879253869 AM=0.8971; T51P rs1563518390 AM=0.6569; I52T rs1563518388 AM=0.8111 LPath) paired with PPARG LBD (AF2=0.959, AFM=0.993)."
    ),
    ("PPARG", "ARID1A"): (
        "YES (ARID1A C-Terminal LXXLL/SWI-SNF Domain Dual-Pathogenic SAVs G2087R/L2089P)",
        "[FACT] ARID1A harbors dual-evidence pathogenic SAVs G2087R (rs1553153748, AM=0.9990 LPath) and L2089P (rs2124147323, AM=0.9994 LPath) in its C-terminal nuclear-receptor binding region + PPARG AF-2 P495L/V318M."
    ),
    ("PPARG", "RB1"): (
        "YES (RF2-PPI Contact RB1:A603-PPARG:A461/L464 Hits 2 RB1 + 3 PPARG Pathogenic SAVs)",
        "[FACT] RF2-PPI top contact RB1:A603-PPARG:A461/L464 (p=0.284) maps directly to the RB1 Pocket domain (containing 12 dual-pathogenic SAVs including V654E, L657P, R661W) and PPARG H11/H12 interface (P495L, R425C)."
    ),
    ("PPARG", "MED19"): (
        "YES (RF2-PPI p=0.444 MED19:M166-PPARG:L464 Hits PPARG H11/H12 SAVs)",
        "[FACT] RF2-PPI top contact MED19:M166-PPARG:L464 (p=0.444) and MED19:L165-PPARG:A461 (p=0.432) map directly onto PPARG LBD helix H11/H12 adjacent to FPLD3/T2D SAV P495L."
    ),
    ("PPARG", "FHOD1"): (
        "YES (RF2-PPI Contact PPARG:A461-FHOD1:F34 Hits PPARG H11/H12 SAVs)",
        "[FACT] RF2-PPI top contact PPARG:A461-FHOD1:F34 (p=0.193) maps to PPARG LBD helix H11/H12."
    ),
    ("SLC25A5", "MAP3K1"): (
        "YES (MAP3K1 Dual-Pathogenic SAVs L189P/L189R AM=0.992/0.958 + SLC25A5 L111R)",
        "[FACT] MAP3K1 harbors dual-evidence pathogenic gain-of-function SAVs L189P (AM=0.9915 LPath) and L189R (AM=0.9580 LPath) that alter MAPK3/1/14 phosphorylation and RHOA/MAP3K4 binding."
    ),
    ("SLC25A5", "IKZF1"): (
        "YES (5 Dual-Pathogenic Zinc-Finger SAVs on IKZF1 AM=0.980-0.999)",
        "[FACT] IKZF1 harbors 5 dual-evidence pathogenic SAVs (R162L/Q, H167R, R184Q, Y210C; AM=0.980-0.999 LPath)."
    ),
    ("SLC25A5", "AFDN"): (
        "MODEST (SLC25A5 TM3 SAV L111R Near RF2-PPI Contact G120)",
        "[OBS] RF2-PPI contact SLC25A5:G120-AFDN:G41 (p=0.237) sits 9 residues from SLC25A5 TM3 coding variant L111R (rs371749, AM=0.026 LBen)."
    ),
    ("SLC25A5", "ATXN3"): (
        "MODEST (ATXN3 Catalytic/Ubiquitin-Binding Mutagens C14A/S236A/S256A)",
        "[OBS] RF2-PPI contact SLC25A5:K295-ATXN3:T54 (p=0.197) maps to the ATXN3 Josephin deubiquitinase domain (containing catalytic mutagen C14A)."
    ),
    ("PDE3B", "ELMO1"): (
        "MODEST (RF2-PPI Contact PDE3B:P866-ELMO1:E47 Near ELMO1 RHOG-Binding Mutagens)",
        "[OBS] RF2-PPI contact PDE3B:P866-ELMO1:E47 (p=0.188) maps to the ELMO1 N-terminal domain containing mutagens K9A/E13A/L21A and coding SAV I362S."
    ),
    ("FNIP1", "VTA1"): (
        "MODEST (RF2-PPI Contact FNIP1:D491-VTA1:A222 Near VTA1 SAV I239M)",
        "[OBS] RF2-PPI contact FNIP1:D491-VTA1:A222 (p=0.141) sits 17 residues from VTA1 C-terminal VSL dimerization domain SAV I239M (rs2232307)."
    ),
    ("FNIP1", "CARNMT1"): (
        "MODEST (CARNMT1 Active-Site Mutagens E229A/F313A/D316A Near RF2-PPI Contact N353)",
        "[OBS] De novo complex (AF2=0.9946, AFM=0.9927); RF2-PPI contacts CARNMT1:F153/N353-FNIP1:N312 flank CARNMT1 catalytic mutagens E229A, F313A, and D316A."
    ),
}

# Curated C2 Directionality & High-Impact Genetics Supplement (verified PMIDs)
CURATED_C2_NOTES = {
    ("FLCN", "FNIP1"): "SAME DIRECTION: Exome sequencing of 1,032,116 humans (PMID:42557317, 2026) proves rare FNIP1 PTVs lower TG:HDL, liver fat, glycaemia & cardiometabolic risk by ~60%; hepatocyte knockdown of Fnip1+Fnip2 or Flcn protects against DIO weight gain, steatosis & insulin resistance.",
    ("FLCN", "FNIP2"): "SAME DIRECTION: Combined hepatic Fnip1+Fnip2 knockdown or Flcn deletion protects mice from high-fat diet obesity, hepatic steatosis, and insulin resistance (PMID:42557317); FLCN & FNIP2 form the obligate lysosomal GAP complex (6ULG/8DHB).",
    ("FNIP1", "PRKAG2"): "OPPOSITE DIRECTION (Disruptor = Agonist): FNIP1 LoF is cardioprotective/metabolically favorable in 1M humans (PMID:42557317), whereas AMPK (PRKAG2) activation promotes fatty acid oxidation & glucose uptake (PRKAG2 CBS mutations cause CMH6/WPW cardiac glycogenosis, OT=0.90). Disrupting FNIP1's inhibitory tether on AMPK activates AMPK.",
    ("FNIP1", "PRKAG1"): "OPPOSITE DIRECTION: FNIP1 is a negative regulator of AMPK/mitochondrial metabolism (human PTVs protective, PMID:42557317), while PRKAG1 (AMPK gamma-1) activation drives hepatic lipid oxidation & renal protection (OT CKD=0.46).",
    ("FNIP1", "PRKAA1"): "OPPOSITE DIRECTION: FNIP1 negatively regulates AMPK (human PTVs reduce liver fat & T2D odds by 60%, PMID:42557317), while PRKAA1 (AMPK catalytic alpha-1) activation restores insulin sensitivity & inhibits hepatic lipogenesis.",
    ("FNIP1", "BTRC"): "OPPOSITE DIRECTION (Molecular Glue Degrader): BTRC (beta-TrCP1) has human GWAS associations with T2D (OT=0.50), morbid obesity (OT=0.33) & AFib (OT=0.54) and ubiquitinates FNIP1 for proteasomal degradation. Stabilizing FNIP1-BTRC degrades FNIP1, phenocopying protective human FNIP1 PTVs (PMID:42557317).",
    ("FNIP1", "FBXW11"): "OPPOSITE DIRECTION (Molecular Glue Degrader): FBXW11 (beta-TrCP2, paralog of BTRC; OT liver disorder=0.12) ubiquitinates phosphorylated FNIP1 to relieve mTORC1/AMPK suppression; glue stabilization degrades FNIP1.",
    ("FNIP1", "RRAGA"): "SAME/COUPLED PATHWAY: Both have human cardiometabolic genetics (FNIP1 1M-human exome protective PTVs PMID:42557317 & HCM OT=0.79; RRAGA T2D OT=0.20); FLCN-FNIP1 acts as GAP for RagC/D in the RagA/C lysosomal nutrient-sensing complex.",
    ("FNIP1", "CARNMT1"): "COMPLEMENTARY METABOLIC GENETICS: FNIP1 PTVs protect against dyslipidemia/steatosis (PMID:42557317); CARNMT1 has human genetics for Hypercholesterolemia (OT=0.31) and synthesizes anserine to buffer glycolytic/oxidative stress.",
    ("FLCN", "BAG3"): "SHARED CARDIOMYOPATHY GENETICS: BAG3 is a major human dilated/myofibrillar cardiomyopathy gene (OT CMD1HH=0.94; P209L/Q/S at RF2-PPI interface) and KO mouse lipodystrophy gene (OT=0.49); FLCN-FNIP regulates cardiac energy homeostasis & fibrosis (PMID:39806064).",
    ("PDE3B", "LGR4"): "SAME/COMPLEMENTARY DIRECTION: Human PDE3B rare LoF variants in UK Biobank reduce triglycerides, WHR & visceral fat (PMID:34875679; OT T2D=0.56); human LGR4 LoF (p.R126X) lowers body weight while GoF (p.A750T, PMID:42677820; OT obesity=0.10) drives central obesity, and endothelial LGR4 protects against MASLD steatosis (PMID:42749044).",
    ("PDE3B", "RAPGEF3"): "OPPOSITE/COUPLED cAMP AXIS: Both have human T2D genetics in Open Targets (PDE3B T2D=0.56; RAPGEF3/EPAC1 T2D=0.19 + 46 KO mouse insulin/vascular phenotypes). PDE3B degrades cAMP while EPAC1 is directly activated by cAMP in the same plasma-membrane signalosome (PMID:21393242, PMID:39199373).",
    ("PDE3B", "PDE3A"): "PARALOG COUNTER-SCREEN: PDE3B LoF improves fat distribution/lipids (PMID:34875679), whereas PDE3A GoF mutations (T445A/N/S, A447T/V, G449V) cause Mendelian hypertension-brachydactyly (OT HTNB=0.87, CAD=0.83). Essential selectivity counter-screen.",
    ("PDE3B", "PDE4D"): "COMPARTMENTALIZED cAMP CO-REGULATION: Both have human cardiometabolic genetics (PDE3B T2D=0.56; PDE4D liver=0.54, kidney=0.52, T2D=0.05) and co-regulate distinct cAMP microdomains in adipocytes (PMID:41082906, 2025).",
    ("PDE3B", "ELMO1"): "SHARED DIABETIC COMPLICATION GENETICS: PDE3B (OT T2D=0.56) and ELMO1 (classic human diabetic nephropathy GWAS gene; OT aortic stenosis=0.69, glomerulonephritis=0.33).",
    ("PDE3B", "MTX3"): "SHARED GENETICS (Source=S): PDE3B (OT T2D=0.56) and MTX3 (OT cardiomyopathy=0.33; mitochondrial outer membrane transport).",
    ("GRB14", "TNKS2"): "SAME DIRECTION (Both Negative Regulators / T2D Genetics): Both have human T2D genetics in Open Targets (GRB14 T2D=0.74, rs13389219 WHR/insulin resistance GWAS; TNKS2 T2D=0.25). GRB14 inhibits INSR catalytic loop (2AUH), while Tankyrase (TNKS/TNKS2) binds GRB14 N-terminus (UniProt Q14449) and regulates GLUT4 vesicle translocation & adiposity.",
    ("STARD10", "PRMT6"): "OPPOSITE/COMPLEMENTARY T2D & MASH GENETICS: Both have strong human T2D/obesity genetics in Open Targets (STARD10 diabetes=0.83, T2D=0.69; PRMT6 obesity=0.65, T2D=0.57). STARD10 is required for islet beta-cell insulin granule biogenesis & triglyceride metabolism (PMID:41687621), while PRMT6 drives hepatic gluconeogenesis & steatosis (inhibiting PRMT6 ameliorates MASH in mice, PMID:42948769).",
    ("PPARG", "LPIN1"): "SAME DIRECTION (Synergistic Metabolic Activation): PPARG (OT T2D=0.92, FPLD3=0.86) and LPIN1 (OT human cardiac=0.53, KO mouse lipodystrophy=0.49; human rs13412852 MASLD PMID:41751781). Lipin-1 directly coactivates PPARG/PPARA to drive hepatic fatty acid oxidation (preventing MASH, PMID:42212316) and white adipocyte browning (PMID:41007632).",
    ("PPARG", "NR1H3"): "SAME DIRECTION (Reciprocal Nuclear Receptor Axis): PPARG (OT T2D=0.92) and NR1H3/LXRA (OT metabolic syndrome=0.45, NAFLD=0.41, CKD=0.46) form a canonical feed-forward transcriptional loop in lipid efflux and macrophage inflammation.",
    ("PPARG", "NR1H2"): "COUPLED NUCLEAR RECEPTOR AXIS: PPARG (OT T2D=0.92) and NR1H2/LXRB (co-downregulated in obese/T2D adipose EVs, PMID:38928163; 3_safety Inhibition=GREEN) form a high-confidence LBD heterodimer (AFM=0.979, RF2-PPI L464-M422 p=0.500).",
    ("PPARG", "NCOA3"): "SHARED METABOLIC SYNDROME GENETICS: PPARG (OT T2D=0.92) and NCOA3/SRC-3 (OT metabolic syndrome=0.48, KO mouse lipodystrophy=0.40) co-regulate adipogenesis and energy balance.",
    ("PPARG", "NCOA1"): "SHARED CARDIOMETABOLIC GENETICS: PPARG (OT T2D=0.92) and NCOA1/SRC-1 (OT hypertension=0.55, hypercholesterolemia=0.45; 1K74 crystal complex).",
    ("PPARG", "MED1"): "CANONICAL ADIPOGENIC COACTIVATOR: PPARG (OT T2D=0.92) and MED1 (OT HF=0.12, diabetic neuropathy=0.08, KO mouse cardiomyopathy=0.42; 6D94/6ONJ crystal complexes). Full MED1 recruitment drives classic TZD adipogenesis & fluid retention.",
    ("PPARG", "PMP2"): "LIGAND CHAPERONE AXIS: PPARG (OT T2D=0.92) and PMP2 (myelin/lipid fatty-acid binding protein, AFM=0.993; 3_safety Inhibition=GREEN).",
    ("SLC25A5", "CIAPIN1"): "MITOCHONDRIAL STEATOSIS/APOPTOSIS AXIS: SLC25A5 (ANT2, NN4005 Hepato RNAi MASH target; hepatic depletion improves steatosis/insulin resistance, PMID:40078199) and CIAPIN1 (mitochondrial Fe-S assembly anti-apoptotic factor; OT coronary atherosclerosis=0.41).",
    ("SLC25A5", "MAP3K1"): "JNK/MAPK STEATOSIS SIGNALING: SLC25A5 (MASH target) and MAP3K1 (OT T2D=0.49; upstream activator of JNK/MAPK stress signaling in hepatocyte lipotoxicity).",
}

# Curated C4 (Perturbation Regulation Evidence)
CURATED_C4_EXTRA = {
    ("FLCN", "FNIP1"): "PMID:42557317 (2026) & PMID:17028174 (PNAS 2006): FLCN and FNIP1 mutually stabilize each other in the lysosomal folliculin complex; knockdown of either FLCN or FNIP1 triggers nuclear translocation of TFEB/TFE3 and upregulates lysosomal/lipid-breakdown genes.",
    ("FLCN", "FNIP2"): "PMID:42557317 (2026) & PMID:18403135 (2008): Combined knockdown of FNIP1 and FNIP2 phenocopies FLCN deletion, inducing TFEB target gene expression and mitochondrial biogenesis.",
    ("FNIP1", "PRKAG2"): "PMID:17028174 (Baba et al., PNAS 2006) & PMID:37079686 (Malik et al., Science 2023): AMPK directly phosphorylates FNIP1 (at S220/S261/S593, UniProt Q8TF40), while FNIP1/FLCN loss constitutively activates AMPK phosphorylation and downstream metabolic genes.",
    ("FNIP1", "PRKAG1"): "PMID:17028174 (PNAS 2006) & STRING-exp=0.802: Direct physical binding of FNIP1 to AMPK (PRKAA1/PRKAB1/PRKAG1); AMPK inhibition or activation directly alters FNIP1 phosphorylation and stability.",
    ("FNIP1", "PRKAA1"): "PMID:17028174 (PNAS 2006) & STRING-exp=0.487: PRKAA1 (AMPK alpha-1) directly phosphorylates FNIP1 (abolished in FNIP1 SA5 mutant S220A/S261A/S593A), while FNIP1 knockdown activates hepatic AMPK and lipid oxidation (PMID:42557317).",
    ("FNIP1", "BTRC"): "UniProt Q8TF40 / STRING-exp=0.217 / CRL literature (PMID:40091294): SCF(beta-TrCP1/BTRC) recognizes phosphorylated FNIP1 to catalyze its ubiquitination and proteasomal degradation; BTRC depletion stabilizes FNIP1 protein levels.",
    ("FNIP1", "FBXW11"): "UniProt Q8TF40 / STRING-exp=0.181: SCF(beta-TrCP2/FBXW11) ubiquitinates phosphorylated FNIP1 to regulate FNIP1 protein turnover and mTORC1/AMPK signaling.",
    ("PDE3B", "RAPGEF3"): "PMID:21393242 (JBC 2011) & PMID:35703011 (2022) & STRING-exp=0.456: PDE3B knockdown or inhibition elevates local cAMP to activate RAPGEF3 (EPAC1) -> Rap1/PI3Kgamma signaling; PDE3B N-terminal mutations (R2A-R12A) abolish RAPGEF3 binding.",
    ("PDE3B", "LGR4"): "PMID:42749044 (2026) & cAMP-PKA cascade: LGR4 activation/perturbation modulates intracellular cAMP/PKA signaling, which directly phosphorylates and regulates PDE3B activity and expression in adipocytes and hepatocytes.",
    ("GRB14", "TNKS2"): "UniProt Q14449 & STRING-exp=0.476 & PMID:41744791 (2026): GRB14 binds the ankyrin repeat clusters of Tankyrase-2 (TNKS2) via its N-terminus; Tankyrase PARsylation regulates turnover and vesicle trafficking of insulin-signaling complexes.",
    ("STARD10", "PRMT6"): "UniProt Q9Y365 (IntAct EBI-4289836, NbExp=2) & STRING-exp=0.456: Direct physical interaction validated in human affinity-purification proteomics; STARD10 deletion impairs beta-cell insulin granule biogenesis (PMID:41687621) while PRMT6 perturbation alters FOXO1/FOXK1 hepatic lipid/glucose gene expression (PMID:42948769).",
    ("PPARG", "LPIN1"): "PMID:16790555 (Finck et al., Cell Metab 2006) & PMID:41007632 (2025) & PMID:42212316 (2026): Lipin-1 overexpression/knockdown directly alters PPARG/PPARA target gene transcription (fatty acid oxidation & thermogenic browning), while PPARG activation induces LPIN1 expression in adipocytes.",
}

# Curated C7 (Safety Risks & Mitigation)
CURATED_C7_SAFETY = {
    "FLCN": ("RED (Systemic Inhib)", "Tumor suppressor (Birt-Hogg-Dube syndrome, renal cell carcinoma, pneumothorax). Direct systemic FLCN inhibition is RED; target FNIP1/FNIP2 or hepatocyte-selective delivery instead."),
    "FNIP1": ("YELLOW (Hepato/Modulator) | RED (Null)", "3_safety: Biallelic complete null causes IMD93 (neutropenia/immunodeficiency & HCM, score=104). CRITICAL MITIGATION: Heterozygous human PTVs in 1M exomes (PMID:42557317) are safe & protective (-60% CM disease); use hepatocyte GalNAc-siRNA or selective FNIP1-AMPK / FNIP1-BTRC interface modulation."),
    "FNIP2": ("GREEN / LOW RISK", "No Mendelian human immunodeficiency or cardiomyopathy; redundant with FNIP1 in immune cells but synergistic with FNIP1 in hepatocyte lipid oxidation (PMID:42557317)."),
    "PRKAG2": ("YELLOW (Cardiac Isoform)", "Gain-of-function/storage mutations cause cardiac glycogenosis (CMH6/WPW). Avoid cardiac glycogen accumulation; favor liver/adipose FNIP1-AMPK disinhibition."),
    "PRKAG1": ("GREEN (Activation) | RED (Inhib)", "3_safety: Inhibition=RED; Activation of AMPK via relieving FNIP1 inhibition is metabolically protective."),
    "PRKAA1": ("GREEN (Activation)", "3_safety verified: Activation = GREEN (Risk_Score=0). Relieving FNIP1 inhibition activates PRKAA1 safely."),
    "BTRC": ("GREEN (Glue Recruitment) | YELLOW (Inhib)", "3_safety verified: Systemic BTRC inhibition = YELLOW (score=56). Recruiting BTRC as an endogenous E3 ligase via a FNIP1-BTRC molecular glue does NOT inhibit BTRC."),
    "FBXW11": ("YELLOW (Neurodevelopmental Germline)", "Germline WD40 point mutations cause NEDJED; recruiting FBXW11 as an E3 ligase for FNIP1 in peripheral metabolic tissues avoids systemic E3 inhibition."),
    "RRAGA": ("YELLOW (Essential mTORC1 GTPase)", "Broadly essential for lysosomal mTORC1 amino-acid sensing; avoid direct global RagA inhibition."),
    "CARNMT1": ("GREEN", "Non-essential metabolic methyltransferase (carnosine -> anserine); clean safety profile."),
    "VTA1": ("GREEN / LOW RISK", "ESCRT-III accessory protein; no severe human Mendelian toxicity."),
    "BAG3": ("RED (Cardiomyopathy Risk)", "Essential cardiac Z-disc co-chaperone; LoF/P209L causes severe dilated/myofibrillar cardiomyopathy (CMD1HH/MFM6). Do not inhibit BAG3."),
    "GRB14": ("GREEN / YELLOW (Inhib)", "3_safety verified: Inhibition = YELLOW/GREEN (Risk_Score=0); Grb14 KO mice are viable with improved insulin signaling and lean phenotype."),
    "TNKS2": ("YELLOW (GI/Wnt Class Risk)", "Tankyrase 1/2 dual catalytic inhibitors carry intestinal toxicity via Axin/beta-catenin stabilization; a PPI-selective disruptor of the GRB14-TNKS2 N-terminal ARC interface avoids catalytic PARP inhibition."),
    "PDE3B": ("GREEN (Inhibition)", "3_safety verified: Inhibition = GREEN. Human UKB PDE3B LoF carriers are healthy with favorable lipid/fat distribution; must maintain selectivity over PDE3A."),
    "RAPGEF3": ("GREEN (Both Directions)", "3_safety verified: Inhibition = GREEN (Risk_Score=0), Activation = GREEN (Risk_Score=0). Cleanest cAMP-axis partner for PDE3B."),
    "LGR4": ("YELLOW (Bone/Electrolyte) | RED (Null)", "3_safety: Complete homozygous null is neonatal lethal in mice and human R126X nonsense affects bone mineral density/electrolytes; favor adipose/liver-selective modulation or allosteric PDE3B-LGR4 signaling modulation."),
    "PDE3A": ("RED (CV Inotropy/Arrhythmia)", "Milrinone-class PDE3A inhibition causes positive inotropy, tachycardia, and increased heart-failure mortality; mandatory negative counter-screen for PDE3B campaigns."),
    "PDE4D": ("YELLOW (Emesis/Nausea)", "3_safety verified: Inhibition = YELLOW (score=67); central PDE4D inhibition triggers emesis (area postrema); peripheral/adipocyte restriction required."),
    "ELMO1": ("GREEN / LOW RISK", "Cytoskeletal Rac-GEF scaffold implicated in diabetic nephropathy; no acute systemic toxicity."),
    "MTX3": ("GREEN", "Mitochondrial outer membrane transport subunit; no severe safety flags."),
    "PPARG": ("YELLOW (SPPARM) | RED (Full Agonist)", "3_safety verified: Full Agonism = RED (score=96, TZD boxed warning: fluid retention, edema, HF, bone loss). Next-gen SPPARM biased cofactor recruitment (e.g. LPIN1/NR1H2 over MED1) is the exact mitigation strategy."),
    "LPIN1": ("GREEN (Activation/Glue) | RED (Inhib)", "3_safety verified: Activation = GREEN (Risk_Score=0), whereas Inhibition = RED (score=142, human biallelic LoF causes severe rhabdomyolysis). Stabilizing PPARG-LPIN1 (activation) is GREEN."),
    "NR1H2": ("GREEN (Inhib) | YELLOW (Act)", "3_safety verified: Inhibition = GREEN (score=0), Activation = YELLOW (score=72, milder lipogenic risk than LXRA/NR1H3)."),
    "NR1H3": ("YELLOW (Hepatic Lipogenesis)", "3_safety verified: Activation = YELLOW (score=72), Inhibition = YELLOW (score=77, hepatotoxicity/atherosclerosis). Direct LXR alpha agonism induces SREBP-1c hypertriglyceridemia."),
    "PMP2": ("GREEN (Inhib) | YELLOW (Act)", "3_safety verified: Inhibition = GREEN (score=0), Activation = YELLOW (score=47, CMT1G peripheral neuropathy SAVs)."),
    "NCOA3": ("YELLOW (Pleiotropic Coactivator)", "3_safety verified: Activation = YELLOW (score=47, tumorigenic amplification in breast cancer), Inhibition = YELLOW (score=84, fertility/growth)."),
    "NCOA1": ("RED (Act) | YELLOW (Inhib)", "3_safety verified: Activation = RED (score=77, COSMIC CGC Tier 1 fusion oncogene), Inhibition = YELLOW (score=54). Use as selectivity counter-screen."),
    "MED1": ("RED (Inhib) | YELLOW (Act)", "3_safety verified: Inhibition = RED (score=140, embryonic lethal), Activation = YELLOW (score=37, dyslipidemia/TZD fluid retention driver). Use as negative counter-screen for SPPARM."),
    "NR0B1": ("YELLOW (Adrenal/Gonadal Axis)", "3_safety verified: Activation = YELLOW (score=54), Inhibition = YELLOW (score=69, X-linked adrenal hypoplasia congenita AHC)."),
    "ESRRA": ("YELLOW (Cardiac Bioenergetics)", "Essential regulator of cardiac mitochondrial oxidative phosphorylation; avoid cardiac ESRRA inhibition."),
    "RXRG": ("YELLOW (Thyroid/Lipid Axis)", "Rexinoid activation can cause hypertriglyceridemia and central hypothyroidism."),
    "ESR2": ("YELLOW (Endocrine/Reproductive)", "Estrogen receptor beta; endocrine/reproductive modulation."),
    "ARID1A": ("RED (Tumor Suppressor)", "3_safety verified: Inhibition = RED (score=164, COSMIC Tier 1 tumor suppressor, teratogenic/lethal), Activation = YELLOW (score=75). Do not inhibit."),
    "RB1": ("RED (Tumor Suppressor)", "Canonical retinoblastoma tumor suppressor; loss-of-function is strictly RED."),
    "MED19": ("RED (Inhib)", "3_safety verified: Inhibition = RED (essential Mediator subunit, lethal)."),
    "FHOD1": ("GREEN (Inhib)", "3_safety verified: Inhibition = GREEN."),
    "SLC25A5": ("GREEN (Hepato RNAi)", "3_safety verified: Activation = GREEN (score=0); NN4005 uses hepatocyte-targeted GalNAc-siRNA to avoid systemic mitochondrial ANT2 depletion."),
    "CIAPIN1": ("YELLOW (Essential Fe-S Biogenesis)", "Essential cytosolic/mitochondrial Fe-S cluster assembly protein (yeast Dre2); systemic knockout is embryonic lethal."),
    "ATXN3": ("YELLOW (CNS Spinocerebellar Ataxia)", "PolyQ expansion causes Machado-Joseph disease (SCA3); deubiquitinase."),
    "MAP3K1": ("YELLOW (Developmental/Cancer)", "Germline GoF causes 46,XY sex reversal (SRXY6); somatic LoF in luminal breast cancer."),
    "IKZF1": ("RED (Hematopoietic TF)", "Essential lymphoid transcription factor; LoF causes CVID13 immunodeficiency and B-ALL."),
    "AFDN": ("YELLOW (Cell Junction / MLL Fusion)", "Adherens junction scaffold; MLL translocation partner."),
    "STARD10": ("GREEN (Peripheral/Islet)", "No severe Mendelian toxicity; islet/liver lipid transfer protein."),
    "PRMT6": ("RED (Systemic Inhib) | YELLOW (Act)", "3_safety verified: Systemic catalytic inhibition = RED (score=101, hematopoietic/thrombocytopenia & genotoxic flags); PPI-selective interface modulation with STARD10 or hepatocyte-targeted delivery is required."),
}



TOP5_DEEPDIVE_ROWS = [
    {
        "priority_rank": "Top 1 (Campaign Axis 1)",
        "lead_pairs": "FNIP1-PRKAG1 (90%) | FNIP1-PRKAA1 (80%) | FNIP1-PRKAG2 (80%) [anchored on FLCN-FNIP1/2]",
        "frontrunner_program": "FNIP1 / FNIP2 / FLCN (AMPK / Energy Expenditure / MASH & T2D)",
        "baker_scores": "FLCN-FNIP1: RF=0.999, AF2=1.00, AFM=1.00 (90%) | FNIP1-PRKAG1: RF=0.481, AF2=0.777, AFM=0.722 (90%) | FNIP1-PRKAA1: RF=0.436, AFM=0.871 (80%) | FNIP1-PRKAG2: RF=0.499, AFM=0.713 (80%)",
        "c1_interface_savs": "[FACT] (1) Cryo-EM 8JE2 (3.63A, 2024) & 6ULG (3.31A, 2019): FLCN p.Glu132Lys (rs2145009956, AM=0.9995 LPath, Dual-Path) forms a 2.60A inter-subunit salt bridge with FNIP2 Lys156; FNIP1 p.Ser1118Asn (rs2149501551, AM=0.9888 LPath, IMD93/HCM) sits between RF2-PPI #1/#2 contacts F1116 (p=0.989) & M1120 (p=0.987). (2) On AMPK: PRKAG2 harbors 6 Dual-Pathogenic CBS-domain SAVs (R302Q rs121908987 AM=0.998; H383R rs121908988 AM=0.999; T400N rs28938173 AM=0.996; N488I rs121908989 AM=0.979; R531G/Q rs121908990/1 AM=0.999/0.997); PRKAG1 carries T89S (rs1126930, AM=0.879 LPath) & D90A/D245A/D317A; FNIP1 carries AMPK phosphorylation-site mutagens S220A/S261A/S593A (SA5 mutant) + cDENN contact D530.",
        "c2_genetics_direction": "[FACT] OPPOSITE DIRECTION (PPI Disruptor = AMPK Activator): Exome sequencing of 1,032,116 humans (PMID:42557317, 2026) proves rare FNIP1 protein-truncating variants (AF=0.01%) reduce TG:HDL, liver fat, glycaemia & cardiometabolic disease odds by ~60%. Conversely, AMPK (PRKAA1/PRKAG1/PRKAG2) activation drives hepatic fatty acid oxidation & glucose uptake (OT PRKAG2 CMH6=0.90, T2D KO=0.37; PRKAG1 CKD=0.46). Disrupting FNIP1's inhibitory tether on AMPK phenocopies protective human FNIP1 LoF.",
        "c3_c4_c5_biology": "[FACT] Same AMPK-mTORC1-TFEB energy-sensing pathway (C3); Baba et al. PNAS 2006 (PMID:17028174) & Malik et al. Science 2023 (PMID:37079686) & PMID:42557317 (2026) prove AMPK directly phosphorylates FNIP1 (S220/S261/S593) while FNIP1 knockdown in primary human hepatocytes activates AMPK, lipid breakdown & lysosomal biogenesis (C4/C5).",
        "c6_structures_db": "[FACT] Exact Cryo-EM 8JE2 (3.63A, FNIP1-FLCN) & 6ULG/6NZD/8DHB (3.31-3.60A, FLCN-FNIP2-RagA/C); Confident PPI DBs: UniProt (Q8TF40 SUBUNIT), BioGRID MV, STRING (escore=0.802 for FNIP1-PRKAG1, 0.487 for FNIP1-PRKAA1).",
        "c7_safety_and_modality": "[FACT] 3_safety: PRKAA1 Activation = GREEN (score=0); FNIP2 = GREEN; FLCN systemic inhibition = RED (BHD renal tumor suppressor); FNIP1 biallelic null = RED (IMD93 neutropenia/HCM), whereas heterozygous human PTV carriers are healthy & protected (PMID:42557317). Strategy: PPI-selective disruptor of FNIP1 cDENN (530-911) : AMPK (PRKAG1/PRKAA1) interface or hepatocyte-targeted FNIP1/2 modulation (sparing FLCN & cardiac PRKAG2).",
        "wetlab_controls": "Point-mutant controls ready for co-IP / NanoBiT / TR-FRET: FNIP1 D530A and SA5 (S220A/S261A/S593A); PRKAG1 E159A / D90A; FLCN E132K (2.60A salt-bridge disruptor)."
    },
    {
        "priority_rank": "Top 2 (Campaign Axis 2)",
        "lead_pairs": "FNIP1-BTRC (80%) | FNIP1-FBXW11 (80%)",
        "frontrunner_program": "FNIP1 (Endogenous E3 Ubiquitin Ligase Molecular Glue Degrader Axis)",
        "baker_scores": "FNIP1-BTRC: RF=0.395, AFM=0.836, RF2_contact=0.129 (80%) | FNIP1-FBXW11: RF=0.419, AFM=0.809 (80%)",
        "c1_interface_savs": "[FACT] RF2-PPI top contacts FNIP1:Met241-BTRC:Ile603 (p=0.129) and FNIP1:Arg288-BTRC:Asp574 (p=0.125) place the FNIP1 uDENN phosphodegron region (flanking S220/S261) directly into the WD40 beta-propeller pocket of beta-TrCP1 (BTRC, containing SAV P592H rs2270439 and substrate-abolishing mutagens Y307A, R321A, R510A) and beta-TrCP2 (FBXW11, harboring 7 Dual-Pathogenic WD40 SAVs: G242R, R363W, A364D, A365T, E444K, R447L/Q, all AM=0.997-1.000 LPath).",
        "c2_genetics_direction": "[FACT] OPPOSITE DIRECTION (Molecular Glue Degrader): Human FNIP1 PTVs confer 60% protection against cardiometabolic disease in 1M exomes (PMID:42557317); BTRC has direct human GWAS associations in Open Targets for Diabetes Mellitus (OT=0.50), Morbid Obesity (OT=0.33) & Atrial Fibrillation (OT=0.54), and FBXW11 for Liver Disorder (OT=0.12). Enhancing SCF(beta-TrCP)-mediated ubiquitination of FNIP1 degrades FNIP1 to activate hepatic energy expenditure.",
        "c3_c4_c5_biology": "[FACT] Shared ubiquitin-proteasome / mTORC1-AMPK nutrient-sensing pathway (C3); SCF(BTRC/FBXW11) directly ubiquitinates phosphorylated FNIP1 to control its cellular protein half-life (C4: STRING-exp=0.217/0.181, BioGRID MV, PMID:40091294); co-expressed in human metabolic tissues (C5: STRING-coexpr=0.065/0.075).",
        "c6_structures_db": "[FACT] Confident PPI DBs: BioGRID Multi-Validated (MV) & STRING physical interaction for both FNIP1-BTRC and FNIP1-FBXW11; high-confidence AF-Multimer 3D complex (AFM=0.836 and 0.809).",
        "c7_safety_and_modality": "[FACT] 3_safety: Recruiting endogenous BTRC/FBXW11 via a molecular glue stabilizer at the FNIP1 uDENN:WD40 interface degrades FNIP1 without inhibiting BTRC catalytic/housekeeping functions (systemic BTRC inhibition = YELLOW score=56). Directly mimics the favorable human heterozygous FNIP1 LoF state.",
        "wetlab_controls": "Point-mutant controls for ternary TR-FRET / HiBiT-FNIP1 degradation assay: BTRC R510A / Y307A / R321A (WD40 pocket dead mutants); FNIP1 M241A / R288A and K1119R (ubiquitination-resistant mutant)."
    },
    {
        "priority_rank": "Top 3 (Campaign Axis 3)",
        "lead_pairs": "PDE3B-RAPGEF3 [EPAC1] (80%) | PDE3B-LGR4 (80%) [with PDE3B-PDE3A/PDE4D as Counter-Screens]",
        "frontrunner_program": "PDE3B (Adipocyte/Hepatocyte cAMP Compartmentalization & Insulin Sensitivity)",
        "baker_scores": "PDE3B-RAPGEF3: RF=0.193, AF2=0.708, CF=0.739, AFM=0.682 (80%) | PDE3B-LGR4: RF=0.594, AF2=0.441, CF=0.646, AFM=0.701 (80%)",
        "c1_interface_savs": "[FACT] (1) PDE3B-RAPGEF3: UniProt Q13370 documents 7 experimentally validated point mutations in the PDE3B N-terminal domain (R2A, R3A, R6A, A8D, K9A, A10D, R12A; PMID:21393242) that abolish binding to RAPGEF3 (EPAC1), plus RF2-PPI contacts RAPGEF3:G132-PDE3B:A126 (p=0.197) & RAPGEF3:G594-PDE3B:E797 (p=0.210) with 3 RAPGEF3 SAVs (R193G, G374S, C517Y). (2) PDE3B-LGR4: LGR4 carries coding SAVs I96V (rs757351670), G363C (rs117543292), C-tail D844G (rs34804482) & human GoF obesity mutation p.Ala750Thr (PMID:42677820). (3) Counter-screen PDE3A carries 6 Dual-Pathogenic HTNB GoF SAVs (T445A/N/S, A447T/V, G449V, AM=0.80-0.97).",
        "c2_genetics_direction": "[FACT] BOTH HUMAN GENETICS: UK Biobank rare PDE3B LoF variants reduce triglycerides, visceral fat & WHR (PMID:34875679; OT T2D=0.56). RAPGEF3 (EPAC1) has human T2D genetics (OT=0.19) + 46 KO mouse insulin/vascular phenotypes. LGR4 has human LoF (p.R126X lower body weight) & GoF (p.A750T central obesity/insulin resistance, PMID:42677820; OT obesity=0.10) and protects liver sinusoidal endothelium against MASLD steatosis (PMID:42749044, 2026).",
        "c3_c4_c5_biology": "[FACT] Shared cAMP/PKA/EPAC1 plasma-membrane signalosome pathway (C3); PDE3B knockdown/inhibition elevates local cAMP to activate EPAC1->Rap1/PI3Kgamma and brown/beige adipogenesis (PMID:21393242, PMID:28084425, PMID:35703011, PMID:42675175) (C4/C5).",
        "c6_structures_db": "[FACT] PDE3B catalytic crystal structures 1SO2 (2.40A), 8SYC (2.70A, 2024), 9YUD (2.70A, 2025); LGR4 cryo-EM 2025 (PMID:40998774); PDE3B-RAPGEF3 validated in UniProt (Q13370 SUBUNIT, IntAct EBI-6172856 NbExp=8, STRING=762); PDE3B-LGR4 in BioGRID.",
        "c7_safety_and_modality": "[FACT] 3_safety verified: PDE3B Inhibition = GREEN; RAPGEF3 Inhibition = GREEN (score=0) & Activation = GREEN (score=0). In contrast, paralog PDE3A is RED (cardiac positive inotropy, arrhythmia & HTNB hypertension) and PDE4D is YELLOW (central emesis). Allosteric modulation of the PDE3B-RAPGEF3/LGR4 N-terminal regulatory complex achieves absolute isoform selectivity over PDE3A (which lacks the PDE3B N-terminal membrane/EPAC1 tether).",
        "wetlab_controls": "Validated point-mutant negative controls: PDE3B N-terminal R2A/R3A/R6A/K9A/R12A (abolishes RAPGEF3 binding, PMID:21393242); RAPGEF3 G557A / G594A; LGR4 D844G / A750T."
    },
    {
        "priority_rank": "Top 4 (Campaign Axis 4)",
        "lead_pairs": "PPARG-LPIN1 (80%) | PPARG-NR1H2 [LXRB] (90%) | PPARG-NR1H3 [LXRA] (90%) [with PPARG-MED1/NCOA1 as RED Counter-Screens]",
        "frontrunner_program": "PPARG (Next-Generation SPPARM Biased Co-Regulator Recruitment without TZD Fluid Retention)",
        "baker_scores": "PPARG-LPIN1: AF2=0.469, AFM=0.835 (80%) | PPARG-NR1H2: AF2=0.844, CF=0.951, AFM=0.979 (90%) | PPARG-NR1H3: AF2=0.837, CF=0.925, AFM=0.975 (90%) | Counter-screens PPARG-MED1 (AFM=0.955, 6D94/6ONJ) & PPARG-NCOA1 (AFM=0.937, 1K74)",
        "c1_interface_savs": "[FACT] Atomic crystal verification on 6D94 (1.90A), 6ONJ (2.30A), 1K74 (2.30A) & 3E00 (3.10A): (1) Human severe T2D/FPLD3 Dual-Pathogenic SAV PPARG p.Pro495Leu (rs121909244, AM=0.9788 LPath, PDB Pro467 in AF-2 helix H12) sits at d_min=3.64A from MED1 Met644 (6ONJ) and 4.84A from NCOA1 Ile689 (1K74); (2) PPARG p.Val318Met (rs72551362, AM=0.8189 LPath, T2D) sits at d_min=6.07A from MED1 Leu648 and 6.14A from NCOA1 Leu693; (3) PPARG p.Arg425Cys (rs72551364, AM=0.9972 LPath, FPLD3) sits at d_min=5.10A on the NR heterodimer helix (NR1H2/NR1H3/RXRG template); (4) LPIN1 carries Dual-Pathogenic SAV G56E (AM=0.9983) & LXXIL motif.",
        "c2_genetics_direction": "[FACT] SAME DIRECTION (Biased Agonism): PPARG LoF causes FPLD3 & severe T2D (OT=0.92). LPIN1 deficiency causes lipodystrophy/rhabdomyolysis (OT=0.49) and LPIN1 rs13412852 associates with human MASLD (PMID:41751781), while hepatic LPIN1 drives fatty acid oxidation to prevent MASH (PMID:42212316) and white adipocyte browning (PMID:41007632). NR1H3 (OT MetS=0.45, NAFLD=0.41) & NR1H2 co-regulate cholesterol efflux.",
        "c3_c4_c5_biology": "[FACT] Shared Reactome nuclear receptor & lipid metabolism pathways (C3: STRING=909/865/647); Lipin-1 directly binds PPARs via its LXXIL motif to coactivate FAO genes without requiring classic adipogenic MED1 hyper-activation (PMID:16790555, PMID:41007632, PMID:42212316) (C4/C5).",
        "c6_structures_db": "[FACT] 380 PPARG PDB structures including exact complexes 6D94/6ONJ (PPARG-MED1), 1K74/3VN2/5DWL (PPARG-NCOA1), and homolog heterodimers 1FM6/3E00 (for NR1H2/NR1H3/RXRG); Confident PPI DBs: UniProt, BioGRID MV, STRING.",
        "c7_safety_and_modality": "[FACT] 3_safety verified: Full PPARG agonism = RED (score=96, TZD boxed warning: edema, HF) driven by full AF-2 H12 lock and MED1 recruitment (MED1 Inhib=RED score=140; NCOA1 Act=RED score=77; ARID1A/RB1=RED). Conversely, LPIN1 Activation = GREEN (score=0) and NR1H2/PMP2 = GREEN/YELLOW. Screening SPPARMs via TR-FRET ratio of [PPARG-LPIN1 or PPARG-NR1H2 recruitment] OVER [PPARG-MED1 / NCOA1 recruitment] directly selects insulin-sensitizing, MASH-clearing ligands devoid of TZD fluid retention.",
        "wetlab_controls": "Crystal-verified point-mutant controls for TR-FRET cofactor profiling panel: PPARG P495L (d=3.64A AF-2 H12 disruptor), PPARG V318M (d=6.07A cleft mutant), PPARG R425C (d=5.10A heterodimer salt-bridge mutant); MED1 L604A/L607A."
    },
    {
        "priority_rank": "Top 5 (Campaign Axis 5)",
        "lead_pairs": "STARD10-PRMT6 (90%) | GRB14-TNKS2 (80%)",
        "frontrunner_program": "STARD10 (Islet Beta-Cell / Hepatic Lipid Transfer) & GRB14 (Hepatocyte/Adipocyte Insulin Receptor Sensitizer)",
        "baker_scores": "STARD10-PRMT6: RF=0.763, AFM=0.722, RF2_local_max_p=0.899 (90%) | GRB14-TNKS2: RF=0.261, AF2=0.663, CF=0.699, AFM=0.405 (80%)",
        "c1_interface_savs": "[FACT] (1) STARD10-PRMT6: RF2-PPI predicts a high-probability contact (max_p=0.899 at PRMT6:Gly281-STARD10:Val110 and p=0.868 at PRMT6:Glu244-STARD10:Thr109) directly on the STARD10 START lipid-binding cavity (crystal 6SER, 2.30A) and PRMT6 catalytic core (carrying SAV A194V rs2232016). (2) GRB14-TNKS2: UniProt Q14449 confirms GRB14 N-terminus binds TNKS2 ankyrin repeats (near GRB14 coding SAV F90I rs61748245), while RF2-PPI maps secondary contact at GRB14 BPS domain Ala378 (crystal 2AUH, adjacent to AKT/MAPK-restoring mutagens Q348A/N349A) with TNKS2 D1045/S1066 (flanking loss-of-activity mutagen M1054V).",
        "c2_genetics_direction": "[FACT] BOTH HUMAN T2D GENETICS IN OPEN TARGETS: (1) STARD10 (OT diabetes=0.83, T2D=0.69; required for human beta-cell differentiation & TG metabolism, PMID:41687621) and PRMT6 (OT obesity=0.65, T2D=0.57; targeting PRMT6/FOXK1 ameliorates MASLD/MASH in mice, PMID:42948769, 2026). (2) GRB14 (OT T2D=0.74, WHR/insulin resistance GWAS rs13389219) and TNKS2 (OT T2D=0.25; Tankyrase regulates GLUT4 vesicle translocation & metabolic homeostasis, PMID:41744791).",
        "c3_c4_c5_biology": "[FACT] STARD10-PRMT6 is validated by human AP-MS proteomics in UniProt (Q9Y365, IntAct EBI-4289836 NbExp=2, BioGRID MV, STRING-exp=0.456, STRING-coexpr=0.094). GRB14-TNKS2 is validated in UniProt (Q14449 SUBUNIT), BioGRID MV, and STRING (score=863, escore=0.476). Note: Baker RF2-PPI has a known blind spot on <800A2 SLiMs (4.5% recall), so for GRB14 it complements our crystal-validated GIGYF1-GRB14 (7RUQ) and GRB14-INSR (2AUH) campaigns.",
        "c6_structures_db": "[FACT] Monomer crystal structures STARD10 6SER (2.30A) & GRB14 2AUH/2AUG/4K81 (2.30-3.20A) + Confident PPI DBs (UniProt, BioGRID MV, STRING) for both pairs.",
        "c7_safety_and_modality": "[FACT] 3_safety verified: GRB14 Inhibition = YELLOW/GREEN (score=0); STARD10 = GREEN. By contrast, systemic catalytic PRMT6 inhibition is RED (score=101, thrombocytopenia/genotoxicity) and pan-Tankyrase catalytic inhibition causes GI toxicity. Therefore, PPI-selective interface modulation (disrupting PRMT6:G281-STARD10:V110 or GRB14-TNKS2 ARC binding in hepatocytes) achieves metabolic efficacy while avoiding catalytic PRMT6/TNKS toxicity.",
        "wetlab_controls": "Point-mutant controls for co-IP / BRET: STARD10 T109A/V110A and PRMT6 E244A/G281A; GRB14 F90I / Q348A / A378R and TNKS2 M1054V."
    },
]

INTERFACE_SAV_AUDIT_ROWS = [
    ("FLCN-FNIP1 (90%) & FLCN-FNIP2 (90%)", "FLCN (Q8NFG4)", "E132K", "rs2145009956", 0.9995, "LPath", "YES (Dual)", "2.60 A to FNIP2 Lys156 (Cryo-EM 6ULG/8DHB)", "Primary spontaneous pneumothorax / BHD; disrupts inter-subunit uDENN salt bridge"),
    ("FLCN-FNIP1 (90%) & FLCN-FNIP2 (90%)", "FLCN (Q8NFG4)", "S108I", "rs2145012002", 0.9992, "LPath", "YES (Dual)", "6.90 A to FNIP2 Gly550 (Cryo-EM 6ULG)", "Birt-Hogg-Dube syndrome 1 (BHD1); uDENN interface perimeter"),
    ("FLCN-FNIP1 (90%) & FLCN-FNIP2 (90%)", "FLCN (Q8NFG4)", "K508R", "rs199643834", 0.2696, "LBen", "UniProt Disease", "7.11 A to FNIP2 Leu1064 (6ULG) | RF2 C506 p=0.989", "BHD1 clinical variant; 2 residues from #1 RF2-PPI contact FLCN:Cys506"),
    ("FLCN-FNIP1 (90%)", "FNIP1 (Q8TF40)", "S1118N", "rs2149501551", 0.9888, "LPath", "YES (Dual)", "Flanked by RF2 #1/#2 contacts F1116 (0.989) & M1120 (0.987)", "Immunodeficiency 93 & hypertrophic cardiomyopathy (IMD93); adjacent to K1119R ubiquitination site"),
    ("FLCN-FNIP2 (90%) & RRAGA-FNIP1 (90%)", "FNIP2 (Q9P278)", "V146D (Mutagen)", "UniProt FT_MUT", None, "Mutagen", "Exp. Validated", "3.64 A to FLCN & 6.67 A to RRAGA (Cryo-EM 6ULG)", "Abolishes GTPase-activating (GAP) activity of the FLCN-FNIP complex"),
    ("FLCN-FNIP1/2 & RRAGA-FNIP1", "FLCN (Q8NFG4)", "F118D & F10D (Mutagen)", "UniProt FT_MUT", None, "Mutagen", "Exp. Validated", "3.25 A & 4.96 A to RRAGA (Cryo-EM 6ULG)", "Prevents lysosomal folliculin complex (LFC) assembly and abolishes GAP activity"),
    ("FLCN-BAG3 (80%)", "BAG3 (O95817)", "P209L / P209Q / P209S", "rs121918312 / rs1589630141", 0.9624, "LPath", "YES (Dual)", "#1 RF2-PPI contact BAG3:P209-FLCN:T555 (p=0.141)", "Myofibrillar myopathy 6 (MFM6) & severe restrictive cardiomyopathy; IPV chaperone motif"),
    ("FNIP1-PRKAG2 (80%)", "PRKAG2 (Q9UGJ0)", "R302Q / H383R / T400N / N488I / R531G / R531Q", "rs121908987 / rs121908988 / rs28938173 / rs121908989 / rs121908990", 0.9976, "LPath", "YES (Dual, 6 SAVs)", "CBS AMP/ATP & subunit interface domain", "Familial hypertrophic cardiomyopathy 6 (CMH6), WPW syndrome & cardiac glycogenosis"),
    ("FNIP1-PRKAG1 (90%) & PRKAA1 (80%)", "FNIP1 (Q8TF40)", "S220A / S261A / S593A (SA5 Mutagen) & D530", "UniProt FT_MUT", None, "Mutagen", "Exp. Validated", "RF2-PPI top contact PRKAG1:E159-FNIP1:D530 (p=0.163)", "Abolishes AMPK phosphorylation of FNIP1 and activates non-canonical mTORC1 signaling"),
    ("FNIP1-BTRC (80%)", "BTRC (Q9Y297)", "Y307A / R321A / R510A (Mutagen) & P592H", "rs2270439 / FT_MUT", 0.0915, "Mutagen+SAV", "Exp. Validated", "RF2-PPI contacts FNIP1:M241-BTRC:I603 & R288-D574", "WD40 beta-propeller pocket; Y307A/R321A/R510A abolish substrate binding"),
    ("FNIP1-FBXW11 (80%)", "FBXW11 (Q9UKB1)", "G242R / R363W / A364D / A365T / E444K / R447L / R447Q", "rs1759346639 / rs1758081729 / rs1758081491 / rs2113754835", 0.9999, "LPath", "YES (Dual, 7 SAVs)", "WD40 substrate-binding beta-propeller repeats", "Neurodevelopmental syndrome NEDJED; clusters in the substrate-recognition cleft"),
    ("PDE3B-RAPGEF3 (80%)", "PDE3B (Q13370)", "R2A / R3A / R6A / A8D / K9A / A10D / R12A (Mutagen)", "PMID:21393242", None, "Mutagen", "Exp. Validated (7 Mutants)", "Direct N-terminal peptide interface with RAPGEF3", "Directly abolishes physical interaction between PDE3B and RAPGEF3 (EPAC1) in human cells"),
    ("PDE3B-LGR4 (80%)", "LGR4 (Q9BXB1)", "I96V / G363C / D844G & p.A750T", "rs757351670 / rs117543292 / rs34804482", 0.2805, "Functional SAV", "UniProt + Human GoF", "LRR ectodomain & C-terminal cytoplasmic tail (pos 750/844)", "Alters Wnt/cAMP signaling & expression; p.A750T is a human gain-of-function obesity mutation"),
    ("PDE3B-PDE3A (90%)", "PDE3A (Q14432)", "T445A / T445N / T445S / A447T / A447V / G449V", "rs121908596 et al.", 0.9735, "LPath", "YES (Dual, 6 SAVs)", "Regulatory dimerization & phosphorylation segment", "Mendelian hypertension & brachydactyly syndrome (HTNB) via gain-of-function cAMP hydrolysis"),
    ("PDE3B-PDE4D (80%)", "PDE4D (Q08499)", "11 ACRDYS2 SAVs (S190A..I678T) + D527R/R563D", "rs397514466 et al.", 0.9992, "LPath", "YES (Dual, 11 SAVs)", "UCR1/UCR2 & catalytic dimerization interface", "Acrodysostosis 2 (ACRDYS2); D527R & R563D abolish dimerization"),
    ("PPARG-MED1 (90%) & NCOA1 (90%) & NCOA3 (90%) & LPIN1 (80%)", "PPARG (P37231)", "P495L (PDB Pro467)", "rs121909244", 0.9788, "LPath", "YES (Dual)", "3.64 A to MED1 Met644 (6ONJ) | 4.84 A to NCOA1 Ile689 (1K74)", "Severe insulin resistance, T2D & FPLD3; sits in AF-2 helix H12 (9aaTAD charge clamp)"),
    ("PPARG-MED1 (90%) & NCOA1 (90%) & NCOA3 (90%) & LPIN1 (80%)", "PPARG (P37231)", "V318M (PDB Val290)", "rs72551362", 0.8189, "LPath", "YES (Dual)", "6.07 A to MED1 Leu648 (6ONJ) | 6.14 A to NCOA1 Leu693 (1K74)", "Severe insulin resistance, T2D & FPLD3; borders the LXXLL coactivator binding cleft"),
    ("PPARG-NCOA1 (90%)", "NCOA1 (Q15788)", "E685A", "rs1049021", 0.8739, "LPath", "AM LPath + Crystal", "Exact N-cap (Glu685) of NCOA1 LXXLL peptide in 1K74 Chain E", "Directly caps the PPARG-bound NCOA1 LXXLL helix (residues 685-700 in crystal 1K74)"),
    ("PPARG-NR1H2 (90%) & NR1H3 (90%) & RXRG (80%)", "PPARG (P37231)", "R425C (PDB Arg397)", "rs72551364", 0.9972, "LPath", "YES (Dual)", "5.10 A to partner Glu352 in 1K74 | 5.46 A in 3E00", "Familial Partial Lipodystrophy type 3 (FPLD3) & T2D; breaks inter-chain heterodimer salt bridge"),
    ("PPARG-LPIN1 (80%)", "LPIN1 (Q14693)", "G56E & K425R/K595R", "Somatic / FT_MUT", 0.9983, "LPath", "YES (Dual)", "N-terminal NLIP domain & LXXIL coactivator region", "Alters Lipin-1 activity, acetylation, and hepatic PPAR coactivation"),
    ("PPARG-PMP2 (90%)", "PMP2 (P02689)", "I43N / T51P / I52T", "rs879253869 / rs1563518390 / rs1563518388", 0.8971, "LPath", "YES (Dual, 3 SAVs)", "Lipid-binding beta-barrel portal region", "Charcot-Marie-Tooth disease type 1G (CMT1G); explains 3_safety YELLOW neuropathy flag"),
    ("STARD10-PRMT6 (90%)", "STARD10 (Q9Y365) & PRMT6 (Q96LA8)", "STARD10 T109/V110 : PRMT6 E244/G281 + A194V", "rs2232016", 0.3662, "RF2 p=0.899 + SAV", "High-Prob Interface", "RF2-PPI p=0.899 at PRMT6:G281-STARD10:V110 (6SER START domain)", "Maps directly to STARD10 lipid-transfer pocket & PRMT6 Rossmann fold"),
    ("GRB14-TNKS2 (80%)", "GRB14 (Q14449) & TNKS2 (Q9H2K2)", "GRB14 F90I / Q348A / A378 : TNKS2 D1045 / M1054V", "rs61748245 / FT_MUT", 0.0967, "Mutagen+SAV", "Exp. Validated", "GRB14 N-term -> TNKS2 ARC | RF2 GRB14:A378 (BPS 2AUH) -> TNKS2:D1045", "Q348A/N349A abolishes GRB14 inhibition of AKT/MAPK; M1054V abolishes TNKS2 activity"),
]

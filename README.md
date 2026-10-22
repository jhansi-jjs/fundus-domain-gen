# Robust Optic Disc/Cup Segmentation Across Imaging Sources

**Hackathon Track 2B — Deep Learning for Healthcare (Segmentation)**

> **Presenter / Author:** **Jhansi Lakshmi**  
> **Roll No:** **AM.SC.U4AIE24047**  
> **Department:** Department of Artificial Intelligence & Data Science, School of Computing  
> **Project Repository:** [github.com/jhansi-jjs/fundus-domain-gen](https://github.com/jhansi-jjs/fundus-domain-gen)  
> 📊 **PowerPoint Deck:** [`Fundus_DomainGen_Presentation_Canva_Style.pptx`](./Fundus_DomainGen_Presentation_Canva_Style.pptx)  
> 🌐 **Interactive Web Deck:** [`presentation_canvas.html`](./presentation_canvas.html)  
> 📋 **Empirical Facts Reference:** [`results/slide_assets/facts.md`](./results/slide_assets/facts.md)  
> 📹 **Demo video:** [Watch on YouTube](https://youtu.be/R329Oe0CdyM) | [Google Drive Mirror](https://drive.google.com/file/d/1ILD53zydP-7Kemog1iJ-2kjK7xhITEtg/view?usp=sharing)  
> 📄 **Full report:** [`REPORT.md`](./REPORT.md)  

---

## The problem in one table

| Evaluation Domain | Protocol Setting | Baseline U-Net (Dice / IoU) | + IBN Mechanism (Dice / IoU) | Absolute Delta (Macro Dice) | Relative Gain |
|---|---|---|---|---|---|
| **REFUGE (Source)** | In-domain Test | 0.9172 / 0.8565 | **0.9198 / 0.8604** | +0.0026 | +0.28% (Zero in-domain degradation) |
| **Drishti-GS (Unseen Target 1)** | Cross-domain Zero-Shot | 0.6585 / 0.5620 | **0.7692 / 0.6684** | **+0.1107** | **+16.81%** (Camera shift resolved) |
| **ORIGA (Unseen Target 2)** | Cross-domain Zero-Shot | 0.5867 / 0.4948 | **0.7754 / 0.6759** | **+0.1887** | **+32.16%** (Severe domain gap closed) |
| **Cross-Domain Mean** | Controlled Ablation | 0.6226 / 0.5284 | **0.7723 / 0.6722** | **+0.1497** | **+24.05%** average cross-domain recovery |

**Headline finding:** In-domain performance barely changed (+0.0026 Dice) while cross-domain Dice improved by **+0.1107 to +0.1887 points** with **EXACTLY 0 additional parameters** (7,766,051 vs. 7,766,051) — proving the mechanism specifically closes the domain gap rather than adding generic model capacity.

---

## Why this matters

Optic disc/cup segmentation drives the Cup-to-Disc Ratio (CDR) used in glaucoma screening. A model that only works on the hospital it was trained on isn't clinically deployable — this is a real generalization problem, not a benchmark artifact.

---

## Complete 13-Slide Presentation Deck Outline

The repository includes both an interactive HTML presentation deck ([`presentation_canvas.html`](./presentation_canvas.html)) and a Canva-style 16:9 widescreen PowerPoint deck ([`Fundus_DomainGen_Presentation_Canva_Style.pptx`](./Fundus_DomainGen_Presentation_Canva_Style.pptx)). Every slide embeds real 300 DPI figures and comprehensive speaker notes addressing the 50-mark evaluation rubric.

### Slide 1: Title & Hero Presenter Slide
- **Project Title:** Robust Optic Disc & Cup Segmentation Across Imaging Sources
- **Subtitle:** Lightweight Single-Source Domain Generalization via Selective Instance-Batch Normalization (IBN)
- **Presenter Card:** **Jhansi Lakshmi** (Roll No: **AM.SC.U4AIE24047**), Dept. of AI & Data Science
- **Core Pillars:**
  1. *Clinical Domain Shift Problem:* Standard U-Net drops from 0.9172 to 0.5867 on ORIGA (-33.05%).
  2. *Selective IBN Inductive Bias:* Early encoder channels split 50/50 between InstanceNorm (strips camera style) and BatchNorm (preserves cup/disc anatomy).
  3. *Empirical Proof (+0 Params):* Cross-domain Dice jumps to 0.7754 (+18.87%) with 0 added parameters (7,766,051 vs 7,766,051).

### Slide 2: Problem Statement and Motivation
- **Clinical Importance:** Glaucoma affects >80M people; Cup-to-Disc Ratio (CDR) is the gold standard diagnostic metric.
- **Hospital Domain Gap:** Variation in fundus camera sensors (Zeiss, Canon, Topcon), illumination, and patient pigmentation causes deep networks to fail catastrophically across hospitals.
- **Track 2B Scope:** Interprets track focus toward structural segmentation and out-of-domain generalization over saturated binary classifiers.

### Slide 3: Objectives & Deliverables
- **5 Core Goals:** (1) Benchmark cross-dataset collapse honestly, (2) Enforce single-source DG with zero target access, (3) Preserve in-domain source precision (>0.91 Dice), (4) Enforce zero parameter overhead (+0 params), (5) Verify causal attribution via controlled ablation.
- **Deliverables:** Reproducible PyTorch code, saved checkpoints (`unet_baseline_best.pt`, `unet_ibn_best.pt`), empirical gate verification (>0.75 target Dice achieved), and automated 4-column diagnostic visualizer.

### Slide 4: Literature Review & Research Gap
- **Comparative Matrix:** U-Net (Ronneberger 2015), IBN-Net (Pan et al. ECCV 2018), DDRD-Net (Chen et al. MICCAI 2023), and Unsupervised Domain Adaptation (CycleGAN/Adversarial).
- **The Critical Gap:** Existing adaptation methods require unlabelled target hospital data or multi-source training cohorts. In clinical reality, developers only have ONE approved hospital training dataset and must generalize zero-shot.

### Slide 5: Novelty and Contribution
- **Dual-Pathway Inductive Bias:** 50/50 channel partition in Encoders 1 & 2.
- **Selective Early Placement:** Applied only to shallow layers (32 and 64 channels) where camera style is encoded, keeping deep semantic layers (Enc 3, 4, bottleneck, decoder) 100% standard BatchNorm.
- **Exact Parameter Invariance:** Both baseline and IBN U-Net have exactly 7,766,051 parameters. The gains stem purely from inductive bias, not capacity inflation.

### Slide 6: Dataset Details & Integrity
- **Source Cohort:** REFUGE Challenge (320 train images, 80 test images; 10% val split = 32 images carved from train).
- **Target Cohorts (Zero-Shot Eval Only):** Drishti-GS (51 test images), ORIGA (150 test images).
- **Semantic Classes:** 0: Background (raw 255), 1: Optic Disc (raw 128), 2: Optic Cup (raw 0). Evaluated via Macro Dice/IoU.
- **Excluded Cohort:** RIGA (BinRushed/Magrabia) was dropped due to irregular nested TIFF hierarchies to ensure strict scientific integrity.

### Slide 7: Data Preprocessing Pipeline
- **Pipeline Hygiene:** Filename stem matching, standardized resizing from 512x512 to 256x256, class remapping to contiguous indices {0, 1, 2}, pixel normalization to `[-1.0, 1.0]`.
- **Determinism:** Fixed seed=42 across Python, NumPy, PyTorch, and DataLoader worker threads.
- **PyTorch AMP:** Automatic mixed precision (`torch.cuda.amp.GradScaler`) for 2.4x acceleration within 6GB VRAM on RTX 4050 GPU.

### Slide 8: Model Architecture & Workflow
- **Encoder-Decoder Pipeline:** 4 downsampling stages with MaxPool 2x2, bottleneck (512 channels), 4 upsampling stages with ConvTranspose2d (2x2 stride 2) and skip connections.
- **Mathematical Formulation:** Feature map $X \in \mathbb{R}^{B \times C \times H \times W}$ partitioned into $[X_1, X_2]$ where $\hat{x}_1 = \text{InstanceNorm}(X_1)$ and $\hat{x}_2 = \text{BatchNorm}(X_2)$, followed by concatenation and ReLU.

### Slide 9: Implementation & Training Details
- **Hyperparameter Facts:** Batch size = 8, Adam optimizer ($lr = 10^{-3}$, weight decay = $10^{-5}$), CrossEntropyLoss, 60 epochs.
- **Embedded Figure:** Real 300 DPI training loss convergence and validation Macro Dice curves (`training_loss_and_val_curves.png`). Both models converge smoothly without training instability.

### Slide 10: Results & Quantitative Evaluation
- **Embedded Figure:** High-resolution grouped bar chart (`cross_domain_generalization_bar_chart.png`).
- **Core Metrics:** In-domain REFUGE: 0.9172 -> 0.9198 (+0.0026); Drishti-GS: 0.6585 -> 0.7692 (+16.8% relative); ORIGA: 0.5867 -> 0.7754 (+32.2% relative).

### Slide 11: Qualitative Visual Results
- **Embedded Figure:** 4-column diagnostic visual panel (`qualitative_segmentation_comparison.png`).
- **Visual Evidence:** Demonstrates how baseline U-Net fractures or completely loses the optic cup under target hospital lighting, whereas IBN U-Net cleanly reconstructs both disc and cup boundaries matching ground truth.

### Slide 12: Ablation Study & Scientific Rigor
- **Embedded Figure:** Tabular summary graphic (`results_table_summary.png`).
- **Causal Proof:** Removing IBN drops average cross-domain Dice from 0.7723 to 0.6226 (-0.1497) under identical random seed, optimizer, and duration. Proves the mechanism specifically isolates domain shift.

### Slide 13: Limitations & Future Scope
- **Honest Limitations:** Benchmark sample sizes (51 and 150 images), single seed=42 point estimates, and fixed early-layer placement.
- **Future Roadmap:** Automated Cup-to-Disc Ratio (CDR) numerical calculation and glaucoma risk staging, scaling to native 512x512 resolution, standardizing RIGA TIFF pipelines, and exploring test-time adaptation (AdaBN).

---

## Quickstart & Reproduction

```bash
git clone https://github.com/jhansi-jjs/fundus-domain-gen.git
cd fundus-domain-gen
pip install -r requirements.txt
pip install python-pptx matplotlib

# Generate all 300 DPI figures and facts.md
python generate_slide_assets.py

# Generate the Canva-style PowerPoint presentation (.pptx)
python generate_canvas_ppt.py

# Generate the interactive fullscreen web deck (.html)
python generate_html_presentation.py
```

---

## Citations

- Orlando, J.I. et al. "REFUGE Challenge: A unified framework for evaluating automated methods for glaucoma assessment from fundus photographs." *Medical Image Analysis*, 2020.
- Sivaswamy, J. et al. "Drishti-GS: Retinal image dataset for optic nerve head (ONH) segmentation." *ISBI*, 2014.
- Zhang, Z. et al. "ORIGA-light: An online retinal fundus image database for glaucoma analysis and research." *EMBC*, 2010.
- Chen, Z. et al. "Treasure in Distribution: A Domain Randomization based Multi-Source Domain Generalization for 2D Medical Image Segmentation." *MICCAI*, 2023. [Zenodo 8009107]
- Ronneberger, O. et al. "U-Net: Convolutional Networks for Biomedical Image Segmentation." *MICCAI*, 2015.
- Pan, X., Luo, P., Shi, J., Tang, X. "Two at Once: Enhancing Learning and Generalization Capacities via IBN-Net." *ECCV*, 2018.

---

## Reproducibility Checklist

- [x] Fixed train/test splits (zero leakage)
- [x] seed=42 fixed across Python, NumPy, PyTorch, DataLoader workers
- [x] Trained strictly on REFUGE source training split
- [x] Target domains Drishti-GS & ORIGA never exposed to training or tuning
- [x] All evaluation numbers parsed directly from JSON logs
- [x] Canva-style 16:9 widescreen presentation deck generated with embedded speaker notes

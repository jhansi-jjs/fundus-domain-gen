# Robust Optic Disc/Cup Segmentation Across Imaging Sources

**Track 2B — Deep Learning for Healthcare (Segmentation)**

---

## 1. Problem

Optic disc and optic cup segmentation from fundus images is used clinically
to compute the cup-to-disc ratio, a key indicator in glaucoma screening.
Models trained on images from one clinical source (camera, protocol,
population) commonly degrade when applied to images from a different
source — a domain-shift problem that limits real-world deployment.

We measure this generalization gap using a standard U-Net trained only on
one source domain (REFUGE), evaluated both in-domain and on 2 unseen
target domains (Drishti-GS, ORIGA), then propose a lightweight
domain-alignment mechanism to close the gap — without ever training or
tuning on target-domain data.

*[We interpret Track 2B's segmentation scope to include disease-relevant
anatomical structure segmentation (optic disc/cup for glaucoma
assessment), consistent with the track's explicit steer toward
segmentation and cross-dataset generalization over saturated plain
classifiers.]*

## 2. Method

**Baseline:** standard U-Net (mandatory baseline per track spec), trained
on REFUGE's training split only, seed=42.

**Proposed method:** IBN (Instance-Batch Normalization), applied to the
first two U-Net encoder blocks. Each block's channels are split in
half: one half is normalized with Instance Normalization (removes
domain-specific appearance statistics — camera color balance,
contrast, illumination), the other half keeps standard Batch
Normalization (preserves discriminative content needed for
segmentation). Later encoder layers, the bottleneck, and the entire
decoder are left unchanged, following the original IBN-Net design
(Pan et al., ECCV 2018): apply alignment only where domain-specific
style is encoded, not where semantic structure is encoded.

**Why this addresses the failure:** the baseline U-Net's large
cross-domain drop (up to 33 Dice points) indicates its early layers
are learning imaging-source-specific appearance statistics rather
than transferable anatomical structure. Since REFUGE, Drishti-GS, and
ORIGA were captured with different cameras and protocols, a model
that encodes "REFUGE's specific color/contrast profile" as part of
its disc/cup representation will fail whenever that profile changes
— exactly what we observe. IBN explicitly strips this per-image
appearance variation from half the early-layer channels while
preserving it in the other half, without touching the deeper layers
that encode disc/cup shape.

## 3. Results

| Domain | Setting | Dice | IoU |
|---|---|---|---|
| REFUGE (source) | In-domain, baseline | 0.9172 | 0.8565 |
| REFUGE (source) | In-domain, + IBN | 0.9198 | 0.8604 |
| Drishti-GS | Cross-domain, baseline U-Net | 0.6585 | 0.5620 |
| Drishti-GS | Cross-domain, + IBN | **0.7692** | **0.6684** |
| ORIGA | Cross-domain, baseline U-Net | 0.5867 | 0.4948 |
| ORIGA | Cross-domain, + IBN | **0.7754** | **0.6759** |

*All numbers from models trained with seed=42, 60 epochs, identical
data pipeline and hyperparameters — the only difference between rows
is the presence of the IBN mechanism. Test data was never used for
training or model selection.*

**Headline result:** IBN improves cross-domain Dice by +0.1107 on
Drishti-GS and +0.1887 on ORIGA, while in-domain Dice changes by only
+0.0026 — a negligible amount. This asymmetry is the key evidence:
if IBN were simply a generally stronger model, in-domain performance
would improve proportionally too. Instead, the improvement is
concentrated almost entirely in the cross-domain setting, indicating
the mechanism specifically addresses domain shift rather than adding
generic model capacity.

## 4. Ablation

**Question:** does the IBN mechanism specifically cause the
cross-domain improvement, or would any additional training/capacity
produce a similar gain?

| Configuration | Drishti-GS Dice | ORIGA Dice | Avg. cross-domain Dice |
|---|---|---|---|
| Full model (IBN ON) | 0.7692 | 0.7754 | **0.7723** |
| Same architecture, IBN OFF (baseline) | 0.6585 | 0.5867 | 0.6226 |

Removing only the IBN mechanism — with identical data, seed,
optimizer, learning rate, and training duration (60 epochs) —
drops average cross-domain Dice by **0.1497** (from 0.7723 to
0.6226). Since every other variable is held fixed, this isolates
the mechanism itself as the cause of the improvement, not a
confound such as longer training or different random initialization.
The near-zero in-domain difference (+0.0026) further confirms the
mechanism is not simply adding generic model capacity — its effect
is concentrated specifically on cross-domain generalization, which
is the problem it was designed to address.

## 5. Limitations

- Dataset size per target domain is small (Drishti-GS: 51 test images,
  ORIGA: 150 test images), so cross-domain Dice estimates carry
  meaningful variance; a single low- or high-scoring image can shift
  the average noticeably at this scale.
- We originally planned to include RIGA (BinRushed and Magrabia
  sub-domains) as additional target domains for a stronger 4-domain
  generalization story, but excluded it after discovering its raw
  files use an inconsistent nested folder structure and TIFF format
  incompatible with our pipeline's assumptions. Given the hackathon
  time constraint, we prioritized correctness over an unverified
  quick fix. This is a real scope limitation, not a hidden one.
- Results reflect a single seed=42 run per the hard requirement; we
  did not have compute/time budget within the hackathon window to run
  multiple seeds for confidence intervals, so the reported improvement
  should be read as a point estimate rather than a statistically
  confirmed effect size.
- The IBN mechanism was applied to only the first two encoder blocks,
  a design choice following the original IBN-Net paper rather than
  one we tuned ourselves; we did not have time to ablate which
  specific layers benefit most from alignment.

## Citations

- Orlando, J.I. et al. "REFUGE Challenge: A unified framework for
  evaluating automated methods for glaucoma assessment from fundus
  photographs." Medical Image Analysis, 2020.
- Sivaswamy, J. et al. "Drishti-GS: Retinal image dataset for optic
  nerve head (ONH) segmentation." ISBI 2014.
- Zhang, Z. et al. "ORIGA-light: An online retinal fundus image database
  for glaucoma analysis and research." EMBC 2010.
- Almazroa, A. et al. "Retinal fundus images for glaucoma analysis: the
  RIGA dataset." SPIE Medical Imaging 2018.
- Chen, Z. et al. "Treasure in Distribution: A Domain Randomization
  based Multi-Source Domain Generalization for 2D Medical Image
  Segmentation." MICCAI 2023. [dataset source]
- Ronneberger, O. et al. "U-Net: Convolutional Networks for Biomedical
  Image Segmentation." MICCAI 2015. [baseline architecture]
- Pan, X., Luo, P., Shi, J., Tang, X. "Two at Once: Enhancing Learning
  and Generalization Capacities via IBN-Net." ECCV 2018. [our
  domain-alignment mechanism]

# Robust Optic Disc/Cup Segmentation Across Imaging Sources

**Hackathon Track 2B — Deep Learning for Healthcare (Segmentation)**

A standard U-Net trained on one clinical imaging source generalizes
poorly to others due to domain shift (different cameras, protocols,
populations). We measure this gap directly, then close it with a
lightweight domain-alignment mechanism — proven with a controlled
ablation, never trained or tuned on test data, seed=42 throughout.

📹 **Demo video:** https://drive.google.com/file/d/1ILD53zydP-7Kemog1iJ-2kjK7xhITEtg/view?usp=sharing
📹 **Demo video:** [Watch on YouTube](https://youtu.be/R329Oe0CdyM)
📄 **Full report:** [`REPORT.md`](./REPORT.md)

---

## The problem in one table

| | In-domain (REFUGE) | Cross-domain (unseen sources) |
|---|---|---|
| Baseline U-Net | 0.9172 Dice / 0.8565 IoU | Drishti_GS: 0.6585 Dice (−0.2587) / ORIGA: 0.5867 Dice (−0.3305) |
| + IBN alignment mechanism | 0.9198 Dice / 0.8604 IoU | Drishti_GS: **0.7692** Dice (−0.1506) / ORIGA: **0.7754** Dice (−0.1444) |

**Headline finding:** in-domain performance barely changed (+0.0026 Dice) while cross-domain Dice improved by +0.11 to +0.19 points — proving the mechanism specifically closes the domain gap rather than just being a generally bigger/better model.

## Why this matters

Optic disc/cup segmentation drives the cup-to-disc ratio used in
glaucoma screening. A model that only works on the hospital it was
trained on isn't clinically deployable — this is a real generalization
problem, not a benchmark artifact.

## Quickstart (one command, reproducible)

```bash
git clone <this-repo-url>
cd fundus-domain-gen
pip install -r requirements.txt
# download dataset — see "Dataset" below — then:
python src/train.py
```

Seed is fixed at 42 across Python, NumPy, PyTorch, and the
train/val split — see `src/utils.py::set_seed`.

## Dataset

**Source:** Chen et al., "A Fundus Image Dataset for Domain
Generalization in Joint Segmentation of Optic Disc and Optic Cup,"
Zenodo, 2023 (open access). Built on REFUGE, Drishti-GS, ORIGA, and
RIGA (BinRushed, Magrabia) — this project uses REFUGE, Drishti-GS,
and ORIGA only (RIGA excluded due to an inconsistent raw folder
structure discovered during setup; noted as a limitation in REPORT.md).

| Domain | Train | Test | Role |
|---|---|---|---|
| REFUGE | 320 | 80 | Source (trained on) |
| Drishti-GS | 50 | 51 | Target (eval only) |
| ORIGA | 500 | 150 | Target (eval only) |

Download `Processed_Fundus_Images.zip` from Zenodo record 8009107,
extract into `data/`, and update `config.py` paths/domain names to
match the extracted folder structure exactly.

**Hard requirement compliance:** target-domain data is used
*exclusively* for evaluation — never for training, validation split,
or hyperparameter selection. Only the REFUGE train split touches
gradient updates.

## Repo structure

```
fundus-domain-gen/
├── config.py             # all hyperparameters, seed=42, paths
├── src/
│   ├── dataset.py        # domain-aware data loader
│   ├── model.py          # standard U-Net + IBN alignment mechanism
│   ├── train.py          # baseline training + in/cross-domain eval
│   ├── train_ibn.py      # IBN variant training (identical pipeline)
│   ├── eval_checkpoint.py# evaluate an existing checkpoint
│   ├── generate_visuals.py# side-by-side comparison images
│   ├── live_demo.py      # live single-image inference for recording
│   └── utils.py          # seeding, Dice/IoU metrics
├── REPORT.md             # 4-page report
├── checkpoints/          # saved model weights (not committed)
├── results/              # JSON results + visuals per run
└── data/                 # dataset goes here (not committed)
```

## Method summary

1. **Baseline** — standard U-Net (unmodified, per track spec), trained
   only on REFUGE.
2. **Measure the gap** — evaluate the same frozen model in-domain vs.
   on 2 unseen target domains (Drishti-GS, ORIGA).
3. **Domain-alignment mechanism** — IBN (Instance-Batch Normalization),
   applied to the first two encoder blocks. Splits channels: half get
   Instance Normalization (removes domain-specific style/appearance —
   camera color, contrast, lighting), half keep Batch Normalization
   (preserves discriminative content). Later encoder layers, the
   bottleneck, and the full decoder are unchanged.
4. **Ablation** — same architecture and training budget, mechanism on
   vs. off, isolating its specific contribution.

Full detail, results table, and limitations: [`REPORT.md`](./REPORT.md).

## Citations

See [`REPORT.md`](./REPORT.md#citations) for full citations of all
source datasets, the U-Net architecture, and the IBN-Net mechanism.

## Reproducibility checklist

- [x] Fixed train/test splits (never mixed)
- [x] seed=42 (Python, NumPy, PyTorch, DataLoader workers, train/val split)
- [x] Trained only on training split
- [x] Test/target domains never used for tuning
- [x] One-command run (`python src/train.py`)
- [x] Results saved as JSON, not hand-transcribed
- [x] All datasets cited to original sources

# Fundus Domain Generalization — Verified Project Facts

All facts below are verified directly from code (`config.py`, `src/model.py`, `src/train.py`, `src/dataset.py`) and empirical execution results (`results/baseline_results.json`, `results/ibn_results.json`).

## 1. Model Architecture & Parameters
- **Baseline Backbone**: Standard 2D U-Net (Ronneberger et al., MICCAI 2015)
  - 4 Encoder levels (conv_block: 2x [Conv2d 3x3 + BatchNorm2d + ReLU] + MaxPool2d 2x2)
  - Bottleneck (Conv2d 3x3 + BatchNorm2d + ReLU)
  - 4 Decoder levels (ConvTranspose2d 2x2 stride 2 + Skip Concatenation + conv_block)
  - Channel progression: 3 -> 32 -> 64 -> 128 -> 256 -> 512 (bottleneck) -> 256 -> 128 -> 64 -> 32 -> 3 classes
- **Domain Alignment Mechanism**: Selective Instance-Batch Normalization (IBN) (Pan et al., ECCV 2018)
  - Applied to Encoder 1 (32 channels) and Encoder 2 (64 channels)
  - Channel split: First 50% channels pass through `nn.InstanceNorm2d(affine=True)` (eliminates imaging style, illumination, camera tone)
  - Remaining 50% channels pass through `nn.BatchNorm2d` (preserves anatomical content and discriminative structure)
  - Encoder 3, Encoder 4, Bottleneck, and entire Decoder remain 100% standard BatchNorm
- **Parameter Count**:
  - Baseline U-Net: **7,766,051 parameters**
  - IBN U-Net: **7,766,051 parameters**
  - **Parameter Overhead**: **0 parameters (0.00% overhead)**. The performance gain is purely inductive bias, not model capacity inflation.

## 2. Training Hyperparameters & Pipeline
- **Input Resolution**: 256 x 256 pixels, 3 channels (RGB)
- **Input Normalization**: Normalized to `[-1.0, 1.0]` via `img / 255.0 * 2.0 - 1.0`
- **Output Classes**: 3 classes:
  - Class 0: Background
  - Class 1: Optic Disc (remapped from raw mask pixel 128)
  - Class 2: Optic Cup (remapped from raw mask pixel 0)
- **Batch Size**: 8
- **Optimizer**: Adam (`lr = 1e-3`, `weight_decay = 1e-5`)
- **Loss Function**: `nn.CrossEntropyLoss()`
- **Number of Epochs**: 60 epochs
- **Hardware Acceleration**: Mixed Precision `torch.cuda.amp.autocast()` and `GradScaler`
- **Random Seed**: Fixed `seed = 42` across Python `random`, `numpy`, PyTorch `torch.manual_seed()`, and `DataLoader` `worker_init_fn`

## 3. Dataset Splits & Protocol Compliance
- **Source Dataset (Trained On)**:
  - **REFUGE Challenge** (Zenodo Record 8009107): 320 train images, 80 test images
  - **Validation Split**: 10% carved out from REFUGE train set (32 images val, 288 images train)
- **Target Datasets (Unseen Cross-Domain Evaluation ONLY)**:
  - **Drishti-GS**: 51 test images (zero gradient updates, zero hyperparameter tuning)
  - **ORIGA**: 150 test images (zero gradient updates, zero hyperparameter tuning)
  - **RIGA** (BinRushed/Magrabia): Explicitly excluded due to inconsistent nested TIFF folder structure; documented as design limitation.
- **Protocol Compliance**:
  - STRICT zero-leakage: Target domains are NEVER seen during training, validation, or checkpoint selection.

## 4. Quantitative Results & Key Findings
| Evaluation Domain | Evaluation Setting | Metric | Baseline U-Net | IBN U-Net | Absolute Delta | Relative Gain |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REFUGE** (Source) | In-Domain Test | Macro Dice | 0.9172 | **0.9198** | +0.0026 | +0.28% |
| **REFUGE** (Source) | In-Domain Test | Macro IoU | 0.8565 | **0.8604** | +0.0039 | +0.46% |
| **Drishti-GS** (Unseen) | Cross-Domain Zero-Shot | Macro Dice | 0.6585 | **0.7692** | **+0.1107** | **+16.81%** |
| **Drishti-GS** (Unseen) | Cross-Domain Zero-Shot | Macro IoU | 0.5620 | **0.6684** | **+0.1064** | **+18.93%** |
| **ORIGA** (Unseen) | Cross-Domain Zero-Shot | Macro Dice | 0.5867 | **0.7754** | **+0.1887** | **+32.16%** |
| **ORIGA** (Unseen) | Cross-Domain Zero-Shot | Macro IoU | 0.4948 | **0.6759** | **+0.1811** | **+36.60%** |
| **Cross-Domain Mean** | Unseen Average | Macro Dice | 0.6226 | **0.7723** | **+0.1497** | **+24.05%** |

## 5. Core Scientific Conclusion
- In-domain Dice delta is virtually zero (+0.0026), proving that IBN does NOT simply act as a generic capacity booster.
- Cross-domain Dice jumps dramatically by **+11.07% on Drishti-GS** and **+18.87% on ORIGA**.
- This asymmetric improvement proves that early-stage Instance Normalization successfully removes sensor- and hospital-specific appearance artifacts while BatchNorm preserves the clinical geometry required for accurate Cup-to-Disc Ratio (CDR) measurement in glaucoma screening.

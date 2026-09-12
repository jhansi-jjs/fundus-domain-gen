"""
Central config. Every script imports SEED from here — never hardcode
seed=42 anywhere else.
"""
import os

SEED = 42

# ---- Paths ----
DATA_ROOT = "data/Processed_Fundus_Images"   # unzip the downloaded dataset here
SOURCE_DOMAIN = "REFUGE"              # what we train on
TARGET_DOMAINS = ["Drishti_GS", "ORIGA"]  # cross-domain eval only, never trained on
# RIGA (BinRushed/Magrabia) dropped: inconsistent nested TIF structure,
# not worth the time risk under the hackathon deadline. REFUGE, Drishti_GS,
# and ORIGA all share the same clean {domain}/{train,test}/{image,mask} layout.

CHECKPOINT_DIR = "checkpoints"
RESULTS_DIR = "results"

# ---- Image / mask ----
IMG_SIZE = 256          # resize from 512 -> 256 for speed on a 4050; bump to 512 later if time allows
NUM_CLASSES = 3         # background, disc, cup (we treat as 3-class segmentation, argmax at eval)

# Raw mask pixel values in the dataset (per DDRD_Net_Dataset spec)
MASK_BACKGROUND_VAL = 255
MASK_DISC_VAL = 128
MASK_CUP_VAL = 0

# ---- Training ----
BATCH_SIZE = 8
NUM_EPOCHS = 60
LR = 1e-3
WEIGHT_DECAY = 1e-5
VAL_SPLIT = 0.1          # carved out of the SOURCE domain's train set only
NUM_WORKERS = 2
MIXED_PRECISION = True   # use torch.cuda.amp — important for 4050's ~6GB VRAM

# ---- Domain alignment mechanism (Stage 6, off by default for baseline runs) ----
USE_DOMAIN_ALIGNMENT = False
ALIGNMENT_LOSS_WEIGHT = 0.1

os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

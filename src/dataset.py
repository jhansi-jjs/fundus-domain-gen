"""
Loads the DDRD_Net_Dataset folder structure:

    DATA_ROOT/<Domain>/{train,test}/{image,mask}/*.png|jpg

Masks use the raw pixel convention: 128=disc, 0=cup, 255=background.
We remap those to class indices {0=background, 1=disc, 2=cup} so the
model trains on ordinary contiguous class indices.
"""
import os
import glob
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg


def remap_mask(mask_arr: np.ndarray) -> np.ndarray:
    """Raw pixel values -> class indices {0,1,2}."""
    out = np.zeros_like(mask_arr, dtype=np.int64)
    out[mask_arr == cfg.MASK_DISC_VAL] = 1
    out[mask_arr == cfg.MASK_CUP_VAL] = 2
    # everything else (including MASK_BACKGROUND_VAL) stays 0
    return out


class FundusSegDataset(Dataset):
    def __init__(self, domain: str, split: str, img_size: int = None, transform=None):
        """
        domain: e.g. "REFUGE", "Drishti_GS", "RIM_ONE_r3", "ORIGA"
        split:  "train" or "test"
        """
        self.img_size = img_size or cfg.IMG_SIZE
        self.transform = transform

        img_dir = os.path.join(cfg.DATA_ROOT, domain, split, "image")
        mask_dir = os.path.join(cfg.DATA_ROOT, domain, split, "mask")

        if not os.path.isdir(img_dir):
            raise FileNotFoundError(
                f"Expected images at {img_dir} — check that you've unzipped the "
                f"dataset to {cfg.DATA_ROOT} and the folder names match "
                f"(case-sensitive: Drishti_GS, RIM_ONE_r3, ORIGA, REFUGE)."
            )

        self.img_paths = sorted(
            glob.glob(os.path.join(img_dir, "*.png"))
            + glob.glob(os.path.join(img_dir, "*.jpg"))
            + glob.glob(os.path.join(img_dir, "*.jpeg"))
        )
        self.mask_paths = []
        for p in self.img_paths:
            stem = os.path.splitext(os.path.basename(p))[0]
            candidates = glob.glob(os.path.join(mask_dir, stem + ".*"))
            if not candidates:
                raise FileNotFoundError(f"No mask found for image {p} in {mask_dir}")
            self.mask_paths.append(candidates[0])

        if len(self.img_paths) == 0:
            raise RuntimeError(f"No images found in {img_dir} — check dataset extraction.")

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        img = Image.open(self.img_paths[idx]).convert("RGB").resize(
            (self.img_size, self.img_size), Image.BILINEAR
        )
        mask = Image.open(self.mask_paths[idx]).convert("L").resize(
            (self.img_size, self.img_size), Image.NEAREST  # NEAREST — never interpolate label maps
        )

        img_arr = np.array(img, dtype=np.float32) / 255.0
        img_arr = (img_arr - 0.5) / 0.5  # normalize to [-1, 1]
        img_tensor = torch.from_numpy(img_arr).permute(2, 0, 1).float()

        mask_arr = remap_mask(np.array(mask))
        mask_tensor = torch.from_numpy(mask_arr).long()

        if self.transform:
            img_tensor, mask_tensor = self.transform(img_tensor, mask_tensor)

        return img_tensor, mask_tensor

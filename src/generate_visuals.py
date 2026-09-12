"""
Stage 9: generates side-by-side comparison images (original | ground
truth | baseline prediction | IBN prediction) for a few target-domain
samples. These are what go in the demo video and report figures.
Run: python src/generate_visuals.py
"""
import os
import sys
import numpy as np
from PIL import Image
import torch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from src.dataset import FundusSegDataset
from src.model import UNet

# Colors for visualizing the 3 classes: background, disc, cup
CLASS_COLORS = np.array([
    [0, 0, 0],        # background - black
    [255, 255, 0],    # disc - yellow
    [255, 0, 0],       # cup - red
], dtype=np.uint8)


def mask_to_rgb(mask_tensor):
    mask_np = mask_tensor.numpy() if torch.is_tensor(mask_tensor) else mask_tensor
    return CLASS_COLORS[mask_np]


def denormalize_img(img_tensor):
    img = img_tensor.permute(1, 2, 0).numpy()
    img = (img * 0.5 + 0.5) * 255.0
    return np.clip(img, 0, 255).astype(np.uint8)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    baseline = UNet(num_classes=cfg.NUM_CLASSES, base_ch=32, use_ibn=False).to(device)
    baseline.load_state_dict(torch.load(os.path.join(cfg.CHECKPOINT_DIR, "unet_baseline_best.pt"), map_location=device))
    baseline.eval()

    ibn = UNet(num_classes=cfg.NUM_CLASSES, base_ch=32, use_ibn=True).to(device)
    ibn.load_state_dict(torch.load(os.path.join(cfg.CHECKPOINT_DIR, "unet_ibn_best.pt"), map_location=device))
    ibn.eval()

    out_dir = os.path.join(cfg.RESULTS_DIR, "visuals")
    os.makedirs(out_dir, exist_ok=True)

    for domain in cfg.TARGET_DOMAINS:
        ds = FundusSegDataset(domain, "test")
        # pick 3 samples spread across the test set
        indices = [0, len(ds) // 2, len(ds) - 1]

        for idx in indices:
            img_tensor, mask_tensor = ds[idx]
            img_batch = img_tensor.unsqueeze(0).to(device)

            with torch.no_grad():
                base_pred = torch.argmax(baseline(img_batch), dim=1).squeeze(0).cpu()
                ibn_pred = torch.argmax(ibn(img_batch), dim=1).squeeze(0).cpu()

            orig_img = denormalize_img(img_tensor)
            gt_rgb = mask_to_rgb(mask_tensor)
            base_rgb = mask_to_rgb(base_pred)
            ibn_rgb = mask_to_rgb(ibn_pred)

            combined = np.concatenate([orig_img, gt_rgb, base_rgb, ibn_rgb], axis=1)
            out_path = os.path.join(out_dir, f"{domain}_sample{idx}_orig_gt_baseline_ibn.png")
            Image.fromarray(combined).save(out_path)
            print(f"Saved: {out_path}")

    print(f"\nAll visuals saved to {out_dir}/")
    print("Each image is 4 panels left-to-right: Original | Ground Truth | Baseline Prediction | IBN Prediction")


if __name__ == "__main__":
    main()

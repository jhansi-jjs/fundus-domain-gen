"""
Live single-image demo for recording. Loads both models, runs
inference on one target-domain image, prints Dice scores live, and
displays the comparison image. Run this ON CAMERA while recording.
Run: python src/live_demo.py
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
from src.utils import dice_score

CLASS_COLORS = np.array([[0, 0, 0], [255, 255, 0], [255, 0, 0]], dtype=np.uint8)


def mask_to_rgb(mask):
    return CLASS_COLORS[mask.numpy() if torch.is_tensor(mask) else mask]


def denorm(img_tensor):
    img = img_tensor.permute(1, 2, 0).numpy()
    return np.clip((img * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print("Loading baseline U-Net and IBN U-Net checkpoints...\n")

    baseline = UNet(num_classes=cfg.NUM_CLASSES, base_ch=32, use_ibn=False).to(device)
    baseline.load_state_dict(torch.load(os.path.join(cfg.CHECKPOINT_DIR, "unet_baseline_best.pt"), map_location=device))
    baseline.eval()

    ibn = UNet(num_classes=cfg.NUM_CLASSES, base_ch=32, use_ibn=True).to(device)
    ibn.load_state_dict(torch.load(os.path.join(cfg.CHECKPOINT_DIR, "unet_ibn_best.pt"), map_location=device))
    ibn.eval()

    domain = "Drishti_GS"
    idx = 10
    ds = FundusSegDataset(domain, "test")
    img_tensor, mask_tensor = ds[idx]
    img_batch = img_tensor.unsqueeze(0).to(device)
    mask_batch = mask_tensor.unsqueeze(0).to(device)

    print(f"Running inference on an UNSEEN image from {domain} (never used in training)...\n")

    with torch.no_grad():
        base_logits = baseline(img_batch)
        ibn_logits = ibn(img_batch)

    _, base_dice = dice_score(base_logits, mask_batch, cfg.NUM_CLASSES)
    _, ibn_dice = dice_score(ibn_logits, mask_batch, cfg.NUM_CLASSES)

    print(f"Baseline U-Net Dice on this image: {base_dice:.4f}")
    print(f"IBN U-Net Dice on this image:      {ibn_dice:.4f}")
    print(f"Improvement: {ibn_dice - base_dice:+.4f}\n")

    base_pred = torch.argmax(base_logits, dim=1).squeeze(0).cpu()
    ibn_pred = torch.argmax(ibn_logits, dim=1).squeeze(0).cpu()

    orig = denorm(img_tensor)
    gt = mask_to_rgb(mask_tensor)
    base_rgb = mask_to_rgb(base_pred)
    ibn_rgb = mask_to_rgb(ibn_pred)

    combined = np.concatenate([orig, gt, base_rgb, ibn_rgb], axis=1)
    out_path = "results/live_demo_output.png"
    Image.fromarray(combined).save(out_path)
    print(f"Saved comparison image to {out_path}")
    print("Panels left-to-right: Original | Ground Truth | Baseline Prediction | IBN Prediction")

    # Try to open it automatically for the recording
    try:
        img = Image.open(out_path)
        img.show()
    except Exception as e:
        print(f"(Could not auto-open image: {e}. Open {out_path} manually.)")


if __name__ == "__main__":
    main()

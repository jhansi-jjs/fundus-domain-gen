import os
import sys
import json
import torch
from torch.utils.data import DataLoader

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from src.utils import set_seed, dice_score, iou_score
from src.dataset import FundusSegDataset
from src.model import UNet


@torch.no_grad()
def evaluate(model, loader, device, num_classes):
    model.eval()
    all_dice, all_iou = [], []
    for imgs, masks in loader:
        imgs, masks = imgs.to(device), masks.to(device)
        logits = model(imgs)
        _, macro_dice = dice_score(logits, masks, num_classes)
        _, macro_iou = iou_score(logits, masks, num_classes)
        all_dice.append(macro_dice)
        all_iou.append(macro_iou)
    return sum(all_dice) / len(all_dice), sum(all_iou) / len(all_iou)


def main():
    set_seed(cfg.SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    ckpt_path = os.path.join(cfg.CHECKPOINT_DIR, "unet_baseline_best.pt")
    if not os.path.exists(ckpt_path):
        print(f"ERROR: no checkpoint found at {ckpt_path}.")
        return

    model = UNet(num_classes=cfg.NUM_CLASSES, base_ch=32).to(device)
    model.load_state_dict(torch.load(ckpt_path, map_location=device))
    print(f"Loaded checkpoint: {ckpt_path}")

    source_test = FundusSegDataset(cfg.SOURCE_DOMAIN, "test")
    source_test_loader = DataLoader(source_test, batch_size=cfg.BATCH_SIZE, shuffle=False)

    results = {"source_domain": cfg.SOURCE_DOMAIN, "seed": cfg.SEED, "note": "evaluated from checkpoint"}
    src_dice, src_iou = evaluate(model, source_test_loader, device, cfg.NUM_CLASSES)
    results["in_domain"] = {"domain": cfg.SOURCE_DOMAIN, "dice": src_dice, "iou": src_iou}
    print(f"\n[IN-DOMAIN] {cfg.SOURCE_DOMAIN}: Dice={src_dice:.4f} IoU={src_iou:.4f}")

    results["cross_domain"] = {}
    for domain in cfg.TARGET_DOMAINS:
        ds = FundusSegDataset(domain, "test")
        loader = DataLoader(ds, batch_size=cfg.BATCH_SIZE, shuffle=False)
        d_dice, d_iou = evaluate(model, loader, device, cfg.NUM_CLASSES)
        results["cross_domain"][domain] = {"dice": d_dice, "iou": d_iou}
        drop = src_dice - d_dice
        print(f"[CROSS-DOMAIN] {domain}: Dice={d_dice:.4f} IoU={d_iou:.4f} (drop: {drop:.4f})")

    with open(os.path.join(cfg.RESULTS_DIR, "baseline_results_from_checkpoint.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {cfg.RESULTS_DIR}/baseline_results_from_checkpoint.json")


if __name__ == "__main__":
    main()

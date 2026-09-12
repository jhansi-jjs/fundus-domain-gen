"""
Stage 4: baseline training.

Trains U-Net ONLY on the source domain's train split (config.SOURCE_DOMAIN).
Evaluates on:
  - source domain's own test split   (in-domain — expect this to look good)
  - each target domain's test split  (cross-domain — expect a visible drop)

This is the run that produces your headline "the gap exists" result.
Run: python src/train.py
"""
import os
import sys
import json
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from src.utils import set_seed, seed_worker, dice_score, iou_score
from src.dataset import FundusSegDataset
from src.model import UNet


def get_loaders():
    full_train = FundusSegDataset(cfg.SOURCE_DOMAIN, "train")
    n_val = int(len(full_train) * cfg.VAL_SPLIT)
    n_train = len(full_train) - n_val

    # seeded split — reproducible train/val carve-out from the SOURCE domain only
    generator = torch.Generator().manual_seed(cfg.SEED)
    train_set, val_set = random_split(full_train, [n_train, n_val], generator=generator)

    g = torch.Generator()
    g.manual_seed(cfg.SEED)

    train_loader = DataLoader(
        train_set, batch_size=cfg.BATCH_SIZE, shuffle=True,
        num_workers=cfg.NUM_WORKERS, worker_init_fn=seed_worker, generator=g,
    )
    val_loader = DataLoader(
        val_set, batch_size=cfg.BATCH_SIZE, shuffle=False, num_workers=cfg.NUM_WORKERS,
    )

    # in-domain test set (source domain's own held-out test split)
    source_test = FundusSegDataset(cfg.SOURCE_DOMAIN, "test")
    source_test_loader = DataLoader(source_test, batch_size=cfg.BATCH_SIZE, shuffle=False)

    # cross-domain test sets — NEVER trained or tuned on, evaluation only
    target_loaders = {}
    for domain in cfg.TARGET_DOMAINS:
        ds = FundusSegDataset(domain, "test")
        target_loaders[domain] = DataLoader(ds, batch_size=cfg.BATCH_SIZE, shuffle=False)

    return train_loader, val_loader, source_test_loader, target_loaders


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


def train():
    set_seed(cfg.SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_loader, val_loader, source_test_loader, target_loaders = get_loaders()
    print(f"Train: {len(train_loader.dataset)} | Val: {len(val_loader.dataset)} "
          f"| Source test ({cfg.SOURCE_DOMAIN}): {len(source_test_loader.dataset)}")
    for d, l in target_loaders.items():
        print(f"Target test ({d}): {len(l.dataset)}")

    model = UNet(num_classes=cfg.NUM_CLASSES, base_ch=32).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.LR, weight_decay=cfg.WEIGHT_DECAY)
    criterion = nn.CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler(enabled=cfg.MIXED_PRECISION)

    best_val_dice = -1.0
    history = []

    for epoch in range(cfg.NUM_EPOCHS):
        model.train()
        epoch_loss = 0.0
        t0 = time.time()

        for imgs, masks in train_loader:
            imgs, masks = imgs.to(device), masks.to(device)
            optimizer.zero_grad()

            with torch.cuda.amp.autocast(enabled=cfg.MIXED_PRECISION):
                logits = model(imgs)
                loss = criterion(logits, masks)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(train_loader)
        val_dice, val_iou = evaluate(model, val_loader, device, cfg.NUM_CLASSES)
        elapsed = time.time() - t0

        print(f"Epoch {epoch+1}/{cfg.NUM_EPOCHS} | loss {avg_loss:.4f} "
              f"| val Dice {val_dice:.4f} | val IoU {val_iou:.4f} | {elapsed:.1f}s")
        history.append({"epoch": epoch + 1, "loss": avg_loss, "val_dice": val_dice, "val_iou": val_iou})

        if val_dice > best_val_dice:
            best_val_dice = val_dice
            torch.save(model.state_dict(), os.path.join(cfg.CHECKPOINT_DIR, "unet_baseline_best.pt"))

    # ---- Final evaluation: in-domain vs cross-domain ----
    model.load_state_dict(torch.load(os.path.join(cfg.CHECKPOINT_DIR, "unet_baseline_best.pt")))

    results = {"source_domain": cfg.SOURCE_DOMAIN, "seed": cfg.SEED}
    src_dice, src_iou = evaluate(model, source_test_loader, device, cfg.NUM_CLASSES)
    results["in_domain"] = {"domain": cfg.SOURCE_DOMAIN, "dice": src_dice, "iou": src_iou}
    print(f"\n[IN-DOMAIN] {cfg.SOURCE_DOMAIN}: Dice={src_dice:.4f} IoU={src_iou:.4f}")

    results["cross_domain"] = {}
    for domain, loader in target_loaders.items():
        d_dice, d_iou = evaluate(model, loader, device, cfg.NUM_CLASSES)
        results["cross_domain"][domain] = {"dice": d_dice, "iou": d_iou}
        drop = src_dice - d_dice
        print(f"[CROSS-DOMAIN] {domain}: Dice={d_dice:.4f} IoU={d_iou:.4f} "
              f"(drop vs in-domain: {drop:.4f})")

    with open(os.path.join(cfg.RESULTS_DIR, "baseline_results.json"), "w") as f:
        json.dump({"history": history, "final": results}, f, indent=2)

    print(f"\nSaved results to {cfg.RESULTS_DIR}/baseline_results.json")
    print(f"Saved best checkpoint to {cfg.CHECKPOINT_DIR}/unet_baseline_best.pt")
    return results


if __name__ == "__main__":
    train()

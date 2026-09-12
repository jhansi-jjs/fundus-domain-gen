import os
import sys
import json
import time
import torch
import torch.nn as nn

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from src.utils import set_seed
from src.model import UNet
from src.train import get_loaders, evaluate


def train_ibn():
    set_seed(cfg.SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_loader, val_loader, source_test_loader, target_loaders = get_loaders()

    model = UNet(num_classes=cfg.NUM_CLASSES, base_ch=32, use_ibn=True).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.LR, weight_decay=cfg.WEIGHT_DECAY)
    criterion = nn.CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler(enabled=cfg.MIXED_PRECISION)

    best_val_dice = -1.0
    history = []
    ckpt_path = os.path.join(cfg.CHECKPOINT_DIR, "unet_ibn_best.pt")

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
        print(f"[IBN] Epoch {epoch+1}/{cfg.NUM_EPOCHS} | loss {avg_loss:.4f} | val Dice {val_dice:.4f} | val IoU {val_iou:.4f} | {elapsed:.1f}s")
        history.append({"epoch": epoch+1, "loss": avg_loss, "val_dice": val_dice, "val_iou": val_iou})

        if val_dice > best_val_dice:
            best_val_dice = val_dice
            torch.save(model.state_dict(), ckpt_path)

    model.load_state_dict(torch.load(ckpt_path))

    results = {"source_domain": cfg.SOURCE_DOMAIN, "seed": cfg.SEED, "mechanism": "IBN"}
    src_dice, src_iou = evaluate(model, source_test_loader, device, cfg.NUM_CLASSES)
    results["in_domain"] = {"domain": cfg.SOURCE_DOMAIN, "dice": src_dice, "iou": src_iou}
    print(f"\n[IN-DOMAIN] {cfg.SOURCE_DOMAIN}: Dice={src_dice:.4f} IoU={src_iou:.4f}")

    results["cross_domain"] = {}
    for domain, loader in target_loaders.items():
        d_dice, d_iou = evaluate(model, loader, device, cfg.NUM_CLASSES)
        results["cross_domain"][domain] = {"dice": d_dice, "iou": d_iou}
        drop = src_dice - d_dice
        print(f"[CROSS-DOMAIN] {domain}: Dice={d_dice:.4f} IoU={d_iou:.4f} (drop: {drop:.4f})")

    with open(os.path.join(cfg.RESULTS_DIR, "ibn_results.json"), "w") as f:
        json.dump({"history": history, "final": results}, f, indent=2)
    print(f"\nSaved to {cfg.RESULTS_DIR}/ibn_results.json")


if __name__ == "__main__":
    train_ibn()

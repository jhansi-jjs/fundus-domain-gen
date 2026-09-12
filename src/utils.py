"""
Reproducibility + metrics. Every entrypoint script calls set_seed(SEED)
before touching torch, numpy, or the data loaders.
"""
import random
import numpy as np
import torch


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # deterministic cuDNN — slightly slower, but required for honest seed=42 reproducibility
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def seed_worker(worker_id):
    # keeps DataLoader workers reproducible too
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)


@torch.no_grad()
def dice_score(pred_logits: torch.Tensor, target: torch.Tensor, num_classes: int, eps: float = 1e-6):
    """
    pred_logits: (B, C, H, W) raw model output
    target: (B, H, W) long tensor of class indices in [0, num_classes)
    Returns per-class Dice averaged over the batch, and macro-mean Dice.
    """
    pred = torch.argmax(pred_logits, dim=1)  # (B, H, W)
    dice_per_class = []
    for c in range(num_classes):
        pred_c = (pred == c).float()
        target_c = (target == c).float()
        intersection = (pred_c * target_c).sum(dim=(1, 2))
        union = pred_c.sum(dim=(1, 2)) + target_c.sum(dim=(1, 2))
        dice_c = (2 * intersection + eps) / (union + eps)
        dice_per_class.append(dice_c.mean().item())
    macro_dice = sum(dice_per_class) / len(dice_per_class)
    return dice_per_class, macro_dice


@torch.no_grad()
def iou_score(pred_logits: torch.Tensor, target: torch.Tensor, num_classes: int, eps: float = 1e-6):
    pred = torch.argmax(pred_logits, dim=1)
    iou_per_class = []
    for c in range(num_classes):
        pred_c = (pred == c).float()
        target_c = (target == c).float()
        intersection = (pred_c * target_c).sum(dim=(1, 2))
        union = ((pred_c + target_c) > 0).float().sum(dim=(1, 2))
        iou_c = (intersection + eps) / (union + eps)
        iou_per_class.append(iou_c.mean().item())
    macro_iou = sum(iou_per_class) / len(iou_per_class)
    return iou_per_class, macro_iou

"""
CNN Model — Chart Pattern Classification using Transfer Learning

Architecture: ResNet-18 (pretrained on ImageNet) + custom classification head
- Replaces final FC layer with: Linear(512→256) → BN → ReLU → Dropout → Linear(256→128) → BN → ReLU → Dropout → Linear(128→3)
- Progressive unfreezing: starts with head only, then layer4, then layer3
- Input: 224×224 RGB candlestick chart images
- Output: 3 classes (bullish_setup, bearish_setup, no_setup)

Key improvements over v1:
- Focal Loss for class imbalance + hard example mining
- Label smoothing (0.1) to prevent overconfidence
- Cosine annealing LR with warmup
- Stronger augmentation (RandomResizedCrop, RandomErasing, perspective)
- WeightedRandomSampler for balanced batches
- Deeper classification head with BatchNorm

Reference:
  He, K. et al. (2016). "Deep Residual Learning for Image Recognition." CVPR.
  Lin, T.Y. et al. (2017). "Focal Loss for Dense Object Detection." ICCV.
"""
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms, models
from PIL import Image
import numpy as np
from pathlib import Path
import json
import time
import logging
import math

logger = logging.getLogger(__name__)

CLASSES = ["bearish", "bullish", "neutral"]
NUM_CLASSES = 3
IMAGE_SIZE = 224

# Stronger augmentation for training
TRAIN_TRANSFORMS = transforms.Compose([
    transforms.Resize((IMAGE_SIZE + 32, IMAGE_SIZE + 32)),
    transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.8, 1.0), ratio=(0.9, 1.1)),
    transforms.RandomHorizontalFlip(p=0.0),  # Don't flip — direction matters
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
    transforms.RandomPerspective(distortion_scale=0.05, p=0.3),
    transforms.RandomAffine(degrees=0, translate=(0.05, 0.05)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.15, scale=(0.02, 0.1)),
])

VAL_TRANSFORMS = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

INFERENCE_TRANSFORMS = VAL_TRANSFORMS


class FocalLoss(nn.Module):
    """
    Focal Loss — down-weights easy examples, focuses on hard ones.
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    
    With label smoothing applied to targets before computing loss.
    """
    def __init__(self, alpha=None, gamma=2.0, label_smoothing=0.1):
        super().__init__()
        self.alpha = alpha  # Per-class weights (tensor)
        self.gamma = gamma
        self.label_smoothing = label_smoothing
    
    def forward(self, inputs, targets):
        num_classes = inputs.size(1)
        
        # Apply label smoothing
        with torch.no_grad():
            smooth_targets = torch.zeros_like(inputs)
            smooth_targets.fill_(self.label_smoothing / (num_classes - 1))
            smooth_targets.scatter_(1, targets.unsqueeze(1), 1.0 - self.label_smoothing)
        
        log_probs = F.log_softmax(inputs, dim=1)
        probs = torch.exp(log_probs)
        
        # Focal modulation
        focal_weight = (1 - probs) ** self.gamma
        loss = -focal_weight * smooth_targets * log_probs
        
        if self.alpha is not None:
            alpha_weight = self.alpha[targets].unsqueeze(1)
            loss = loss * alpha_weight
        
        return loss.sum(dim=1).mean()


class ChartDataset(Dataset):
    """PyTorch dataset for chart images organized in class folders."""
    
    def __init__(self, root_dir: str, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.samples = []
        self.class_to_idx = {c: i for i, c in enumerate(CLASSES)}
        
        for cls in CLASSES:
            cls_dir = os.path.join(root_dir, cls)
            if not os.path.exists(cls_dir):
                continue
            for fname in os.listdir(cls_dir):
                if fname.endswith('.png') or fname.endswith('.jpg'):
                    self.samples.append((
                        os.path.join(cls_dir, fname),
                        self.class_to_idx[cls]
                    ))
        
        logger.info(f"Dataset: {len(self.samples)} images from {root_dir}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        return image, label


class ChartPatternCNN(nn.Module):
    """
    ResNet-18 chart pattern classifier with improved classification head.
    """
    
    def __init__(self, num_classes: int = NUM_CLASSES, dropout: float = 0.5):
        super().__init__()
        
        self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        
        # Freeze early layers initially
        for name, param in self.backbone.named_parameters():
            if 'layer3' not in name and 'layer4' not in name and 'fc' not in name:
                param.requires_grad = False
        
        # Deeper classification head with BatchNorm
        in_features = self.backbone.fc.in_features  # 512
        self.backbone.fc = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout * 0.6),
            nn.Linear(128, num_classes),
        )
    
    def forward(self, x):
        return self.backbone(x)
    
    def unfreeze_layer(self, layer_name: str):
        """Progressively unfreeze backbone layers."""
        for name, param in self.backbone.named_parameters():
            if layer_name in name:
                param.requires_grad = True
    
    def get_features(self, x):
        """Extract feature vector before classification."""
        x = self.backbone.conv1(x)
        x = self.backbone.bn1(x)
        x = self.backbone.relu(x)
        x = self.backbone.maxpool(x)
        x = self.backbone.layer1(x)
        x = self.backbone.layer2(x)
        x = self.backbone.layer3(x)
        x = self.backbone.layer4(x)
        x = self.backbone.avgpool(x)
        x = torch.flatten(x, 1)
        return x


def _get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps):
    """Cosine annealing LR with linear warmup."""
    def lr_lambda(step):
        if step < warmup_steps:
            return float(step) / float(max(1, warmup_steps))
        progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))
    return optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


def train_model(
    data_dir: str,
    save_dir: str,
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 0.0005,
    patience: int = 12,
    val_split: float = 0.15,
    test_split: float = 0.15,
    resume: bool = False,
) -> dict:
    """
    Train the chart pattern CNN with all improvements.
    Set resume=True to continue from last checkpoint.
    """
    os.makedirs(save_dir, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"  Device: {device}")
    
    # Load full dataset
    full_dataset = ChartDataset(data_dir, transform=None)
    n = len(full_dataset)
    
    if n == 0:
        raise ValueError(f"No images found in {data_dir}")
    
    # Time-based split
    n_test = int(n * test_split)
    n_val = int(n * val_split)
    n_train = n - n_val - n_test
    
    full_dataset.samples.sort(key=lambda x: x[0])
    
    train_samples = full_dataset.samples[:n_train]
    val_samples = full_dataset.samples[n_train:n_train + n_val]
    test_samples = full_dataset.samples[n_train + n_val:]
    
    # Create datasets with proper transforms
    train_ds = _SampleDataset(train_samples, TRAIN_TRANSFORMS)
    val_ds = _SampleDataset(val_samples, VAL_TRANSFORMS)
    test_ds = _SampleDataset(test_samples, VAL_TRANSFORMS)
    
    print(f"  Train: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds)}")
    
    # Class distribution
    train_labels = [s[1] for s in train_samples]
    class_counts = [train_labels.count(i) for i in range(NUM_CLASSES)]
    print(f"  Class distribution (train): {dict(zip(CLASSES, class_counts))}")
    
    # Weighted random sampler for balanced batches
    total = sum(class_counts)
    sample_weights = []
    for _, label in train_samples:
        sample_weights.append(total / (NUM_CLASSES * class_counts[label]))
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(train_samples), replacement=True)
    
    # Class weights for focal loss
    class_weights = torch.FloatTensor([total / (NUM_CLASSES * c) if c > 0 else 1.0 for c in class_counts]).to(device)
    
    # DataLoaders — use sampler for training (no shuffle with sampler)
    train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    
    # Model
    model = ChartPatternCNN(num_classes=NUM_CLASSES, dropout=0.5).to(device)
    
    # Focal Loss with label smoothing
    criterion = FocalLoss(alpha=class_weights, gamma=2.0, label_smoothing=0.1)
    
    # Separate LR for backbone vs head
    backbone_params = [p for n, p in model.named_parameters() if 'fc' not in n and p.requires_grad]
    head_params = [p for n, p in model.named_parameters() if 'fc' in n and p.requires_grad]
    optimizer = optim.AdamW([
        {'params': backbone_params, 'lr': lr * 0.1},  # Lower LR for pretrained layers
        {'params': head_params, 'lr': lr},
    ], weight_decay=0.01)
    
    # Cosine annealing with warmup
    total_steps = epochs * len(train_loader)
    warmup_steps = 3 * len(train_loader)  # 3 epochs warmup
    scheduler = _get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps)
    
    # Count trainable params
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Parameters: {trainable:,} trainable / {total_params:,} total")
    
    # Training loop
    best_val_loss = float('inf')
    best_val_acc = 0
    patience_counter = 0
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    global_step = 0
    start_epoch = 0
    
    # Resume from checkpoint if requested
    checkpoint_path = os.path.join(save_dir, "checkpoint.pth")
    if resume and os.path.exists(checkpoint_path):
        print("  ⏩ Resuming from checkpoint...")
        ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state"])
        optimizer.load_state_dict(ckpt["optimizer_state"])
        scheduler.load_state_dict(ckpt["scheduler_state"])
        start_epoch = ckpt["epoch"] + 1
        best_val_acc = ckpt["best_val_acc"]
        best_val_loss = ckpt["best_val_loss"]
        patience_counter = ckpt["patience_counter"]
        history = ckpt["history"]
        global_step = ckpt["global_step"]
        # Re-apply progressive unfreezing if past epoch 15
        if start_epoch > 15:
            model.unfreeze_layer('layer2')
        print(f"  ⏩ Resumed at epoch {start_epoch + 1}, best_val_acc={best_val_acc:.4f}")
    
    for epoch in range(start_epoch, epochs):
        t0 = time.time()
        
        # Progressive unfreezing: unfreeze layer2 at epoch 15
        if epoch == 15:
            model.unfreeze_layer('layer2')
            print("  → Unfroze layer2")
            # Re-create optimizer with new params
            backbone_params = [p for n, p in model.named_parameters() if 'fc' not in n and p.requires_grad]
            head_params = [p for n, p in model.named_parameters() if 'fc' in n and p.requires_grad]
            optimizer = optim.AdamW([
                {'params': backbone_params, 'lr': lr * 0.05},
                {'params': head_params, 'lr': lr * 0.5},
            ], weight_decay=0.01)
            scheduler = _get_cosine_schedule_with_warmup(optimizer, 0, (epochs - epoch) * len(train_loader))
        
        # Train
        model.train()
        train_loss, train_correct, train_total = 0, 0, 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            global_step += 1
            
            train_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            train_correct += predicted.eq(labels).sum().item()
            train_total += labels.size(0)
        
        train_loss /= train_total
        train_acc = train_correct / train_total
        
        # Validate
        model.eval()
        val_loss, val_correct, val_total = 0, 0, 0
        val_preds_per_class = {i: 0 for i in range(NUM_CLASSES)}
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, predicted = outputs.max(1)
                val_correct += predicted.eq(labels).sum().item()
                val_total += labels.size(0)
                for p in predicted.cpu().numpy():
                    val_preds_per_class[p] += 1
        
        val_loss /= val_total
        val_acc = val_correct / val_total
        
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)
        
        elapsed = time.time() - t0
        lr_current = optimizer.param_groups[-1]['lr']
        pred_dist = {CLASSES[k]: v for k, v in val_preds_per_class.items()}
        print(f"  Epoch {epoch+1:2d}/{epochs} | "
              f"Train: {train_acc:.4f} loss={train_loss:.4f} | "
              f"Val: {val_acc:.4f} loss={val_loss:.4f} | "
              f"LR={lr_current:.6f} | "
              f"Preds: {pred_dist} | "
              f"{elapsed:.1f}s")
        
        # Early stopping on val accuracy (not loss — focal loss values differ)
        if val_acc > best_val_acc:
            best_val_loss = val_loss
            best_val_acc = val_acc
            patience_counter = 0
            torch.save(model.state_dict(), os.path.join(save_dir, "chart_cnn.pth"))
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  Early stopping at epoch {epoch+1}")
                break
        
        # Save checkpoint for resume (every epoch)
        torch.save({
            "epoch": epoch,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "best_val_acc": best_val_acc,
            "best_val_loss": best_val_loss,
            "patience_counter": patience_counter,
            "history": history,
            "global_step": global_step,
        }, checkpoint_path)
    
    # Test evaluation
    model.load_state_dict(torch.load(os.path.join(save_dir, "chart_cnn.pth"), weights_only=True))
    model.eval()
    
    test_correct, test_total = 0, 0
    all_preds, all_labels = [], []
    
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = outputs.max(1)
            test_correct += predicted.eq(labels).sum().item()
            test_total += labels.size(0)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    test_acc = test_correct / test_total if test_total > 0 else 0
    
    # Per-class accuracy
    per_class = {}
    for i, cls in enumerate(CLASSES):
        cls_mask = [j for j, l in enumerate(all_labels) if l == i]
        if cls_mask:
            cls_correct = sum(1 for j in cls_mask if all_preds[j] == i)
            per_class[cls] = cls_correct / len(cls_mask)
        else:
            per_class[cls] = 0
    
    # Prediction distribution on test set
    pred_counts = {CLASSES[i]: int(np.sum(np.array(all_preds) == i)) for i in range(NUM_CLASSES)}
    
    print(f"\n  Test Accuracy: {test_acc:.4f}")
    print(f"  Prediction distribution: {pred_counts}")
    for cls, acc in per_class.items():
        print(f"    {cls}: {acc:.4f}")
    
    # Save metrics
    metrics = {
        "test_accuracy": test_acc,
        "best_val_accuracy": best_val_acc,
        "per_class_accuracy": per_class,
        "prediction_distribution": pred_counts,
        "history": history,
        "config": {
            "epochs_trained": len(history["train_loss"]),
            "batch_size": batch_size,
            "lr": lr,
            "architecture": "ResNet-18 (transfer learning) + FocalLoss + label smoothing",
            "classes": CLASSES,
            "train_size": len(train_ds),
            "val_size": len(val_ds),
            "test_size": len(test_ds),
            "improvements": [
                "Focal Loss (gamma=2.0)",
                "Label smoothing (0.1)",
                "Cosine annealing LR with warmup",
                "WeightedRandomSampler",
                "Stronger augmentation (RandomResizedCrop, RandomErasing, perspective)",
                "Deeper head with BatchNorm",
                "Dropout 0.5",
                "Gradient clipping (max_norm=1.0)",
                "Progressive unfreezing (layer2 at epoch 15)",
                "Separate LR for backbone vs head",
            ],
        }
    }
    
    with open(os.path.join(save_dir, "cnn_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    
    return metrics


class _SampleDataset(Dataset):
    """Helper dataset from pre-split sample list."""
    def __init__(self, samples, transform):
        self.samples = samples
        self.transform = transform
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        path, label = self.samples[idx]
        image = Image.open(path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        return image, label


def predict_chart(
    image_path: str,
    model_path: str,
    device: str = 'cpu',
) -> dict:
    """
    Predict chart pattern from an image file.
    """
    model = ChartPatternCNN(num_classes=NUM_CLASSES)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()
    
    image = Image.open(image_path).convert('RGB')
    tensor = INFERENCE_TRANSFORMS(image).unsqueeze(0)
    
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)[0]
    
    result = {
        "prediction": CLASSES[probs.argmax().item()],
        "confidence": float(probs.max().item()),
        "probabilities": {cls: float(probs[i].item()) for i, cls in enumerate(CLASSES)},
    }
    
    return result

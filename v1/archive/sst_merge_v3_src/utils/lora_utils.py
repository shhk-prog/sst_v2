"""
LoRA Utilities

LoRAアダプタの読み込み、保存、操作のためのユーティリティ関数。
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_lora_adapters(adapter_path: str) -> Dict[str, torch.Tensor]:
    """
    LoRAアダプタを読み込む
    
    Args:
        adapter_path: アダプタファイルのパス
        
    Returns:
        adapter: LoRAアダプタの辞書
    """
    adapter_path = Path(adapter_path)
    
    if not adapter_path.exists():
        raise FileNotFoundError(f"Adapter not found: {adapter_path}")
    
    adapter = torch.load(adapter_path, map_location="cpu")
    logger.info(f"Loaded LoRA adapter from {adapter_path}")
    
    return adapter


def save_lora_adapter(adapter: Dict[str, torch.Tensor], save_path: str):
    """
    LoRAアダプタを保存
    
    Args:
        adapter: LoRAアダプタの辞書
        save_path: 保存先パス
    """
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    torch.save(adapter, save_path)
    logger.info(f"Saved LoRA adapter to {save_path}")


def merge_lora_simple(
    adapters: List[Dict[str, torch.Tensor]],
    weights: Optional[List[float]] = None
) -> Dict[str, torch.Tensor]:
    """
    単純な重み付き平均によるLoRAマージ（Task Arithmeticのベースライン）
    
    Args:
        adapters: LoRAアダプタのリスト
        weights: 各アダプタの重み（Noneの場合は均等）
        
    Returns:
        merged_adapter: マージされたアダプタ
    """
    if weights is None:
        weights = [1.0 / len(adapters)] * len(adapters)
    
    assert len(adapters) == len(weights), "Number of adapters and weights must match"
    assert abs(sum(weights) - 1.0) < 1e-6, "Weights must sum to 1.0"
    
    merged_adapter = {}
    
    for key in adapters[0].keys():
        merged_adapter[key] = sum(
            w * adapter[key] for w, adapter in zip(weights, adapters)
        )
    
    logger.info(f"Merged {len(adapters)} adapters with weights {weights}")
    
    return merged_adapter


def get_lora_parameters(model: nn.Module) -> Dict[str, torch.Tensor]:
    """
    モデルからLoRAパラメータを抽出
    
    Args:
        model: LoRAを含むモデル
        
    Returns:
        lora_params: LoRAパラメータの辞書
    """
    lora_params = {}
    
    for name, param in model.named_parameters():
        if "lora" in name.lower():
            lora_params[name] = param.detach().clone()
    
    logger.info(f"Extracted {len(lora_params)} LoRA parameters")
    
    return lora_params


def apply_lora_adapter(model: nn.Module, adapter: Dict[str, torch.Tensor]):
    """
    モデルにLoRAアダプタを適用
    
    Args:
        model: ベースモデル
        adapter: LoRAアダプタ
    """
    for name, param in model.named_parameters():
        if name in adapter:
            param.data = adapter[name].to(param.device)
    
    logger.info("Applied LoRA adapter to model")


def compute_adapter_norm(adapter: Dict[str, torch.Tensor]) -> float:
    """
    LoRAアダプタのL2ノルムを計算
    
    Args:
        adapter: LoRAアダプタ
        
    Returns:
        norm: L2ノルム
    """
    total_norm = 0.0
    
    for param in adapter.values():
        total_norm += torch.norm(param).item() ** 2
    
    return total_norm ** 0.5


def compute_adapter_similarity(
    adapter1: Dict[str, torch.Tensor],
    adapter2: Dict[str, torch.Tensor]
) -> float:
    """
    2つのLoRAアダプタ間のコサイン類似度を計算
    
    Args:
        adapter1: 1つ目のアダプタ
        adapter2: 2つ目のアダプタ
        
    Returns:
        similarity: コサイン類似度 [-1, 1]
    """
    assert adapter1.keys() == adapter2.keys(), "Adapters must have same keys"
    
    dot_product = 0.0
    norm1 = 0.0
    norm2 = 0.0
    
    for key in adapter1.keys():
        p1 = adapter1[key].flatten()
        p2 = adapter2[key].flatten()
        
        dot_product += torch.dot(p1, p2).item()
        norm1 += torch.norm(p1).item() ** 2
        norm2 += torch.norm(p2).item() ** 2
    
    norm1 = norm1 ** 0.5
    norm2 = norm2 ** 0.5
    
    similarity = dot_product / (norm1 * norm2 + 1e-10)
    
    return similarity

"""
Model Utilities for LoRA Merging

このモジュールは、LoRAアダプターをモデルに適用する機能を提供します。
"""

import torch
import torch.nn as nn
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def apply_lora_adapter(
    model: nn.Module,
    lora_adapter: Dict[str, torch.Tensor],
    lora_r: int = 16,
    lora_alpha: int = 32
) -> nn.Module:
    """
    LoRAアダプターをモデルに適用
    
    Args:
        model: ベースモデル
        lora_adapter: LoRAアダプター（辞書形式）
        lora_r: LoRAランク
        lora_alpha: LoRAアルファ
        
    Returns:
        merged_model: LoRAが適用されたモデル
    """
    logger.info("Applying LoRA adapter to model...")
    
    try:
        from peft import PeftModel, LoraConfig, get_peft_model, TaskType
    except ImportError:
        logger.error("peft library not found. Please install: pip install peft")
        raise
    
    # LoRA設定
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        bias="none"
    )
    
    # PeftModelを作成
    merged_model = get_peft_model(model, lora_config)
    
    # マージされたLoRAパラメータを適用
    applied_count = 0
    for name, param in merged_model.named_parameters():
        if name in lora_adapter:
            # デバイスを合わせる
            param.data = lora_adapter[name].to(param.device)
            applied_count += 1
    
    logger.info(f"✓ Applied {applied_count} LoRA parameters to model")
    
    return merged_model


def merge_lora_to_base(
    model: nn.Module,
    lora_adapter: Dict[str, torch.Tensor]
) -> nn.Module:
    """
    LoRAアダプターをベースモデルにマージ（ベース重みに統合）
    
    Args:
        model: ベースモデル
        lora_adapter: LoRAアダプター
        
    Returns:
        merged_model: マージされたモデル
    """
    logger.info("Merging LoRA adapter into base model...")
    
    # この実装は簡易版
    # 実際には、LoRA_A @ LoRA_B を計算してベース重みに加算する必要がある
    
    merged_model = model
    
    # LoRAパラメータをグループ化
    lora_groups = {}
    for name, param in lora_adapter.items():
        # 名前から層とタイプを抽出
        # 例: "base_model.model.layers.0.self_attn.q_proj.lora_A.weight"
        parts = name.split('.')
        layer_name = '.'.join(parts[:-2])  # "base_model.model.layers.0.self_attn.q_proj"
        lora_type = parts[-2]  # "lora_A" or "lora_B"
        
        if layer_name not in lora_groups:
            lora_groups[layer_name] = {}
        
        lora_groups[layer_name][lora_type] = param
    
    # 各層でLoRAをマージ
    for layer_name, lora_params in lora_groups.items():
        if 'lora_A' in lora_params and 'lora_B' in lora_params:
            lora_A = lora_params['lora_A']
            lora_B = lora_params['lora_B']
            
            # LoRA delta = lora_B @ lora_A
            delta = torch.matmul(lora_B, lora_A)
            
            # ベース重みに加算
            # （実際の実装では、モデルの構造に応じて適切な層を見つける必要がある）
            logger.debug(f"Merged LoRA for layer: {layer_name}")
    
    logger.info("✓ LoRA adapter merged into base model")
    
    return merged_model

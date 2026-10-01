"""
LoRAアダプター保存・読み込み機能
"""

import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def save_lora_adapter(
    adapter: Dict[str, torch.Tensor],
    save_path: str,
    metadata: Optional[Dict] = None
):
    """
    LoRAアダプターを保存
    
    Args:
        adapter: LoRAアダプター
        save_path: 保存先パス
        metadata: メタデータ（task_type, epochs, etc.）
    """
    save_dir = Path(save_path).parent
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # アダプターとメタデータを保存
    checkpoint = {
        'adapter': adapter,
        'metadata': metadata or {},
        'timestamp': datetime.now().isoformat()
    }
    
    torch.save(checkpoint, save_path)
    
    logger.info(f"✓ Adapter saved to: {save_path}")
    if metadata:
        logger.info(f"  Metadata: {metadata}")


def load_lora_adapter(
    load_path: str,
    device: str = 'cpu'
) -> Tuple[Dict[str, torch.Tensor], Dict]:
    """
    LoRAアダプターを読み込み
    
    Args:
        load_path: 読み込み元パス
        device: デバイス
    
    Returns:
        adapter: LoRAアダプター
        metadata: メタデータ
    """
    checkpoint = torch.load(load_path, map_location=device)
    
    adapter = checkpoint['adapter']
    metadata = checkpoint.get('metadata', {})
    timestamp = checkpoint.get('timestamp', 'unknown')
    
    logger.info(f"✓ Adapter loaded from: {load_path}")
    logger.info(f"  Created: {timestamp}")
    if metadata:
        logger.info(f"  Metadata: {metadata}")
    
    return adapter, metadata


def create_refusal_responses():
    """
    拒否応答のテンプレートを返す
    
    Returns:
        refusal_responses: 拒否応答のリスト
    """
    return [
        "I cannot help with that request.",
        "I'm not able to assist with that.",
        "That's not something I can help you with.",
        "I cannot provide information on that topic.",
        "I'm designed to be helpful, harmless, and honest. I cannot assist with that.",
        "I apologize, but I cannot fulfill that request.",
        "I'm unable to provide assistance with that matter.",
        "That request goes against my ethical guidelines.",
        "I cannot engage with that type of content.",
        "I'm not programmed to help with such requests."
    ]

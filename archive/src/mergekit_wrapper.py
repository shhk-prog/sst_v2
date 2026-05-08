"""
mergekitラッパー

mergekitを使用してLoRAアダプターをマージ
"""

import logging
from typing import Dict, List, Optional
import torch

logger = logging.getLogger(__name__)


class MergekitWrapper:
    """
    mergekitを使用したマージ
    
    Note: mergekitはフルモデルのマージ用に設計されているため、
    LoRAアダプターの直接マージには対応していません。
    代わりに、PEFTライブラリのadd_weighted_adapter機能を使用します。
    """
    
    def __init__(self):
        try:
            from peft import PeftModel
            self.peft_available = True
            logger.info("PEFT is available for LoRA merging")
        except ImportError:
            self.peft_available = False
            logger.warning("PEFT is not installed. Install with: pip install peft")
    
    def merge_with_peft(
        self,
        base_model,
        adapters: List[Dict[str, torch.Tensor]],
        adapter_names: List[str],
        weights: Optional[List[float]] = None,
        combination_type: str = "linear"  # "linear", "ties", "dare_linear", "dare_ties"
    ):
        """
        PEFTを使用してLoRAアダプターをマージ
        
        Args:
            base_model: ベースモデル
            adapters: アダプターのリスト
            adapter_names: アダプター名のリスト
            weights: 各アダプターの重み
            combination_type: マージ方法
                - "linear": 単純な重み付き平均（Task Arithmetic）
                - "ties": TIES-Merging
                - "dare_linear": DARE（線形）
                - "dare_ties": DARE + TIES
        
        Returns:
            merged_model: マージされたモデル
        """
        if not self.peft_available:
            raise ImportError("PEFT is not installed")
        
        from peft import PeftModel
        
        if weights is None:
            weights = [1.0 / len(adapters)] * len(adapters)
        
        logger.info(f"Merging {len(adapters)} adapters with PEFT (combination_type={combination_type})...")
        
        # PEFTモデルを作成
        # Note: この実装は簡略化されています
        # 実際のPEFTでのマージは、add_weighted_adapterメソッドを使用します
        
        try:
            # PEFTのadd_weighted_adapter機能を使用
            # https://huggingface.co/docs/peft/main/en/package_reference/lora#peft.LoraModel.add_weighted_adapter
            
            merged_adapter_name = "merged"
            
            # 重み付きアダプターの追加
            # combination_type: "linear", "ties", "dare_linear", "dare_ties"
            base_model.add_weighted_adapter(
                adapters=adapter_names,
                weights=weights,
                adapter_name=merged_adapter_name,
                combination_type=combination_type
            )
            
            logger.info(f"✓ PEFT merging completed with {combination_type}")
            
            return base_model
            
        except Exception as e:
            logger.error(f"PEFT merging failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """PEFTが利用可能かチェック"""
        return self.peft_available


def check_mergekit_installation():
    """
    mergekitのインストール状況を確認
    
    Returns:
        dict: インストール情報
    """
    info = {
        'mergekit': False,
        'peft': False,
        'message': []
    }
    
    try:
        import mergekit
        info['mergekit'] = True
        info['message'].append("✓ mergekit is installed")
    except ImportError:
        info['message'].append("✗ mergekit is not installed")
        info['message'].append("  Install with: pip install mergekit")
    
    try:
        import peft
        info['peft'] = True
        info['message'].append("✓ PEFT is installed")
    except ImportError:
        info['message'].append("✗ PEFT is not installed")
        info['message'].append("  Install with: pip install peft")
    
    return info

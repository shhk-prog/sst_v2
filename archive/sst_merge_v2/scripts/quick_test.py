#!/usr/bin/env python3
"""
SST-Merge V2 クイックテスト

実際のアダプターを使用して動作確認を行う
"""

import torch
import logging
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sst_merge_v2 import SSTMergeV2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_adapter(path):
    """アダプターをロード"""
    data = torch.load(path, map_location='cpu')
    if isinstance(data, dict) and 'adapter' in data:
        return data['adapter']
    return data


def main():
    logger.info("=" * 70)
    logger.info("SST-MERGE V2 QUICK TEST")
    logger.info("=" * 70)
    
    # アダプターのパス
    adapter_dir = project_root / 'saved_adapters/llama-3.1-8b/utility_model'
    
    A5_path = adapter_dir / 'utility_model_A5.pt'
    A7_path = adapter_dir / 'utility_model_A7.pt'
    
    if not A5_path.exists() or not A7_path.exists():
        logger.error("Adapters not found. Please run training first.")
        logger.info(f"Expected paths:")
        logger.info(f"  A5: {A5_path}")
        logger.info(f"  A7: {A7_path}")
        return
    
    # アダプターをロード
    logger.info("\nLoading adapters...")
    A5 = load_adapter(A5_path)
    A7 = load_adapter(A7_path)
    
    logger.info(f"  A5 keys: {len(A5)} parameters")
    logger.info(f"  A7 keys: {len(A7)} parameters")
    
    # テスト1: Direct Mode
    logger.info("\n" + "=" * 50)
    logger.info("TEST 1: Direct Mode")
    logger.info("=" * 50)
    
    merger_direct = SSTMergeV2(
        k=10,
        mode="direct",
        device="cpu"
    )
    
    merged_direct = merger_direct.merge_utility_safety(
        model=None,
        utility_adapters=[A5],
        safety_adapter=A7,
        safety_weight=1.0
    )
    
    logger.info(f"  Merged keys: {len(merged_direct)}")
    
    # パラメータの変化を確認
    for key in list(merged_direct.keys())[:3]:
        if key in A5 and key in A7:
            a5_norm = torch.norm(A5[key]).item()
            a7_norm = torch.norm(A7[key]).item()
            merged_norm = torch.norm(merged_direct[key]).item()
            logger.info(f"  {key}: A5={a5_norm:.4f}, A7={a7_norm:.4f}, merged={merged_norm:.4f}")
    
    # テスト2: Residual Mode
    logger.info("\n" + "=" * 50)
    logger.info("TEST 2: Residual Mode (r=0.7)")
    logger.info("=" * 50)
    
    merger_residual = SSTMergeV2(
        k=10,
        mode="residual",
        residual_ratio=0.7,
        device="cpu"
    )
    
    # residual modeでもdataloaderがない場合はdirectにフォールバック
    merged_residual = merger_residual.merge_utility_safety(
        model=None,
        utility_adapters=[A5],
        safety_adapter=A7,
        safety_weight=1.0
    )
    
    logger.info(f"  Merged keys: {len(merged_residual)}")
    
    # テスト3: Safety weight variation
    logger.info("\n" + "=" * 50)
    logger.info("TEST 3: Safety Weight Variation")
    logger.info("=" * 50)
    
    for weight in [0.5, 1.0, 1.5]:
        merger = SSTMergeV2(k=10, mode="direct", device="cpu")
        merged = merger.merge_utility_safety(
            model=None,
            utility_adapters=[A5],
            safety_adapter=A7,
            safety_weight=weight
        )
        
        # 任意のキーでノルムを確認
        sample_key = list(merged.keys())[0]
        merged_norm = torch.norm(merged[sample_key]).item()
        logger.info(f"  weight={weight}: {sample_key} norm={merged_norm:.4f}")
    
    # 結果を保存
    output_dir = Path(__file__).parent.parent / 'results' / 'quick_test'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / 'test_merged_direct.pt'
    merger_direct.save_merged_adapter(
        merged_direct,
        str(output_path),
        {'test': True, 'mode': 'direct'}
    )
    
    logger.info("\n" + "=" * 70)
    logger.info("QUICK TEST COMPLETED SUCCESSFULLY")
    logger.info("=" * 70)
    logger.info(f"Output saved to: {output_path}")


if __name__ == '__main__':
    main()

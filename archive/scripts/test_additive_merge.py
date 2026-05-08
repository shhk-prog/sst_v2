#!/usr/bin/env python3
"""
加算ベース結合戦略のテストスクリプト

改善前: alpha * A5 + (1-alpha) * A7 → alpha=1.0でA7が消える
改善後: alpha * A5 + alpha * A7 → 両方を保持
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_combine_adapters():
    """_combine_adaptersメソッドの動作を確認"""
    
    # ダミーアダプター
    a5_adapter = {
        'layer.0.weight': torch.ones(10, 10) * 5.0,  # A5: 全て5.0
        'layer.1.weight': torch.ones(10, 10) * 5.0,
    }
    
    a7_adapter = {
        'layer.0.weight': torch.ones(10, 10) * 7.0,  # A7: 全て7.0
        'layer.1.weight': torch.ones(10, 10) * 7.0,
    }
    
    # SST-Mergeをインポート
    from sst_merge import SSTMerge
    
    merger = SSTMerge(k=10)
    
    # 各alpha値でテスト
    alpha_values = [0.5, 0.8, 1.0]
    
    print("=" * 60)
    print("加算ベース結合戦略のテスト")
    print("=" * 60)
    print(f"A5の値: 5.0")
    print(f"A7の値: 7.0")
    print()
    
    for alpha in alpha_values:
        merged = merger._combine_adapters(a5_adapter, a7_adapter, alpha=alpha)
        
        merged_value = merged['layer.0.weight'][0, 0].item()
        
        # 期待値: alpha * 5.0 + alpha * 7.0 = alpha * 12.0
        expected = alpha * 12.0
        
        print(f"α={alpha}:")
        print(f"  結合式: {alpha} * A5 + {alpha} * A7")
        print(f"  期待値: {alpha} * 5.0 + {alpha} * 7.0 = {expected:.1f}")
        print(f"  実測値: {merged_value:.1f}")
        print(f"  一致: {'✓' if abs(merged_value - expected) < 0.01 else '✗'}")
        print()
    
    print("=" * 60)
    print("従来方式との比較")
    print("=" * 60)
    
    alpha = 1.0
    
    # 従来方式: alpha * A5 + (1-alpha) * A7
    old_merged_value = alpha * 5.0 + (1 - alpha) * 7.0
    
    # 新方式: alpha * A5 + alpha * A7
    new_merged_value = alpha * 5.0 + alpha * 7.0
    
    print(f"α={alpha}の場合:")
    print(f"  従来方式: {alpha} * A5 + {1-alpha} * A7 = {old_merged_value:.1f}")
    print(f"            → A7が消える！")
    print(f"  新方式:   {alpha} * A5 + {alpha} * A7 = {new_merged_value:.1f}")
    print(f"            → 両方を保持！")
    print()

if __name__ == '__main__':
    test_combine_adapters()

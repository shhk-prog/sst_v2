"""
データフリーSST-Merge 簡易テスト

小規模なダミーアダプターで動作確認
"""

import torch
import sys
from pathlib import Path

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from sst_merge_data_free import SSTMergeDataFree, FIMCalculatorDataFree


def create_dummy_lora_adapter(num_layers=2, rank=16, dim=64):
    """
    テスト用のダミーLoRAアダプターを作成
    
    Args:
        num_layers: レイヤー数
        rank: LoRAランク
        dim: 次元数
    
    Returns:
        adapter_dict: ダミーアダプター
    """
    adapter = {}
    
    for i in range(num_layers):
        # lora_A: (rank, dim)
        adapter[f"layer.{i}.lora_A.weight"] = torch.randn(rank, dim) * 0.01
        
        # lora_B: (dim, rank)
        adapter[f"layer.{i}.lora_B.weight"] = torch.randn(dim, rank) * 0.01
    
    return adapter


def test_fim_calculation():
    """FIM計算のテスト"""
    print("\n" + "="*60)
    print("Test 1: FIM Calculation (Data-Free)")
    print("="*60)
    
    # ダミーアダプター作成
    adapter = create_dummy_lora_adapter(num_layers=2, rank=16, dim=64)
    print(f"Created dummy adapter with {len(adapter)} parameters")
    
    # FIM計算
    fim_calc = FIMCalculatorDataFree(regularization=1e-6)
    fim = fim_calc.compute_fim_from_lora(adapter)
    
    print(f"\nFIM computed:")
    print(f"  Shape: {fim.shape}")
    print(f"  Mean: {fim.mean():.6f}")
    print(f"  Std: {fim.std():.6f}")
    print(f"  Min: {fim.min():.6f}")
    print(f"  Max: {fim.max():.6f}")
    
    # 期待される形状
    expected_size = 2 * 64 * 64  # 2層 × (dim × dim)
    assert fim.shape[0] == expected_size, f"Expected {expected_size}, got {fim.shape[0]}"
    
    print("\n✓ FIM calculation test passed!")
    return fim


def test_sst_merge():
    """SST-Mergeのテスト"""
    print("\n" + "="*60)
    print("Test 2: Data-Free SST-Merge")
    print("="*60)
    
    # ダミーアダプター作成
    utility_adapter = create_dummy_lora_adapter(num_layers=2, rank=16, dim=64)
    safety_adapter = create_dummy_lora_adapter(num_layers=2, rank=16, dim=64)
    
    print(f"Created utility adapter: {len(utility_adapter)} keys")
    print(f"Created safety adapter: {len(safety_adapter)} keys")
    
    # SST-Merge実行
    sst_merge = SSTMergeDataFree(
        safety_weight=0.1,
        use_gevp=True,
        regularization=1e-6
    )
    
    merged = sst_merge.merge(utility_adapter, safety_adapter)
    
    print(f"\nMerged adapter:")
    print(f"  Keys: {len(merged)}")
    
    # 検証: キーが保存されているか
    assert len(merged) == len(utility_adapter), "Key count mismatch"
    
    # 検証: 形状が保存されているか
    for key in utility_adapter.keys():
        assert merged[key].shape == utility_adapter[key].shape, f"Shape mismatch for {key}"
    
    print("\n✓ SST-Merge test passed!")
    return merged


def test_comparison_with_simple_merge():
    """シンプルマージとの比較"""
    print("\n" + "="*60)
    print("Test 3: Comparison with Simple Merge")
    print("="*60)
    
    # ダミーアダプター作成
    utility_adapter = create_dummy_lora_adapter(num_layers=2, rank=16, dim=64)
    safety_adapter = create_dummy_lora_adapter(num_layers=2, rank=16, dim=64)
    
    alpha = 0.1
    
    # GEVP版
    sst_merge_gevp = SSTMergeDataFree(
        safety_weight=alpha,
        use_gevp=True
    )
    merged_gevp = sst_merge_gevp.merge(utility_adapter, safety_adapter)
    
    # シンプル版（Task Arithmetic）
    sst_merge_simple = SSTMergeDataFree(
        safety_weight=alpha,
        use_gevp=False
    )
    merged_simple = sst_merge_simple.merge(utility_adapter, safety_adapter)
    
    # 差分を計算
    diff_norms = []
    for key in utility_adapter.keys():
        diff = (merged_gevp[key] - merged_simple[key]).norm().item()
        diff_norms.append(diff)
    
    avg_diff = sum(diff_norms) / len(diff_norms)
    
    print(f"\nAverage difference between GEVP and Simple merge:")
    print(f"  {avg_diff:.6f}")
    
    # GEVP版は異なる重みを適用するはず
    assert avg_diff > 0, "GEVP and Simple should differ"
    
    print("\n✓ Comparison test passed!")


def main():
    """全テスト実行"""
    print("\n" + "="*70)
    print("Data-Free SST-Merge Test Suite")
    print("="*70)
    
    try:
        # Test 1: FIM計算
        test_fim_calculation()
        
        # Test 2: SST-Merge
        test_sst_merge()
        
        # Test 3: 比較
        test_comparison_with_simple_merge()
        
        print("\n" + "="*70)
        print("✓ All tests passed!")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

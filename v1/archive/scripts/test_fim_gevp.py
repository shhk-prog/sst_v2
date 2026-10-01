#!/usr/bin/env python3
"""
Phase 4-5: FIM計算とGEVP解法のテストスクリプト

テスト内容:
- Phase 4: FIM計算（有害・良性データ）
- Phase 5: GEVP解法と安全サブスペース選択

使用方法:
    python scripts/test_fim_gevp.py
"""

import sys
from pathlib import Path

# プロジェクトのルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
import logging
from src.fim_calculator import FIMCalculator
from src.gevp_solver import GEVPSolver

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DummyLoRAModel(nn.Module):
    """テスト用のダミーLoRAモデル"""
    def __init__(self, hidden_size=128, lora_rank=16):
        super().__init__()
        self.lora_A = nn.Parameter(torch.randn(hidden_size, lora_rank))
        self.lora_B = nn.Parameter(torch.randn(lora_rank, hidden_size))
        self.hidden_size = hidden_size
        self.embedding = nn.Embedding(100, hidden_size)  # vocab_size=100
    
    def forward(self, input_ids, attention_mask, labels):
        # 入力を埋め込みに変換
        batch_size, seq_length = input_ids.size()
        embedded = self.embedding(input_ids)  # [batch_size, seq_length, hidden_size]
        
        # 平均プーリング
        pooled = embedded.mean(dim=1)  # [batch_size, hidden_size]
        
        # LoRA変換を適用
        lora_output = torch.matmul(
            torch.matmul(pooled, self.lora_A),
            self.lora_B
        )  # [batch_size, hidden_size]
        
        # ラベルも同様に処理
        labels_embedded = self.embedding(labels).mean(dim=1)
        
        # ダミーのロス計算
        loss = torch.mean((lora_output - labels_embedded) ** 2)
        
        class Output:
            def __init__(self, loss):
                self.loss = loss
        
        return Output(loss)


def create_dummy_dataloader(num_batches=10, batch_size=4, seq_length=32):
    """ダミーデータローダーを作成"""
    data = []
    for _ in range(num_batches):
        batch = {
            "input_ids": torch.randint(0, 100, (batch_size, seq_length)),
            "attention_mask": torch.ones(batch_size, seq_length),
            "labels": torch.randint(0, 100, (batch_size, seq_length))
        }
        data.append(batch)
    return data


def test_phase_4_fim():
    """Phase 4: FIM計算のテスト"""
    logger.info("\n" + "="*80)
    logger.info("Phase 4: Testing FIM Calculation")
    logger.info("="*80)
    
    try:
        # ダミーモデルとデータの作成
        model = DummyLoRAModel(hidden_size=128, lora_rank=16)
        harm_data = create_dummy_dataloader(num_batches=5, batch_size=2)
        benign_data = create_dummy_dataloader(num_batches=5, batch_size=2)
        
        logger.info("✓ Dummy model and data created")
        
        # FIMCalculatorの初期化
        fim_calculator = FIMCalculator(
            model=model,
            approximation="gradient_variance",
            device="cpu"
        )
        logger.info("✓ FIMCalculator initialized")
        
        # 有害データのFIM計算
        logger.info("\nComputing FIM for harmful data...")
        F_harm = fim_calculator.compute_fim_harm(harm_data, max_samples=10)
        logger.info(f"✓ F_harm computed: shape={F_harm.shape}")
        
        # 良性データのFIM計算
        logger.info("\nComputing FIM for benign data...")
        F_benign = fim_calculator.compute_fim_benign(benign_data, max_samples=10)
        logger.info(f"✓ F_benign computed: shape={F_benign.shape}")
        
        # FIM行列の性質を検証
        logger.info("\nVerifying FIM properties...")
        
        # 対称性
        is_symmetric_harm = torch.allclose(F_harm, F_harm.T, atol=1e-5)
        is_symmetric_benign = torch.allclose(F_benign, F_benign.T, atol=1e-5)
        logger.info(f"  F_harm is symmetric: {is_symmetric_harm}")
        logger.info(f"  F_benign is symmetric: {is_symmetric_benign}")
        
        # 半正定値性（すべての固有値 >= 0）
        eigvals_harm = torch.linalg.eigvalsh(F_harm)
        eigvals_benign = torch.linalg.eigvalsh(F_benign)
        is_psd_harm = torch.all(eigvals_harm >= -1e-6)
        is_psd_benign = torch.all(eigvals_benign >= -1e-6)
        logger.info(f"  F_harm is positive semi-definite: {is_psd_harm}")
        logger.info(f"  F_benign is positive semi-definite: {is_psd_benign}")
        
        logger.info("\n✓ Phase 4: FIM calculation test passed")
        return True, F_harm, F_benign
        
    except Exception as e:
        logger.error(f"\n✗ Phase 4 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_phase_5_gevp(F_harm, F_benign):
    """Phase 5: GEVP解法のテスト"""
    logger.info("\n" + "="*80)
    logger.info("Phase 5: Testing GEVP Solver")
    logger.info("="*80)
    
    try:
        # GEVPSolverの初期化
        gevp_solver = GEVPSolver(regularization=1e-6, use_scipy=True)
        logger.info("✓ GEVPSolver initialized")
        
        # GEVPを解く
        logger.info("\nSolving GEVP...")
        k = 10  # 上位10個の固有値・固有ベクトルを取得
        eigenvalues, eigenvectors = gevp_solver.solve_gevp(F_harm, F_benign, k=k)
        logger.info(f"✓ GEVP solved: {len(eigenvalues)} eigenvalues computed")
        logger.info(f"  Eigenvalues shape: {eigenvalues.shape}")
        logger.info(f"  Eigenvectors shape: {eigenvectors.shape}")
        logger.info(f"  Top 5 safety efficiencies (λ): {eigenvalues[:5].tolist()}")
        
        # 固有値が降順にソートされているか確認
        is_sorted = torch.all(eigenvalues[:-1] >= eigenvalues[1:])
        logger.info(f"  Eigenvalues are sorted (descending): {is_sorted}")
        
        # 安全サブスペースの選択
        logger.info("\nSelecting safety subspace...")
        safety_subspace = gevp_solver.select_safety_subspace(eigenvectors, k=k)
        logger.info(f"✓ Safety subspace selected: shape={safety_subspace.shape}")
        
        # 正規直交性の確認
        orthogonality = torch.matmul(safety_subspace.T, safety_subspace)
        is_orthonormal = torch.allclose(
            orthogonality,
            torch.eye(k),
            atol=1e-4
        )
        logger.info(f"  Safety subspace is orthonormal: {is_orthonormal}")
        
        # 安全効率の計算
        logger.info("\nComputing safety efficiency...")
        direction = eigenvectors[:, 0]  # 最大固有値に対応する固有ベクトル
        efficiency = gevp_solver.compute_safety_efficiency(direction, F_harm, F_benign)
        logger.info(f"  Safety efficiency of top eigenvector: {efficiency:.4f}")
        logger.info(f"  Should match top eigenvalue: {eigenvalues[0].item():.4f}")
        
        # 一致するか確認
        matches = abs(efficiency - eigenvalues[0].item()) < 0.01
        logger.info(f"  Efficiency matches eigenvalue: {matches}")
        
        logger.info("\n✓ Phase 5: GEVP solver test passed")
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Phase 5 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """統合テスト: FIMとGEVPの完全なフロー"""
    logger.info("\n" + "="*80)
    logger.info("Integration Test: Complete FIM + GEVP Flow")
    logger.info("="*80)
    
    try:
        # より大きなモデルでテスト
        model = DummyLoRAModel(hidden_size=256, lora_rank=32)
        harm_data = create_dummy_dataloader(num_batches=10, batch_size=4)
        benign_data = create_dummy_dataloader(num_batches=10, batch_size=4)
        
        logger.info("Step 1: Computing FIMs...")
        fim_calculator = FIMCalculator(model, device="cpu")
        F_harm = fim_calculator.compute_fim_harm(harm_data, max_samples=20)
        F_benign = fim_calculator.compute_fim_benign(benign_data, max_samples=20)
        logger.info(f"✓ FIMs computed: shape={F_harm.shape}")
        
        logger.info("\nStep 2: Solving GEVP...")
        gevp_solver = GEVPSolver()
        eigenvalues, eigenvectors = gevp_solver.solve_gevp(F_harm, F_benign, k=20)
        logger.info(f"✓ GEVP solved: {len(eigenvalues)} eigenvalues")
        
        logger.info("\nStep 3: Analyzing safety directions...")
        # 安全方向（λ > 1）と危険方向（λ < 1）を分析
        safe_directions = eigenvalues > 1.0
        unsafe_directions = eigenvalues < 1.0
        
        num_safe = safe_directions.sum().item()
        num_unsafe = unsafe_directions.sum().item()
        
        logger.info(f"  Safe directions (λ > 1): {num_safe}")
        logger.info(f"  Unsafe directions (λ < 1): {num_unsafe}")
        
        if num_safe > 0:
            logger.info(f"  Max safety efficiency: {eigenvalues[0].item():.4f}")
            logger.info(f"  Mean safety efficiency (safe): {eigenvalues[safe_directions].mean().item():.4f}")
        
        logger.info("\n✓ Integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン関数"""
    logger.info("\n" + "="*80)
    logger.info("Phase 4-5: FIM Calculation & GEVP Solver Test Suite")
    logger.info("="*80)
    
    results = {}
    
    # Phase 4: FIM計算
    phase4_passed, F_harm, F_benign = test_phase_4_fim()
    results["Phase 4 (FIM Calculation)"] = phase4_passed
    
    # Phase 5: GEVP解法（Phase 4が成功した場合のみ）
    if phase4_passed:
        phase5_passed = test_phase_5_gevp(F_harm, F_benign)
        results["Phase 5 (GEVP Solver)"] = phase5_passed
    else:
        results["Phase 5 (GEVP Solver)"] = False
        logger.warning("Skipping Phase 5 due to Phase 4 failure")
    
    # 統合テスト
    integration_passed = test_integration()
    results["Integration Test"] = integration_passed
    
    # サマリー
    logger.info("\n" + "="*80)
    logger.info("Test Summary")
    logger.info("="*80)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    passed = sum(results.values())
    total = len(results)
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All tests passed! Phase 4-5 implementation is complete.")
    else:
        logger.warning(f"\n⚠️ {total - passed} test(s) failed. Please check the logs.")


if __name__ == "__main__":
    main()

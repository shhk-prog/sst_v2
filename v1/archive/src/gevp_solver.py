"""
Generalized Eigenvalue Problem (GEVP) Solver

一般化固有値問題 F_harm v = λ F_benign v を解き、安全サブスペースを特定します。
理論的基礎: Phase 1で確立されたGEVPによる二元最適化フレームワーク。
"""

import torch
import numpy as np
from typing import Tuple, Optional
import logging
from scipy import linalg

logger = logging.getLogger(__name__)


class GEVPSolver:
    """
    一般化固有値問題ソルバー
    
    F_harm v = λ F_benign v を解き、安全効率λが最大となる方向vを特定します。
    """
    
    def __init__(
        self,
        regularization: float = 1e-6,
        use_scipy: bool = True
    ):
        """
        Args:
            regularization: F_benignの正定値性を確保するための正則化項
            use_scipy: scipyのソルバーを使用するか（より安定）
        """
        self.regularization = regularization
        self.use_scipy = use_scipy
    
    def solve_gevp(
        self,
        F_harm: torch.Tensor,
        F_benign: torch.Tensor,
        k: Optional[int] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        一般化固有値問題を解く（安定性改善版）
        
        Args:
            F_harm: 有害データのFIM (shape: [n, n])
            F_benign: 良性データのFIM (shape: [n, n])
            k: 取得する固有値・固有ベクトルの数（Noneの場合は全て）
            
        Returns:
            eigenvalues: 安全効率λ (shape: [k] or [n])、降順にソート
            eigenvectors: 対応する固有ベクトル (shape: [n, k] or [n, n])
        """
        logger.info("Solving GEVP...")
        
        # 対角FIMの場合（1次元テンソル）
        if F_harm.dim() == 1 and F_benign.dim() == 1:
            logger.info("  Using diagonal FIM approximation")
            
            # 対角GEVPの解: λ_i = F_harm[i] / F_benign[i]
            eigenvalues = F_harm / (F_benign + self.regularization)
            
            # 固有値を降順にソート
            sorted_indices = torch.argsort(eigenvalues, descending=True)
            
            # k個の固有値を取得
            if k is None:
                k = eigenvalues.size(0)
            k = min(k, eigenvalues.size(0))
            
            eigenvalues = eigenvalues[sorted_indices[:k]]
            
            # 固有ベクトルは単位ベクトル（対角行列の場合）
            eigenvectors = torch.zeros(F_harm.size(0), k, device=F_harm.device)
            for i in range(k):
                eigenvectors[sorted_indices[i], i] = 1.0
            
            logger.info(f"  Top eigenvalue: {eigenvalues[0].item():.6f}")
            logger.info(f"  Bottom eigenvalue: {eigenvalues[-1].item():.6f}")
            
            return eigenvalues, eigenvectors
        
        # フルFIMの場合（2次元テンソル）
        # 入力検証
        assert F_harm.shape == F_benign.shape, "FIM matrices must have same shape"
        assert F_harm.shape[0] == F_harm.shape[1], "FIM matrices must be square"
        
        n = F_harm.shape[0]
        
        # 正則化を強化（安定性改善）
        # 元の正則化に加えて、F_benignの最小固有値を確認
        min_eigenvalue = torch.linalg.eigvalsh(F_benign).min()
        
        if min_eigenvalue < 1e-6:
            # F_benignが正定値でない場合、より強い正則化を適用
            adaptive_reg = max(1e-4, abs(min_eigenvalue.item()) * 2)
            logger.warning(f"F_benign has small eigenvalue {min_eigenvalue:.2e}, using adaptive regularization {adaptive_reg:.2e}")
            F_benign_reg = F_benign + adaptive_reg * torch.eye(n, device=F_benign.device)
        else:
            # 通常の正則化
            F_benign_reg = F_benign + self.regularization * torch.eye(n, device=F_benign.device)
        
        # 対称性の確保（数値誤差対策）
        F_harm = (F_harm + F_harm.T) / 2
        F_benign_reg = (F_benign_reg + F_benign_reg.T) / 2
        
        if self.use_scipy:
            eigenvalues, eigenvectors = self._solve_with_scipy(F_harm, F_benign_reg, k)
        else:
            eigenvalues, eigenvectors = self._solve_with_torch(F_harm, F_benign_reg, k)
        
        # 降順にソート
        sorted_indices = torch.argsort(eigenvalues, descending=True)
        eigenvalues = eigenvalues[sorted_indices]
        eigenvectors = eigenvectors[:, sorted_indices]
        
        if k is not None:
            eigenvalues = eigenvalues[:k]
            eigenvectors = eigenvectors[:, :k]
        
        logger.info(f"GEVP solved: {len(eigenvalues)} eigenvalues computed")
        logger.info(f"Top 5 safety efficiencies (λ): {eigenvalues[:5].tolist()}")
        
        return eigenvalues, eigenvectors
    
    def _solve_with_scipy(
        self,
        F_harm: torch.Tensor,
        F_benign: torch.Tensor,
        k: Optional[int]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        scipyを使用してGEVPを解く（より安定）
        
        scipy.linalg.eighを使用: Cholesky分解による変換
        F_harm v = λ F_benign v → L^{-1} F_harm L^{-T} w = λ w
        ここで F_benign = L L^T (Cholesky分解)
        """
        device = F_harm.device
        dtype = F_harm.dtype
        
        # CPUに移動（scipyはCPUのみ）
        F_harm_np = F_harm.cpu().numpy()
        F_benign_np = F_benign.cpu().numpy()
        
        n = F_harm_np.shape[0]  # 行列のサイズ
        
        try:
            # scipy.linalg.eighでGEVPを解く
            # eigvals_only=Falseで固有値と固有ベクトルの両方を取得
            eigenvalues_np, eigenvectors_np = linalg.eigh(
                F_harm_np,
                F_benign_np
            )
            
            # Torchテンソルに変換
            eigenvalues = torch.from_numpy(eigenvalues_np).to(device=device, dtype=dtype)
            eigenvectors = torch.from_numpy(eigenvectors_np).to(device=device, dtype=dtype)
            
        except np.linalg.LinAlgError as e:
            logger.error(f"GEVP solving failed: {e}")
            logger.warning("Falling back to standard eigenvalue decomposition")
            
            # フォールバック: F_benignの逆行列を使用
            F_benign_inv = torch.linalg.inv(F_benign)
            A = F_benign_inv @ F_harm
            eigenvalues, eigenvectors = torch.linalg.eigh(A)
        
        return eigenvalues, eigenvectors
    
    def _solve_with_torch(
        self,
        F_harm: torch.Tensor,
        F_benign: torch.Tensor,
        k: Optional[int]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        PyTorchを使用してGEVPを解く
        
        変換: F_benign^{-1} F_harm v = λ v
        """
        # F_benignの逆行列を計算
        try:
            F_benign_inv = torch.linalg.inv(F_benign)
        except RuntimeError:
            logger.warning("F_benign is singular, using pseudo-inverse")
            F_benign_inv = torch.linalg.pinv(F_benign)
        
        # 標準固有値問題に変換
        A = F_benign_inv @ F_harm
        
        # 固有値分解
        eigenvalues, eigenvectors = torch.linalg.eigh(A)
        
        return eigenvalues, eigenvectors
    
    def select_safety_subspace(
        self,
        eigenvectors: torch.Tensor,
        k: int
    ) -> torch.Tensor:
        """
        上位k個の固有ベクトルで安全サブスペースを構築
        
        Args:
            eigenvectors: GEVP の固有ベクトル (shape: [n, m])
            k: サブスペースの次元数
            
        Returns:
            safety_subspace: 安全サブスペースの基底 (shape: [n, k])
        """
        assert k <= eigenvectors.shape[1], f"k={k} exceeds number of eigenvectors={eigenvectors.shape[1]}"
        
        # 上位k個の固有ベクトルを選択（既にソート済みと仮定）
        safety_subspace = eigenvectors[:, :k]
        
        # 正規直交性の確認
        orthogonality = torch.matmul(safety_subspace.T, safety_subspace)
        is_orthonormal = torch.allclose(
            orthogonality,
            torch.eye(k, device=safety_subspace.device),
            atol=1e-4
        )
        
        if not is_orthonormal:
            logger.warning("Safety subspace is not orthonormal, applying Gram-Schmidt")
            safety_subspace = self._gram_schmidt(safety_subspace)
        
        logger.info(f"Safety subspace selected: dimension={k}")
        
        return safety_subspace
    
    def _gram_schmidt(self, vectors: torch.Tensor) -> torch.Tensor:
        """
        Gram-Schmidt直交化
        
        Args:
            vectors: 入力ベクトル (shape: [n, k])
            
        Returns:
            orthonormal_vectors: 正規直交ベクトル (shape: [n, k])
        """
        n, k = vectors.shape
        orthonormal = torch.zeros_like(vectors)
        
        for i in range(k):
            # 現在のベクトル
            vec = vectors[:, i].clone()
            
            # 既存の正規直交ベクトルとの直交化
            for j in range(i):
                vec -= torch.dot(vec, orthonormal[:, j]) * orthonormal[:, j]
            
            # 正規化
            norm = torch.norm(vec)
            if norm > 1e-10:
                orthonormal[:, i] = vec / norm
            else:
                logger.warning(f"Vector {i} is nearly zero after orthogonalization")
                orthonormal[:, i] = vec
        
        return orthonormal
    
    def compute_safety_efficiency(
        self,
        direction: torch.Tensor,
        F_harm: torch.Tensor,
        F_benign: torch.Tensor
    ) -> float:
        """
        特定の方向における安全効率λを計算
        
        λ = (v^T F_harm v) / (v^T F_benign v)
        
        Args:
            direction: 方向ベクトル (shape: [n])
            F_harm: 有害データのFIM
            F_benign: 良性データのFIM
            
        Returns:
            safety_efficiency: 安全効率λ
        """
        # 正規化
        direction = direction / torch.norm(direction)
        
        # Rayleigh quotient
        numerator = torch.matmul(direction, torch.matmul(F_harm, direction))
        denominator = torch.matmul(direction, torch.matmul(F_benign, direction))
        
        # ゼロ除算対策
        if denominator < 1e-10:
            logger.warning("Denominator is nearly zero in safety efficiency calculation")
            return 0.0
        
        safety_efficiency = (numerator / denominator).item()
        
        return safety_efficiency


def test_gevp_solver():
    """GEVPSolverの簡易テスト"""
    
    # ダミーのFIM行列を生成
    n = 100
    k = 10
    
    # F_harm: ランダムな正定値行列
    A_harm = torch.randn(n, n)
    F_harm = A_harm @ A_harm.T + 0.1 * torch.eye(n)
    
    # F_benign: 別のランダムな正定値行列
    A_benign = torch.randn(n, n)
    F_benign = A_benign @ A_benign.T + 0.1 * torch.eye(n)
    
    # GEVPソルバーのテスト
    solver = GEVPSolver()
    
    # GEVPを解く
    eigenvalues, eigenvectors = solver.solve_gevp(F_harm, F_benign, k=k)
    
    print(f"Eigenvalues shape: {eigenvalues.shape}")
    print(f"Eigenvectors shape: {eigenvectors.shape}")
    print(f"Top 5 eigenvalues: {eigenvalues[:5]}")
    
    # 安全サブスペースの選択
    safety_subspace = solver.select_safety_subspace(eigenvectors, k=k)
    print(f"Safety subspace shape: {safety_subspace.shape}")
    
    # 正規直交性の確認
    orthogonality = torch.matmul(safety_subspace.T, safety_subspace)
    print(f"Orthogonality check (should be I):\n{orthogonality[:5, :5]}")
    
    # 安全効率の計算
    direction = eigenvectors[:, 0]  # 最大固有値に対応する固有ベクトル
    efficiency = solver.compute_safety_efficiency(direction, F_harm, F_benign)
    print(f"Safety efficiency of top eigenvector: {efficiency:.4f}")
    print(f"Should match top eigenvalue: {eigenvalues[0].item():.4f}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_gevp_solver()

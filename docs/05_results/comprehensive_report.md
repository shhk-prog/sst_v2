# SST-Merge v5 包括的実験結果レポート

**評価日**: 2026-02-02
**総評価結果数**: 1667

## 1. 実験概要

### 評価カテゴリ

| カテゴリ | 評価数 | 説明 |
|----------|--------|------|
| ベースモデル・アダプター | 31 | 個別アダプターおよびベースモデル |
| Baselineマージ | 556 | Task Arithmetic, TIES, DARE |
| SST-Merge (加算型) | 556 | 従来のSST-Merge |
| SST-Merge (補間型) | 160 | Task Arithmetic互換版 |
| SST-Merge (Data-Free) | 364 | データなしGEVP |

### α値の範囲

- 最小: 0.05
- 最大: 1.0
- テスト値: [0.05, 0.07, 0.09, 0.1, 0.12, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

## 2. 主要結果（A6_A7ペア、α=1.0）

### 2.1 Jailbreak耐性

| 手法 | GEVP | Layer-wise | Resistance | ASR |
|------|------|------------|------------|-----|
| DARE | ✗ | ✗ | 0.0% | 100.0% |
| SST-Merge (Additive) | ✓ | ✓ | 84.6% | 15.4% |
| SST-Merge (Additive) | ✓ | ✗ | 84.0% | 16.0% |
| SST-Merge (Additive) | ✗ | ✗ | 81.4% | 18.6% |
| SST-Merge (Data-Free) | ✗ | ✓ | 87.0% | 13.0% |
| SST-Merge (Data-Free) | ✗ | ✗ | 87.0% | 13.0% |
| SST-Merge (Interpolation) | ✓ | ✓ | 91.6% | 8.4% |
| SST-Merge (Interpolation) | ✓ | ✗ | 93.2% | 6.8% |
| SST-Merge (Interpolation) | ✗ | ✓ | 99.8% | 0.2% |
| SST-Merge (Interpolation) | ✗ | ✗ | 100.0% | 0.0% |
| TIES | ✗ | ✗ | 99.6% | 0.4% |
| Task Arithmetic | ✗ | ✗ | 100.0% | 0.0% |

### 2.2 Alpaca性能

| 手法 | GEVP | Layer-wise | ROUGE-1 | ROUGE-2 | ROUGE-L |
|------|------|------------|---------|---------|---------|
| DARE | ✗ | ✗ | 0.0187 | 0.0018 | 0.0183 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5931 | 0.3642 | 0.5134 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5989 | 0.3652 | 0.5198 |
| SST-Merge (Additive) | ✗ | ✗ | 0.5577 | 0.3282 | 0.4758 |
| SST-Merge (Data-Free) | ✗ | ✓ | 0.6163 | 0.3904 | 0.5407 |
| SST-Merge (Data-Free) | ✗ | ✗ | 0.6163 | 0.3904 | 0.5407 |
| SST-Merge (Interpolation) | ✓ | ✓ | 0.4691 | 0.2514 | 0.3902 |
| SST-Merge (Interpolation) | ✓ | ✗ | 0.4472 | 0.2384 | 0.3697 |
| SST-Merge (Interpolation) | ✗ | ✓ | 0.2967 | 0.1420 | 0.2340 |
| SST-Merge (Interpolation) | ✗ | ✗ | 0.2690 | 0.1200 | 0.2075 |
| TIES | ✗ | ✗ | 0.3054 | 0.1421 | 0.2368 |
| Task Arithmetic | ✗ | ✗ | 0.2690 | 0.1200 | 0.2075 |

## 3. α値による性能変化

### 3.1 SST-Merge補間型（GEVP無効）

| α | Jailbreak Resistance | Alpaca ROUGE-1 | バランス指標 |
|---|---------------------|----------------|--------------|
| 0.10 | 74.2% | 0.6895 | 0.7148 |
| 0.20 | 76.0% | 0.6332 | 0.6908 |
| 0.30 | 78.8% | 0.5769 | 0.6662 |
| 0.40 | 85.2% | 0.5236 | 0.6486 |
| 0.50 | 89.4% | 0.4652 | 0.6120 |
| 0.60 | 95.2% | 0.4100 | 0.5732 |
| 0.70 | 98.2% | 0.3638 | 0.5309 |
| 0.80 | 99.6% | 0.3245 | 0.4895 |
| 0.90 | 100.0% | 0.2953 | 0.4560 |
| 1.00 | 100.0% | 0.2690 | 0.4239 |

### 3.2 SST-Merge加算型（GEVP無効）

| α | Jailbreak Resistance | Alpaca ROUGE-1 | バランス指標 |
|---|---------------------|----------------|--------------|
| 1.00 | 81.4% | 0.5577 | 0.6619 |

## 4. 重要な発見

### 4.1 補間型 vs 加算型（α=1.0）

- **Jailbreak耐性**:
  - 補間型: 100.0%
  - 加算型: 81.4%
  - **差分: +18.6%**

- **Alpaca性能（ROUGE-1）**:
  - 補間型: 0.2690
  - 加算型: 0.5577
  - **差分: -0.2888**

### 4.2 GEVP効果（補間型、α=1.0）

- **Jailbreak耐性**:
  - GEVP有効: 93.2%
  - GEVP無効: 100.0%
  - **GEVP効果: -6.8%**

### 4.3 Task Arithmetic互換性検証

**補間型（GEVP無効）とTask Arithmeticの比較**:

- Jailbreak耐性: 100.0% vs 100.0% （差: 0.0%）
- Alpaca ROUGE-1: 0.2690 vs 0.2690 （差: 0.0000）

**結論**: 補間型はTask Arithmeticと 完全に同等です。

## 5. 推奨設定

### 5.1 最高Jailbreak耐性
- **手法**: Task Arithmetic
- **α**: 1.0
- **GEVP**: 無効
- **Layer-wise**: 無効
- **性能**: 100.0% resistance

### 5.2 最高Utility性能
- **手法**: Task Arithmetic
- **α**: 0.05
- **GEVP**: 無効
- **Layer-wise**: 無効
- **性能**: ROUGE-1 = 0.7108

### 5.3 最良バランス（補間型）
- **手法**: SST-Merge (Interpolation)
- **α**: 0.1
- **GEVP**: 無効
- **Layer-wise**: 有効
- **Jailbreak耐性**: 77.8%
- **Alpaca ROUGE-1**: 0.6999
- **バランス指標**: 0.7369

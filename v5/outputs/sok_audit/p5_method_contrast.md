# SoK P5 対照監査: v3 内での精度設計の違い（SST vs Data-Free SST vs Matena-Fisher）

## 1. Data-Free SST（`v3/scripts/mergers/sst.py` L150–181）の CPU 実測結果

`data_free_sst` は FIM を使わず重み差分の二乗 `phi_h = delta_safe ** 2`, `phi_b = delta_util ** 2` を
**`torch.float16` のまま**計算し、`lambda_val = phi_h / (phi_b + 1e-6)` に `>= threshold` のハードマスクを適用している。
fp16 の最小非正規数は $2^{-24} \approx 5.96 \times 10^{-8}$ のため、$|\delta_s| < 2^{-12} \approx 2.44 \times 10^{-4}$ の座標は
二乗した瞬間に 0 へ桁落ちする。

| Pattern | Seed | `delta_safe==0` (fp16) | `phi_h==0` (fp16) | `phi_h==0` (fp32) | `phi_b==0` (fp16) | 実効マスク平均 (k=0.20) | 中央値 | 全1テンソル (>0.99) | 異常テンソル (>0.25) | L24–31 全1 | `inf` 件数 |
|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| safety+math | 42 | 2.59% | 65.48% | 2.59% | 27.41% | 0.3075 | 0.2094 | 27/224 (12.1%) | 32/224 (14.3%) | 1/56 (1.8%) | 0 |
| safety+math | 43 | 2.59% | 65.16% | 2.59% | 27.41% | 0.3025 | 0.2072 | 26/224 (11.6%) | 28/224 (12.5%) | 0/56 (0.0%) | 0 |
| safety+math | 44 | 2.56% | 65.10% | 2.56% | 27.41% | 0.3105 | 0.2096 | 28/224 (12.5%) | 35/224 (15.6%) | 1/56 (1.8%) | 0 |
| safety+code | 42 | 2.59% | 65.48% | 2.59% | 0.70% | 0.2965 | 0.2000 | 27/224 (12.1%) | 27/224 (12.1%) | 1/56 (1.8%) | 0 |
| safety+medical | 42 | 2.59% | 65.48% | 2.59% | 0.49% | 0.2965 | 0.2000 | 27/224 (12.1%) | 27/224 (12.1%) | 1/56 (1.8%) | 0 |

## 2. 同一リポジトリ（v3）内における 4 実装の P5 対照表

| 実装（v3 内コード箇所） | 重要度/FIM の計算 dtype | 正規化・下限処理 | 選択/重み付け方式 | P5 退化の発生 | 根拠（実測・コード） |
|:---|:---|:---|:---|:---|:---|
| `diagonal_sst` (`v3/scripts/mergers/sst.py` L118–148, L177–181; `fim.py` L161) | **fp16**（`get_fim_tensor` で `like_tensor.dtype` にキャスト） | なし（`eps=1e-6` 加算のみ、正規化オフ） | ハードマスク `lambda_val >= threshold` | **発生（重度）** | `F_h` の fp16 ゼロ率 79.2%（fp32 では 0.0025%）。60.4% のテンソルが全 1 マスク（L24–31 は 89.3%）、`inf=17,813`、実効マスク平均 0.7043、注入量比中央値 1.000（TA と同等）。 |
| `data_free_sst` (`v3/scripts/mergers/sst.py` L150–181) | **fp16**（`delta_safe ** 2`, `delta_util ** 2` を fp16 のまま二乗） | なし（`eps=1e-6` 加算のみ） | ハードマスク `lambda_val >= threshold` | **発生** | `safety+math`（3 seed 平均）で `phi_h==0` が fp32 の 2.58% → fp16 で 65.25% へ増加。実効マスク平均 0.3068、全 1 テンソル 12.1%、異常 (>0.25) 14.1%。 |
| `fisher_weighted` (`v3/scripts/mergers/sst.py` L74–101; `fim.py` L161) | **fp16**（`get_fim_tensor` で fp16 キャスト） | なし（`denom = f_b + f_h + 1e-6` in fp16） | 連続重み `w_u = f_b/denom, w_s = f_h/denom` | **発生（別形態: ゼロ重み化）** | `f_b`・`f_h` とも fp16 で 0 落ちした座標では `w_u = w_s = 0` となり、出力重み自体が 0 に崩壊するリスクがある（`matena_fisher` と異なり floor も fp32 変換もない）。 |
| `matena_fisher` (`v3/scripts/merging/matena_fisher.py` L48–54, L140–171) | **fp32**（`numerator/denominator` を `float32` 初期化、`theta_i.float()`, `f_i_raw.float()`） | グローバル L2 正規化（fp32）＋ `clamp(min=1e-6)` | 連続加重平均（`>= threshold` マスクなし） | **発生しない（安全）** | `get_fim_tensor` を経由せず `fim_dict.get(param_name).float()` を fp32 で直接計算し、最終保存直前（L171）のみ `base_tensor.dtype` へ戻すため、P5 の桁落ち・全 1 退化は構造的に起きない。 |

## 3. SoK 論文への示唆

- **同一コードベース内での対照証拠**: 同じ `v3/cache/fim/*.pt`（fp32）を入力にしていても、`matena_fisher.py`（fp32 演算＋L2 正規化＋floor）は P5 を完全に回避している一方、`sst.py` の `diagonal_sst` / `data_free_sst` は fp16 演算と `>= threshold` の組み合わせにより静かにマスクが退化する。
- **対策の一般性（設計指針）**: FIM や二乗勾配・二乗差分のような微小正値を扱う重要度ベースのマージでは、(a) 重要度比の計算を必ず fp32 以上で行うこと、(b) ハードマスクは閾値比較 `>=` ではなくインデックス `topk().indices` で厳密に $k$ 個選ぶこと、(c) マージ直後に実効マスク比率と対 TA 注入量比を自動検証すること、の 3 点を標準チェックリストとして組み込むべきである。

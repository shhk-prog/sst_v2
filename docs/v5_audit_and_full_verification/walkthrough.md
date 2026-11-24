# 修正内容の確認（Walkthrough）：v5 監査修正および V1〜V9 フル検証

## 1. 実施概要
AI-DLC（`survey-summary`）が生成した `v5/` 成果物を監査した結果、以下の課題が見つかったため、`v5/` 配下の実装・テスト・図・レポートを修正し、CPU 専用・読み取り専用（NFR2・NFR4 厳守）で V1〜V9 の全範囲検証および文字化けすり抜けの定量確認を完了した。

## 2. 主なコード修正（`v5/` 配下のみ）
- [tensor_checks.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/src/v5lib/tensor_checks.py):
  - `TensorSource` に PyTorch `.bin`（単一および `pytorch_model.bin.index.json` 分割シャード、直近 1 シャード CPU mmap キャッシュ）対応を追加。これにより HF キャッシュ上の `WizardMath-7B-V1.0`・`WizardCoder-Python-7B-V1.0` のフル重みが読めるようになった。
  - `rankdata_average` を純 NumPy ベクトル化版へ置換、`topk_mask` を `np.partition` ベースへ高速化（数値完全一致）。
- [verify.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/src/v5lib/verify.py):
  - `has_weights()` と `_dir_summary()` に `.bin` 判定を追加。
  - `run_v2_v3`・`run_v4`・`run_v5` のループ順を最適化し、FIM キャッシュおよび `.bin` シャードの重複読込を削減（NFR1 の数値同一性を維持）。
- [plots.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/src/v5lib/plots.py):
  - 凡例をプロット枠外右側へ移動して点との重なりを解消し、`sst`・`task_arithmetic` の主要点（$\alpha \in \{0, 0.6, 1\}$）に注釈を付与。
- [report.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/src/v5lib/report.py):
  - 図の埋め込みリンクを `report.md` 基準の相対パス（`../../outputs/figures/pareto_*.png`）に修正。
- [probe_gibberish_escape.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/probe_gibberish_escape.py)（新規）:
  - `is_gibberish=False` をすり抜けた多言語文字化け崩壊と分類器乖離を $\alpha=0.6$ 全 432 ファイルで定量集計。
- 単体テスト追加（[test_hypotheses.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/tests/test_hypotheses.py)、[test_report.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/tests/test_report.py)）。

## 3. 全範囲検証の結果（V1〜V9 および文字化け探索）

| 仮説 | 判定 | 主指標と実測値（全範囲: seed 42〜44・全 4 パターン・全 32 層） | 出典 |
|:---|:---|:---|:---|
| **V1** FIM の fp16 0 率 | **支持** | `0.6042`（406/672 テンソルが 80% 超。fp32 平均 0.0025% → fp16 平均 79.24%、最大 99.53%） | [v1_v9.json](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/hypotheses/v1_v9.json) |
| **V2** 実マスク比率・inf | **支持** | 異常率 `0.750`（2,016/2,688）、平均マスク比率 **70.4%**（期待値 20%）、**60.4% が全 1 退化**（L24–31 は 89.3%）、`inf` 17,813 | 同上 |
| **V3** マスクの FIM 依存 | **判定不能** | `Jaccard(Fh/Fb, |δ_s|) = 0.2003`、`Jaccard(Fh/Fb, random) = 0.2000`、Spearman `-0.0026`（中央値テンソルが全 1 退化のため 0.20 に張り付く） | 同上 |
| **V4** fp16 丸め消失率 | **判定不能** | 平均 `4.43%`（最大 `15.25%`、2,016 テンソル。事前基準 0.01〜0.10 の間） | 同上 |
| **V5** 実注入量比 SST/TA | **不支持** | 中央値 **`1.000`**（`0.999993`、ノルム比 `0.999995`、平均 `0.70`、p10〜p25 `0.21〜0.30`、p50〜p75 `1.000`） | 同上 |
| **V6** WizardMath 系統 | **不支持** | 比 `0.0204`（相対差分: WizardMath **2.74%** vs WizardCoder **113.5%**、MedAlpaca **154.7%**） | 同上 |
| **V7** code `rope_theta` | **支持** | 不一致率 `1.0`（123/123 モデルが `10000.0` ≠ `1000000.0`） | 同上 |
| **V8** FIM データ実体 | **不支持** | プレースホルダ率 `0.0`（harmful 1,400 件、各 benign 1,000 件） | 同上 |
| **V9** mergekit 語彙 | **不支持** | 不一致 `0` / 288 モデル | 同上 |

### 文字化け崩壊のすり抜け確認（[gibberish_escape_probe.md](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/probe/gibberish_escape_probe.md)）
- `safety+medical`（異系統 LLaMA-1）: `safemerge`（0.0%）を除く全手法で `is_gibberish=False` 応答の **100.0%** が文字化け崩壊。
- `safety+code`（異系統 CodeLlama）: `dare` 97.5%、`della` 96.6%、`data_free_sst` 96.3%、`sst` 89.1% が文字化け崩壊（`safemerge` 0.0%）。
- `safety+math`（同系統 Llama-2）: 全 10 手法とも **0.0〜0.4%**。

## 4. 最終検証
- 単体テスト: `CUDA_VISIBLE_DEVICES="" venv_sst/bin/python -m pytest v5/tests -q` → **50 passed**
- レポート再生成互換: `build_report.py` 再実行で手書きセクション（3 節・4 節）が保持され、全画像相対リンクが実在することを確認。
- 既存資産保全（NFR2）: `git status --short -- v3/results v1 v2` が空であることを確認。

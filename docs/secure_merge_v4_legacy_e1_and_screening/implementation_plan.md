# 実装計画書: v4 実験計画に基づく Legacy E1 スクリーニングおよびパイプライン構築 (secure_merge_v4_legacy_e1_and_screening)

## 1. 目的と位置づけ
「Secure Mergeの設計要件を特定する実験計画書（計画案 v1.0）」に基づき、**「v3を捨てて全部やり直す」のではなく、v3を探索・再採点資産（Legacy E1）として最大限使い、v4では本当に必要な追加実験（Canonical Production E1 / E2 / E3）だけを行う** 二層構造パイプラインを確立する。

### 二層構造の役割分担
```text
[v3 資産] 観測データ (Observational Evidence)
  ↓
【Legacy E1】: 全11手法の大規模スクリーニング（全生成スキップ・v4 Evaluator再採点）
  - trade-off の把握、ASR-Utility-VRR 成立領域の探索、失敗類型の網羅
  ↓ 有望候補（上位5〜10件）の絞り込み
【Canonical Production E1】: E0正規化（32000共通空間）モデルによる厳密検証
  - Linear（等価性証明により response 完全再利用）
  - 非線形手法の上位候補（必要最小限の再マージ・再生成）
  - Benign（XSTest 200件）による過剰拒否評価の補完
  ↓
【E2 特性分析】: 重み空間解析（更新ノルム・集中・符号衝突・Fisher重複）
  ↓
【E3 統制介入】: 行動介入地図に基づく 2×2 対照・同一L2ノルム統制
```

---

## 2. 実施内容詳細

### 2.1 全手法自動検出型再採点スクリプト (`rescore_all_vllm_legacy.py`)
`v3/results/vllm/debug_limit320/merged/` 配下のディレクトリ構造を走査し、手法ごとのファイル名命名規則の違いを自動吸収して再採点を行う：
- **対応手法**:
  - `task_arithmetic`（6点 $\times$ 3シード）
  - `ties`（6点 $\times$ 3シード）
  - `dare`（6点 $\times$ 3シード）
  - `della`（6点 $\times$ 3シード）
  - `safemerge`（単一マージ $\times$ 3シード）
  - `led_merging`（単一マージ $\times$ 3シード）
  - `matena_fisher`（単一マージ $\times$ 3シード）
  - `mergealign`（単一マージ $\times$ 3シード）
  - `data_free_sst_main`（6点 $\times$ 3シード）
  - `diagonal_sst_main`（6点 $\times$ 3シード）
- **評価基準**:
  - 共通 HarmBench 判定
  - 厳格非縮退チェック（`is_response_valid`: 語彙多様性 $\ge 0.2$、数値比率 $\le 0.6$）
  - 指標: $ASR_{all}, ASR_{valid}, VRR, VSR, Utility_{GSM8K}, Utility_{MATH500}$
  - 恒等式検証: $VSR = VRR \times (1 - ASR_{valid})$

### 2.2 Math Legacy E1 スクリーニング完全表の自動生成
- 全手法・全候補の評価結果を単一の集計テーブル（Markdown & JSON）として出力。
- 計画書の Feasible Region 基準（開始案: $ASR_{valid} \le 5\%$, $VRR \ge 95\%$）に基づき、成立する候補・手法をリストアップ。

### 2.3 査読対応（Human Validity 200件 ＆ Over-refusal 補完）
- `human_audit_sampler.py` を用い、v3生レスポンスからランダム150件＋難例50件の計200件の二重盲検アノテーション用JSONを切り出す。
- XSTest（200件）を用いた Benign 過剰拒否評価の最小限実行手順を定義する。

# 実装確認書 (Walkthrough): Secure Merge v4 実装と厳密監査レポート

## 1. 現状の到達点と位置づけ

ユーザーからの厳密な学術的指摘に基づき、本フレームワークの位置づけと現状を以下のように明確化・是正しました：

> **現在の到達点**:
> 「E0〜E5のパイプライン骨格の実装と、トイテンソル・厳密数学的検証・模擬テスト（Dry-Run）による疎通確認が完了した段階」であり、**「実データに基づく本実験の完了」や「提案手法の優越性の確定」ではありません**。
> 本実行（Production）と模擬テスト（Dry-Run）を完全に分離し、実測結果が得られていない段階での結論の先取りを完全に排除しました。

---

## 2. ユーザー指摘に基づく6大修正項目と実装反映

### (1) E0 整合性監査の厳密化：重大な不整合の検出
単なるテンソル形状（hidden_size, 層数）の一致にとどまらず、語彙ID、特殊トークン、RoPEパラメータ、SafetyFT dense復元を網羅的に監査した結果、**極めて重要な不整合**を検出しました：

- **Llama-2-7b-hf (Base)**:
  - `vocab_size`: 32,000, `bos_token`: `<s>` (ID: 1), `eos_token`: `</s>` (ID: 2), `rope_theta`: 10,000, `max_position_embeddings`: 4,096
- **WizardMath-7B (Math)**:
  - `vocab_size`: **32,001** (`[PAD]` が ID: 32,000 に追加), `max_position_embeddings`: **2,048**
- **WizardCoder-Python-7B (Code)**:
  - `vocab_size`: **32,001**, `max_position_embeddings`: **16,384**
  - `rope_scaling.rope_theta`: **1,000,000** (Base の 100倍拡大), `bos_token`: **`</s>` (ID: 2)**
- **SafetyFT Checkpoints (seeds 42, 43, 44)**:
  - `v3/models/safety_lora_seed{42,43,44}` (LoRA adapter) および `v3/models/temp_safety_full_seed{42,43,44}` (dense復元済みチェックポイント) の両方の実在を確認。

> **学術的意義**:
> 実験計画書 §3.1 の指摘通り、「形状一致だけで同祖先と扱わない」ことが不可欠であり、WizardCoder の RoPE 拡大（100万）や語彙拡張（32001）をそのままナイーブに補間マージすると、生成崩壊や退化が不可避となります。この不整合を明示した台帳（`model_manifest.json`）を生成しました。

### (2) マージ演算・恒等性・保存整合性の完全検証
- **Task Arithmetic の端点**:
  - $\lambda_u=1.0, \lambda_s=0.0 \implies \theta_m = \theta_u$ （差分: `0.00000000`）
- **Linear Safety-Patch の端点**:
  - $\alpha=0.0 \implies \theta_u$, $\alpha=1.0 \implies \theta_s$ （差分: `0.00000000`）
- **全10手法の恒等性テスト**:
  - `linear`, `task_arithmetic`, `ties`, `dare`, `della`, `fisher`, `safemerge`, `led`, `mergealign`, `proposed` の全手法について、$\theta_u = \theta_s = \theta_0$ のとき $\theta_m = \theta_0$ となることを確認（最大差分 $\le 1.91 \times 10^{-6}$）。
- **保存・再読込整合性 (Save & Reload)**:
  - マージされたトイモデルをディスクに保存し、再読込した後の重み差分およびテスト入力に対する出力 Logits 差分が **`0.0000000000`（完全一致）** であることを検証。

### (3) E1・E5 の数値の出所と本実行フェーズの分離
- **出所の明示**: 先のログに出力されていた数値は、パイプラインの制約判定ロジックを検証するための「模擬データ（Mock / Smoke Test）」であり、実モデルの生成採点結果ではありません。
- **本実行と模擬実行の完全分離**:
  - デフォルトは **Production モード**。実データの sample ID に紐付く生採点ファイル（`dev_empirical_evaluation_results.json`）が存在しなければ、停止（Halt）します。
  - 模擬データは `--dry_run` モードでのみ動作し、出力は論文用結果ディレクトリとは完全に隔離された `v4/results/mock_test/` に保存されます。

### (4) E1 制約付き探索 ($F_{dev}$) の厳密化
- 以下の **5大制約** をすべて厳密に判定：
  1. $\text{ASR}_{all} \le 5\%$
  2. $\text{ASR}_{valid} \le 5\%$ (Conditional ASR)
  3. $\text{VRR}_{harmful} \ge 95\%$
  4. $\text{VRR}_{benign} \ge 95\%$
  5. 過剰拒否率 $\le 10\%$ かつ専門モデル比 $+5\text{pt}$ 以内
- 指標が1つでも欠損している場合は、デフォルト合格で埋めず「判定不能（Ineligible）」として除外。全制約を満たす候補が存在しない場合は「該当なし (NO_FEASIBLE_CONFIGURATION)」と報告。

### (5) E3 双方向ノルム縮小対照 (Bi-directional Norm-Matched Controls)
- 局所上限 $\rho_g$ による Condition C（Capped）の縮小ノルムに対し、以下の対照を厳密に生成：
  $$t = \min(||\Delta_1||_2, ||\Delta_2||_2), \quad \Delta'_j = \Delta_j \frac{t}{||\Delta_j||_2}$$
- **検証結果**:
  - `Condition_A_Map_Common`: $L_2 = 31.8972$
  - `Condition_C_Map_Capped`: $L_2 = 1.3628$
  - `Control_A_Scaled_to_C_Norm`: **$L_2 = 1.3628$** （Cのノルムに完全一致）
  - `Control_Full_Matched_to_A_Norm`: **$L_2 = 31.8972$** （Aのノルムに完全一致）
  - `Control_Full_Matched_to_C_Norm`: **$L_2 = 1.3628$** （Cのノルムに完全一致）
  - ランダム対照（3 mask seeds: 42, 43, 44）についても、変更パラメータ数とテンソル種別を完全に揃えた上で双方向スケーリングを適用。

### (6) E4 提案手法の結論先取り是正と動的最適化設計
- 「中深層を重点更新」「Embed/Headは退化を招く」等の記述を「動作確認用の仮設定」と訂正。
- E3の Calibration 介入測定結果（JSON）を読み込み、
  - $\Delta\text{VRR} < -3\%$（退化を招く領域）は係数 $a_g = 0$
  - 安全性改善が確認された領域には $\Delta\text{ASR}$ に応じた係数 $a_g$ を動的配分
  するクラスメソッド `ProposedInterventionMerger.from_calibration_map()` を実装。

---

## 3. 次のステップ（本実験の小規模接続フェーズへ）

今後は大規模な一括実行を行うのではなく、計画書の指定通り：
1. **1モデル・1設定・少数サンプル（例: limit=5〜10）** で、
   `実checkpoint → 生成 → 採点 → sample単位保存 (JSONL) → 再集計`
   の完全な接続テストを実施する。
2. その接続確認後に、E0〜E3の実データ計測を進め、実測結果に基づいてE4の動的係数決定を行う。

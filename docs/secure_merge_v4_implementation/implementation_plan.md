# 実装計画書: Secure Merge v4 実装計画 (Secure_Merge_Experiment_Plan.md 準拠)

## 1. 概要と背景

本計画は、`docs/Secure_Merge_Experiment_Plan.md` に基づき、**セキュアモデルマージ (Secure Model Merge) において最適なマージ手法を特定し、その成功・失敗を説明する更新特性を明らかにすることで、その特性に適応した新たなマージ手法の提案へ繋げる** ための実験・評価システムを `v4` として新規構築・実装するものである。

中心研究課題（RQ）:
- **中心RQ**: セキュアmergeに最適なmerge手法はどんなものかを調べて，その特性に合ったmerge手法を提案するのに繋げる
  - **RQ1（条件の特定）**: 安全性と非退化性を満たす領域で、手法ごとに保持できる utility と頑健性はどう異なるか？ (E1)
  - **RQ2（成否の説明）**: マージの成否は「更新箇所の選択性(H1)」か、「局所層への集中(H2)」か、あるいは「全体の更新量の縮小」か？ (E2, E3)
  - **RQ3（安全性と退化の分離）**: 安全性への寄与と生成退化・utilityへの悪影響は、特定領域で分離可能か？ (E3)
  - **RQ4（設計への応用）**: 測定した寄与に基づき更新箇所と量を最適制御することで、既存手法を上回る新手法を設計できるか？ (E4, E5)

---

## 2. システム構成とディレクトリ設計 (`v4/`)

既存の `v3` の成果（データ、ベースモデル、評価器の資産）を活用しつつ、実験計画書で指摘された概念的・数式的不整合（Task ArithmeticとLinearの混同、不完全な退化判定、恒等マージの不検査など）を完全に排除したクリーンな `v4` ディレクトリを構築する。

```text
v4/
├── README.md                      # v4の全体仕様と実行手順書
├── configs/                       # 実験設定ファイル
│   ├── config_base.yaml           # ベースモデル、タスク定義、共通パス
│   ├── config_e0_audit.yaml       # E0: 整合性監査設定
│   ├── config_e1_comparison.yaml  # E1: 9手法×2領域×パラメータ候補比較
│   ├── config_e2_analysis.yaml    # E2: 重み特性・行動変化測定
│   ├── config_e3_intervention.yaml# E3: 6群介入地図・2×2統制介入
│   ├── config_e4_proposed.yaml    # E4: 行動介入制約付きマージ
│   └── config_e5_validation.yaml  # E5: 独立検証・アブレーション
├── scripts/
│   ├── audit/                     # E0: 整合性監査ツール群
│   │   ├── audit_models.py        # モデル出自・トークナイザ・設定台帳化
│   │   ├── audit_mergers.py       # マージ演算の数学的検証（端点・恒等性・差分定義）
│   │   ├── audit_metrics.py       # 指標算出の数学的一貫性テスト (ASR_all, VRR, ASR_valid, VSR)
│   │   └── human_audit_sampler.py # 200件人手点検用無作為・難例サンプラー
│   ├── mergers/                   # マージ手法コアモジュール
│   │   ├── base_merger.py         # マージ手法抽象基底クラス
│   │   ├── linear_patch.py        # Linear Safety-Patch: (1 - α)θ_u + α θ_s
│   │   ├── task_arithmetic.py     # 標準 Task Arithmetic: θ_0 + λ_u τ_u + λ_s τ_s
│   │   ├── ties_merger.py         # TIES (Trim, Elect Sign, Merge)
│   │   ├── dare_merger.py         # DARE (Random Drop & Rescale)
│   │   ├── della_merger.py        # DELLA (Magnitude-based Sampling)
│   │   ├── fisher_merger.py       # Fisher-Weighted Averaging
│   │   ├── safemerge.py           # SafeMERGE (Selective Layer-wise Projection)
│   │   ├── led_merger.py          # LED-Merging (Location-Election-Disjoint)
│   │   ├── mergealign.py          # MergeAlign (Domain & Alignment Vectors)
│   │   └── proposed_intervention_merge.py # E4: 行動介入に基づく非退化制約付きマージ
│   ├── analysis/                  # 特性分析および統制介入モジュール
│   │   ├── characteristic_analyzer.py # E2: 更新量比 r_g, 層別ノルム, 選択性, 競合, cosine, 符号衝突
│   │   ├── intervention_mapper.py     # E3.1: 6群(深さ4群+Norm+embed)×2強度(0.2, 0.6) 介入地図
│   │   └── controlled_intervention.py # E3.2: 2×2比較 (選択性×配分) + 同一ノルム対照
│   ├── eval/                      # 評価実行モジュール
│   │   ├── eval_safety_v4.py      # 公式判定器/HarmBench判定器による厳密評価
│   │   ├── eval_utility_v4.py     # math (GSM8K/MATH500), code (HumanEval/MBPP)
│   │   └── eval_overrefusal_v4.py # XSTest による過剰拒否測定
│   └── run_v4_pipeline.py         # E0〜E5 の一括・個別実行エントリーポイント
├── data -> ../v3/data             # データセットシンボリックリンク
└── results/                       # 実験結果出力ディレクトリ
    ├── e0_audit/
    ├── e1_comparison/
    ├── e2_characteristics/
    ├── e3_intervention/
    ├── e4_proposed/
    └── e5_validation/
```

---

## 3. 実装フェーズと詳細仕様

### Phase 1: E0 整合性監査 (Integrity Audit)
1. **モデル出自・Tokenizer・設定の台帳化 (`audit_models.py`)**:
   - ベースモデル (`Llama-2-7b-hf`), 専門モデル (`MetaMath-7B-V1.0` or `Llama-2-7b-math`, `WizardCoder-Python-7B-V1.0`), 安全モデル (`SafetyFT`) の checkpoint, revision, 祖先関係, vocab_size, 特殊トークン, RoPE, テンソル形状を網羅した manifest JSON を出力。
2. **マージ演算の厳密な区別と端点性検査 (`audit_mergers.py`)**:
   - `Linear Safety-Patch`: $\theta_m = (1-\alpha)\theta_u + \alpha\theta_s$ (端点 $\alpha=0 \to \theta_u$, $\alpha=1 \to \theta_s$)
   - `Task Arithmetic`: $\theta_0 + \lambda_u(\theta_u - \theta_0) + \lambda_s(\theta_s - \theta_0)$ （$\theta_0$ からのタスクベクトル合成）
   - TIES, DARE, DELLA, Fisher, SafeMERGE, LED, MergeAlign のトイテンソルによる恒等性・有限性・差分定義の検証。
3. **指標計算の整合性監査 (`audit_metrics.py`)**:
   - $\text{ASR}_{all} = \sum H_i / N$, $\text{VRR} = \sum V_i / N$
   - $\text{ASR}_{valid} = \sum (V_i H_i) / \sum V_i$
   - $\text{VSR} = \sum [V_i (1 - H_i)] / N$
   - 恒等式 $\text{VSR} = \text{VRR} \times (1 - \text{ASR}_{valid})$ の検査。
   - 「無効(gibberish)だから即座に無害($H_i=0$)とする」等の不正な短絡を排除。

### Phase 2: E1 手法比較の再構築 (Reconstruction of Baseline Comparison)
1. **9手法の標準化マージ**:
   - 対象領域: math (GSM8K, MATH500), code (HumanEval, MBPP)。
   - 各手法に最大6個の候補ハイパーパラメータを設定（公式推奨値を必ず包含）。
2. **制約付き最適化選択 ($F_{dev}$)**:
   - Development集合上で、制約 ($\text{ASR}_{all} \le 5\%$, $\text{ASR}_{valid} \le 5\%$, $\text{VRR} \ge 95\%$, 過剰拒否率 $\le 10\%$) を満たす中で対象領域の utility を最大化する最適パラメータ $z^*_m$ を特定。
3. **可視化・主比較表**:
   - ASR vs Utility パレート散布図、VRR・過剰拒否併記、通過率テーブルの生成。

### Phase 3: E2 特性分析 (Characteristic Measurement)
マージ手法ごとの「重み空間の物理的変化」と「行動変化」を網羅測定：
1. **更新量と局所集中度**:
   - 相対更新ノルム $r_g = ||\theta_{m,g} - \theta_{u,g}|| / (||\theta_{u,g}|| + \epsilon)$
   - 層別・モジュール別の配分比率、最大更新層の特定。
2. **選択性と幾何学的競合**:
   - 非ゼロパラメータ率、選択マスクの重複度。
   - 安全タスクベクトル $\tau_s$ と専門タスクベクトル $\tau_u$ の cosine 類似度、符号衝突率、Fisher情報重みの偏り。
3. **行動変化との相関分析**:
   - Calibration集合での $\Delta\text{ASR}, \Delta\text{VRR}, \Delta\text{utility}, \Delta\text{拒否率}$ と上記重み特性の相関・散布図分析。

### Phase 4: E3 小規模な統制介入 (Controlled Intervention Study)
1. **9.1: 介入地図の作成 (`intervention_mapper.py`)**:
   - モデルを6群に分割:
     - 領域1〜4: Transformerブロック深さ順4分割 (Norm除く)
     - 領域5: 全レイヤーの LayerNorm / RMSNorm
     - 領域6: Embedding層 & LM Head
   - 各群単独介入: $\theta^{(g,a)} = \theta_u + a P_g(\theta_s - \theta_u), a \in \{0.2, 0.6\}$
   - 各群の $\Delta\text{ASR}_{all}, \Delta\text{VRR}, \Delta\text{utility}$ を測定し、「安全性を高めるが退化を起こさない層」「退化を招く危険な層」をマッピング。
   - 群ペアの同時介入による相互作用検定。
2. **9.2: 選択性と更新量を分離する 2×2 要因配置 (`controlled_intervention.py`)**:
   - 要因1: 更新箇所（介入地図に基づく選択 vs 同数のランダム選択）
   - 要因2: 更新配分（共通係数 vs 領域別上限 $\rho_g$）
   - 対照群: 同一全体L2ノルムまで一様に縮小した対照 (Uniform norm-matched control)。
   - 結論分岐の判定: 箇所選択が効くか、単に全体更新量を減らせばよいのかを科学的に決定。

### Phase 5: E4 特性適応型セキュアマージ新手法 (Behavior-Intervention Guided Constrained Merge)
E3の知見に基づく新手法の実装：
$$\theta_{new} = \theta_u + \sum_{g=1}^G a_g P_g (\theta_s - \theta_u)$$
$$\text{subject to} \quad \frac{||a_g P_g(\theta_s - \theta_u)||}{ ||\theta_{u,g}|| + \epsilon} \le \rho_g$$
- Calibrationデータ上で、生成退化・utility低下を招く領域の更新を抑制し、安全性の改善効率が高い領域を優先的に更新。
- 領域ごとの上限 $\rho_g$ を動的に配分する最適化アルゴリズムを実装。

### Phase 6: E5 独立検証・アブレーション・統合テスト
1. **最強Baseline vs 単純縮小 vs 提案手法 の対決**:
   - 未見Test集合での評価。
   - アブレーション実験: ①非退化性情報の除去、②箇所選択の除去、③領域別上限の除去。
2. **200件規模の人手点検サンプラー (`human_audit_sampler.py`)**:
   - 150件の無作為抽出 + 50件の境界・難例（ルール通過の異常例、判定器不一致例など）をブラインド評価用に抽出するツールの実装。
3. **総合パイプライン (`run_v4_pipeline.py`) と単体テスト**:
   - E0からE5までを再現可能に実行できるコマンド体系を完成。

---

## 4. 検証・テスト手順
1. `audit_mergers.py`, `audit_metrics.py` によるトイテンソルでの数学的整合性テスト。
2. 既存 checkpoint / ダミーモデルを用いた E0 監査レポート生成。
3. E1, E2, E3, E4 の各スクリプトのドライラン（軽量設定 `limit=2` またはトイデータ）による動作保証。
4. 全コードの構文チェック・型アノテーション・例外処理の確認。

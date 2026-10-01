# Secure Merge v4 実装環境 (Secure_Merge_Experiment_Plan.md 準拠)

本環境は、**「Secure Mergeの設計要件を特定する実験計画書」(`docs/Secure_Merge_Experiment_Plan.md`)** に基づき、中心研究課題：
> **「セキュアmergeに最適なmerge手法はどんなものかを調べて，その特性に合ったmerge手法を提案するのに繋げる」**

を検証・達成するために新規構築された包括的な実験・評価・手法設計フレームワークです。

---

## 1. モジュールおよびディレクトリ構成

```text
v4/
├── README.md                      # 本仕様書
├── configs/                       # 実験設定ファイル
│   └── config_e1_comparison.yaml  # E1: 9手法×パラメータ候補×制約F_dev
├── scripts/
│   ├── audit/                     # E0: 整合性監査ツール
│   │   ├── audit_models.py        # モデル出自・トークナイザ・設定台帳化 (manifest)
│   │   ├── audit_mergers.py       # マージ演算の数学的厳密化 (端点・恒等性・有限性)
│   │   ├── audit_metrics.py       # 指標算出の数学的一貫性 (ASR, VRR, ASR_valid, VSR)
│   │   └── human_audit_sampler.py # 200件規模人手点検用サンプラー (150無作為+50難例)
│   ├── mergers/                   # マージ手法コアモジュール
│   │   ├── base_merger.py         # マージ手法抽象基底クラス
│   │   ├── linear_patch.py        # Linear Safety-Patch: (1 - α)θ_u + α θ_s
│   │   ├── task_arithmetic.py     # 標準 Task Arithmetic: θ_0 + λ_u τ_u + λ_s τ_s
│   │   ├── ties_merger.py         # TIES-Merging (Trim, Elect Sign, Disjoint Merge)
│   │   ├── dare_merger.py         # DARE (Drop And Rescale)
│   │   ├── della_merger.py        # DELLA (Magnitude-based Sampling & Rescale)
│   │   ├── fisher_merger.py       # Fisher-Weighted Averaging
│   │   ├── safemerge.py           # SafeMERGE (Selective Layer-wise Projection)
│   │   ├── led_merger.py          # LED-Merging (Location-Election-Disjoint)
│   │   ├── mergealign.py          # MergeAlign (Domain & Alignment Vectors)
│   │   ├── proposed_intervention_merge.py # E4: 行動介入に基づく非退化制約付きマージ
│   │   └── merge_cli.py           # CLI モデルマージ実行スクリプト
│   ├── analysis/                  # 特性分析および統制介入モジュール
│   │   ├── characteristic_analyzer.py # E2: 更新量比 r_g, 層別集中, 選択性, 幾何学的競合
│   │   ├── intervention_mapper.py     # E3.1: 6群×2強度 介入地図生成器
│   │   ├── controlled_intervention.py # E3.2: 2×2要因配置 & 同一ノルム縮小対照
│   │   └── e1_selector.py             # E1: 制約付き最適パラメータ選定 & 感度分析
│   ├── eval/                      # 評価実行モジュール
│   │   ├── eval_safety_v4.py      # 安全性・非退化性評価 (ASR_all, VRR, ASR_valid, VSR)
│   │   ├── eval_utility_v4.py     # 有用性評価 (math: GSM8K/MATH500, code: HumanEval/MBPP)
│   │   └── eval_overrefusal_v4.py # 過剰拒否評価 (XSTest等)
│   └── run_v4_pipeline.py         # E0〜E5 統合実行ランナー
└── results/                       # 実験結果出力先
    ├── e0_audit/                  # モデルマニフェスト、人手点検シート
    ├── e1_comparison/             # 9手法比較選定サマリー、感度マトリクス
    ├── e2_characteristics/        # 重み特性レポート
    ├── e3_intervention/           # 介入地図、2x2要因配置結果
    ├── e4_proposed/               # 提案モデル重み・設定
    └── e5_validation/             # アブレーション検証結果サマリー
```

---

## 2. 実験計画書 (E0〜E5) に対応した実行コマンド

全ステージは `v3/venv_v3/bin/python` を用いて一括または個別で実行可能です。

### 2.1 全ステージの一括実行 (E0 〜 E5)
```bash
v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --stage all
```

### 2.2 個別ステージの実行

#### Stage E0: 整合性監査 (Integrity Audit)
モデル出自・トークナイザ整合性、マージ演算の端点・恒等性、指標恒等式 $VSR = VRR \times (1 - ASR_{valid})$ の完全検証：
```bash
v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --stage e0
```

#### Stage E1: 比較の再構築 (Reconstruction of Baseline Comparison)
9つの既存マージ手法に対し、Development制約 $F_{dev}$（$\text{ASR} \le 5\%$, $\text{VRR} \ge 95\%$, 過剰拒否 $\le 10\%$）を満たす utility 最大化パラメータ $z^*_m$ を探索：
```bash
v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --stage e1
```

#### Stage E2: 特性分析 (Characteristic Measurement)
マージ手法ごとの相対更新量 $r_g = ||\theta_{m,g} - \theta_{u,g}|| / ||\theta_{u,g}||$、最大集中層、非ゼロ選択率、cosine類似度、符号衝突を測定：
```bash
v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --stage e2
```

#### Stage E3: 統制介入実験 (Controlled Intervention Study)
6群（Transformer 4分割 + Norm + Embed/Head）× 2強度による介入地図の作成、および「選択性 × 更新配分」の 2×2 要因配置と同一全体ノルム縮小対照モデルを生成：
```bash
v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --stage e3
```

#### Stage E4: 観測特性に適応した新マージ手法の試作
行動介入に基づく非退化制約付きマージ（Behavior-Intervention Guided Constrained Merge）を適用：
```bash
v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --stage e4
```

#### Stage E5: 独立検証とアブレーション
最強Baseline vs 単純縮小 vs 提案手法の対決、および3種のアブレーション（非退化情報除去、箇所選択除去、領域別上限除去）を比較：
```bash
v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --stage e5
```

---

## 3. 実装上の重要改善点 (v3からの刷新)

1. **Linear Safety-Patch と標準 Task Arithmetic の完全分離**:
   - `Linear Safety-Patch`: $\theta_m = (1 - \alpha)\theta_u + \alpha\theta_s$
   - `Task Arithmetic`: $\theta_0 + \lambda_u \tau_u + \lambda_s \tau_s$ ($\theta_0$ からのタスクベクトル合成)
   - 既存原稿で混同されていた両者を明確に独立クラスとして実装し、端点テストを通過。
2. **非退化性指標と安全指標の数学的一貫性保証**:
   - $VSR = VRR \times (1 - ASR_{valid})$ の厳密な恒等式検証。
   - 退化・無効出力を自動的に無害とみなす短絡ロジックを排除。
3. **200件ブラインド人手点検サンプラーの整備**:
   - 150件の無作為抽出 + 50件の難例・境界例（短文拒否、判定器不一致）を二重盲検形式で出力。
4. **統制介入による成否因子の科学的分離**:
   - 「箇所選択の効果」と「更新量縮小の効果」を同一ノルム対照によって完全に切り分けて実証。
5. **特性適応型新マージ手法の実装**:
   - $\theta_{new} = \theta_u + \sum_g a_g P_g(\theta_s - \theta_u)$ subject to $\frac{||a_g P_g(\theta_s - \theta_u)||}{ ||\theta_{u,g}|| + \epsilon} \le \rho_g$

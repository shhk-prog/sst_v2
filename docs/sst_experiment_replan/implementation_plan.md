# 実装計画: SST-Merge 実験再計画（ゼロベース・トップ会議向け）

## 目的 (Goal Description)
過去の実験結果を完全にリセットし、NeurIPS / ICLR / ICML / ACL などのトップ会議採択に足る「再現性・客観性・スケール」を備えた実験をゼロベースで再構築します。

特に、予算の制約を取り払い、LLM-as-a-Judge (GPT-4o等) をフル活用した詳細で正確な評価を行います。また、マージの実装や評価においては、**Mergekit** や **lm-evaluation-harness** などの標準化されたオープンソースツール・公式リポジトリを必ず用い、査読に対する「実装の正当性・再現性の根拠」を確保します。さらに、Utilityモデルとして現実の事業応用に即した「金融特化モデル」等を採用し、SST-Mergeの実社会での有用性を強くアピールします。

## ユーザー確認事項 (User Review Required)

本計画はご提示いただいた「予算無制限」「ゼロベースでのやり直し」「事業モデル（金融）の検討」「公式実装・Mergekitの利用」の要件を完全に反映しています。方針に相違がないか、内容のご確認をお願いします。

## 提案する実験計画 (Proposed Changes)

実験をゼロから以下の4つのフェーズで構築します。

### フェーズ1: モデル作成と標準化環境の構築 (Model Preparation & Setup)
現実の事業応用を想定し、強力なベースモデルからドメイン特化 Utility モデルを作成します。

* **ベースモデル**:
    * `Meta-Llama-3-8B-Instruct`
    * `Mistral-7B-Instruct-v0.3`
* **Utility FT ($\theta_{util}$)**:
    1. **金融ドメイン特化モデル (Financial Model)**:
        * データセット: `FinGPT` 関連データセット または `FPB (Financial PhraseBank)`, `FinQA` 等の金融コーパス。
        * 目的: 現実のエンタープライズ事業でLLMを活用するシナリオの再現。
    2. **推論/コーディング特化モデル (Reasoning Model)**:
        * データセット: `MetaMathQA` または `Magicoder`
        * 目的: Safetyパッチによって最も破壊されやすい論理推論能力の維持を証明。
* **Safety FT ($\theta_{safe}$)**:
    * データセット: `HarmBench` (Training Split), `AdvBench`, および **`TrustLLM JailbreakTrigger`**。
    * 目的: 最新かつ多様な攻撃手法（JailbreakTrigger等）のデータを用いて、より汎用性の高い強力な防御モデルを作る。

### フェーズ2: マージ実行 (Merge Execution with Standard Tools)
自作のスクリプトによるマージ実装を避け、コミュニティ標準のツール（Mergekit等）および各手法の公式実装を用いて、結果の正当性を担保します。

* **提案手法**:
    1. **SST-Merge (Full / Diagonal / Data-Free)**: FIM比（GEVP最適化）による補間型・加算型マージ。
* **比較ベースライン手法（公式実装ベース）**:
    1. **Direct Safety FT** (ベースラインの下限・上限確認用)
    2. **Task Arithmetic**: `Mergekit` を用いて実行。
    3. **TIES / DARE-TIES**: `Mergekit` を用いて実行（疎化マージの標準実装）。
    4. **Fisher-Weighted Averaging (FWA)**: NeurIPS 2022 公式実装または標準的再現コードを利用。
    5. **SafeMERGE / AlignMerge**: 2025年最新手法として、著者の公式GitHubリポジトリ実装を利用。

各手法において、マージ強度 $\alpha$ や 選択比率 $k$ などのハイパーパラメータを広範にスイープし、正確なパレートフロンティアを描画します。

### フェーズ3: 大規模評価 (Evaluation with Standard Benchmarks)
予算制約なしを前提とし、標準化フレームワークと GPT-4o API を用いた厳密な評価を実施します。

* **Utility評価 (via `lm-evaluation-harness`)**:
    * **金融タスク**: `FPB`, `FiQA` （金融モデルのドメイン維持能力を測る）
    * **一般・推論タスク**: `MMLU`, `GSM8K`
* **Safety評価 (via 公式リポジトリ)**:
    * **HarmBench**: 最新・最高難易度のJailbreak攻撃に対する Attack Success Rate (ASR) を公式評価スクリプトで測定。
    * **AdvBench**: 従来の標準ベンチマーク。
* **過剰拒絶・崩壊の評価 (最重要)**:
    * **XSTest 公式評価**: 安全なプロンプトに対する False Positive (過剰拒絶) 率の測定。
    * **LLM-as-a-Judge (GPT-4o)**: `MT-Bench` を用い、マージ後のモデルが「無限ループ」や「推論崩壊」を起こしていないか、対話品質を詳細に採点。

### フェーズ4: 詳細分析 (Deep Dive Analysis)
査読者（Reviewer）を納得させる強固な理論的証拠を提示します。

1. **Surrogate Hierarchy の相関分析**:
    * Data-Free SSTのタスクベクトル二乗比と、Diagonal SSTのFIM値の順位相関 (Spearman相関等) を実証。
2. **失敗モードの定量化**:
    * 既存手法 (DARE, TIES等) が「推論崩壊」や「過剰拒絶」によってのみ高Safetyスコアを達成している（偽陽性である）ことを、GPT-4oを用いた採点で明確にグラフ化して告発する。
3. **パラメータの感度分析とFIMの妥当性検証 (Proxy Validation)**:
    * **「Utilityを壊す方向はどこか？」** を正確に特定できているかを検証します。
    * FIMがそのProxyとして本当に機能しているかを示すため、**破壊テスト（Prune Top-K）**と**保護テスト（Modify Bottom-K）**を実施します。
    * FIMが重要と判定したパラメータ群と、Weight Magnitude（重みの大きさ）ベースで判定したパラメータ群を意図的に破壊（ノイズ付加・ゼロ化）した際の、予測Lossの増加やベンチマークスコアの劣化を比較します。
    * これにより、既存の重みベースの疎化手法に比べ、SST-Mergeの選別（FIM）が「真に保護すべき急所」を正しく捉えていることを証明します。
4. **FIM サンプルサイズアブレーション**:
    * FIM推定に必要なデータ量が少数（100件程度）で十分であることを証明。

## 成果物の構成 (File Structure Updates)

本計画に沿って作業を進めるためのファイルを整備します。

#### [NEW] docs/sst_experiment_replan/task.md
実行タスクの進捗を管理する詳細なチェックリスト（データ準備〜モデル学習〜評価までを段階的に記載）。

#### [NEW] docs/sst_experiment_replan/walkthrough.md
各フェーズ完了後に、得られた洞察やパレートフロンティアのグラフ描画結果などを蓄積していくレポート。

## 検証計画 (Verification Plan)
1. 金融データセット（FinGPT/FPB等）および HarmBench データセットのダウンロードと前処理。
2. `Mergekit` および `lm-evaluation-harness` のセットアップ。
3. まず Llama-3-8B にて小規模なデータでパイプライン全体（FT → Mergekitマージ → lm-eval/HarmBench評価）が公式実装通りに動作することを確認（Dry run）。
4. 予算をフル活用し、全パラメータスイープの大規模計算と GPT-4o による全出力の判定を実行。

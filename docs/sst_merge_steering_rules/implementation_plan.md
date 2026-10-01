# AAAI-27 実験要件・アブレーション・評価パイプライン設計の追加計画 (改定第2版)

本計画は、ユーザーからの指示に基づき、SST-Merge の AAAI-27 投稿を見据えた実験・評価設計（必須比較手法、アブレーション内容、詳細な評価ベンチマーク、Pareto AUC等の主要指標、データ分離設計、新規作成スクリプト規約）を Specs (`kiro/specs/sst-merge-aaai27/`) および Steering (`kiro/steering/`) に追加で組み込むための実装計画です。

---

## ユーザーレビュー要求事項

> [!IMPORTANT]
> - **AAAI向け比較手法の網羅化**: DELLA, Breadcrumbs, RegMean, SafeMERGE, LED-Merging, AlignMerge などの必須比較手法および non-merge/guardrail baseline を specs に追加します。
> - **SST内アブレーションの設計**: F_h/F_b ratio と F_h only、1/F_b only、magnitude の比較を含め、合計 11 項目のアブレーション設計を記述します。
> - **評価ベンチマークの拡充**: Safety（HarmBench, JailbreakBench, StrongREJECT, WildJailbreak）および Utility（MMLU-Pro, IFEval, GSM8K, MBPP, AlpacaEval 2等）の最低構成と主表・補助表のフォーマットを定義します。
> - **主要指標と統計的報告**: ASR, Safety@95% Utility, Pareto AUC などの定義と、最低 3 シードおよび bootstrap 信頼区間/有意差検定の要請を記述します。
> - **FIM用データと評価データの物理分離**: F_h 推定に Custom Jailbreak/BeaverTails train、F_b 推定に RepliQA/Alpaca train を用い、評価ベンチマークと完全に分離する設計を明記します。
> - **コード側への落とし込み (新規スクリプト作成)**:
>   1. `v2/scripts/evaluation/eval_safety_suite.py`
>   2. `v2/scripts/evaluation/eval_utility_suite.py`
>   3. `v2/scripts/merging/baseline_merge.py` (手法追加)
>   4. `v2/scripts/analysis/pareto_auc.py`
>   5. `v2/configs/aaai27/*.yaml` (実験管理YAML化)
>   これらをタスクリストに追加します。

---

## 提案する変更内容

### 1. AAAI-27 実験計画書 (Specs) の拡充

以下の 3 ファイルを、指示された実験・評価・アブレーション構成に合わせて大幅に拡充します。

#### [MODIFY] [requirements.md](file:///mnt/nas/home/hiromi/src/sst_v2/kiro/specs/sst-merge-aaai27/requirements.md)
- **必須比較手法リスト**: Task Arithmetic, TIES, DARE, DELLA, Breadcrumbs, Fisher-weighted, RegMean/Fisher Mask, MergeAlign, SafeMERGE, LED-Merging, AlignMerge, および non-merge/guardrail baseline。
- **SST内アブレーション設計**: 11項目のアブレーションの定義（F_h/F_b, F_h only, 1/F_b only, magnitude, random, soft/hard mask, prior on/off, sample size sweep, data-free validation, negative control）。
- **評価データセット・ベンチマークの最低構成**:
  - Safety: HarmBench, JailbreakBench, StrongREJECT, WildJailbreakを主表とし、AdvBenchを補助表に定義。
  - Utility: MMLU-Pro, MMLU, IFEval, GSM8K, MATH-500, MBPP, AlpacaEval 2, RepliQA, Alpaca。
- **主表の定義**: 指定されたフォーマットを明記。
  `Method | HarmBench ASR↓ | JBB ASR↓ | StrongREJECT↓ | MMLU-Pro↑ | IFEval↑ | AlpacaEval↑ | Safety@95% Utility↑ | Pareto AUC↑`
- **統計的報告**: 最低 3 seed、mean±std、95% bootstrap CI、paired bootstrap test for Pareto AUC を要求。

#### [MODIFY] [design.md](file:///mnt/nas/home/hiromi/src/sst_v2/kiro/specs/sst-merge-aaai27/design.md)
- **データ分離設計**: FIM推定用、LoRA学習用、評価用、検証用の具体的なデータ割り当て（F_h推定: BeaverTails train等、Safety評価: HarmBench等、F_b推定: RepliQA/Alpaca train等、Utility評価: MMLU-Pro等）を明記し、重複を遮断する設計。
- **実験管理のYAML化**: `configs/aaai27/*.yaml` を通じた、モデルパス・アダプタ設定・評価ベンチマーク・ハイパーパラメータ（α, k）の一元管理設計。
- **新規スクリプトの設計**: `eval_safety_suite.py`, `eval_utility_suite.py`, `pareto_auc.py` のモジュール・データフロー設計。

#### [MODIFY] [tasks.md](file:///mnt/nas/home/hiromi/src/sst_v2/kiro/specs/sst-merge-aaai27/tasks.md)
- **具体的なTODOの細分化とスケジュール**:
  - `eval_safety_suite.py` の実装タスク
  - `eval_utility_suite.py` (lm-evaluation-harness統合) の実装タスク
  - `baseline_merge.py` への新マージ手法（DELLA, Breadcrumbs, SafeMERGE, LED-Merging等）の追加タスク
  - `pareto_auc.py` (AUC, Safety@95% Utility自動計算・プロット) の実装タスク
  - `configs/aaai27/*.yaml` の定義タスク
  - 3モデル (Llama-3.1-8B, Mistral-7B, Qwen2.5-7B) に対する実験グリッド実行タスク
  - アブレーション実験の自動化タスク

---

### 2. Steering Rules (`kiro/steering/`) の整合性向上

- **[product.md](file:///mnt/nas/home/hiromi/src/sst_v2/kiro/steering/product.md)**: 
  実験要件（比較手法、ベンチマーク、データ分離など）を Specs と完全に同期させ、永続ルールとして「評価データのFIM・LoRAへの再利用禁止」「全スイープの保存（cherry-pickingの禁止）」などを強化します。

---

### 3. 自動検証フック (`steering_hook.py`) のアップデート
- データセットパスや引数が YAML 設定から渡された場合でも、評価データセットと学習/FIMデータセットが重複していないか（`verify_experiment_config` 内でパスの解像による検証）を厳格にチェックします。

---

## 検証計画

- **仕様書の整合性チェック**: `kiro/steering/` の記述と `kiro/specs/` の要件が完全に一致し、AAA-27 投稿時の指摘を受けないレベルで厳密化されているかを確認します。
- **新規スクリプトのモック動作検証**: 新たに定義するタスクに沿って作成した各スクリプトが、YAML設定を読み込み、正常にフックをパスしてダミーデータで動作することを確認します。

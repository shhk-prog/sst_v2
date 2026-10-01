# SST-Merge 実験再計画：学習データセットと評価体系の定義完了

指示追従能力と専門性を両立させ、トップ会議（NeurIPS/ICML等）の基準に耐えうる厳密な評価を行うため、学習データセットおよび評価体系を再定義し、関連研究に基づく根拠（参考文献）を整理しました。

## 1. 学習構成のアップデート (Fine-Tuning Configuration)

以下の3つの専門領域をカバーするデータセット構成を定義しました。

- **Finance**: `gbharti/finance-alpaca` (4,500件)
    - 従来のセンチメント分類から、推論・QAを含む対話形式へ変更。
- **Coding**: `Magicoder-OSS-Instruct-75K` (4,500件)
    - 高品質なOSSコード指示データ。
- **Safety**: `AdvBench` + `TrustLLM` (~2,000件)
    - 脱獄攻撃への拒絶応答を学習。

## 2. 評価体系の厳密化 (ID/OOD Evaluation)

モデルの「定着度（In-Domain）」と「汎化性能（Out-Of-Domain）」を明確に切り分ける評価体系を構築しました。

| カテゴリ | 指標 (ID/OOD) | ベンチマーク |
| :--- | :--- | :--- |
| **Safety** | 未見の攻撃への耐性 / 過剰拒絶 | HarmBench, XSTest |
| **Finance** | 専門知識の汎化 | MMLU (Finance-related) |
| **Coding** | 論理推論・生成能力 | HumanEval, MBPP, GSM8K |
| **General** | 破滅的忘却の測定 | ARC-C, HellaSwag |

## 3. 文献的根拠の追加 (Academic Grounds)

[実装計画 (implementation_plan.md)](file:///mnt/nas/home/hiromi/src/sst_v2/docs/sst_experiment_replan/implementation_plan.md) に、各データセットおよびベンチマークの初出論文（ICML, ICLR, ACL, NAACL等）を網羅的に追記しました。これにより、実験結果の信頼性と学術的妥当性を担保しています。

## 実施済み内容
- `[x]` 実装計画の更新：データセット件数、ID/OOD評価体系、参考文献の追加
- `[x]` タスクリストの更新：新構成に基づくフェーズ2・フェーズ4のタスク詳細化

## 次のステップ
1.  **データ準備の再確認**: 新しいデータセット件数（4.5k/4.5k/2k）に合わせて `prepare_datasets.py` が正しく動作するか確認します。
2.  **フェーズ2（学習）の実行**: 定義した新構成での Fine-Tuning を開始します。
3.  **評価パイプラインの調整**: ID/OOD 評価が自動で回るよう `run_phase2.sh` の最終調整を行います。

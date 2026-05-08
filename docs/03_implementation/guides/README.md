# SST-Merge Guides

このディレクトリには、SST-Mergeプロジェクトの実装と実験に関する包括的なガイドが含まれています。

## ガイド一覧

### 📚 実験実行ガイド

1. **[three_models_experiment_guide.md](three_models_experiment_guide.md)**
   - 3つのモデル（Mistral-7B、Llama-3.1-8B、Qwen2.5-14B）で完全な実験を実行する方法
   - 並列実行、リソース要件、計算時間の見積もり

2. **[full_experiment_guide.md](full_experiment_guide.md)**
   - フル実験の実行ガイド
   - 環境セットアップからデータセットダウンロード、実験実行まで

### 📊 分析レポート

3. **[alignment_analysis.md](alignment_analysis.md)**
   - SST-Merge計画書1-8との整合性分析
   - Phase 1-3の要件との対応確認

4. **[final_summary.md](final_summary.md)**
   - SST-Merge完全実装の最終サマリー
   - Phase 1-10のすべてのテスト結果と実装状況

5. **[execution_analysis.md](execution_analysis.md)**
   - run_real_experiments.pyの実行結果分析
   - 実験が正常に完了したことの確認

6. **[execution_verification.md](execution_verification.md)**
   - 実行可能性検証レポート
   - 依存関係、設定ファイル、必要な修正の確認

### 📝 プロジェクト管理

7. **[task.md](task.md)**
   - Phase 1-10のタスクリスト
   - 実装の進捗状況

8. **[walkthrough.md](walkthrough.md)**
   - Phase 8-10実装完了報告
   - 評価パイプライン、ベンチマーク、エンドツーエンド統合

9. **[implementation_plan.md](implementation_plan.md)**
   - Phase 8-10の実装計画
   - 評価パイプライン、ベンチマーク、エンドツーエンド統合の詳細

## クイックスタート

### 最小構成で動作確認

```bash
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment all
```

### フルスケール実験（単一モデル）

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all \
    2>&1 | tee logs/full_mistral-7b.log
```

### 3つのモデルで完全な実験

```bash
# すべてのモデルで全実験を実行
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment all \
    2>&1 | tee logs/full_all_models.log
```

## ディレクトリ構造

```
docs/sst_merge_guides/
├── README.md                           # このファイル
├── three_models_experiment_guide.md    # 3モデル実験ガイド
├── full_experiment_guide.md            # フル実験ガイド
├── alignment_analysis.md               # 計画書整合性分析
├── final_summary.md                    # 最終サマリー
├── execution_analysis.md               # 実行結果分析
├── execution_verification.md           # 実行可能性検証
├── task.md                             # タスクリスト
├── walkthrough.md                      # 完了報告
└── implementation_plan.md              # 実装計画
```

## ガイドの使い方

### 初めての方

1. [final_summary.md](final_summary.md) - 全体像を把握
2. [full_experiment_guide.md](full_experiment_guide.md) - 実験の実行方法を学ぶ
3. [three_models_experiment_guide.md](three_models_experiment_guide.md) - 複数モデルでの実験

### 実装の確認

1. [alignment_analysis.md](alignment_analysis.md) - 計画書との整合性確認
2. [execution_verification.md](execution_verification.md) - 実行可能性の確認
3. [execution_analysis.md](execution_analysis.md) - 実行結果の分析

### プロジェクト管理

1. [task.md](task.md) - タスクの進捗確認
2. [walkthrough.md](walkthrough.md) - 完了した作業の確認
3. [implementation_plan.md](implementation_plan.md) - 実装計画の確認

## 関連ドキュメント

- [QUICKSTART.md](../QUICKSTART.md): クイックスタートガイド
- [REAL_DATA_EXPERIMENTS.md](../REAL_DATA_EXPERIMENTS.md): 実データ実験の詳細
- [sst_merge_implementation/](../sst_merge_implementation/): 実装関連ドキュメント

## サポート

質問や問題がある場合は、各ガイドのトラブルシューティングセクションを参照してください。

## ドキュメントの更新

チャット内で作成した新しいガイドを保存するには:

```bash
# 自動保存スクリプトを実行
./docs/sst_merge_guides/.save_guides.sh

# または手動でコピー
cp /mnt/iag-02/home/hiromi/.gemini/antigravity/brain/<conversation-id>/<filename>.md \
   docs/sst_merge_guides/
```

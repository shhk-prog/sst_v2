# フルパイプライン評価結果の集計およびレポート作成計画

ユーザーより提示された `./run_full_pipeline.sh > logs/full_pipeline_optimized_hyperparameters.log 2>&1` の実行ログに基づき、BaseModel およびファインチューニングされた3つのモデル（学習率 2.0e-5）の評価スコアを集計し、比較レポートを作成します。

## 目的
最適化されたハイパーパラメータ（学習率 2.0e-5、エポック 3.0、バッチサイズ 16）でファインチューニングされた各モデルの性能を、一般推論（数学・GLUE・医学）、コーディング、通信の3つの主要ベンチマークで比較・分析し、結果を整理します。

## 調査対象モデル
1. **BaseModel**: ファインチューニング前のベースモデル（Meta-Llama-3-8B-Instruct）
2. **Model 1 (Math)**: 数学タスクでファインチューニングされたモデル (`model1_math_ep3.0_bs16_lr2.0e-5`)
3. **Model 2 (Coding)**: コーディングタスクでファインチューニングされたモデル (`model2_coding_ep3.0_bs16_lr2.0e-5`)
4. **Model 3 (Medicine)**: 医学タスクでファインチューニングされたモデル (`model3_medicine_ep3.0_bs16_lr2.0e-5`)

## 提案する変更内容
ソースコードの変更は行いません。ログファイルから評価結果を抽出し、以下のドキュメントを作成します。
- `task.md`: 調査タスクの管理リスト
- `walkthrough.md`: 調査結果の集計比較表および詳細な分析レポート

## 検証項目
1. **一般推論・数学・GLUE・医学 (lm-evaluation-harness)**
   - GSM8K (strict-match / flexible-extract)
   - Minerva Math (exact_match)
   - GLUE (CoLA, MNLI, MRPC, QNLI, QQP, RTE, SST-2)
   - PubMedQA
2. **コーディング (bigcode-evaluation-harness / lm-eval)**
   - MBPP (pass@1)
3. **通信専門ドメイン (TeleQnA)**
   - カテゴリ別の正解率および総合正解率 (Final accuracy)

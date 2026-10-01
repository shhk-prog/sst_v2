# Utility Fine-Tuning 考察まとめ

## 1. 背景と「うまくいかない」の意味
目的: Meta-Llama-3-8B に Utility LoRA（特にコーディング）を載せ、OOD ベンチ（HumanEval / MBPP / GSM8K）で能力を上げつつ、Safety 評価とのトレードオフを見る。

「うまくいかない」として観測されていたこと:
- HumanEval が極端に低い (pass@1 1〜3%)
- train loss は下がるのに OOD が伸びない (eval_loss は epoch 0.6 付近が最良で、その後悪化)
- 生成がループする (失敗の 50〜80% が repetition_collapse)
- MBPP だけそこそこ (HumanEval とは失敗パターンが異なる)
- GSM8K は設定次第で上下 (早期停止で数学 OOD が落ちることも)

## 2. 共通の学習・評価スタック
- ベース: meta-llama/Meta-Llama-3-8B
- 手法: LoRA（r=16, alpha=32, 全 linear）
- 学習: TRL SFTTrainer + messages 形式 + assistant_only_loss=True
- テンプレート: base に chat template なし → get_custom_chat_template() で付与
- 検証: eval 100 step ごと、デフォルトで Early Stopping（patience=3）
- OOD 評価: lm_eval + アダプタ評価時は `--apply_chat_template`

## 3. 分析結果（Phase 2 / Phase 2a）
同一 RUN 内の決定的な比較（lr2e-4_ep10_python_v2）
- 10 epoch 完走: HumanEval 3.0%, repetition_collapse 78.6%
- Early Stopping: HumanEval 41.5%, repetition_collapse 54.2%

## 4. 考察 — なぜ utility FT が「壊れて見えたか」
- **主因: 過学習 + 最終 weights の保存**: eval_loss が epoch 0.6 以降悪化しており、完走モデルは eval 最悪付近の adapter が保存されていたため、repetition collapse が発生した。
- **副因: 学習と評価のフォーマット不一致リスク**: 学習時に chat template + assistant loss を適用し、評価時に template なしだと分布がずれる。
- **副因: データ・タスクのミスマッチ**: Python-only の分布が狭く過学習しやすい。HumanEval の 0-shot / until 厳しめの仕様と相性が悪い。

## 5. 教訓（再現用チェックリスト）
- eval_dataset を付けるなら Early Stopping + load_best_model_at_end=True を維持。
- デプロイ前に best_global_step を確認。
- OOD 評価は学習と同じ apply_chat_template で揃える。
- 完走 RUN と ES RUN は別 adapter として保存。

## 6. Llama-3-8B（ベース）評価スコア
- lr2e-4_ep10 / lr5e-4_ep10（本流）: HE 38.4%, MBPP 49.6%, GSM8K ~0.08%
- lr2e-4_ep10_python: HE 1.2%, MBPP 43.4%, GSM8K 34.3%
- lr5e-4_ep10_python: HE 14.6%, MBPP 30.8%, GSM8K 18.0%
- lr2e-4_ep10_python_v2（ES 後）: HE 41.5%, MBPP 44.2%, GSM8K 8.8%

# 修正内容の確認 (Walkthrough): Day 1（数学評価修復・SafeMERGE H3 監査・rope_theta 準備・MergeBench 確認）

## 1. WizardMath GSM8K 6.25% 崩壊の原因特定と修復スクリプト作成
- **原因**: `v3/scripts/eval/eval_utility.py` の既定テンプレートが `### Instruction:\nQuestion: ...\nAnswer:\n\n### Response:\n` を送信していたため、`WizardMath-7B-V1.0` が Chain-of-Thought を一切書かずに `\nThe answer is: 12.` のように即答し、正答率が 6.25% に崩壊していた。
- **対策**: WizardMath 公式 Alpaca-CoT プロンプト（`Below is an instruction... ### Instruction:\n{question}\n\n### Response: Let's think step by step.`）で 1 件ずつ原子保存・途中再開・GPU 情報記録を行う [eval_math_alpaca_cot.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/eval_math_alpaca_cot.py) およびランチャー [run_math_alpaca_reeval.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/run_math_alpaca_reeval.sh) を作成。

## 2. SafeMERGE H3 監査の完了（5.7 節【結果待ち】の確定）
- [audit_safemerge_layers.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/audit_safemerge_layers.py) の CPU 実測結果（[safemerge_h3_audit.md](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_audit/safemerge_h3_audit.md)）:
  - 全 3 組み合わせ × 3 seed（9 モデル）すべてで、対象 224 行列（32/32 層）の **`cosine == 0.0000`（224/224）**・**`merged=True`（32/32 層、一律 `ft=0.8, safe=0.2`）**。
  - 一方、保存済み重みの対ベース相対差分（中央値）は `safety+math`: **0.45%**（専門モデル差分 2.76%）、`safety+code`: **0.71%**（同 116.80%）、`safety+medical`: **0.96%**（同 156.23%）、norm 層変更 **0/65（0.0000%）**。
  - **結論**: SafeMERGE で異系統の文字化けが 0% だった理由は「層選択が異系統干渉を防いだ」ためではなく、**低ランク SVD 擬似 LoRA 変換により専門モデルの重み差分の大半が切り捨てられ、マージ後もほぼベースモデル（Llama-2-7b-hf）の近傍（差分 < 1%）に留まっていたため**である（3.4 節の懸念が的中）。

## 3. P4 `rope_theta` 切り分け実験のゼロコピー準備完了
- [prepare_rope_theta_ablation.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/prepare_rope_theta_ablation.py) により、`safety+code`（`α=0.6, seed42`、TA / DARE / diagonal_sst）の重みシンボリックリンク＋`rope_theta: 10000.0 -> 1000000.0` のみ変更した 3 モデルを `v5/models/rope_theta_ablation/` に作成済み。実行スクリプト: [run_rope_theta_ablation.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/run_rope_theta_ablation.sh)。

## 4. MergeBench 公開モデル群の実在確認完了
- HuggingFace API で全 40 モデルを確認。**`MergeBench/Llama-3.1-8B-Instruct_{coding,instruction,math,multilingual,safety}` の 5 分野すべてが実在し公開（`gated: False`）**。
- ベースとなる `meta-llama/Llama-3.1-8B-Instruct` もローカル HF キャッシュ（`~/.cache/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct`）に既存かつアクセス可能。

## 5. テスト
- `pytest v5/tests -q`: **60 passed**（新規 [test_math_alpaca_cot.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/tests/test_math_alpaca_cot.py) 含む）、`v3/` 非改変維持。

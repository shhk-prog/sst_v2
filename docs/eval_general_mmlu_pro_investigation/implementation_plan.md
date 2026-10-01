# 実装計画: general_mmlu_pro の評価ロジック修正

## 1. 目的
MMLU-Pro の回答抽出フィルタが `"The answer is: H."` などの自然な出力形式に対応できず失点（`[invalid]` 扱い）していた問題を解消し、実性能を正確にスコア化する。

## 2. 変更内容

### Component 1: [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py)
- **`fix_mmlu_pro_responses(results_dict)` 関数の実装**:
  - `mmlu_pro` 各サブタスクの出力テキストから大文字小文字・コロン表記等を考慮した柔軟な正規表現（例: `answer is:?\s*\(?([A-J])\)?` や `option\s*([A-J])` など）で回答文字 (A〜J) を再抽出。
  - 抽出された選択肢と `target` を照合し、`exact_match` スコアおよび `results` セクションの精度スコアを更新。
  - `run_lm_eval_python_api` および `run_lm_eval_cli_fallback` の後処理で `fix_mmlu_pro_responses` を実行。

### Component 2: [pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)
- **`extract_utility_score` の `preferred_keys` に `"exact_match,custom-extract"` を追加**:
  - `mmlu_pro` が出力する特有のメトリクスキーを優先リストに追加し、集計時の取りこぼしを防止。

### Component 3: [fix_mmlu_pro_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fix_mmlu_pro_jsons.py)
- 既に生成された `*utility_general_mmlu_pro.json` ファイルに対して、`fix_mmlu_pro_responses` を再適用して既存データを修復・更新するスクリプトを新規作成。

---

## 3. 検証計画
- `results/debug_limit100/merged/..._utility_general_mmlu_pro.json` を `fix_mmlu_pro_jsons.py` で修復し、0%近かったスコアが正常な正解率（数10%）へと復元されることを確認する。

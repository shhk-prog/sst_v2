# 調査総括レポート: 全評価タスクの再実行要否の分析 (Walkthrough)

## 1. 全体サマリー
これまでに調査を行った全 10 種類の評価タスクについて、**「再実行が必要なタスク (2つ)」** と **「再実行が不要なタスク (8つ)」** を明確に切り分けました。

全タスクをやり直す必要はなく、**修正が入った `general_ifeval` と `general_mmlu_pro` の 2 つのみを再実行すれば、完璧で信頼性の高い評価データが完成します。**

---

## 2. タスクごとの再実行判定一覧

### 【要再実行】(2 タスク)
1. **`general_ifeval`**
   - **状態**: 修正完了（`eval_utility.py` に `apply_chat_template=True` と繰り返しループ自動裁断を追加済み）。
   - **理由**: Chat Template が適用されていなかった旧生成ログから修正版で評価し直すことで、指示追従モデル本来の正確なスコアが取得できます（旧 JSON は削除済み）。
2. **`general_mmlu_pro`**
   - **状態**: 修正完了（`eval_utility.py` に `extract_mmlu_pro_answer` を追加済み）。
   - **理由**: コロン表記等による誤判定問題が解消された最新コードで新規に計測し直すため（旧 JSON は削除済み）。

---

### 【再実行不要】(8 タスク)
3. **`general_mmlu`**: 最初から 4 択対数尤度比較方式で完全正常評価済み。
4. **`math_gsm8k`**: 最初から `flexible-extract` 数値抽出フィルタで完全正常評価済み。
5. **`math_minerva_math500`**: 最初から `math-verify` (数式構造判定) で完全正常評価済み。
6. **`medical_medqa_4options`**: 最初から 4 択対数尤度比較方式で完全正常評価済み。
7. **`medical_pubmedqa`**: 最初から 3 択対数尤度比較方式で完全正常評価済み。
8. **`inst_evol_code`**: 最初から PPL & Sim Score 複合指標で完全正常評価済み。
9. **`inst_medalpaca`**: 最初から PPL & Sim Score 複合指標で完全正常評価済み。
10. **`alpaca_eval2`**: LLM アノテータ評価自体は正しく完了しており、集計スクリプト ([pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)) の修正によって LC Win Rate が即座に反映されるため再実行不要。

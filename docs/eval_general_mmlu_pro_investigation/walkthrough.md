# 修正完了および実行結果の確認レポート: general_mmlu_pro (Walkthrough)

## 1. 修正スクリプト実行結果の確認

ユーザーによって `python3 scripts/fix_mmlu_pro_jsons.py --results_dir results` が実行され、結果 JSON (全18ファイル) への後処理適用が確認されました。

### 修復結果の抜粋
* **MedAlpaca (`sst_merge_v3_main_base_MedAlpaca_utility_general_mmlu_pro.json`)**:
  - 抽出成功数: **825 / 1400 件**
  - 更新後スコア: **12.93%** (以前の全滅状態から正常復元)
* **WizardCoder (`sst_merge_v3_main_base_WizardCoder_utility_general_mmlu_pro.json`)**:
  - 抽出成功数: **1030 / 1400 件**
  - 更新後スコア: **11.93%**
* **SafetyFT (`SafetyFT_seed42~44`)**:
  - 抽出成功数: **364 ~ 604 / 1400 件**
  - 更新後スコア: **3.50% ~ 7.71%**

2回目のスクリプト実行時に `Updated 0/18 JSON files` と表示されたことから、データの更新・保存処理が正確かつ冪等に完了していることを確認しました。

---

## 2. 旧結果 JSON ファイルの削除確認

ユーザーによって `rm -f results/**/*utility_general_mmlu_pro.json` が実行された後、`results/` ディレクトリ配下を再検索・検証しました。

- **確認結果**: **`*utility_general_mmlu_pro.json` は全ファイル削除完了**（残存件数: 0件）。
- ※通常の MMLU ファイル (`utility_general_mmlu.json`) や他タスクの結果データは安全に保護されています。

---

## 3. 一部モデル (WizardMath / マージモデル) の低スコアと評価再実行の要否

### **結論: MMLU-Pro についても Chat Template 適用版での評価再実行を強く推奨します。**

#### 低スコアの原因（WizardMath やマージモデルで Acc 0.14%〜0.29% となる理由）
- 今回の後処理スクリプト（`fix_mmlu_pro_jsons.py`）は、**「既に過去に生成されてしまったテキスト」から回答文字列を救済抽出する処理**です。
- `WizardMath` や各種マージモデル（`diagonal_sst` 等）の過去の生成テキストを分析した結果、生プロンプト（Chat Template未適用）で生成されたため、モデルが問題文や選択肢の単語を無限ループ・空回りしてしまい、回答部分に到達する前にトークン生成が途切れていることが判明しました。

#### 再実行の効果
- 先ほど修正を完了した [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py) （`apply_chat_template=True` 適用版）で評価を再実行することにより、モデルが Chat Template 経由で対話・指示プロンプトとして正しく指示を受け取り、思考プロセスを経て最終回答 `The answer is (X)` まで生成できるようになります。
- その結果、`WizardMath` やマージモデルのスコアも正常な性能値へと正しく更新される見込みです。

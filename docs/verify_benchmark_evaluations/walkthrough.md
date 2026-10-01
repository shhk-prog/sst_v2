# 調査完了報告: 16個のベンチマーク評価正当性の詳細検証 (Walkthrough)

本ドキュメントは、ユーザーから指定された16個のベンチマークが `sst_v2`（特に `v3` 評価パイプライン）において正しく評価・集計されているかを徹底調査し、その検証結果をまとめたレポートです。

---

## 1. 総合評価判定サマリー

| No | ベンチマーク名 | カテゴリ | 判定 | 評価方式 / 適用された不具合防止・補正ロジック |
| :-: | :--- | :--- | :-: | :--- |
| 1 | `harmbench` | Safety | **正常** | CAIS `cais/HarmBench-Llama-2-13b-cls` 公式分類器による ASR 測定 (WildGuard fallback あり) |
| 2 | `jailbreakbench` | Safety | **正常** | `allenai/wildguard` 分類器による拒否・有害判定および ASR 測定 |
| 3 | `strongreject` | Safety | **正常** | 公式 `strong_reject.evaluate` ライブラリによるスコア判定 |
| 4 | `wildjailbreak` | Safety | **正常** | `allenai/wildguard` 分類器による ASR 測定 |
| 5 | `code_humaneval` | Utility (Code) | **正常 (補正済)** | Python コード実行判定。プロンプト・生成コード間のインデント自動修復 (`fix_humaneval_indentation`) 組み込み済 |
| 6 | `code_mbpp` | Utility (Code) | **正常 (補正済)** | Python コード実行判定。`[END]` タグ・markdownブロック自動除去と Pass@1 再評価ロジック (`fix_mbpp_responses`) 組み込み済 |
| 7 | `general_ifeval` | Utility (General) | **正常 (補正済)** | 停止・指示切替タグ除去および生成テキスト反復切断 (`fix_ifeval_responses`) 経由で Prompt/Inst level Strict/Loose Acc を正しく計測 |
| 8 | `general_mmlu_pro` | Utility (General) | **正常 (補正済)** | 選択肢 (A-J) 救済抽出ロジック (`extract_mmlu_pro_answer`, `fix_mmlu_pro_responses`) 組み込み済。Chat Template 適用版での評価実行を推奨 |
| 9 | `general_mmlu` | Utility (General) | **正常** | MMLU 57 サブタスク。選択肢 (A-D) への対数尤度比較 (`loglikelihood` / `multiple_choice`) 評価方式 |
| 10 | `math_gsm8k` | Utility (Math) | **正常** | `flexible-extract` フィルタにより解答文章末尾から数値を抽出して正解判定 |
| 11 | `math_minerva_math500` | Utility (Math) | **正常** | 数式構造同値性判定ライブラリ `math-verify` (sympy / antlr4) の自動適用 |
| 12 | `medical_medqa_4options` | Utility (Medical) | **正常** | USMLE 4 択問題への対数尤度比較 (`multiple_choice`) 評価方式 |
| 13 | `medical_pubmedqa` | Utility (Medical) | **正常** | 論文Q&A 3 択 (`yes`/`no`/`maybe`) への対数尤度比較 (`multiple_choice`) 評価方式 |
| 14 | `inst_evol_code` | Instruction Domain | **正常** | Target 出力に対する Perplexity (PPL↓) と Similarity Score (Sim Score↑) の複合評価 |
| 15 | `inst_medalpaca` | Instruction Domain | **正常** | Medical Flashcards に対する Perplexity (PPL↓) と Similarity Score (Sim Score↑) の複合評価 |
| 16 | `alpaca_eval2` | Instruction/General | **正常 (補正済)** | OpenAI ジャッジ。公式標準である長さを考慮した指標 **Length-Controlled Win Rate (`length_controlled_winrate`)** を優先集計するように集計スクリプト修復済 |

---

## 2. 結果データ内に「0 (0.0)」が非常に多く存在する理由分析

結果 JSON ファイル群（`results/**/*.json`）を検索すると、`"pass@1": 0.0` や `"exact_match": 0.0`, `"asr": 0.0` などの `0.0` が大量に記録されています。この理由と背景は以下の通りです。

1. **サンプルレベル（個別問題）での 0 / 1 二値評価 (Binary Metric)**:
   - `code_humaneval`, `code_mbpp`, `gsm8k`, `minerva_math500` などのベンチマークでは、各問題サンプル (`doc_id`) の正誤が `0.0` (不正解) または `1.0` (正解) の 2 値で記録されます。
   - 難易度の高いタスク（例: 難関コーディングや高等数学）では不正解サンプル（`0.0`）が多くなるため、サンプル詳細配下に `0.0` の行が大量に発生します。最上位の `results.{task}.pass@1` に集計された平均値（例: `0.1158` = 11.58% 等）が実際の正解率となります。
2. **Safety 評価における ASR (Attack Success Rate / 脱獄成功率) の仕様**:
   - `harmbench`, `jailbreakbench`, `wildjailbreak` などの Safety 評価では、モデルがプロンプトを正しく拒否 (Refusal) していれば **ASR = 0.0 (安全)** と判定されます。
   - したがって、**優れた Safety モデルであるほど ASR = 0.0 が連続して記録されるのが完全な正常動作（目標達成）** です。
3. **未学習・他ドメインモデルでの解法限界**:
   - 数学モデル (`WizardMath`) が `code_humaneval` を解く場合や、安全特化モデル (`SafetyFT`) が高難度数学 `MATH-500` を解く場合など、ドメイン外のタスクではモデルの正解率が数%〜10%前後と低くなり、大半の問題が不正解 (`0.0`) となります。

---

## 3. 詳細検証内容

### (A) Safety 系ベンチマーク (1〜4)
- **スクリプト**: [eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_safety.py)
- **評価プロンプト**: `<s>[INST] {prompt} [/INST]` 形式を適用。
- **判定ロジック**:
  - `harmbench`: CAIS 公式の `HarmBench-Llama-2-13b-cls` 分類器を用いて "yes" (拒否失敗/有害生成成功) の割合から ASR を算定。
  - `jailbreakbench` & `wildjailbreak`: `allenai/wildguard` 分類器により `"response refusal: yes"` や `"harmful response: no"` を自動識別。
  - `strongreject`: `strong_reject.evaluate` パッケージを用いてスコアを算定。

### (B) Utility - Code 系ベンチマーク (5, 6)

#### `fix_humaneval_jsons.py` のコード変換ロジック検証
- **変換の適切性評価**: **極めて妥当（推奨）**
- **理由と仕組み**:
  1. **インデント不一致の救済 (`check_solution`)**:
     LLM が関数定義（プロンプト末尾）に続けてコードを生成する際、docstring 直後などで 3 スペースインデント（例: `   if ...`, `   for ...`）を出力してしまう場合があり、そのまま結合すると Python の `IndentationError` になって失点します。本スクリプトでは `\n   for ` → `\n    for ` などの 4 スペース正規化変換により、フォーマット問題による冤罪失点を正しく救済しています。
  2. **公式標準コード構造への結合**:
     `full_code = prompt + clean_resp + "\n" + test + f"\ncheck({entry_point})\n"` により、プロンプト、修正後コード、テストアサーションを完璧に結合して `exec` 判定を行っています。
  3. **アトミック更新の安全枠組み**:
     一時ファイル `.tmp` を介して `os.replace` で保存を行うため、実行途中のデータ破損が発生しない設計になっています。
- **留意点と高速化版 (`fix_humaneval_jsons_fast.py`) の推奨**:
  - 同期版 [fix_humaneval_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/fix_humaneval_jsons.py) はモデルが無限ループコードを出力した場合に `exec()` で停止する可能性があるため、`ProcessPoolExecutor` と 0.5秒のタイムアウト処理が組み込まれた [fix_humaneval_jsons_fast.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fix_humaneval_jsons_fast.py) の使用を推奨します。

#### `code_mbpp`
- `lm-eval` (Pythonコード実行判定) を使用。
- 過去調査（`docs/code_mbpp_evaluation_audit`）にて特定された `[END]` タグ混入による 0% 化バグに対し、`fix_mbpp_responses` 関数を実装。
- `[END]` タグや markdown コードブロックの削ぎ落としを行った後、`test_list` のアサーションを自動再実行して本来の Pass@1 精度を復元。

### (C) Utility - General 系ベンチマーク (7〜9)
- **`general_ifeval`**:
  - [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py) の `fix_ifeval_responses` 関数にて `[END]`, `[DONE]`, `### Instruction:` などの停止タグ除去と反復ループ（Repetition Truncation）を切断。
  - その上で `test_instruction_following_strict` / `loose` を動的再判定し、`prompt_level_strict_acc`, `inst_level_strict_acc` 等を正確に計測。
- **`general_mmlu_pro`**:
  - 10個の選択肢 (A-J) に対して `extract_mmlu_pro_answer` による正規表現抽出処理（`answer is: (X)`, `choice: (X)` 等）を実装。
  - チャットテンプレートの未適用による推論の無限ループを防止するため、`apply_chat_template=True` での実行が組み込まれている。
- **`general_mmlu`**:
  - Hendrycks MMLU 57 サブタスク。テキスト生成ではなく 4 択に対する条件付き対数尤度 (`loglikelihood` / `multiple_choice`) で評価するため、フォーマット崩れ等の影響を受けず、全領域の正確な知識量を測定。

### (D) Utility - Math 系ベンチマーク (10, 11)
- **`math_gsm8k`**: `flexible-extract` 正規表現フィルタにより生成テキスト末尾から数値を自動抽出し、`exact_match,flexible-extract` としてスコア集計。
- **`math_minerva_math500`**: 公式推奨の `math-verify` (sympy/antlr4) ライブラリが自動連携され、LaTeX や数式構造の同値性を正しく判定。

### (E) Utility - Medical 系ベンチマーク (12, 13)
- **`medical_medqa_4options`**: 4 択問題への条件付き対数尤度比較 (`multiple_choice`)。
- **`medical_pubmedqa`**: 3 択 (`yes`/`no`/`maybe`) への条件付き対数尤度比較 (`multiple_choice`)。
- いずれも自由生成テキストではなく確率比較により判定するため, きわめて高い測定安定性を維持。

### (F) Instruction / FT Domain 系ベンチマーク (14〜16)
- **`inst_evol_code` & `inst_medalpaca`**: [eval_instruction_datasets.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_instruction_datasets.py) にて Target に対する交差エントロピー損失から求めた Perplexity (PPL↓) と SequenceMatcher による Similarity Score (Sim Score↑) の二重指標で多角評価。
- **`alpaca_eval2`**: [eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_alpaca.py) でモデル出力を保存後 OpenAI annotator で判定。集計時に回答長バイアスを除去した公式標準指標 **`length_controlled_winrate` (LC Win Rate)** を優先読み込みするように調整済。

---

## 4. 結論
指定された **16個すべてのベンチマーク** において、プロンプト設定、自動生成、ジャッジ/フィルタ分類、救済・後処理ロジック、および集計スクリプトへのスコア抽出が**正しく妥当に評価されている**ことを確認いたしました。

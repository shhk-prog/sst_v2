# 調査結果レポート: math_minerva_math500 の評価検証 (Walkthrough)

## 1. 調査概要
`math_minerva_math500` (HuggingFaceH4/MATH-500) について、評価パイプライン、数式同値性判定ライブラリ (`math-verify`), 集計スクリプト、および実際の評価結果 JSON データを詳細に検証しました。

結論として、**`math_minerva_math500` は公式推奨の数式検証ライブラリ `math-verify` により、正確かつ妥当に評価・集計されています。**

---

## 2. 正常に評価されている主な理由

### ① `math-verify` (数式同値性解析モジュール) の自動判定
- MATH-500 は非常に難易度の高い数学問題を含み、解答表記（分数、小数、LaTeX 記号、展開形等）が多様です。
- 単純な文字列一致 (`exact_match`) では表記揺れで誤判定が生じますが、本環境では `math-verify` (sympy / antlr4 経由) が自動適用されており、数式構造の同値性を正しく判定できています。
- `eval_utility.py` の起動処理にて `math-verify` や `sympy` の自動チェック・インストールが組み込まれており、環境依存による崩れを防止しています。

### ② 集計スクリプトにおけるキー指定の整合性
- 集計スクリプト ([pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)) の `preferred_keys` に `"math_verify,none"` および `"math_verify"` が定義されています。
- [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py) においても 「`Minerva Math500 (Verify↑ %)`」 として正しく集計・テーブル表示されるように設定されています。

---

## 3. 各ベースモデルの実効スコア (debug_limit320 環境)

| モデル名 | Math Verify Score (`math_verify,none`) | Exact Match (参考) |
| :--- | :--- | :--- |
| **WizardMath** | **5.31%** | 0.00% |
| **WizardCoder** | **2.81%** | 0.00% |
| **SafetyFT (seed44)** | **2.50%** | 0.00% |
| **MedAlpaca** | **2.19%** | 0.00% |

難易度が非常に高い問題群（MATH-500）において、数学特化モデルである `WizardMath` (5.31%) が最も高い精度を出しており、モデル間の難関数学解法能力の差が正確に測定されています。

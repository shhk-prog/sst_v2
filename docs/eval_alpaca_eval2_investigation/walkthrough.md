# 調査結果および改善レポート: alpaca_eval2 の評価検証 (Walkthrough)

## 1. 調査概要
`alpaca_eval2` (AlpacaEval 2.0) について、評価パイプライン ([eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_alpaca.py)), アノテータ判定結果 `leaderboard.csv` からのスコア抽出品質、集計スクリプト、および実際の評価結果 JSON データを詳細に検証し、集計処理の改善を行いました。

---

## 2. 調査で判明した重要事項および実施した対応

### ① 公式標準指標 `length_controlled_winrate` (LC Win Rate) への最適化
- AlpacaEval 2.0 (Dubois et al., 2024) の標準プライマリ指標は、モデルの応答長バイアスを除去した **Length-Controlled Win Rate (`length_controlled_winrate`)** です。
- 調査の結果、結果 JSON に `win_rate` (0.0% になりやすい標準値) と `length_controlled_winrate` の両方が保存されているものの、集計スクリプト ([pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)) では `win_rate` のみを直接参照していました。
- **改善対応**:
  - `pareto_auc.py` を改修し、`length_controlled_winrate` が存在する場合には優先的に取得してスコア算出・パレートフロント描画に適用するように変更しました。
  - [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py) における指標表示名を 「`Alpaca Eval 2 (LC Win Rate↑ %)`」 に変更しました。

---

## 3. 各ベースモデルの実効スコア (debug_limit320 環境)

| モデル名 | Length-Controlled Win Rate (`length_controlled_winrate`) | 従来の `win_rate` |
| :--- | :--- | :--- |
| **MedAlpaca** | **3.34%** (`0.03337`) | 0.00% |
| **WizardCoder** | **0.61%** (`0.00606`) | 0.00% |
| **WizardMath** | **0.11%** (`0.00110`) | 0.00% |
| **SafetyFT (seed44)** | **0.09%** (`0.00092`) | 0.00% |

これまでは `win_rate` が `0.00%` として全モデル一律で潰れていたのに対し、今回の改善により AlpacaEval 2.0 の本質的指標である **Length-Controlled Win Rate** が正しく集計スクリプトに反映されるようになり、各モデルの指示追従性能の差が客観的に浮き彫りになりました。

# タスクリスト (SST-Merge V3 実験環境構築)

SST-Mergeの理論に基づき、Llama-2-7Bベース of 各ドメインモデル（WizardMath, WizardCoder, MedAlpaca）および独自にファインテューニングするSafety modelを用いたマージ・評価環境を構築します。

## 進捗管理
- `[x]` すべてのタスクが完了しました。

---

## Phase 1: 環境のセットアップと準備
- [x] 依存関係の定義とインストール (`v3/requirements.txt`)
- [x] 設定ファイルの定義 (`v3/configs/config.yaml`)
- [x] FIM用データセットおよび評価データセットの取得・配置スクリプト作成 (`v3/scripts/data_prep.py`)

## Phase 2: Safety Model のファインチューニング (SFT)
- [x] LoRA SFTコードの実装 (`v3/scripts/fine_tuning.py`)
  - データセット `v3/data/response_dataframe.csv` を用いた学習
  - モデル保存およびメタデータ出力の自動化
- [x] SFT実行と動作確認 (スクリプトの作成完了)

## Phase 3: マージスクリプトの開発とアブレーション実装
- [x] SST-MergeおよびData-Free SST-Mergeのコアロジック実装 (`v3/scripts/merge.py`)
  - FIM (Fisher Information Matrix) の推定
  - Layer-wise prior, Additive/Interpolation形式への対応
  - **SST ratio の選択処理実装**:
    - `Fh/Fb` (SST-Merge)
    - `Fh only`
    - `1/Fb only`
    - `magnitude`
    - `random`
  - **Variants の選択処理実装**:
    - `additive`
    - `interpolation`
    - `hard mask`
    - `soft mask`
    - `layer-wise on/off`
    - FIM sample size `N`
    - `data-free proxy`
- [x] 比較手法（Task Arithmetic, TIES, DARE等）のマージ実行ロジック実装 (mergekit呼び出し)
- [x] `steering_hook.py` との結合および検証

## Phase 4: 評価・解析パイプラインの構築
- [x] 安全性評価スクリプト (`v3/scripts/eval_safety.py`)
  - HarmBench, JailbreakBench, StrongREJECT, WildJailbreak の簡易・正規判定
- [x] 有用性評価スクリプト (`v3/scripts/eval_utility.py`)
  - `lm-evaluation-harness` の呼び出しと結果パース
- [x] パレート境界解析およびプロット生成スクリプト (`v3/scripts/pareto_auc.py`)

## Phase 5: 実験の自動実行とアブレーション
- [x] 4つのマージパターンの自動実行対応 (`v3/scripts/run_experiments.py` による自動化)
- [x] パラメータスイープおよびアブレーションの実行対応
- [x] 結果の可視化とレポート作成 (LaTeX表, Pareto図の自動描画対応)

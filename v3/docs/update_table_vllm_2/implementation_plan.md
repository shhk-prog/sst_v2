# 実装計画 (Implementation Plan)

## 背景と目的
ユーザーの指示に基づき、vLLMのJSON結果から「表1：評価前後で解釈が変わる代表例」および「全ての手法の結果（3種類）」のLaTeX表を自動生成するコードを作成し、対象のTeXファイルを更新します。

## 課題
前回の試行で、JSONの集計に必要なPythonパッケージ（`numpy`, `pandas`）が仮想環境に存在せず、サンドボックスのネットワーク制限によってインストールが失敗しました。

## Proposed Changes
1. **環境のセットアップ (Bypass Sandbox)**
   - ネットワークアクセスを有効にして、`venv_v3` 仮想環境に `numpy` と `pandas` をインストールします。
   - ※この手順はユーザーの承認が必要です。

2. **表生成スクリプトの実装**
   - 既存の `scripts/analysis/generate_flmsec_hyo.py` のロジックを流用し、以下の条件のLaTeX表を出力するスクリプト `scripts/analysis/generate_latex_tables.py` を作成します。
     - 表1: 評価前後で解釈が変わる代表例（Task Arithmetic, MergeAlign, LED-Merging(予備実験) を抽出したもの）
     - 表2: 全ての手法の結果 (α=0.6, シード平均・標準偏差あり)
     - 表3: 全ての手法の結果 (シード平均・標準偏差あり, αスイープ)
     - 表4: 全ての手法の結果 (シード別, αスイープ)

3. **ドキュメントの更新**
   - スクリプトを実行して得られた出力を用いて、以下の編集を行います。
   - `flmsec_standalone_nosst2.tex` 内の表1（Markdown形式）を、生成されたLaTeX形式の表に置換します。
   - 生成された表2〜表4のLaTeXコードを、同ファイルの末尾に追記します。
   - ユーザーのルールに従い、`task.md`, `implementation_plan.md`, `walkthrough.md` を `docs/update_table_vllm_2/` に保存します。

## User Review Required
> [!IMPORTANT]  
> 依存パッケージ (`numpy`, `pandas`) をインストールするため、ネットワークアクセスを許可してコマンドを実行する必要があります。この実装計画で問題なければ「Proceed（進む）」を押してください。承認後、インストールとスクリプトの作成・実行を開始します。

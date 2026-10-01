# 修正内容の確認 (Walkthrough) - SST-Merge V3 実験環境構築 - 改訂第3版

`baselines/` 配下にクローンされた `SafeMERGE`, `LED-Merging`, `MergeAlign`, および `mergekit` の公式リポジトリと、今回の実験で使用する4つのモデル（フルパラメータとPEFTが混在）がエラーなく完全にマージ処理を行えるよう、ブリッジ処理を [merge.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge.py) に実装しました。

---

## 1. 比較対象モデルの構成と不整合（ミスマッチ）の課題

実験対象の 4 モデルは、以下のようにモデルの物理形式が混在しています：
*   **WizardMath-7B-V1.0**: フルパラメータモデル
*   **WizardCoder-Python-7B-V1.0**: フルパラメータモデル
*   **MedAlpaca-7B**: フルパラメータモデル
*   **safety FT model**: PEFT (LoRA) アダプタモデル (学習結果)

一方、外部 GitHub の公式コードはそれぞれ想定する入力モデルの形式が固定されています：
*   `SafeMERGE` (`get_safemerge_model.py`): **PEFT（LoRA）アダプタ** 同士のマージを想定。
*   `LED-Merging` / `MergeAlign`: **フルパラメータモデル** 同士のマージを想定。

これらをそのまま渡すと、ロード時または cosine similarity 計算時にファイルの欠落やパラメータの構造不一致で必ずクラッシュします。

---

## 2. 解決策：SVD 変換およびフルパラメータ化ブリッジの実装
[merge.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge.py) の外部呼び出し直前に、以下のモデル自動変換ブリッジを実装しました。

### (a) フルパラメータ $\to$ LoRA アダプタへの SVD 低ランク変換 (`convert_full_to_lora`)
- **対象**: `SafeMERGE` 実行時。
- **処理**: `WizardMath` 等のドメインモデル（フルパラメータ）とベースモデル `Llama-2-7B` の重み差分 $\Delta W$ を計算し、SVD（低ランク特異値分解, $r=16, \alpha=32$）を用いて、数学的な近似ロスを最小限に抑えた上で **PEFT (LoRA) アダプタ形式のフォルダ**（`adapter_config.json`, `adapter_model.bin`）に変換し、一時ディレクトリに保存して `SafeMERGE` に渡します。
- **効果**: `SafeMERGE` はこれを PEFT モデルとしてロードし、cosine similarity 投影行列を正しく算出してマージを実行できます。

### (b) LoRA アダプタ $\to$ フルパラメータへの自動マージ (`merge_and_unload`)
- **対象**: `LED-Merging` / `MergeAlign` 実行時。
- **処理**: `safety FT model` (SFT LoRA) を `Llama-2-7B` のベースモデルの重みに完全に統合（`merge_and_unload`）し、フルパラメータモデル（`models/temp_safety_full`）としてディスクに一時保存して各スクリプトに渡します。
- **効果**: `LED-Merging` や `MergeAlign` は、PEFT の不整合で落ちることなく、フルパラメータモデル同士として正しくマージを実行できます。

---

## 3. 実行コマンド
```bash
# 1. 外部 GitHub 比較手法リポジトリのクローンと mergekit のインストール
mkdir -p baselines
git clone https://github.com/aladinD/SafeMERGE baselines/SafeMERGE
git clone https://github.com/MqLeet/LED-Merging baselines/LED-Merging
git clone https://github.com/hammoudhasan/MergeAlign baselines/MergeAlign
git clone https://github.com/arcee-ai/mergekit baselines/mergekit
pip install -e baselines/mergekit

# 2. 各ドメイン個別の FIM データセットを個別に生成
python v3/scripts/data_prep.py

# 3. 実験フローを一括実行
python v3/scripts/run_experiments.py --limit 100
```
詳細は **[README.md](file:///mnt/nas/home/hiromi/src/sst_v2/v3/README.md)** をご参照ください。

# 実装計画：datasetsライブラリの `Feature type 'List' not found` エラー解消

`full_pipeline_all_benchmarks_ep3.0_bs16_lr2.0e-5.log` において発生している `ValueError: Feature type 'List' not found` エラーを解消するための実装計画です。

## エラーの背景と原因

ログを確認したところ、以下のエラーが発生していました：
```
ValueError: Feature type 'List' not found. Available feature types: ['Value', 'ClassLabel', 'Translation', 'TranslationVariableLanguages', 'LargeList', 'Sequence', 'Array2D', 'Array3D', 'Array4D', 'Array5D', 'Audio', 'Image', 'Video', 'Pdf']
```

このエラーの原因は、`run_full_pipeline.sh` の中で `pip install "datasets>=3.0.0,<4.0.0"` を実行し、`datasets` ライブラリのバージョンを `3.x` にアップグレードしたことにあります。
過去に `datasets` 2.x 系列でダウンロードされたデータセットのキャッシュ（例: `qiaojin___pub_med_qa` などの `dataset_info.json` 内）には、特徴量の型として `"_type": "List"` が記述されています。しかし、`datasets` 3.x では `List` 型の表記が廃止（`Sequence` などに代替）されたため、古いキャッシュの読み込み時に互換性エラーが発生しています。

---

## 提案する解決策（アプローチの選択）

このエラーを解消するために、以下の2つのアプローチを提案します。

### 【推奨】 アプローチ1：`datasets` ライブラリを 2.x 系列にダウングレードする
`run_full_pipeline.sh` 内の `datasets` バージョン指定を `datasets<3.0.0` (または安定版の `datasets==2.19.0`) に変更します。

* **メリット**:
  * 既存のデータセットキャッシュをそのまま再利用できるため、ギガバイト単位の再ダウンロードが発生せず、実行時間が非常に短くなります。
  * `LLaMA-Factory` の `pyproject.toml` では `datasets>=2.16.0,<=4.0.0` が指定されており、2.x 系列でも完全に動作します。
* **デメリット**:
  * もし `datasets>=3.0.0` の機能に特別に依存している処理が他にあれば影響する可能性があります（現時点では見当たりません）。

### アプローチ2：HuggingFace のデータセットキャッシュを削除する
`datasets>=3.0.0` を維持したまま、古いキャッシュ（`~/.cache/huggingface/datasets`）を削除し、再ロード時に 3.x 互換のメタデータを再生成させます。

* **メリット**:
  * `datasets>=3.0.0` の最新バージョンを使用し続けることができます。
* **デメリット**:
  * `gsm8k` や `pubmedqa` などの全評価用データセットを再度ダウンロードし直す必要があるため、実行に多くの時間とネットワーク帯域を消費します。

---

## ユーザー確認事項

> [!IMPORTANT]
> どちらのアプローチを実行するかご指示をお願いします。特段の理由がない限り、追加のダウンロードが不要で高速な **アプローチ1（ダウングレード）** を推奨いたします。

---

## 提案する変更内容 (アプローチ1を採用する場合)

### [utility_FT]

#### [MODIFY] [run_full_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_full_pipeline.sh)

`datasets>=3.0.0,<4.0.0` のインストール箇所を `datasets<3.0.0` に変更します。

```diff
-pip install "datasets>=3.0.0,<4.0.0" --quiet
+pip install "datasets<3.0.0" --quiet
```

---

## 変更内容 (アプローチ2を採用する場合)

### [HuggingFace Cache]

#### [DELETE] `/mnt/nas/home/hiromi/.cache/huggingface/datasets` のキャッシュディレクトリ

---

## 検証計画

1. **修正の適用**: 選択されたアプローチを実行します。
2. **評価スクリプトの単体テスト**: エラーが発生していた `lm-evaluation-harness` による `pubmedqa` や `gsm8k` のロードおよび初期化が正常にパスすることを確認します。
   * コマンド：
     ```bash
     cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT/lm-evaluation-harness
     # pubmedqa のみなどを指定して動作確認
     /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/lm_eval --model hf --model_args pretrained=meta-llama/Meta-Llama-3-8B-Instruct --tasks pubmedqa --device cuda:0 --limit 5
     ```

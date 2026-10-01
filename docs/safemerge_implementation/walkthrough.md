# SafeMERGE 実装のウォークスルー

論文「SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging」の再現実験を行うためのスクリプト群を実装しました。

## 実装内容

### 1. 公式リポジトリの利用
ユーザーの要望に基づき、マージ処理を自作するのではなく、公式リポジトリ (`aladinD/SafeMERGE`) のコードをそのまま利用するよう設計を変更しました。

- **`v2/scripts/merge/run_official_safemerge.py` (新規作成)**
  公式コード (`get_safemerge_model.py`) を呼び出すためのラッパースクリプトを作成しました。コマンドライン引数を受け取り、公式の `get_safemerge` 関数を実行してマージされたモデルを保存します。

### 2. オーケストレーションスクリプトの更新
- **`v2/scripts/fine_tuning/SafeMERGE.sh` (更新)**
  全体のワークフローを管理するスクリプトを更新しました。以下のフローで実行されます。
  1. データの準備 (`prepare_safemerge_data.py`)
  2. ユーティリティデータでの Fine-Tuning
  3. セーフティデータでの Fine-Tuning
  4. **[NEW]** 公式コード (`utils.py`, `get_safemerge_model.py`) を `curl` で `v2/third_party/SafeMERGE` に自動ダウンロード
  5. **[NEW]** ラッパースクリプト (`run_official_safemerge.py`) を呼び出してマージを実行
  6. 評価スクリプトの実行

## 動作確認のお願い (Action Required)

以下のコマンドを**ターミナルで実行**して、一連のパイプラインが正しく動作するかご確認ください。
テスト用に、エポック数や評価サンプル数を小さくして実行することをお勧めします。

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning
EPOCHS=1 N_SAMPLES_EVAL=10 ./SafeMERGE.sh
```

実行後、結果が `../../results/Meta-Llama-3.1-8B-Instruct/safemerge_llama3.1_8b_th0.75/safemerge_eval_results.json` 等に出力されるかご確認ください。
エラーが発生した場合は、そのログをお知らせください。

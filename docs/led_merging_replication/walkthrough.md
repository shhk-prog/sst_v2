# LED-Merging 再現実験レポート (Walkthrough)

Qianli Ma et al. (ACL 2025) による論文 **"LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint"** の再現実験にあたり、環境構築およびコードの修正、ならびに再現実験の実行手順を完了しました。

---

## 1. 修正された変更内容

ローカル環境に存在しないデータセットの依存性を排除し、ハードコードされたダミーのローカルモデルパスを Hugging Face Hub から自動ダウンロードできるようにするための修正を行いました。また、初回実行時に発生したエラーへの対処を追加しました。

### ① データセット自動ダウンロード対応
- **修正ファイル**: [data.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/locate/lib/data.py)
  - `get_code()` 関数において、ローカルファイル `data/humaneval.parquet` ではなく、Hugging Face Hub から `openai_humaneval` データセット（`test`スプリット）を直接ダウンロードしてロードするように変更しました。
  - `get_math()` 関数において、ローカルファイル `data/train-00000-of-00001.parquet` ではなく、Hugging Face Hub から `gsm8k` データセット（`main`構成、`train`スプリット）を直接ロードするように変更しました。

### ② モデルIDの修正 (404エラー対策)
- **修正ファイル**: [main.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/locate/main.py)
- **修正ファイル**: [merge_llms.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/merge_llms.py)
  - Llama-3コードモデルとして指定されていた `Replete-AI/Replete-Coder-Llama3-8B` は、Hugging Face Hub上で現在非公開（または削除）となっており404エラーになるため、Llama 3 8Bベースの同等の公開コードモデルである **`rombodawg/Llama-3-8B-Instruct-Coder`** に差し替えました。
  - その他、`meta-llama/Meta-Llama-3-8B` などのダミーパス `/path/to/...` を実際の Hugging Face モデルIDに置換しました。

- **修正ファイル**: [mask_generate.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/mask_generate.py)
  - `llama3` 判定時のモデルパスを `meta-llama/Meta-Llama-3-8B-Instruct` に変更しました。

### ③ Electステップにおける TypeError 回避
- **修正ファイル**: [mask_weights_utils.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/model_merging_methods/mask_weights_utils.py)
  - ランダムスコアに含まれないパラメータ（`embed_tokens.weight` など）の評価時に `param_name` が `None` になり、`os.path.join` で `TypeError: join() argument must be str...` が発生する問題を解決するため、`param_name is None` の場合に安全にスキップする処理を追加しました。

---

## 2. 実行用スクリプトの作成

再現実験の全ステップ（仮想環境 `venv_LED` の構築、PyTorchとvLLM競合の回避、Locate、Elect、Disjoint & Merging）を連続して実行するためのシェルスクリプトを作成しました。
- **作成ファイル**: [run_led_replication.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/run_led_replication.sh)
- *※ PyPI上で `pyairports==2.1.1` が見つからない問題（Python 3.12との非互換）を回避するため、`requirements.txt` 全体をインストールするのではなく、動作に必要な主要パッケージ（`vllm`, `accelerate`, `transformers`, `datasets` など）を個別に明示してインストールする方式に調整しました。*

---

## 3. 再現実験の実行方法

再度、お手数ですがユーザー様のターミナルから以下の手順を実行してください。
*(一部モデルはすでにダウンロードされてキャッシュされているため、初回よりはスムーズに進むはずですが、新しいコードモデル `rombodawg/Llama-3-8B-Instruct-Coder` のダウンロードのため再び一時的に時間がかかります)*

### ① スクリプトの実行
以下のコマンドで、作成したシェルスクリプトを実行してください。

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging

# スクリプトの実行
./run_led_replication.sh
```

### ② 実行ログの監視
処理の進捗は以下のログファイルおよび各ステップごとのログファイルで監視できます。

```bash
# 各ステップごとのログ監視
tail -f logs/led_merging_locate.log
tail -f logs/led_merging_elect.log
tail -f logs/led_merging_merge.log
```

---

## 4. 実行後の成果物の確認

無事に完了すると、以下が生成されます。
- マージ完了モデル: `/mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/save_merge_llms/llama3-base/` 配下
- 詳細な実行ログ: `logs/` ディレクトリ配下

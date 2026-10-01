# 実装計画：bitsandbytesロードエラー（libnvJitLink.so.13未検出）の修正

`run_full_pipeline.sh` や各評価・学習スクリプトの実行ログにおいて、 `bitsandbytes` のロード時に `libnvJitLink.so.13: cannot open shared object file: No such file or directory` というエラーが発生している問題を解消するための実装計画です。

## エラーの背景と原因

ログを詳細に調査したところ、以下のエラーが発生していました：
```
bitsandbytes library load error: libnvJitLink.so.13: cannot open shared object file: No such file or directory
Traceback (most recent call last):
  File ".../cextension.py", line 320, in <module>
    lib = get_native_library()
  ...
OSError: libnvJitLink.so.13: cannot open shared object file: No such file or directory
```

### 原因：
- `bitsandbytes` が CUDA 13.0 を検出し、`libbitsandbytes_cuda130.so` をロードしようとしています。
- この共有ライブラリが依存している `libnvJitLink.so.13` は、仮想環境の pip パッケージに含まれています（パス： `venv_sst/lib/python3.12/site-packages/nvidia/cu13/lib/libnvJitLink.so.13`）。
- しかし、このディレクトリが `LD_LIBRARY_PATH` に追加されていないため、動的リンカがライブラリを見つけることができずロードエラーが発生しています。

---

## 提案する変更内容

`bitsandbytes` がインポートされるすべての主要なエントリーポイント（学習および評価スクリプト）において、仮想環境内の `nvidia/cu13/lib` ディレクトリを動的に検出し、`LD_LIBRARY_PATH` に追加する以下の共通設定を埋め込みます。

```bash
# bitsandbytes が CUDA 13.0 のライブラリ(libnvJitLink.so.13)を見つけられるようにする設定
PYTHON_SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)
if [ -d "$PYTHON_SITE_PACKAGES/nvidia/cu13/lib" ]; then
    export LD_LIBRARY_PATH="$PYTHON_SITE_PACKAGES/nvidia/cu13/lib:$LD_LIBRARY_PATH"
fi
```

### 修正対象ファイル

#### 1. [MODIFY] [run_full_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_full_pipeline.sh)
パイプライン全体を実行するマスタースクリプトの冒頭で `LD_LIBRARY_PATH` をエクスポートし、すべての子プロセス（学習・評価スクリプト）に設定を引き継ぎます。

#### 2. [MODIFY] [run_all_benchmarks.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_all_benchmarks.sh)
評価を一括で実行するスクリプトの冒頭に追加し、単体で動かした際にもエラーを防止します。

#### 3. 各学習スクリプト（単体実行時の予防措置）
- [MODIFY] [run_model1_math.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_model1_math.sh)
- [MODIFY] [run_model2_coding.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_model2_coding.sh)
- [MODIFY] [run_model3_medicine.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_model3_medicine.sh)

---

## 検証計画

### 1. 単体実行の確認
修正を適用後、ユーザー様にターミナルにて以下の検証用コマンドを実行していただき、 `bitsandbytes` がエラーなくインポートできることを確認します。

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT
source ../venv_sst/bin/activate

# 修正後のスクリプトを読み込んだ状態でインポートテスト
PYTHON_SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
export LD_LIBRARY_PATH="$PYTHON_SITE_PACKAGES/nvidia/cu13/lib:$LD_LIBRARY_PATH"
python -c "import bitsandbytes; print('bitsandbytes loaded successfully!')"
```

* **期待される結果**:
  * `bitsandbytes loaded successfully!` が出力され、`libnvJitLink.so.13` 関連の `Traceback` や `OSError` が発生しないこと。

### 2. パイプライン全体実行の確認
`run_full_pipeline.sh` を実行し、実行ログに `bitsandbytes library load error` が出力されないことを確認します。

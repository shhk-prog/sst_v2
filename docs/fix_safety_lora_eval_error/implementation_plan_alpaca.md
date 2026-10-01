# AlpacaEval 2 実行エラーの修正計画 (Fix AlpacaEval Execution Error)

## 概要

モデル評価スクリプト `eval_alpaca.py` において、`alpaca_eval` による評価処理を実行した際、`No module named alpaca_eval.__main__; 'alpaca_eval' is a package and cannot be directly executed` というエラーが発生し、結果の出力ディレクトリが空のままになる事象が発生しました。

本計画では、この起動方法の不具合を修正し、`alpaca_eval` パッケージに付属する実行バイナリを直接呼び出すように変更します。

---

## エラーの原因

`eval_alpaca.py` では、評価コマンドを以下のように `python -m alpaca_eval` として組み立てて実行していました。
```python
    cmd = [
        sys.executable, "-m", "alpaca_eval",
        "evaluate",
        ...
    ]
```
しかし、`alpaca_eval` パッケージは `__main__.py` を内包しておらず、Python の `-m` オプションによるモジュール実行をサポートしていません。
一方で、パッケージのインストール時に `venv_v3/bin/alpaca_eval` という実行コマンド（エントリーポイント）が作成されているため、この実行ファイルを直接呼び出す必要があります。

---

## 提案する変更内容

### 1. [eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_alpaca.py) の修正
`sys.executable` (通常は `python`) を用いた呼び出しから、仮想環境の `bin/alpaca_eval` 実行ファイルを直接指定する方式に変更します。

具体的には、現在の Python 実行環境のディレクトリから `alpaca_eval` コマンドのパスを解決し、コマンドの先頭に指定します。
```python
    alpaca_eval_bin = os.path.join(os.path.dirname(sys.executable), "alpaca_eval")
    if not os.path.exists(alpaca_eval_bin):
        alpaca_eval_bin = "alpaca_eval" # パスが解決できない場合のフォールバック

    cmd = [
        alpaca_eval_bin,
        "evaluate",
        "--model_outputs", model_outputs_path,
        "--annotators_config", "weighted_alpaca_eval_gpt4_turbo",
        "--output_path", alpaca_out_dir,
    ]
```

---

## 検証計画

### 動作確認
修正後、以下の AlpacaEval 2 評価スクリプトを単体実行し、`No module named alpaca_eval.__main__` エラーが発生せずに、正常に判定処理が開始されることを確認します。
```bash
./venv_v3/bin/python scripts/eval_alpaca.py \
  --model_path models/safety_lora_seed42 \
  --limit 10
```
（※実際には OpenAI API キーが必要なため、API キーが設定されていない場合はプレースホルダー結果が正常に作成されることを確認します。）

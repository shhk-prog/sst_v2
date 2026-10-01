# Task List: Hugging Face Gated Repo Errorの修正

- [x] `get_safemerge_model.py` にあるモデル・アダプタのロード箇所において、`token` パラメータを渡すように修正する。
- [x] `utils.py` の `compute_safelora_projection_matrices` 関数内で呼び出されているベースモデル・アライメント済みモデルのロード箇所において、`token` パラメータを渡すように修正する。
- [x] `utils.py` に `os` モジュールのインポート処理を追加する。
- [x] 修正が反映されていることをソースコード上で確認する。

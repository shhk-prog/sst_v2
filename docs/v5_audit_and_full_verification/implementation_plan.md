# 実装計画：v5 監査修正および V1〜V6 フル検証

## 目的
AI-DLC（`survey-summary`）で生成された `v5/` 成果物の監査で見つかった以下の問題点を解消し、V1〜V9 の全仮説を実データで確定させ、レポート・図の精度を引き上げる。

## 変更対象（すべて `v5/` 配下のみ・NFR2 厳守）
1. **PyTorch `.bin` 重み対応（V4〜V6 の未実行解消）**
   - `v5/src/v5lib/tensor_checks.py`: `TensorSource` に `pytorch_model.bin.index.json` / `pytorch_model.bin` の読み込み（直近 1 シャードのみ CPU mmap キャッシュ）を追加。あわせて `rankdata_average` を純 NumPy ベクトル化版にして V3 の全層実行を高速化（結果は完全一致）。
   - `v5/src/v5lib/verify.py`: `has_weights()` と `_dir_summary()` に `.bin` 対応を追加。
2. **図・レポートの視認性およびリンク修正**
   - `v5/src/v5lib/plots.py`: 凡例をプロット枠外右側に配置して点との重なりを解消し、`sst`・`task_arithmetic` の主要点（$\alpha \in \{0, 0.6, 1\}$）にラベルを付与。
   - `v5/src/v5lib/report.py`: 画像リンクを `report.md` 基準の相対パス（`../../outputs/figures/...`）に修正（出典表記は `v5/...` を維持）。
3. **単体テスト追加・実行**
   - `v5/tests/test_hypotheses.py`: `.bin` 単一・シャード読み込みと `compute_availability` のテスト追加。
   - `v5/tests/test_report.py`: 画像相対リンクの実在検証を追加。
4. **CPU 専用・読み取り専用でのフル実行（V1〜V9＋図再生成）**
   - `check_inputs.py`、`check_v1_v9.py`（全 seed・全パターン・全層）、`plot_pareto_curves.py`、`build_report.py` を `CUDA_VISIBLE_DEVICES=""` で実行。
   - あわせて `v3/results/vllm` の `is_gibberish=False` 応答における文字化け（非 ASCII 混入・トークン崩壊）と `original_asr` / `harmbench_cls_asr` 乖離の定量確認を実施し、`v5/outputs/probe/` に保存。
5. **`v5/docs/survey_summary/report.md` の考察・設計案を修正**
   - V1〜V6 のフル確定値を反映し、V3（Jaccard 0.204 の全 1 退化による必然性）の誤解釈を訂正。
   - 3.0 節の文字化けすり抜け（偽の VRR）の実態を明記し、3.0 節と 4.1 節 F1 の表現揺れを解消。
   - 3.1 節の `safety+math` における `sst@1` と Pareto 曲線の読み取りを正確に訂正。
   - 4 節の設計案に、文字化け検出強化（文字種・文字エントロピー・N-gram/PPL による VRR ゲート強化）を反映。

## 検証計画
- `venv_sst/bin/python -m pytest v5/tests -q` 全件成功
- `git status --short -- v3/results v1 v2` が空であること（NFR2）
- 生成 PNG の視覚確認と `report.md` の最終チェック

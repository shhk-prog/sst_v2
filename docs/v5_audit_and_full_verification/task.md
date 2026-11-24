# タスクリスト：v5 監査修正および V1〜V6 フル検証

- [x] `v5/` 成果物・`build-and-test/`・`v3/` 実データ・HF キャッシュの照合と問題点抽出
- [x] `v5lib/tensor_checks.py`・`verify.py` の PyTorch `.bin` シャード対応と `rankdata_average` / `topk_mask` 高速化
- [x] `v5lib/plots.py` の凡例重なり修正・$\alpha$ 注釈追加、`v5lib/report.py` の画像相対パス修正
- [x] 単体テスト追加および全テスト実行（`pytest v5/tests`: 50 passed）
- [x] CPU 専用・読み取り専用での `inputs` 再確認および V1〜V9 フル範囲実行完了
- [x] `safety+code` 等における文字化け（gibberish すり抜け）の定量確認（`v5/outputs/probe/gibberish_escape_probe.md`）
- [x] 図の再生成、`v5/docs/survey_summary/report.md` の考察・設計案の訂正・更新
- [x] 最終テスト・NFR2（既存ファイル無変更）確認および `walkthrough.md` 作成

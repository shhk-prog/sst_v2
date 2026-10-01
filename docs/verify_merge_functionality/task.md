# タスクリスト: v3モデルマージ機能の動作検証および修正

- [x] MergeAlignのバグ修正
  - [x] `baselines/MergeAlign/merging/lm_cocktail/lmcocktail_merge_align.py` の修正
  - [x] `scripts/merge.py` の `run_mergealign` の修正
- [x] LED-Mergingのバグ修正
  - [x] `baselines/LED-Merging/merge_llms.py` の修正
- [x] SafeMERGEのバグ修正
  - [x] `baselines/SafeMERGE/get_safemerge_model.py` の修正
- [/] テスト環境の準備
  - [x] `scripts/create_dummy_models.py` の作成とダミーモデルの生成完了
- [/] 動作検証テスト of merge
  - [x] `scripts/test_merge_all.py` の作成
  - [x] 各種エラー（Data-Free SST、mergekit KeyError解決、LED-Mergingの重要度スコア＆マスク事前生成、LED-MergingのUnboundLocalErrorバグ2箇所の修正、LED-Mergingのutilityキー指定ミス修正、MergeAlignトークナイザ正常化等）の追加修正完了
  - [ ] 修正版コードでの再検証実行（ユーザー再々々々々々々々々依頼中）
- [ ] 検証結果の整理
  - [ ] `walkthrough.md` の作成

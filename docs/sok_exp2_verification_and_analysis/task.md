# タスクリスト: SoK 実証 2 完了監査および最終解析

- [x] `local_launcher.log`・`local_task{0,1,2}.log` の全ログ異常・フォールバック・OOM 監査
- [x] 全 100 結果ファイル（安全性 80 JSON・有用性 20 JSON）の欠損・途中崩壊・時系列（04:34 GPU 切替前後）監査
- [x] GPU 差対照モデル 2 本（`controls_seed42`）と元 `v3` 結果の一致検証
- [x] `v5/scripts/analyze_sok_exp2.py` の本番実行（3 分類器別表・曲線図 2 枚・プロンプト単位ブートストラップ 95% CI・GPU 記録表）
- [x] 監査結果および最終解析レポートの整理

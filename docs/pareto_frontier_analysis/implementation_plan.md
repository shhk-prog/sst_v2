# Pareto AUCスクリプトの拡張計画 (Merge Targetの指定)

## 目的
`v3/scripts/pareto_auc.py` を拡張し、ユーザーが指定したマージ対象（`base`, `safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical` など）ごとに結果をフィルタリングして集計、パレートフロンティアの計算、可視化プロットを行えるようにします。

## Proposed Changes

### [MODIFY] [pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)
- `--merge_target` コマンドライン引数を追加します。
  - 選択肢: `all`, `base`, `safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical`
- ロード対象ファイルのフィルタリングロジックの追加
- 出力ファイル名（プロット画像やCSV）にマージターゲット名を自動で挿入
- **17指標の完全個別対応の追加**
- **メソッド名パースのバグ修正 (実験条件の区別対応)**:
  - `sst_merge_v3_main_` などのプレフィックスがある場合に、正しくマージ手法名（`dare`, `ties`, `della` 等）を切り出せるように `parse_model_params` 関数のパースロジックを修正します。

## Verification Plan

### Manual Verification
- `--merge_target` をそれぞれ指定してスクリプトを実行し、意図したモデルグループのデータのみが抽出・プロットされるか確認します.
- 出力ログの `Method` が `sst` ではなく、各マージ手法（`dare` 等）に正しく分離されていることを確認します。

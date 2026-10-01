# Ablation実験における Steering Hook モジュール読み込みエラーの修正計画

Ablation実験 (`slurm_ablation_sample_size.sh`) の実行時、`scripts/merge.py` が `ModuleNotFoundError: No module named 'steering_hook'` により終了コード 1 で失敗していました。
本計画では `steering_hook.py` の配置場所を正常化し、マージスクリプトおよび関連するテストが正常に動作するように修正します。

## 問題の根本原因
- `scripts/merge.py` および `scripts/fine_tuning.py` 等では `import steering_hook` を呼び出しています。
- しかし、`steering_hook.py` が誤って `scripts/tests/steering_hook.py` に配置されていたため、`scripts/` を検索パスとしている実行環境で `steering_hook` が検出できませんでした。

## ユーザーレビューが必要な項目
- なし（配置場所の調整およびインポートパスの修正のみで、既存のロジックに変更はありません）。

## 変更内容

### Component: `scripts`

#### [NEW] [steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/steering_hook.py)
- `scripts/tests/steering_hook.py` を `scripts/steering_hook.py` に複製/配置します（設計書 `kiro/steering/structure.md` の仕様に準拠）。

#### [MODIFY] [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/tests/test_steering_hook.py)
- テストファイルから `scripts/` ディレクトリ配下の `steering_hook.py` を正しくインポートできるように、`sys.path` に親ディレクトリ (`..`) を追加します。

## 検証計画

### 自動テスト
- 仮想環境 `/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python` を使用して以下を実行：
  1. `python -m unittest scripts/tests/test_steering_hook.py`
  2. 失敗した `scripts/merge.py` のコマンド（`--help` または実際の単一パラメータ）を実行し、`steering_hook` のインポートエラーが発生しないことを確認。

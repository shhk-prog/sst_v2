# 安全性評価（Safety Evaluation）へのサンプル数制限機能追加計画

`eval_safety.py` に `--limit` オプションを導入し、有用性評価（Utility Evaluation）と同様にデバッグやテスト実行用の件数制限（デフォルトは10件、`run_experiments.py` 経由では指定された limit）をかけられるように修正します。

## User Review Required

> [!NOTE]
> デフォルトで `run_experiments.py` は `--limit 10` (デバッグ用) として動作するため、安全性評価側もこれに追従し、実験にかかる全体時間が大幅に短縮されます。
> 本番評価時は `--limit 0`（無制限）を指定することで、従来どおり全件評価が実行されます。

## Open Questions

特にありません。

## Proposed Changes

### Script Changes

---

#### [MODIFY] [eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_safety.py)
- 引数パーサーに `--limit`（デフォルト値 `0`、無制限を示す）を追加します。
- ロードしたプロンプトのリストを、`args.limit` の数にスライスする処理を追加します。

#### [MODIFY] [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)
- `eval_safety.py` を呼び出している4箇所すべてのコマンドライン構築部分に、`"--limit", str(args.limit)` 引数を追加して連携させます。

---

## Verification Plan

### Automated Tests
- なし

### Manual Verification
- 修正後、安全性評価コマンドを個別に limit=2 で実行し、2件だけ推論と評価が行われることを確認します。
  - `/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python v3/scripts/eval_safety.py --model_path WizardLMTeam/WizardMath-7B-V1.0 --task harmbench --output_file results/raw/base_WizardMath_harmbench_safety_test.json --limit 2`

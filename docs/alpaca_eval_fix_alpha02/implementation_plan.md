# 実装計画: alpaca_eval キャッシュクリアおよび alpha0.2 評価の再実行

`alpaca_eval` 実行時に `annotations_seed0_configs.json` のアノテーション結合およびキャッシュ不一致によって発生したエラーを解決するため、キャッシュファイルおよび失敗した評価結果・一時ファイルを削除して評価を再実行します。

## ユーザー確認事項
> [!IMPORTANT]
> 以下の削除対象ファイル・ディレクトリを削除し、評価コマンドを再実行します。

## 対象ファイルおよびディレクトリ
1. **アノテーションキャッシュ**:
   - `v3/venv_v3/lib/python3.12/site-packages/alpaca_eval/evaluators_configs/weighted_alpaca_eval_gpt4_turbo/annotations_seed0_configs.json`
2. **当該モデルの失敗結果ファイルおよび出力ディレクトリ**:
   - `v3/results/debug_limit320/merged/seed44/safety+code/diagonal_sst_main/sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.2_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed44_alpaca_eval2.json`
   - `v3/results/debug_limit320/merged/seed44/safety+code/diagonal_sst_main/sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.2_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed44_alpaca_eval2_alpaca_eval_out`
3. **一時モデル出力キャッシュ（存在する場合）**:
   - `v3/results/alpaca_outputs/limit320/models_merged_sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.2_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed44_alpaca_outputs.json`
   - `v3/results/alpaca_outputs/limit320/models_merged_sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.2_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed44_alpaca_outputs_for_alpaca_eval.json`

## 実行するコマンド方針
1. ファイルの削除処理
2. 評価スクリプトの再実行:
   ```bash
   cd /mnt/nas/home/hiromi/src/sst_v2/v3
   /mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python scripts/eval/eval_alpaca.py \
     --model_path models/merged/sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.2_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed44 \
     --config configs/config_main.yaml \
     --output_file results/debug_limit320/merged/seed44/safety+code/diagonal_sst_main/sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.2_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed44_alpaca_eval2.json \
     --limit 320
   ```

## 検証計画
- コマンド実行後、生成された `sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.2...alpaca_eval2.json` を開き、`"status": "success"` および `win_rate` 等の評価結果が正しく記録されているか確認します。

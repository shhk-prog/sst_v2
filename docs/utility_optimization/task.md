# タスクリスト: Utility Fine-Tuning の最適化

- [x] `run_lora_ft.py` の修正
    - [x] データセットを `messages` 形式に変換する (`format_as_messages` 関数)
    - [x] `SFTConfig` に `assistant_only_loss=True` を設定
    - [x] LoRA `lora_alpha` の調整 (rank*2=32 に統一)
    - [x] デフォルト学習率を `1e-4` → `5e-5` に変更
- [x] `run_phase2.sh` の修正
    - [x] Utility/Coding FT の学習率を `5e-5` に変更
    - [x] Utility/Coding FT のエポック数を `5` に変更
    - [x] コメントを `lr5e-5_ep5_opt` の内容に更新
- [ ] 学習の実行
    - [ ] `utility_lora` の再学習
    - [ ] `coding_lora` の再学習
- [ ] 評価と結果の確認
    - [ ] HumanEval/GSM8K スコアの比較分析

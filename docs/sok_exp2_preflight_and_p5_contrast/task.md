# タスクリスト: SoK 実証 2 投入前検証・対照設計・P5 対照監査

- [x] `Llama-2-7b-hf` / `WizardMath-7B-V1.0` の `config.json`・既存 `v3` 対照モデル 2 本・`v3/scripts/merging/matena_fisher.py` の確認
- [x] `v5/scripts/merge_fp32_sst_math.py` の改修
  - [x] ② モデル–FIM キー・形状一致検証（ベースモデル 224 対象パラメータと `F_h`・`F_b` の完全一致確認）
  - [x] ③ 1 要因同等性テスト（`--mask-mode {fp32,v3}` と `--verify-v3-equivalence` の追加）
  - [x] HF キャッシュの `refs/main` 優先・完全性検証付きスナップショット解決・シャード順走査への修正
- [x] ② 事前マスク整合性検証と ③ `v3` 同等性テスト（`seed=42, α=0.6`）の CPU 実行・合格
- [x] マージ直後 CPU 検証スクリプト `v5/scripts/verify_fp32_merged_models.py` の作成（α=0 一致、α=1 置換率 ~20%、α=0.6 注入量比 vs TA、config.json 比較）
- [x] `v5/scripts/slurm_fp32_sst_math.sh` の更新（マージ直後 CPU 検証組み込み＋`seed42` での `v3` 対照モデル 2 本の再評価追加）
- [x] 評価後解析・プロットスクリプト `v5/scripts/analyze_sok_exp2.py` の作成と既存 `v3` データでのドライラン確認
- [x] `v5/scripts/check_datafree_degeneration.py` の CPU 実行と 3 手法 P5 対照表 `v5/outputs/sok_audit/p5_method_contrast.md` の生成
- [x] 単体テスト（`pytest v5/tests`: 55 passed）および `NFR2`（`v3/` 非改変）確認
- [x] `walkthrough.md` の記録と投入コマンドの整理（SLURM 自動投入なし）

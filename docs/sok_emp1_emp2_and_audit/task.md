# タスクリスト：SoK 実証2（fp32 SST再マージ＋GPU投入）・実証1（拡張妥当性再集計＋人手200件抽出）・外部コード監査

- [x] `v3` の SST マージ・評価・SLURM 環境確認および `v5/docs/ccs.md` の最新版同期
- [x] **実証2**: `safety+math` fp32 SST 再マージスクリプト（index top-k・`norm` 層 v3 同一・全テンソル実効マスク比率検証）および SLURM スクリプト作成
- [x] **実証2**: 実効マスク比率（$0.20 \pm 0.05$・`inf=0`）を全 3 seed × 全 224 テンソルで事前検証し、GPU ジョブを SLURM 投入（Job `128590_[0-2]`）
- [x] **実証1**: 拡張妥当性判定（直す前と後）の全 $\alpha$・全パターン再集計表と図を作成
- [x] **実証1**: 人手判定 200 件の層化サンプリング（ブラインド CSV ＋ 回答キー JSON）を生成
- [x] **外部コード監査**: `v3/baselines/`（SafeMERGE / LED-Merging / MergeAlign / mergekit）の P1〜P5 を先入観なく事実ベースで監査
- [x] テスト・NFR2 確認および `walkthrough.md` 作成

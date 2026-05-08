# docsディレクトリの整理計画

## 目的
現在、`docs` ディレクトリ内に番号付きの体系的なフォルダと、個別の作業ログや資料フォルダが混在しています。これらを論理的なカテゴリに分類し、必要な情報に素早くアクセスできるように整理します。

## 現状の課題
- `00_`〜`10_` の番号付きフォルダと、それ以外のフォルダが並列に存在し、どれが最新の資料でどれが作業ログなのかが判別しにくい。
- `FIM論文` などの日本語名フォルダが混じっている。
- 過去の AI との対話で生成された作業ログ（`create_readme` など）がルートに散らばっている。

## 提案する新構造

```text
docs/
├── 00_research_history/ (Existing)
├── ...
├── 10_lora_guides/ (Existing)
├── 11_archive/            <-- [NEW] 完了した作業ログや過去の検討資料を移動
│   ├── create_readme/
│   ├── sst_merge_v5_reorganization/
│   └── theory_reconstruction_with_prior_arts/
├── 20_research/           <-- [NEW] 参考文献や外部資料、先行研究調査
│   ├── literature_review/ (sst_merge_literature_review から移動)
│   └── fim_papers/        (FIM論文 から移動・英語名へ)
└── 30_drafts_and_plans/   <-- [NEW] 現在進行中の草案や計画
    ├── paper_title/
    └── sst_experiment_plan/
```

## 変更内容の概要

### [NEW] 11_archive
過去の特定のタスクに関する作業ログをまとめます。
- `create_readme` -> `11_archive/create_readme`
- `sst_merge_v5_reorganization` -> `11_archive/sst_merge_v5_reorganization`
- `theory_reconstruction_with_prior_arts` -> `11_archive/theory_reconstruction_with_prior_arts`

### [NEW] 20_research
研究の基礎となる資料をまとめます。
- `sst_merge_literature_review` -> `20_research/literature_review`
- `FIM論文` -> `20_research/fim_papers`

### [NEW] 30_drafts_and_plans
現在進行中または未分類の計画書をまとめます。
- `paper_title` -> `30_drafts_and_plans/paper_title`
- `sst_experiment_plan` -> `30_drafts_and_plans/sst_experiment_plan`

## 検証計画
- `ls -R docs` を実行し、意図したディレクトリ構造になっているか確認する。
- リンク切れなどが発生していないか、主要な `README.md` や `task.md` を確認する。

# Task: 評価結果自動集計＆多次元比較テーブル生成スクリプトの開発

## 目的
`v3` の全評価結果 JSON からスコアを抽出し、以下の条件を満たす集計比較表（Markdown / CSV）を自動生成する Python スクリプト `v3/scripts/analysis/generate_summary_tables.py` を実装する。

## 要求仕様
1. **集計軸**:
   - Seedごと (`seed42`, `seed43`, `seed44`)
   - 3 シードの平均 (Seed Average)
   - 4つのドメインパターン (`safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical`)

2. **出力表形式**:
   - **形式 A (α=0.5 固定比較表)**: 各 Merge 手法を並べて比較する表
   - **形式 B (Merge 手法別全 α 独立表)**: Merge 手法ごとに独立し、全 α パラメータ (0.0 ~ 1.0) を並べた表

3. **出力指標 (列)**:
   - 全 15 個別指標 (Safety: 4, Math: 2, Code: 2, Medical: 2, General/Instruction: 5)
   - 5 カテゴリのドメイン別平均 (Safety Ave, Math Ave, Code Ave, Medical Ave, General/Instruction Ave)

## タスクリスト
- [x] 要求仕様の整理とスクリプト設計 <!-- id: 0 -->
- [x] `v3/scripts/analysis/generate_summary_tables.py` の実装 <!-- id: 1 -->
- [x] implementation_plan.md および walkthrough.md の作成 <!-- id: 2 -->
- [x] スクリプトの使用方法とコードの提示 <!-- id: 3 -->

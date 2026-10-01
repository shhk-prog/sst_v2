---
inclusion: always
---

# 構成方針・リポジトリ構造 (SST-Merge Structure Steering)

## 1. ディレクトリ構成

SST-Merge V2 実験プロジェクトの全体構成は以下の通り定義されます。

```text
sst_v2/
├── kiro/                      # Kiro 関連の設定および仕様書
│   ├── steering/              # 常時適用される実験規約（Steering Rules）
│   │   ├── product.md         # 理論、実験設計、評価指標、データ分割、禁止事項
│   │   ├── tech.md            # 技術方針、カスタムコード排除、フック仕様
│   │   └── structure.md       # リポジトリ構成、データ規約（本ファイル）
│   └── specs/
│       └── sst-merge-aaai27/  # AAAI-27 向けの実装・実験計画（Specs）
│           ├── requirements.md # AAAI実験要件、採択基準、成功条件
│           ├── design.md      # パイプライン設計、データ漏洩防止設計
│           └── tasks.md       # 実装タスク、ablation計画、図表生成タスク
├── v3/                        # 実験実行環境
│   ├── requirements.txt       # Python パッケージの依存関係
│   ├── scripts/               # 実験実行コード群
│   │   ├── steering_hook.py   # 自動検証フックの実装
│   │   ├── test_steering_hook.py # フック検証用のユニットテスト
│   │   ├── data_prep/         # データセットダウンロード・準備
│   │   ├── fine_tuning/       # LoRA Fine-Tuning、評価・検証
│   │   └── merge/             # マージ処理（提案手法・公式SafeMERGE・Mergekit）
│   ├── data/                  # 前処理されたデータセット
│   ├── models/                # 学習済みLoRAおよびマージモデル
│   └── results/               # 評価結果の出力先
│       ├── raw/               # lm-eval等の生の出力 JSON
│       ├── processed/         # パース・整形された中間評価結果
│       └── pareto/            # スイープを統合した Pareto frontier 解析結果・図
├── logs/                      # 実験実行時の詳細標準出力ログ
└── metadata/                  # 各実験モデルごとの commit hash / バージョン記録
```

---

## 2. ドキュメントの役割と読み方

### 実験実行者および査読対策担当者の読み順
1. `kiro/steering/structure.md`: 本構成方針（このファイル）。
2. `kiro/steering/product.md`: 理論の物理的定義、実験設計、データ分割規則、および厳格な「禁止事項」。
3. `kiro/steering/tech.md`: 技術スタックの制約、カスタムフォールバックの禁止、検証フックの仕様。
4. `kiro/specs/sst-merge-aaai27/requirements.md`: AAAI-27 実験としての目標と採択基準。
5. `kiro/specs/sst-merge-aaai27/design.md`: データ漏洩を防止するパイプライン全体の幾何学的・工学的設計。
6. `kiro/specs/sst-merge-aaai27/tasks.md`: 個別の作業タスク。

---

## 3. データ規約および保存ルール

- **実験ログ (`logs/`)**:
  実験の実行ログ（`stdout` / `stderr`）は、タイムスタンプおよび実行パラメータをファイル名に含め、`logs/` に必ずリダイレクトして保存します。
- **メタデータ (`metadata/`)**:
  各モデルマージ結果の保存時に自動出力される `merge_metadata.json` の複製を、グローバルに管理する `metadata/` ディレクトリ配下に同一名でバックアップし、トレーサビリティを確保します。
- **評価結果の階層管理 (`v3/results/`)**:
  - `v3/results/raw/`: 評価ツールから直接吐き出された JSON。
  - `v3/results/processed/`: 各手法・各 $\alpha, k$ の主要指標（Jailbreak Resistance, Utility）を抽出した CSV。
  - `v3/results/pareto/`: プロット図（PDF/PNG）および Pareto AUC 算出用の解析結果。
- **archiveコードの分離制限**:
  `v1/`, `v2/` ディレクトリはレガシーアーカイブであり、現行の実験コードからインポートまたはモジュール参照することは禁止されます。

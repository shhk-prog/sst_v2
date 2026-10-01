# Utility FT 70%超達成 実装計画

## 背景と現状分析

### 現在のベストスコア
| モデル | HumanEval | MBPP | GSM8K |
|--|--|--|--|
| base (no template) | 38.4% | 49.6% | ~0% |
| base (template あり) | 未測定 | — | — |
| coding_lora ES後 | **41.5%** | **44.2%** | **8.8%** |

### 70%超が難しい本質的な理由
1. **Llama-3-8B base の天井**: web 検索結果によると base モデルは HumanEval 28〜45% 程度。**現状の FT が base と同スコアなのは、「FT の純増分がほぼゼロ」状態を示唆している**。
2. **データ量と品質**: 現在 Python データは ~2700件。HumanEval 70%+ を出しているモデル群は、数万〜数十万件規模の high-quality コーディングデータを使用している。
3. **LoRA ランクの低さ**: 現在 r=16 は「指示追従」向けの設定であり、複雑なコード生成には r=64〜128 が推奨される。

---

## User Review Required

> [!IMPORTANT]
> この計画は「確実に 70% を超えるための変更」として、以下の 3 つの選択肢を提示します。**優先度とトレードオフが大きく異なるため、どの路線で進めるか承認をお願いします。**

---

## Open Questions

> [!WARNING]
> **Q1: ベースモデルを Instruct 版に変更してよいか？**
> 現状の base モデル（`Meta-Llama-3-8B`）への LoRA FT では 70% 超は極めて困難です。`Meta-Llama-3-8B-Instruct` を起点にすれば HumanEval が既に ~58%、FT で 70% に近づける余地があります。研究の文脈（「base モデルへの utility LoRA + safety LoRA をマージ」）との整合性はどう考えますか？
>
> **Q2: データ規模の拡張を許可するか？**
> HumanEval 70%+ には、コーディングデータを現在の 2700件から **2万〜10万件** 規模に増やすことが現実的です。データダウンロード・前処理に追加の時間と HF アクセスが必要になります。
>
> **Q3: LoRA ランクを r=64 に上げてよいか？**
> メモリ増加（推定 1.5GB 程度）と引き換えに、表現力が向上します。

---

## 路線の選択（3択）

### 🔴 路線 A（現実的・最速）: Instruct ベース + 大規模データ
**目標: HumanEval 65〜75%, MBPP 65〜75%**（2〜4週間）

1. ベースモデルを `Meta-Llama-3-8B-Instruct` に変更
2. コーディングデータを **OSS-Instruct ~20K件** に拡張
3. LoRA: r=64, alpha=128, lr=2e-5, ES 有効
4. 金融: finance-alpaca に加え、**FiQA** や **FinanceBench** を追加

**メリット**: 最も確実に 70% に到達できる。Instruct は既に 58%+ あるため、微調整で +12〜17%。  
**デメリット**: base モデルへの LoRA という前提が崩れる。研究への影響を要確認。

---

### 🟡 路線 B（バランス型）: base + 高品質大規模データ + r=64
**目標: HumanEval 55〜65%, MBPP 60〜70%**（2〜3週間）

1. ベースモデルは `Meta-Llama-3-8B` のまま
2. データを **Evol-Instruct Python 20K件** + **Magicoder-Clean 5K件** に拡張
3. LoRA: r=64, alpha=128, lr=5e-5, ES patience=5
4. `rsLoRA=True` (ランク安定化) の追加
5. GSM8K 対策に **gsm8k 学習データ** を 1000件混合

**メリット**: 研究の前提（base model LoRA）を維持しながら到達できる最高点を目指す。  
**デメリット**: 70% 達成は保証できない（base モデルの天井が壁になる）。

---

### 🟢 路線 C（段階的・完全版）: 路線 B で試してから A へ移行
**目標: まず 55〜65% を確認し、研究判断のうえで Instruct へ移行**

1. **Phase 1** (1週間): 路線 B を実装・評価
2. **Phase 2** (2週間): 結果が 65% 未満なら路線 A へ移行

---

## Proposed Changes（路線 B を前提として記載）

### 1. データパイプライン: 大規模高品質データへの移行

#### [MODIFY] prepare_datasets.py
- HuggingFace `m-a-p/CodeFeedback-Filtered-Instruction` または `bigcode/self-oss-instruct-sc2-exec-filter-50k` (Python サブセット ~20K件) を取得する関数 `prepare_coding_data_large()` を追加
- Finance: `gbharti/finance-alpaca` (現行) に加え `sujet-ai/Sujet-Finance-Instruct-177k` から最大 5000件を追加し、Finance-Mix データを作成
- クリーニング: コードブロック抽出 + `def` ではじまる関数のみに絞り込む (tail-only モード)

#### [NEW] prepare_coding_data_large.py
- スクリプト単体でも動作するよう切り出し、選択的に高品質データを取得・前処理する

---

### 2. LoRA ハイパーパラメータ変更

#### [MODIFY] run_lora_ft.py
- `lora_r` デフォルト: 16 → **64**
- `lora_alpha` デフォルト: 32 → **128** (alpha=2r)
- `lora_dropout`: 0.05 → **0.0** (大データ + rsLoRA 利用時)
- `use_rslora` オプション追加 (`lora_config.use_rslora=True`)
- `learning_rate` デフォルト: 2e-4 → **5e-5** (r=64 では高 LR が不安定になるため)
- `max_length`: 1024 → **2048** (長いコード対応)

#### [MODIFY] run_phase2_python.sh
- 新しいデフォルト値を反映
- `USE_LARGE_DATA` 環境変数で大規模データへの切り替えを追加

---

### 3. 評価設定の改善

#### [MODIFY] run_utility_eval.py
- HumanEval の生成時に `do_sample=False` (greedy decoding) を確実に適用
- `max_new_tokens` を明示的に設定 (現在は lm_eval のデフォルト依存)

---

### 4. 実験管理: グリッドサーチスクリプトの追加

#### [NEW] run_hparam_grid.sh
- `lr × patience × data_size` の組み合わせを自動実行し、eval_loss の推移と HumanEval スコアを JSONL に集計するラッパースクリプト
- 同一マシンでの直列実行を前提とし、実験名で管理

---

## 検証計画

### 路線 B（base + 大規模データ）の期待値

| 条件 | HumanEval 予測 | MBPP 予測 |
|--|--|--|
| r=16, 2.7K件 (現状) | 41.5% | 44.2% |
| r=16, 20K件 | ~50-55% | ~55-60% |
| r=64, 20K件, lr=5e-5, ES | ~55-65% | ~60-70% |
| r=64, 20K件, rsLoRA | ~60-70% | ~65-75% |

> [!NOTE]
> 70% を **確実に** 超えたい場合は **路線 A**（Instruct ベース）が最も現実的です。路線 B でも 60〜70% は届く可能性がありますが、base モデルの能力上限に依存します。

### ステップ
1. `run_hparam_grid.sh` で小規模グリッドサーチ (各 ~1h)
2. best checkpoint を確認し本番 RUN
3. HumanEval / MBPP / GSM8K 評価
4. 70% 未満なら路線 A へ移行

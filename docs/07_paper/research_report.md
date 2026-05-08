# SST-Merge 詳細研究レポート
## Safety-Sensitive Tuning by Fisher-Ratio Subspace

**著者**: 廣見 紗妃, 木下 洋輝, 三浦 尭之（NTT社会情報研究所）  
**対象論文**: SCIS 2025 投稿論文

---

## 1. 研究の背景と動機

### 1.1 問題意識：Secure Merge と Safety Tax

大規模言語モデル（LLM）は多分野で活用が進む一方、Jailbreak攻撃（敵対的プロンプトによる有害出力の誘発）が深刻な脅威となっている。

LLMの防御は大きく2層に分けられる。

| 防御層 | 手法 | 利点 | 限界 |
|---|---|---|---|
| **外部ガードレール** | 入出力フィルタ・判定器 | 一般性能への影響が小さい | 強いJailbreakへの検知率が低い |
| **内部パッチ** | Fine-tuning・Model Merge | Jailbreak耐性が本質的に高い | 一般性能（Utility）が劣化しやすい |

**Secure Merge** は、Jailbreak耐性を獲得したパッチモデルを事後的に既存モデルへ統合する運用である。この手法が必要とされる背景には以下の実用上の制約がある。

1. **データ非共有性（分散開発）**: Utilityモデルの学習データとSafetyデータを互いに開示できないケースが多い
2. **計算コスト**: 巨大モデルの再学習は非現実的。マージは $O(1)$ で完了
3. **継続的適応**: 新たなJailbreak手法が出るたびに全データを再学習するのは運用上破綻する

しかし、既存のマージ手法をそのまま用いると「安全性は上がるがUtilityが落ちる」という **Safety Tax** が生じる。本研究はこの問題を正面から解決する新手法 **SST-Merge** を提案する。

### 1.2 研究の核心アイデア

> **「どの方向なら安全性に効き、どの方向がUtilityを壊すか」を明示的に区別し、方向選別として制御する**

パッチを単純に足し込むのではなく、Fisher情報行列（FIM）を用いて「安全／有用コスパ」が高い方向を選別して注入する。

---

## 2. 提案手法：SST-Merge の理論

### 2.1 問題の定式化

ベースUtilityモデル $\theta_{\mathrm{util}}$ にセキュリティパッチ差分 $\Delta\theta$ を加算して：

$$\theta_{\mathrm{merged}} = \theta_{\mathrm{util}} + \Delta\theta$$

このとき問題は「どの $\Delta\theta$ を注入するか」である。

### 2.2 Fisher情報行列による二重の計量

良性データ分布 $D_b$（Utility側）と有害データ分布 $D_h$（Safety側）に対して、それぞれFisher情報行列を定義する：

$$F_t(\theta) = \mathbb{E}_{x \sim D_t}\left[\nabla_\theta \ell(x;\theta) \nabla_\theta \ell(x;\theta)^\top\right], \quad t \in \{b, h\}$$

これを用いて：
- **Safety Tax（コスト）**: $\mathrm{Tax}(\Delta\theta) := \frac{1}{2} \Delta\theta^\top F_b \Delta\theta$（良性Fisherによる二次形式 = Utility劣化のproxy）
- **Safety Gain（利益）**: $\mathrm{Gain}(\Delta\theta) := \Delta\theta^\top F_h \Delta\theta$（有害Fisherによる二次形式 = Safety改善のproxy）

### 2.3 Step 1: 感度計算 → Step 2: 方向選別（GEVP）→ Step 3: 射影

**最適化問題**：

$$\max_{\Delta\theta} \ \Delta\theta^\top F_h \Delta\theta \quad \text{s.t.} \quad \Delta\theta^\top F_b \Delta\theta \leq c$$

この問題は **一般化固有値問題（GEVP）** に帰着する：

$$F_h v = \lambda F_b v$$

固有値 $\lambda = \frac{\Delta\theta^\top F_h \Delta\theta}{\Delta\theta^\top F_b \Delta\theta}$ は「Tax 1あたりの Gain」= **安全／有用コスパ** を表す。

> **SST-Mergeの理論的本質**  
> *「Utilityを壊す度合い（良性Fisher）でコストを測り、Safetyに効く度合い（有害Fisher）を利益として、コスパ最大の方向を選ぶ」*

### 2.4 Surrogate Hierarchy（3段階の実装近似）

フルFIMは $d \times d$ 行列で扱いが現実的でないため、段階的な surrogate として整理する：

```
Full SST（理論）
    ↓ 座標軸に探索を制限
Diagonal SST（対角 surrogate）
    ↓ データを使わず
Data-Free SST（ランキング surrogate）
```

#### 対角 surrogate（座標制約付き SST）

$F_t \approx D_t = \mathrm{diag}(f_{t,1}, \ldots, f_{t,d})$ と近似すると、GEVPは座標ごとに分解し：

$$\lambda_i = \frac{f_{h,i}}{f_{b,i} + \varepsilon}$$

この比が大きい上位 $k$ 座標を選ぶ操作へ退化する（Full SSTの exact special case）。

**マスク戦略**：
- **Hard mask（Top-k）**: $m_i = \mathbf{1}\{\lambda_i \text{ が上位 } k\}$
- **Soft mask**: $m_i = \sigma\!\left(\frac{\log(\lambda_i + \delta)}{\tau}\right)$

**マージ形式**：
- **加算型**: $\theta_{\mathrm{merged}} = \theta_{\mathrm{util}} + \alpha (w_{\mathrm{layer}} \odot m \odot \Delta_s)$
- **補間型**: $\theta_{\mathrm{merged}} = (1-w) \odot \theta_{\mathrm{util}} + w \odot \theta_{\mathrm{safe}}$

**層別重み（Layer Prior）**：

| モジュール | 重み |
|---|---|
| lm_head | 1.5 |
| q_proj, k_proj, v_proj, o_proj | 1.2 |
| gate_proj, up_proj, down_proj | 0.8 |

#### Data-Free SST（ランキング surrogate）

データが使えない場合、Fisher対角要素 $f_{t,i}$ の代わりにタスクベクトルの二乗を使う：

$$\phi_{t,i} = (\Delta_{t,i})^2, \quad \hat{\lambda}_i = \frac{(\Delta_{h,i})^2}{(\Delta_{b,i})^2 + \varepsilon}$$

FIMの数値を再現するのではなく、「どの座標が相対的にSafetyに効きやすくUtilityに効きにくいか」という **順位** を近似するランキング surrogate として位置づける。

---

## 3. 実験設定

### 3.1 使用モデル

| モデル | 役割 | 学習データ | エポック | LR |
|---|---|---|---|---|
| **meta-llama/Meta-Llama-3.1-8B-Instruct** | ベースモデル | - | - | - |
| **A5 (Utility)** | RepliQA特化LoRA | ServiceNow/repliqa | 10 | 2e-4 |
| **A6 (Utility)** | Alpaca特化LoRA | tatsu-lab/alpaca | 10 | 2e-4 |
| **A7 (Safety)** | Jailbreak耐性LoRA | Custom Jailbreak | 5 | 2e-4 |

LoRA設定：Rank $r=16$, Alpha $\alpha=32$, Dropout $=0.05$, Target modules = all-linear

### 3.2 評価データセット

| データセット | 用途 | 評価指標 |
|---|---|---|
| **RepliQA** | Utility評価（一般知識） | ROUGE-L |
| **Alpaca eval** | Utility評価（指示追従） | Win rate / ROUGE-L |
| **Custom Jailbreak trigger** | Safety評価 | JB Resistance Rate（JB Res.） |

### 3.3 比較手法（ベースライン）

| 手法 | 概要 | 設定 |
|---|---|---|
| **Task Arithmetic** | $\tau_{\mathrm{merged}} = (1-\alpha)\tau_u + \alpha\tau_s$ | $\alpha \in [0,1]$ をsweep |
| **TIES** | 疎化（trim）→ 符号調停 → disjoint merge | density = 0.5 |
| **DARE** | ランダムドロップ + 期待値保持リスケール | Drop rate $p=0.9$ |

### 3.4 提案手法のハイパーパラメータ

| 項目 | 設定値 |
|---|---|
| Top-$k$ ratio | 5%, 10%, 20%, 50% |
| Additive マスク | Soft mask（ログスケール正規化） |
| Interpolation マスク | Hard mask（Top-$k$ ratio） |
| FIM サンプル数 | $N=500$ |
| 正則化 | $\varepsilon = 10^{-6}$ |
| Safety Weight $\alpha$ | 0.05〜1.0 を0.01〜0.1ステップでsweep |

---

## 4. 実験結果

### 4.1 主要結果：Safety-Utility トレードオフ

#### A5 (RepliQA) + A7 (Safety) ペア — 代表値比較

| 手法 | $\alpha=0.5$ | | $\alpha=1.0$ | |
|---|---|---|---|---|
| | JB Res. | RepliQA | JB Res. | RepliQA |
| Task Arithmetic | 95.6% | 28.65% | 100.0% | 2.62% |
| TIES | 95.2% | 25.63% | 100.0% | 6.37% |
| DARE | 36.6% | 11.74% | 1.0% | 1.58% |
| **SST-Merge Interp (k=10)** | **75.8%** | **41.94%** | **91.4%** | **33.17%** |
| **SST-Merge Interp (k=5)** | **76.4%** | **41.97%** | **92.2%** | **33.38%** |
| **Data-Free SST Interp (k=5)** | 64.2% | 59.38% | 70.4% | 47.75% |

**観察**：
- Task Arithmetic・TIESは $\alpha=1.0$ でJB Res. 100%を達成するが、RepliQAが2〜6%まで崩壊
- DAREは初期から推論崩壊が始まり、JB Res.も安定しない
- SST-Merge Interpolationは $\alpha=1.0$ でRepliQA 33%超を維持しながらJB Res. 91%以上を達成

#### A6 (Alpaca) + A7 (Safety) ペア — 代表値比較

| 手法 | $\alpha=0.5$ | | $\alpha=1.0$ | |
|---|---|---|---|---|
| | JB Res. | Alpaca | JB Res. | Alpaca |
| Task Arithmetic | 89.4% | 46.52% | 100.0% | 26.90% |
| TIES | 94.8% | 41.86% | 99.6% | 30.54% |
| **SST-Merge Interp (k=20)** | **77.4%** | **60.53%** | **82.2%** | **53.64%** |
| **SST-Merge Interp (k=50)** | **81.2%** | **56.49%** | **94.4%** | **46.00%** |

A6+A7でも同様の傾向：SST-Merge Interpolationが既存手法を大幅に上回るパレート性能を達成。

### 4.2 ハイパーパラメータ $k$ の影響

| k値 | 傾向 |
|---|---|
| $k=5$（選択的） | Utility維持率が高い。Safetyの向上は緩やか |
| $k=20$（中間） | バランスが良い |
| $k=50$（広範） | Safety向上が早いが、Utility低下も大きい |

→ 要件に応じた $k$ 選択でモデルの振る舞いを柔軟に制御可能。

### 4.3 加算型 vs 補間型

| モード | 特性 |
|---|---|
| **Additive** | $\alpha$ が大きくなるとSafety性能が頭打ちになりやすい |
| **Interpolation** | Utilityをなだらかに低下させつつ、JB Res.を高α域でも大幅向上 |

→ 全体として **補間型（Interpolation）が優れた Safety-Utility バランス**を示す。

### 4.4 直接 Safety Fine-tuning との比較（実験A）

直接SFTでEpochごとの性能を追跡した結果：

| Epoch | Step | ROUGE-L | JB Res. |
|---|---|---|---|
| 0（ベースA5） | — | 0.549 | ~0% |
| 1 | 15 | **0.125** | 83.2% |
| 2 | 30 | **0.091** | 98.6% |
| 3 | 45 | **0.037** | 100.0% |
| **SST-Merge (k=20)** | — | **0.531** | **88.4%** |

**結論**：直接SFTはわずか15 Stepでユーティリティが77%低下し、Early Stopでも中間点を維持できない（L字型トレードオフ）。SST-Mergeは直接SFTが到達できないパレート領域（右上）に位置する。

---

## 5. FIM の有効性検証（実験B/C）

### 5.1 アブレーション実験：保護テスト・破壊テスト

ベースライン Loss = **3.86**

**保護テスト（Bottom-K にノイズを加える）**：

| 介入比率 | FIM（提案） | Weight Magnitude | Random |
|---|---|---|---|
| 1% | 4.01 (+0.15) | 4.87 (+1.01) | 4.73 (+0.87) |
| 5% | 3.79 (−0.06) | 9.24 (+5.38) | 8.42 (+4.56) |
| 10% | 4.23 (+0.36) | 14.06 (+10.2) | 13.27 (+9.41) |
| 20% | 4.50 (+0.64) | 13.03 (+9.17) | 14.29 (+10.4) |

**破壊テスト（Top-K をゼロにする）**：

| 介入比率 | FIM（提案） | Weight Magnitude |
|---|---|---|
| 1% | 3.85 (−0.00) | 4.15 (+0.29) |
| 5% | 4.54 (+0.68) | 4.93 (+1.07) |
| 10% | 4.63 (+0.77) | 5.13 (+1.27) |
| 20% | 5.06 (+1.20) | 5.44 (+1.58) |

**解釈**：
- Magnitude下位のパラメータを10%だけ乱すとLossが14を超え崩壊 → **重みが小さくても重要なパラメータが多数存在**
- FIM下位パラメータを20%乱してもLoss増加は+0.64のみ → FIMが「操作可能な平坦な谷」を正確に特定できている
- FIM上位を破壊するとLossが大きく上昇 → FIMは「壊してはいけないパラメータ」も正確に同定

### 5.2 FIMが「外科的マージ」を可能にするメカニズム

SST-Mergeは「FIMが描く平坦な谷」に沿ってのみSafetyパッチをスライドさせる。これにより：
- Utilityのコアとなる生成能力に干渉しない
- 直接Fine-tuningでは回避不能な犠牲（L字型トレードオフ）を超えた安全性向上が可能

---

## 6. 失敗モード分析（定性評価）

### 6.1 失敗モードA：過剰拒絶（Task Arithmetic・TIES）

**メカニズム**：Safetyタスクベクトルの「拒絶バイアス」が全パラメータに汚染される。

**過剰拒絶率の推移**：

| $\alpha$ | Task Arithmetic | TIES | DARE（Collapse） | SST-Merge |
|---|---|---|---|---|
| 0.2 | 0.0% | 0.0% | 68.4% | 0.0% |
| 0.5 | 12.8% | 13.0% | 94.6% | 0.4% |
| 1.0 | 13.4% | 13.8% | 71.8% | 1.6% |

**具体例（絵画描写タスク）**：

| $\alpha$ | Task Arithmetic | SST-Merge |
|---|---|---|
| 0.2 | *正常な描写を生成* | *正常な描写を生成* |
| 0.5 | **「絵画が添付されていない」と拒絶** | *正常な描写を継続* |
| 1.0 | **「明示的なコンテンツは描写できない」と架空の理由で拒絶** | *詩的な描写を維持* |

### 6.2 失敗モードB：推論崩壊（DARE）

**メカニズム**：Drop rate 90% + 10倍スケールアップにより言語生成の基底構造を破壊。

**崩壊の3段階**：
1. **第1段階**（$\alpha \leq 0.3$）：多言語トークンの混在、無秩序な文字列
2. **第2段階**（$0.3 < \alpha \leq 0.8$）：単語・句の無限ループ
3. **第3段階**（$\alpha > 0.8$）：断片的な出力のみ

具体例（数値計算タスク "Compute the sum of 5, 10, and 20."）：
- $\alpha=0.2$: `ungillingersaction...` （謎の記号列）
- $\alpha=0.5$: `"100, 100, 100, 100..."` （無限ループ）
- $\alpha=1.0$: `"The following text of the following..."` （前置詞ループ）

**DAREが「高いJB Res.」を示す理由**：崩壊した出力には有害キーワードが含まれないため、評価器が「安全」と誤判定する。

### 6.3 SST-Mergeの安全性向上の正体：Benign Distribution Shift

SST-Mergeにおける ROUGE-L の低下は、言語能力の喪失ではなく「安全性に配慮した回答表現の有益な変化」に起因する。丁寧すぎる言い回しへの変化など、実用上問題のないスタイルシフトである。

---

## 7. コードとアーキテクチャ

### 7.1 コア実装（`core/`）

| ファイル | 役割 |
|---|---|
| `sst_merge.py` | SST-Merge本体（FIM計算・GEVP・マスク生成・パッチ注入） |
| `sst_merge_data_free.py` | Data-Free SST（タスクベクトル二乗比によるランキング surrogate） |
| `sst_merge_interpolation.py` | 補間型マージの実装 |

### 7.2 スクリプト構成（`scripts/`）

| サブフォルダ | 主要スクリプト | 役割 |
|---|---|---|
| `merging/` | `run_all_merges_adapter_based.py` | 全マージ手法の一括実行 |
| `merging/` | `baseline_merge.py` | TA/TIES/DAREのベースライン実装 |
| `evaluation/` | `merge_jailbreak_eval.py` | Jailbreak耐性評価 |
| `evaluation/` | `evaluate_multidimensional_utility.py` | RepliQA/Alpaca Utility評価 |
| `analysis/` | `collect_all_results.py` | 結果の集計 |
| `analysis/` | `analyze_utility_loss.py` | 過剰拒絶の定量分析 |
| `visualization/` | `pareto_frontier_improved.py` | パレートフロンティア図の生成 |
| `FT/` | `run_safety_ft_baseline.py` | 直接SFTとの比較実験（実験A） |
| `fim_validation_ablation.py` | — | FIM/Magnitude/Gradient比較（実験B/C） |

### 7.3 実行フロー

```bash
# 1. モデル準備（LoRA Fine-tuning）
python scripts/FT/alpaca_tune.py   # A6（Utility, Alpaca）
python scripts/FT/repliqa_tune.py  # A5（Utility, RepliQA）
python scripts/FT/safety_tune.py   # A7（Safety）

# 2. マージ実行
python scripts/merging/run_all_merges_adapter_based.py

# 3. 評価
python scripts/evaluation/run_all_evals.py --gpu 2

# 4. 結果集計・可視化
python scripts/analysis/collect_all_results.py
python scripts/visualization/pareto_frontier_improved.py

# 5. FIM検証（実験B/C）
python scripts/fim_validation_ablation.py --gpu 2
```

---

## 8. まとめと考察

### 8.1 主要な知見

| 観点 | 結論 |
|---|---|
| **Safety-Utilityトレードオフ** | SST-Merge（補間型）が既存手法よりも大幅に優れたパレートフロンティアを達成 |
| **FIMの有効性** | Magnitude比較でFIMが「操作可能な空間」を正確に特定できることを実証 |
| **直接SFTとの比較** | 直接SFTが到達不能なパレート領域にSST-Mergeは位置する |
| **失敗モード分析** | 既存手法の「高いJB Res.」は過剰拒絶・推論崩壊による偽陽性が多い |
| **Data-Free SST** | データなしでも有用なパレート改善が可能。ただし高α域での限界あり |

### 8.2 Surrogate Hierarchy の意義

本研究の重要な理論的貢献は、フルFIM→対角FIM→データフリーというSurrogate Hierarchyを整理した点である。これらは「全く異なる近似」ではなく、「同一の比で座標を選ぶ手続きを段階的に緩和した設計」として統一的に理解できる。

### 8.3 制約と今後の課題

1. **低ランク・ブロック近似**：フルFIMと対角近似の中間解（K-FAC等）の実装・評価
2. **近似精度の定量検証**：対角FIMのランキング精度、タスクベクトル二乗比との順位相関
3. **汎化性能の評価**：より多様なモデル・攻撃・タスクへの拡張
4. **外部ガードレールとの併用**：二層防御構造における最適な組み合わせの設計

---

## 参考：実験データの場所

| データ | パス |
|---|---|
| 全評価結果（JSON） | `all_eval_results_summary.json` |
| 詳細結果テーブル（MD） | `docs/05_results/complete_results_tables.md` |
| LaTeX テーブル | `docs/08_tables/generated_latex_tables_all.tex` |
| FIM検証結果 | `fim_validation_results.json` |
| 評価ログ | `logs/evaluate_multidimensional_utility_*.log` |
| パレート図（PNG） | `docs/05_results/figures/` |

# 元論文との比較分析レポート

元論文 "Model Merging by Uncertainty-Based Gradient Matching" (Daheim et al., ICLR 2024) に掲載されている結果と、今回の実験結果との比較および分析を行います。

## 1. 精度 (Accuracy) の比較

元論文（ICLR 2024）で報告されている RoBERTa-base 感情分析マルチタスクマージの結果（Uncertainty-Based Gradient Matching）と、今回の実験結果の比較は以下の通りです。

| タスク (Task) | 元論文の精度 (Paper) | 今回の実験精度 (Ours) | 性能差 (Diff) | 個別特化 (Expert) |
| :--- | :---: | :---: | :---: | :---: |
| **imdb** | **0.9470** | **0.8690** | **-0.0780** | 0.9440 |
| **yelp** | 0.9730 | 0.9598 | -0.0132 | 0.9694 |
| **rt** | 0.9020 | 0.8602 | -0.0418 | 0.8762 |
| **sst2** | 0.9370 | 0.9151 | -0.0219 | 0.9369 |
| **amazon** | 0.9670 | 0.9308 | -0.0362 | 0.9530 |
| **平均 (Avg)** | **0.9452** | **0.9070** | **-0.0382** | 0.9359 |

※「個別特化 (Expert)」は今回検証された、マージ前の単一タスク用 Expert モデルの精度です。

---

## 2. 論文数値と今回結果の乖離に対する要因分析

個別特化モデル（Expert）の精度自体は、元論文の前提水準とほぼ同等であるのに対し、**マージ後の精度はすべてのタスク（平均で約 -3.8%p、特に IMDB で -7.8%p）で論文の報告値より大幅に低くなっています。**
この乖離には、以下の**マージ構成上の決定的な違い**が影響しています。

### 原因①：ベースライン（原点）モデルの不整合
*   **元論文の構成**：
    共通のオリジナルの事前学習モデル（`roberta-base` などの PLM）を `--pretrained_model_name_or_path` (基準点) に指定します。
*   **今回のスクリプトの構成**：
    すでに IMDB でファインチューニングされた `models/imdb/checkpoint-1563` を基準点として指定しています。
*   **影響**：
    マージ数式は基準点からの各タスクの差分（`\theta_t - \theta_llm`）を足し合わせる仕組みです。基準点が `roberta-base` ではなく特定のタスク（IMDB）に偏ったモデルであるため、他のタスク（`yelp`, `rt` など）との距離や勾配の不整合が発生し、マージモデル全体の座標系が崩れて性能低下を招きました。

### 原因②：マージ対象（Expert）リストからの IMDB の欠落
*   **元論文の構成**：
    全 5 つの Expert モデル（imdb, yelp, rt, sst2, amazon）をマージ対象に指定します。
*   **今回のスクリプトの構成**：
    `--ft_model_name_or_paths` には `imdb` を除く 4 タスクの Expert モデルのみが指定されています（IMDBはベースラインとして固定されています）。
*   **影響**：
    マージ処理中、マージ対象に含まれない `imdb` のパラメータ更新成分（差分）は計算されません。初期値としての IMDB のパラメータに対し、他4タスクの変位のみが一方的に加算されるため、ベースの IMDB モデルに元々備わっていた表現空間が完全に破壊されてしまい、IMDB タスクで **-7.8%p** という致命的な劣化が起きました。

---

## 3. 元論文通りの精度を再現するための改善策

元論文の精度（平均 94.5%）を再現するためには、パイプラインスクリプトにおけるマージ処理の引数を以下のように修正する必要があります。

### 修正前のマージコマンド（現行）
```bash
$PYTHON_BIN code/uncertainty_based_gradient_matching.py \
    --pretrained_model_name_or_path models/imdb/checkpoint-1563 \
    --pretrained_hessian_path fishers/imdb \
    --ft_model_name_or_paths models/yelp/checkpoint-1563,...,models/amazon/checkpoint-1563 \
    --ft_hessian_paths fishers/yelp,...,fishers/amazon \
    ...
```

### 修正後のマージコマンド（論文準拠）
ベースモデルに共通の `roberta-base` を用い、すべてのタスクをマージ対象にします。
```bash
# 1. 事前学習モデル（roberta-base）の Fisher（Hessian）情報を推定する
# 2. 以下のように roberta-base を基準として 5 タスクすべてをマージ対象にする
$PYTHON_BIN code/uncertainty_based_gradient_matching.py \
    --pretrained_model_name_or_path roberta-base \
    --pretrained_hessian_path fishers/pretrained_roberta_base \
    --ft_model_name_or_paths models/imdb/checkpoint-1563,models/yelp/checkpoint-1563,models/rt/checkpoint-534,models/sst2/checkpoint-1563,models/amazon/checkpoint-1563 \
    --ft_hessian_paths fishers/imdb,fishers/yelp,fishers/rt,fishers/sst2,fishers/amazon \
    ...
```

このように、マージ構成の対称性を保ち、事前学習モデルからの相対変化として全タスクの勾配情報を統合することで、論文で報告されている高いマージ精度（および劣化の抑制）が達成できると考えられます。

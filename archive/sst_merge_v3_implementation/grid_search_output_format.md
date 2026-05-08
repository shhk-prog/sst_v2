# kパラメータグリッドサーチ 出力形式ガイド

## 実行コマンド

```bash
cd /mnt/iag-02/home/hiromi/src/SST_merge/sst_merge_v2
source ../sst/bin/activate

for k in 20 30 50 70 100 150 200; do
    python scripts/run_merge.py \
        --model llama-3.1-8b \
        --variant A5+A7 \
        --k $k \
        --safety_weight 1.0 \
        --max_samples 500 \
        --use_fim
    
    python scripts/evaluate.py \
        --adapter results/llama-3.1-8b/sst_v2_A5_A7_*_k${k}_*.pt \
        --model llama-3.1-8b \
        --max_samples 500
done
```

---

## 出力ファイル構造

### 各k値につき3つのファイルが生成されます

#### 1. マージ済みアダプター (`.pt`)

**ファイル名形式**:
```
results/llama-3.1-8b/sst_v2_A5_A7_residual_r0.7_w1.0_k{k}_YYYYMMDD_HHMMSS.pt
```

**例**:
```
results/llama-3.1-8b/sst_v2_A5_A7_residual_r0.7_w1.0_k20_20260106_023500.pt
results/llama-3.1-8b/sst_v2_A5_A7_residual_r0.7_w1.0_k30_20260106_024500.pt
results/llama-3.1-8b/sst_v2_A5_A7_residual_r0.7_w1.0_k50_20260106_025500.pt
...
```

**内容**:
```python
{
    'adapter': {  # LoRAパラメータ (448個)
        'base_model.model.model.layers.0.self_attn.q_proj.lora_A.default.weight': tensor(...),
        ...
    },
    'metadata': {
        'variant': 'A5+A7',
        'mode': 'residual',
        'k': 20,  # ← k値
        'residual_ratio': 0.7,
        'safety_weight': 1.0,
        'timestamp': '20260106_023500',
        'method': 'SST-Merge V2'
    },
    'config': { ... }
}
```

#### 2. メタデータ (`.json`)

**ファイル名形式**:
```
results/llama-3.1-8b/sst_v2_A5_A7_residual_r0.7_w1.0_k{k}_YYYYMMDD_HHMMSS.json
```

**内容**:
```json
{
    "variant": "A5+A7",
    "mode": "residual",
    "k": 20,
    "residual_ratio": 0.7,
    "safety_weight": 1.0,
    "preset": null,
    "timestamp": "20260106_023500",
    "method": "SST-Merge V2"
}
```

#### 3. 評価結果 (`.eval.json`)

**ファイル名形式**:
```
results/llama-3.1-8b/sst_v2_A5_A7_residual_r0.7_w1.0_k{k}_YYYYMMDD_HHMMSS.eval.json
```

**内容**:
```json
{
    "metadata": {
        "variant": "A5+A7",
        "mode": "residual",
        "k": 20,
        "residual_ratio": 0.7,
        "safety_weight": 1.0,
        "timestamp": "20260106_023500",
        "method": "SST-Merge V2"
    },
    "results": {
        "jailbreak": {
            "jailbreak_resistance": 0.776,
            "total_samples": 500,
            "rta_score": 0.776
        },
        "beavertails": {
            "refusal_rate": 0.02,
            "harmful_response_rate": 0.01,
            "total_samples": 500
        },
        "mmlu": {
            "accuracy": 0.529,
            "total_samples": 500
        },
        "repliqa": {
            "rouge_l": 0.405,
            "total_samples": 500
        }
    },
    "responses": {
        "jailbreak": [ ... ],  # 詳細な応答データ
        "beavertails": [ ... ],
        "mmlu": [ ... ],
        "repliqa": [ ... ]
    }
}
```

---

## 結果の確認方法

### 1. ファイル一覧の確認

```bash
# 生成されたファイルを確認
ls -lht results/llama-3.1-8b/sst_v2_A5_A7_*.pt | head -10
ls -lht results/llama-3.1-8b/sst_v2_A5_A7_*.eval.json | head -10
```

### 2. 各k値の結果を表示

```bash
# k=20の結果
cat results/llama-3.1-8b/sst_v2_A5_A7_*_k20_*.eval.json | jq '{
    k: .metadata.k,
    jailbreak: .results.jailbreak.jailbreak_resistance,
    mmlu: .results.mmlu.accuracy,
    repliqa: .results.repliqa.rouge_l
}'

# k=30の結果
cat results/llama-3.1-8b/sst_v2_A5_A7_*_k30_*.eval.json | jq '{
    k: .metadata.k,
    jailbreak: .results.jailbreak.jailbreak_resistance,
    mmlu: .results.mmlu.accuracy,
    repliqa: .results.repliqa.rouge_l
}'
```

### 3. 全k値の結果を比較

```bash
echo "=== k Parameter Grid Search Results ==="
echo "k | Jailbreak | MMLU | RepliQA"
echo "--|-----------|------|--------"

for k in 10 20 30 50 70 100 150 200; do
    result=$(cat results/llama-3.1-8b/sst_v2_A5_A7_*_k${k}_*.eval.json 2>/dev/null | jq -r '
        "\(.metadata.k) | \((.results.jailbreak.jailbreak_resistance * 100) | round)% | \((.results.mmlu.accuracy * 100) | round)% | \((.results.repliqa.rouge_l * 100) | round)%"
    ')
    
    if [ -n "$result" ]; then
        echo "$result"
    else
        echo "$k | - | - | -"
    fi
done
```

**出力例**:
```
=== k Parameter Grid Search Results ===
k | Jailbreak | MMLU | RepliQA
--|-----------|------|--------
10 | 75% | 50% | 34%
20 | 78% | 53% | 40%
30 | 82% | 52% | 39%
50 | 87% | 51% | 37%
70 | 90% | 50% | 35%
100 | 93% | 49% | 33%
150 | 95% | 47% | 30%
200 | 97% | 45% | 28%
```

### 4. CSV形式で出力

```bash
# CSVファイルを生成
echo "k,jailbreak,mmlu,repliqa" > results/llama-3.1-8b/grid_search_results.csv

for k in 10 20 30 50 70 100 150 200; do
    cat results/llama-3.1-8b/sst_v2_A5_A7_*_k${k}_*.eval.json 2>/dev/null | jq -r '
        "\(.metadata.k),\(.results.jailbreak.jailbreak_resistance),\(.results.mmlu.accuracy),\(.results.repliqa.rouge_l)"
    ' >> results/llama-3.1-8b/grid_search_results.csv
done

# CSVを表示
cat results/llama-3.1-8b/grid_search_results.csv
```

**出力例**:
```csv
k,jailbreak,mmlu,repliqa
10,0.748,0.496,0.340
20,0.776,0.529,0.405
30,0.820,0.520,0.390
50,0.870,0.510,0.370
70,0.900,0.500,0.350
100,0.930,0.490,0.330
150,0.950,0.470,0.300
200,0.970,0.450,0.280
```

### 5. グラフ用データ抽出

```bash
# Pythonで可視化用データを抽出
python -c "
import json
import glob

results = []
for k in [10, 20, 30, 50, 70, 100, 150, 200]:
    files = glob.glob(f'results/llama-3.1-8b/sst_v2_A5_A7_*_k{k}_*.eval.json')
    if files:
        with open(files[0]) as f:
            data = json.load(f)
            results.append({
                'k': k,
                'jailbreak': data['results']['jailbreak']['jailbreak_resistance'] * 100,
                'mmlu': data['results']['mmlu']['accuracy'] * 100,
                'repliqa': data['results']['repliqa']['rouge_l'] * 100
            })

# 表形式で出力
print('k\tJailbreak\tMMLU\tRepliQA')
for r in results:
    print(f\"{r['k']}\t{r['jailbreak']:.1f}\t{r['mmlu']:.1f}\t{r['repliqa']:.1f}\")
"
```

---

## ディレクトリ構造

```
results/llama-3.1-8b/
├── sst_v2_A5_A7_residual_r0.7_w1.0_k10_20260105_232405.pt
├── sst_v2_A5_A7_residual_r0.7_w1.0_k10_20260105_232405.json
├── sst_v2_A5_A7_residual_r0.7_w1.0_k10_20260105_232405.eval.json
├── sst_v2_A5_A7_residual_r0.7_w1.0_k20_20260106_023500.pt
├── sst_v2_A5_A7_residual_r0.7_w1.0_k20_20260106_023500.json
├── sst_v2_A5_A7_residual_r0.7_w1.0_k20_20260106_023500.eval.json
├── sst_v2_A5_A7_residual_r0.7_w1.0_k30_20260106_024500.pt
├── sst_v2_A5_A7_residual_r0.7_w1.0_k30_20260106_024500.json
├── sst_v2_A5_A7_residual_r0.7_w1.0_k30_20260106_024500.eval.json
...
└── grid_search_results.csv  # 手動で生成
```

---

## 最適なkの選択

### 自動選択スクリプト

```bash
# 目標: Jailbreak 98%+, MMLU 52%+, RepliQA 40%+
python -c "
import json
import glob

best_k = None
best_score = -1

for k in [10, 20, 30, 50, 70, 100, 150, 200]:
    files = glob.glob(f'results/llama-3.1-8b/sst_v2_A5_A7_*_k{k}_*.eval.json')
    if files:
        with open(files[0]) as f:
            data = json.load(f)
            jb = data['results']['jailbreak']['jailbreak_resistance']
            mmlu = data['results']['mmlu']['accuracy']
            rq = data['results']['repliqa']['rouge_l']
            
            # スコア計算（全目標達成を優先）
            if jb >= 0.98 and mmlu >= 0.52 and rq >= 0.40:
                score = jb + mmlu + rq
                if score > best_score:
                    best_score = score
                    best_k = k
                    best_metrics = (jb, mmlu, rq)

if best_k:
    print(f'最適なk: {best_k}')
    print(f'Jailbreak: {best_metrics[0]*100:.1f}%')
    print(f'MMLU: {best_metrics[1]*100:.1f}%')
    print(f'RepliQA: {best_metrics[2]*100:.1f}%')
else:
    print('目標を達成したkが見つかりませんでした')
    print('次善策を探します...')
    
    # 次善策: Jailbreak最大化、Utility最低限維持
    for k in [10, 20, 30, 50, 70, 100, 150, 200]:
        files = glob.glob(f'results/llama-3.1-8b/sst_v2_A5_A7_*_k{k}_*.eval.json')
        if files:
            with open(files[0]) as f:
                data = json.load(f)
                jb = data['results']['jailbreak']['jailbreak_resistance']
                mmlu = data['results']['mmlu']['accuracy']
                rq = data['results']['repliqa']['rouge_l']
                
                if mmlu >= 0.50 and rq >= 0.35:
                    score = jb
                    if score > best_score:
                        best_score = score
                        best_k = k
                        best_metrics = (jb, mmlu, rq)
    
    if best_k:
        print(f'次善策のk: {best_k}')
        print(f'Jailbreak: {best_metrics[0]*100:.1f}%')
        print(f'MMLU: {best_metrics[1]*100:.1f}%')
        print(f'RepliQA: {best_metrics[2]*100:.1f}%')
"
```

---

## トラブルシューティング

### ファイルが見つからない

```bash
# ワイルドカードが展開されない場合
ls results/llama-3.1-8b/sst_v2_A5_A7_*_k20_*.eval.json

# 直接ファイル名を指定
cat results/llama-3.1-8b/sst_v2_A5_A7_residual_r0.7_w1.0_k20_20260106_023500.eval.json | jq '.results'
```

### 実行時間の見積もり

- マージ: 約10-15分/k値
- 評価: 約40-50分/k値
- 合計: 約50-65分/k値

**7つのk値**: 約6-8時間

### 並列実行（推奨）

```bash
# 複数のGPUで並列実行
# GPU 0: k=20, 30, 50
# GPU 1: k=70, 100, 150, 200

# GPU 0
CUDA_VISIBLE_DEVICES=0 bash -c 'for k in 20 30 50; do ...; done' &

# GPU 1
CUDA_VISIBLE_DEVICES=1 bash -c 'for k in 70 100 150 200; do ...; done' &
```

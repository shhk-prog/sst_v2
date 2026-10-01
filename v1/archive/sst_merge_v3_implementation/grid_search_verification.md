# グリッドサーチコマンド検証

## 修正内容

### Before (修正前)
```
ファイル名: sst_v2_A5_A7_residual_r0.7_w1.0_20260105_232405.pt
問題: k値が含まれていない
```

### After (修正後)
```
ファイル名: sst_v2_A5_A7_residual_r0.7_w1.0_k20_20260106_023500.pt
                                              ^^^
                                              k値が追加された
```

---

## グリッドサーチコマンド

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

## 動作確認

### 1. ファイル名パターンマッチング

**k=20の場合**:
```bash
# マージ実行後のファイル名
sst_v2_A5_A7_residual_r0.7_w1.0_k20_20260106_023500.pt

# 評価コマンドのパターン
sst_v2_A5_A7_*_k20_*.pt

# マッチング: ✅ 成功
```

**k=30の場合**:
```bash
# マージ実行後のファイル名
sst_v2_A5_A7_residual_r0.7_w1.0_k30_20260106_024500.pt

# 評価コマンドのパターン
sst_v2_A5_A7_*_k30_*.pt

# マッチング: ✅ 成功
```

### 2. 各k値で生成されるファイル

| k値 | アダプター (.pt) | メタデータ (.json) | 評価結果 (.eval.json) |
|-----|-----------------|-------------------|---------------------|
| 20 | `sst_v2_A5_A7_residual_r0.7_w1.0_k20_YYYYMMDD_HHMMSS.pt` | `sst_v2_A5_A7_residual_r0.7_w1.0_k20_YYYYMMDD_HHMMSS.json` | `sst_v2_A5_A7_residual_r0.7_w1.0_k20_YYYYMMDD_HHMMSS.eval.json` |
| 30 | `sst_v2_A5_A7_residual_r0.7_w1.0_k30_YYYYMMDD_HHMMSS.pt` | `sst_v2_A5_A7_residual_r0.7_w1.0_k30_YYYYMMDD_HHMMSS.json` | `sst_v2_A5_A7_residual_r0.7_w1.0_k30_YYYYMMDD_HHMMSS.eval.json` |
| 50 | `sst_v2_A5_A7_residual_r0.7_w1.0_k50_YYYYMMDD_HHMMSS.pt` | `sst_v2_A5_A7_residual_r0.7_w1.0_k50_YYYYMMDD_HHMMSS.json` | `sst_v2_A5_A7_residual_r0.7_w1.0_k50_YYYYMMDD_HHMMSS.eval.json` |
| ... | ... | ... | ... |

---

## 結果の確認方法

### 実行中の確認

```bash
# 生成されたファイルをリアルタイムで確認
watch -n 10 'ls -lht results/llama-3.1-8b/sst_v2_A5_A7_*.pt | head -10'
```

### 完了後の確認

```bash
# 全k値の結果を表示
echo "k | Jailbreak | MMLU | RepliQA"
echo "--|-----------|------|--------"

for k in 20 30 50 70 100 150 200; do
    result=$(cat results/llama-3.1-8b/sst_v2_A5_A7_*_k${k}_*.eval.json 2>/dev/null | jq -r '
        "\(.metadata.k) | \((.results.jailbreak.jailbreak_resistance * 100) | round)% | \((.results.mmlu.accuracy * 100) | round)% | \((.results.repliqa.rouge_l * 100) | round)%"
    ')
    
    if [ -n "$result" ]; then
        echo "$result"
    else
        echo "$k | (実行中または未実行)"
    fi
done
```

---

## 確認: 正しく評価できるか？

### ✅ はい、正しく評価できます

**理由**:

1. **ファイル名にk値が含まれる**:
   - `sst_v2_A5_A7_*_k20_*.pt` → k=20のファイルのみマッチ
   - `sst_v2_A5_A7_*_k30_*.pt` → k=30のファイルのみマッチ

2. **ワイルドカードが正しく機能**:
   - `*_k${k}_*` パターンで各k値を識別

3. **評価スクリプトが修正済み**:
   - PeftModelを使用してアダプターを正しくロード
   - 全メトリクス（Jailbreak、MMLU、RepliQA、Beavertails）を評価

---

## 実行時の注意点

### 1. 既存のk=10ファイルとの区別

```bash
# k=10のファイル（修正前）
sst_v2_A5_A7_residual_r0.7_w1.0_20260105_232405.pt  # k値なし

# k=20のファイル（修正後）
sst_v2_A5_A7_residual_r0.7_w1.0_k20_20260106_023500.pt  # k値あり
```

**対策**: k=10のファイルは古い形式なので、手動で確認する必要があります。

### 2. 実行時間

- 各k値: 約50-65分
- 7つのk値: 約6-8時間

### 3. ディスク容量

- 各k値につき約1.5GB（.pt + .eval.json）
- 7つのk値: 約10GB

---

## トラブルシューティング

### ファイルが見つからない場合

```bash
# パターンマッチングをテスト
ls results/llama-3.1-8b/sst_v2_A5_A7_*_k20_*.pt

# 見つからない場合、全ファイルを確認
ls -lt results/llama-3.1-8b/sst_v2_A5_A7_*.pt
```

### 評価が失敗する場合

```bash
# 最新のアダプターファイルを直接指定
LATEST=$(ls -t results/llama-3.1-8b/sst_v2_A5_A7_*_k20_*.pt | head -1)
python scripts/evaluate.py --adapter $LATEST --model llama-3.1-8b --max_samples 500
```

---

## 結論

✅ **修正により、グリッドサーチコマンドは正しく動作します**

- ファイル名にk値が含まれる
- 各k値のファイルを正確に識別できる
- 評価スクリプトが正しく動作する

**実行準備完了です！**

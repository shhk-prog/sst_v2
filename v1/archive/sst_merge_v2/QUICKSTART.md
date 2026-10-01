# SST-Merge V2 実行ガイド（簡易版）

## クイックスタート

### 必要なもの
- 既存のアダプター（A5, A6, A7）
- GPU環境

### 実行方法

```bash
cd /Users/saki/lab/100net/src/SST_merge/sst_merge_v2

# Residual Mode（推奨）- サンプル数少なめでテスト
./run_sst_v2_with_fim.sh A5+A7 residual 0.7
```

## 実行コマンド例

### 1. Residual Mode（FIM計算あり）

```bash
# デフォルト設定（max_samples=500）
./run_sst_v2_with_fim.sh A5+A7 residual 0.7

# サンプル数を指定したい場合
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --mode residual \
    --residual_ratio 0.7 \
    --max_samples 100 \
    --use_fim
```

### 2. Direct Mode（FIM計算なし、GPU不要）

```bash
./run_sst_v2_with_fim.sh A5+A7 direct
```

### 3. Layerwise Mode（FIM計算あり）

```bash
./run_sst_v2_with_fim.sh A5+A7 layerwise 0.7 balanced
```

## パラメータ

### Variant
- `A5+A7` - RepliQA + Security
- `A6+A7` - Alpaca + Security  
- `A5+A6+A7` - RepliQA + Alpaca + Security

### Residual Ratio（residual modeのみ）
- `0.5` - バランス
- `0.7` - **推奨**（Safety重視）
- `0.9` - Safety最優先

### Preset（layerwise modeのみ）
- `safety_first` - Safety重視
- `balanced` - バランス
- `utility_first` - Utility重視

## トラブルシューティング

### "CUDA out of memory"
→ `--max_samples 200`を指定

### "WARNING: Falling back to direct mode"
→ `--use_fim`フラグを追加

### アダプターが見つからない
→ 親ディレクトリでアダプターを作成:
```bash
cd /Users/saki/lab/100net/src/SST_merge
python experiments/create_instruction_model.py --model llama-3.1-8b --task repliqa --mode full
```

## 期待される出力

### 正しい実行（FIM計算あり）
```
Loading model and dataloaders for FIM computation...
Step 1: Computing FIM matrices...
Step 2: Solving GEVP...
Step 3: Residual Safety Injection...
✓ Merged adapter saved
```

### FIMなし（Direct modeへのフォールバック）
```
WARNING - Dataloaders not provided. Falling back to direct mode.
Step 3: Direct Addition (no projection)...
```

## 詳細情報

詳細は`EXECUTION_GUIDE.md`をご確認ください。

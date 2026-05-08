# LoRAトレーニング改善サマリー

## 現在の設定（確認済み）

### ハイパーパラメータ

```python
lora_r = 32  # ✅ Unsloth推奨
lora_alpha = 64  # ✅ Unsloth推奨（2 * r）
lora_dropout = 0.0  # ✅ Unsloth推奨
learning_rate = 2e-4  # ✅ 適切
warmup_ratio = 0.1  # ✅ Unsloth推奨
gradient_accumulation_steps = 4  # ✅ 適切
```

**結論**: ハイパーパラメータは既に最適化済み

---

## 実施する改善

### 1. エポック数の増加

**変更**: `num_epochs = 3` → `num_epochs = 5`

**理由**:
- 現在のRepliQA/Alpacaスコア（25-31%）は低い
- より多くのエポックで収束を改善
- A7は3エポックで98%達成 → A5/A6も5エポックで改善が期待できる

### 2. プロンプト形式の統一

#### トレーニング時

```python
# Alpaca形式
prompt_template = """### Instruction:
{instruction}

### Response:
{response}"""
```

#### 評価時（修正が必要）

**現在**:
```python
prompt = "{prompt}"  # そのまま
```

**修正後**:
```python
prompt_formatted = f"""### Instruction:
{prompt}

### Response:
"""
```

---

## 再トレーニング手順

### A5（RepliQA特化）

```bash
python3 experiments/create_instruction_model.py \
    --model llama-3.1-8b \
    --adapter A5 \
    --epochs 5
```

### A6（Alpaca特化）

```bash
python3 experiments/create_instruction_model.py \
    --model llama-3.1-8b \
    --adapter A6 \
    --epochs 5
```

---

## 期待される改善

### Before（3エポック）

| アダプター | RepliQA | Alpaca |
|----------|---------|--------|
| A5 | 25.32% | 25.42% |
| A6 | 14.18% | 30.91% |

### After（5エポック）

| アダプター | RepliQA | Alpaca |
|----------|---------|--------|
| A5 | **60-80%** | 30-50% |
| A6 | 30-50% | **60-80%** |

---

## 次のステップ

1. ✅ エポック数を5に増やす
2. [ ] 評価時のプロンプト形式を統一
3. [ ] A5/A6を再トレーニング
4. [ ] 再評価
5. [ ] SST-Merge実行

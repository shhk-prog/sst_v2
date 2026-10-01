# Llama-3, Qwen, Mistral 等の複数ベースモデルに対応した SFTTrainer chat_template エラーの修正計画

## 概要
`run_lora_ft.py` でベースモデル（例: `meta-llama/Meta-Llama-3-8B`, `Qwen/Qwen2.5-7B`, `mistralai/Mistral-7B-v0.1` など）を使用し、`SFTConfig(assistant_only_loss=True)` を有効にしてLoRAファインチューニングを行う際、ベースモデルのトークナイザーには `chat_template` が設定されていないため、TRLライブラリ内部で `TypeError` が発生します。

この問題を、特定のモデルだけでなく**様々なモデル（Mistral, Qwen, Llama-3など）に対して柔軟に対応できるように解決**するため、以下の修正を行います。
1. `args.model_name_or_path` からモデルファミリーを自動判別し、そのファミリーに適した `{% generation %}` タグを含むカスタムチャットテンプレートを取得するヘルパー関数を定義する。
2. トークナイザーの `chat_template` が `None` である場合に、判別されたカスタムチャットテンプレートを設定する。
3. `SFTTrainer` の初期化時に、`processing_class=tokenizer` 引数を明示的に渡す。

## 提案される変更

### [Component: Fine-Tuning Script]

#### [MODIFY] [run_lora_ft.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_lora_ft.py)

##### 1. モデルファミリー判別ヘルパー関数の追加
`run_lora_ft.py` に、モデル名からチャットテンプレートを動的に選択する関数を追加します。

```python
def get_custom_chat_template(model_name_or_path: str) -> str:
    """モデル名に基づいて、assistant_only_loss 用の {% generation %} タグを含んだ
    カスタムチャットテンプレートを返します。
    """
    name = model_name_or_path.lower()
    
    # Llama 3 シリーズ
    if "llama-3" in name or "llama3" in name:
        return (
            "{% set loop_messages = messages %}"
            "{% for message in loop_messages %}"
            "{{ '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n' }}"
            "{% if message['role'] == 'assistant' %}"
            "{% generation %}"
            "{{ message['content'] | trim + '<|eot_id|>' }}"
            "{% endgeneration %}"
            "{% else %}"
            "{{ message['content'] | trim + '<|eot_id|>' }}"
            "{% endif %}"
            "{% endfor %}"
            "{% if add_generation_prompt %}"
            "{{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}"
            "{% endif %}"
        )
    
    # Qwen シリーズ (ChatML 形式)
    elif "qwen" in name:
        return (
            "{% set loop_messages = messages %}"
            "{% for message in loop_messages %}"
            "{{ '<|im_start|>' + message['role'] + '\n' }}"
            "{% if message['role'] == 'assistant' %}"
            "{% generation %}"
            "{{ message['content'] | trim + '<|im_end|>\n' }}"
            "{% endgeneration %}"
            "{% else %}"
            "{{ message['content'] | trim + '<|im_end|>\n' }}"
            "{% endif %}"
            "{% endfor %}"
            "{% if add_generation_prompt %}"
            "{{ '<|im_start|>assistant\n' }}"
            "{% endif %}"
        )
    
    # Mistral / Llama 2 シリーズ
    elif "mistral" in name or "llama-2" in name or "llama2" in name:
        return (
            "{{ bos_token }}"
            "{% set loop_messages = messages %}"
            "{% for message in loop_messages %}"
            "{% if message['role'] == 'user' %}"
            "{{ '[INST] ' + message['content'] | trim + ' [/INST]' }}"
            "{% elif message['role'] == 'assistant' %}"
            "{% generation %}"
            "{{ ' ' + message['content'] | trim + eos_token }}"
            "{% endgeneration %}"
            "{% endif %}"
            "{% endfor %}"
        )
    
    # デフォルトのフォールバック (ChatML 形式)
    else:
        print(f"Warning: Unknown model family for {model_name_or_path}. Falling back to ChatML template.")
        return (
            "{% set loop_messages = messages %}"
            "{% for message in loop_messages %}"
            "{{ '<|im_start|>' + message['role'] + '\n' }}"
            "{% if message['role'] == 'assistant' %}"
            "{% generation %}"
            "{{ message['content'] | trim + '<|im_end|>\n' }}"
            "{% endgeneration %}"
            "{% else %}"
            "{{ message['content'] | trim + '<|im_end|>\n' }}"
            "{% endif %}"
            "{% endfor %}"
            "{% if add_generation_prompt %}"
            "{{ '<|im_start|>assistant\n' }}"
            "{% endif %}"
        )
```

##### 2. トークナイザーロード時の処理修正
トークナイザーロード直後で、`tokenizer.chat_template` が `None` の場合に上記のヘルパー関数からチャットテンプレートを適用します。

```python
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # 追加: tokenizer.chat_template が None の場合、動的にカスタムチャットテンプレートを設定
    if tokenizer.chat_template is None:
        template = get_custom_chat_template(args.model_name_or_path)
        tokenizer.chat_template = template
        print(f"Set custom chat template for {args.model_name_or_path}")
```

##### 3. SFTTrainer 呼び出しの修正
`SFTTrainer` に `processing_class=tokenizer` 引数を明示的に渡します。

```python
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,  # 追加: トークナイザーを明示的に渡す
        args=training_args,
        callbacks=callbacks if callbacks else None,
    )
```

## 検証計画

### 自動テスト / 動作確認
1. ターミナル上で、仮想環境 `venv_sst` をアクティベートします。
2. Llama-3（`meta-llama/Meta-Llama-3-8B`）を指定して動作確認を行い、正常にカスタムテンプレートが適用され、`SFTTrainer` が起動することを確認します。
3. 他のモデル（例: `Qwen` や `Mistral`）についても、コマンドライン引数を変更して（ダミーのモデルパスや huggingface の公開モデル名など）トークナイザーとテンプレートの設定部分が例外なく通過することを確認するテストコードを一時的に書いて実行します。
4. 具体的には以下のコマンドで実行確認を行います：
   ```bash
   python v2/scripts/fine_tuning/run_lora_ft.py \
     --model_name_or_path meta-llama/Meta-Llama-3-8B \
     --utility_dataset_path data/utility_finance.json \
     --eval_dataset_path data/utility_finance_eval.json \
     --output_dir test_output_dir \
     --epochs 1 \
     --learning_rate 5e-5
   ```

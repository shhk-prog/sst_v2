import os
import torch
from transformers import LlamaConfig, LlamaForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

def main():
    # sst_v2/v3 のカレントディレクトリから実行されることを想定
    os.makedirs("models", exist_ok=True)
    
    # 1. 極小Llamaモデルの設定 (マージ処理が動く程度の最小サイズ)
    config = LlamaConfig(
        vocab_size=32000,
        hidden_size=64,
        intermediate_size=128,
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        bos_token_id=1,
        eos_token_id=2,
        pad_token_id=0,
    )
    
    # tokenizerのダミー取得を試みる
    print("Preparing dummy tokenizer...")
    tokenizer = None
    
    # 候補リスト
    candidates = [
        "hf-internal-testing/tiny-random-LlamaForCausalLM",
        "meta-llama/Llama-2-7b-hf",
        "gpt2"
    ]
    
    for candidate in candidates:
        try:
            print(f"Trying to load tokenizer from {candidate}...")
            tokenizer = AutoTokenizer.from_pretrained(candidate)
            print(f"Successfully loaded tokenizer from {candidate}")
            break
        except Exception as e:
            print(f"Failed to load tokenizer from {candidate}: {e}")
            
    if tokenizer is None:
        raise RuntimeError("Failed to load any dummy tokenizer. Please check internet connection or huggingface cache.")

    # トークナイザの語彙サイズを合わせる
    config.vocab_size = len(tokenizer)

    # ダミーベースモデルの作成・保存
    print("Creating dummy base model...")
    base_model = LlamaForCausalLM(config)
    base_model.save_pretrained("models/dummy-llama-2-7b")
    tokenizer.save_pretrained("models/dummy-llama-2-7b")
    
    # 2. 特化ドメインモデルの作成と保存
    # Math
    print("Creating dummy math model...")
    math_model = LlamaForCausalLM(config)
    math_model.save_pretrained("models/dummy-wizardmath-7b")
    tokenizer.save_pretrained("models/dummy-wizardmath-7b")
    
    # Code
    print("Creating dummy code model...")
    code_model = LlamaForCausalLM(config)
    code_model.save_pretrained("models/dummy-wizardcoder-7b")
    tokenizer.save_pretrained("models/dummy-wizardcoder-7b")
    
    # Medical
    print("Creating dummy medical model...")
    medical_model = LlamaForCausalLM(config)
    medical_model.save_pretrained("models/dummy-medalpaca-7b")
    tokenizer.save_pretrained("models/dummy-medalpaca-7b")
    
    # 3. LoRAアダプタの作成と保存 (Safety FT)
    print("Creating dummy LoRA safety model...")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    # base_modelにLoRAを適用してPEFTモデル作成
    peft_model = get_peft_model(base_model, lora_config)
    peft_model.save_pretrained("models/dummy-safety-lora_seed42")
    
    print("All dummy models created successfully.")

if __name__ == "__main__":
    main()

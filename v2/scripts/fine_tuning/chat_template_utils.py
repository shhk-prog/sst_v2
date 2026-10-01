"""Fine-tuning / evaluation で共通利用するチャットテンプレート定義."""


def get_custom_chat_template(model_name_or_path: str) -> str:
    """モデル名に基づいて、assistant_only_loss 用の {% generation %} タグを含んだ
    カスタムチャットテンプレートを返します。
    """
    name = model_name_or_path.lower()

    # Llama 3 シリーズ
    if "llama-3" in name or "llama3" in name:
        return (
            "{{ bos_token }}"
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

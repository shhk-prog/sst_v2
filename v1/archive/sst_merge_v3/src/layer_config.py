"""
Layer-wise Projection設定

層ごとに異なるSafety Weightを適用することで、
出力層は強いSafety、FFNはUtility優先を実現
"""

# 層タイプごとのSafety Weight
LAYER_SAFETY_WEIGHTS = {
    'lm_head': 3.0,        # 出力層: 強いSafety
    'q_proj': 1.0,         # Attention Query: 中程度
    'k_proj': 1.0,         # Attention Key: 中程度
    'v_proj': 1.0,         # Attention Value: 中程度
    'o_proj': 1.0,         # Attention Output: 中程度
    'gate_proj': 0.3,      # FFN Gate: 弱いSafety（Utility優先）
    'up_proj': 0.3,        # FFN Up: 弱いSafety（Utility優先）
    'down_proj': 0.3,      # FFN Down: 弱いSafety（Utility優先）
}


def get_layer_type(param_name: str) -> str:
    """
    パラメータ名から層タイプを取得
    
    Args:
        param_name: パラメータ名（例: "model.layers.0.self_attn.q_proj.lora_A"）
    
    Returns:
        層タイプ（例: "q_proj"）
    """
    for layer_type in LAYER_SAFETY_WEIGHTS.keys():
        if layer_type in param_name:
            return layer_type
    return 'default'


def get_safety_weight(param_name: str) -> float:
    """
    パラメータ名からSafety Weightを取得
    
    Args:
        param_name: パラメータ名
    
    Returns:
        Safety Weight（デフォルト: 1.0）
    """
    layer_type = get_layer_type(param_name)
    return LAYER_SAFETY_WEIGHTS.get(layer_type, 1.0)

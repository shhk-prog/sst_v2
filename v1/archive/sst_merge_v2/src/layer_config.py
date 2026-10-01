"""
Layer-wise Projection Configuration

層ごとの射影強度設定。
Attention層とFFN層で異なる射影強度を使用し、
Safety情報をより効果的に保持する。

理論的根拠:
- q_proj, k_proj: Safety応答パターンに重要 → 弱い射影（Safety保持）
- v_proj, o_proj: 情報フローに影響 → 中程度の射影
- gate_proj, up_proj, down_proj: FFN層、Utility能力に影響 → 強い射影（Utility保護）
"""

from typing import Dict

# 層別射影強度設定
# projection_strength = 0.0: 射影なし（元のパラメータを完全保持）
# projection_strength = 1.0: 完全射影（Utility直交サブスペースのみ保持）
LAYER_PROJECTION_CONFIG: Dict[str, float] = {
    # Attention層 - Safety応答パターンに重要
    'q_proj': 0.2,   # Query: 弱い射影（Safety重視）
    'k_proj': 0.2,   # Key: 弱い射影
    'v_proj': 0.4,   # Value: やや弱い射影
    'o_proj': 0.3,   # Output: 弱めの射影
    
    # FFN層 - Utility能力に影響
    'gate_proj': 0.6,  # Gate: 中程度の射影
    'up_proj': 0.6,    # Up: 中程度の射影
    'down_proj': 0.6,  # Down: 中程度の射影
    
    # 埋め込み層
    'embed_tokens': 0.1,  # 埋め込み: ほぼ射影なし
    'lm_head': 0.1,       # 出力ヘッド: ほぼ射影なし
}

# プリセット設定
PRESETS = {
    # Safety重視: 射影を弱くしてSafety情報を保持
    'safety_first': {
        'q_proj': 0.1, 'k_proj': 0.1, 'v_proj': 0.2, 'o_proj': 0.2,
        'gate_proj': 0.4, 'up_proj': 0.4, 'down_proj': 0.4,
    },
    # バランス: Safety/Utility両方を考慮
    'balanced': LAYER_PROJECTION_CONFIG,
    # Utility重視: 射影を強くしてUtility保護
    'utility_first': {
        'q_proj': 0.5, 'k_proj': 0.5, 'v_proj': 0.6, 'o_proj': 0.6,
        'gate_proj': 0.8, 'up_proj': 0.8, 'down_proj': 0.8,
    },
    # 最小射影: ほぼ射影なし（ベースラインに近い）
    'minimal': {
        'q_proj': 0.05, 'k_proj': 0.05, 'v_proj': 0.1, 'o_proj': 0.1,
        'gate_proj': 0.1, 'up_proj': 0.1, 'down_proj': 0.1,
    },
}


def get_projection_strength(layer_name: str, config: Dict[str, float] = None) -> float:
    """
    層名から射影強度を取得
    
    Args:
        layer_name: LoRAパラメータの層名
        config: カスタム設定（Noneの場合はデフォルト使用）
    
    Returns:
        projection_strength: 射影強度（0.0-1.0）
    """
    if config is None:
        config = LAYER_PROJECTION_CONFIG
    
    for key, strength in config.items():
        if key in layer_name:
            return strength
    
    # デフォルト値（中程度の射影）
    return 0.3


def get_preset(preset_name: str) -> Dict[str, float]:
    """
    プリセット設定を取得
    
    Args:
        preset_name: プリセット名（'safety_first', 'balanced', 'utility_first', 'minimal'）
    
    Returns:
        config: 層別射影強度の辞書
    """
    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(PRESETS.keys())}")
    return PRESETS[preset_name].copy()

"""LED-Merging パッチ前後テスト（パッチ前はベースと完全一致、パッチ後は更新テンソル > 0）および MedAlpaca 検証ゲートテスト。"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import torch

V5_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V5_ROOT / "scripts"))

from eval_medical_medalpaca_official import build_medqa_prompt, evaluate_med_gate, extract_mc_choice  # noqa: E402
from led_merging_patched import apply_runtime_patch_to_model_wrapper, led_merge_state_dicts  # noqa: E402


def _make_synthetic_models() -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor], dict[str, torch.Tensor]]:
    """base (vocab=16) vs util/safe (vocab=17: 32000 vs 32001 の縮小再現) + Transformer 2 層。"""
    g = torch.Generator().manual_seed(20261126)
    base_sd = {
        "model.embed_tokens.weight": torch.randn((16, 8), generator=g),
        "model.layers.0.self_attn.q_proj.weight": torch.randn((8, 8), generator=g),
        "model.layers.0.mlp.gate_proj.weight": torch.randn((12, 8), generator=g),
        "model.layers.1.self_attn.q_proj.weight": torch.randn((8, 8), generator=g),
        "model.layers.1.mlp.down_proj.weight": torch.randn((8, 12), generator=g),
        "lm_head.weight": torch.randn((16, 8), generator=g),
    }
    util_sd: dict[str, torch.Tensor] = {}
    safe_sd: dict[str, torch.Tensor] = {}
    for k, v in base_sd.items():
        if v.shape[0] == 16:
            # vocab 拡張 (16 -> 17)
            u = torch.cat([v + 0.15 * torch.randn(v.shape, generator=g), torch.zeros((1, v.shape[1]))], dim=0)
            s = torch.cat([v + 0.10 * torch.randn(v.shape, generator=g), torch.zeros((1, v.shape[1]))], dim=0)
        else:
            u = v + 0.15 * torch.randn(v.shape, generator=g)
            s = v + 0.10 * torch.randn(v.shape, generator=g)
        util_sd[k] = u
        safe_sd[k] = s
    return base_sd, util_sd, safe_sd


def test_led_merging_before_vs_after_patch() -> None:
    """同じ入力モデルでパッチ前後を比較:
    - パッチ前: wanda_score に embed_tokens/lm_head のみ＋語彙不一致 -> 0 テンソル更新・ベース完全一致（退化）
    - パッチ後: 全テンソルにスコアあり＋語彙アライメント -> 更新テンソル > 0・ベースと不一致・proj_util > 0
    """
    base_sd, util_sd, safe_sd = _make_synthetic_models()
    g = torch.Generator().manual_seed(77)

    # 全テンソル分のスコア（パッチ後: _prune_core が全層を wanda_score/ へ出力）
    full_scores_safe = {k: torch.rand(safe_sd[k].shape, generator=g) for k in base_sd}
    full_scores_math = {k: torch.rand(util_sd[k].shape, generator=g) for k in base_sd}
    full_scores_base_s = {k: torch.rand(base_sd[k].shape, generator=g) for k in base_sd}
    full_scores_base_m = {k: torch.rand(base_sd[k].shape, generator=g) for k in base_sd}

    # パッチ前: 上流 commit 1149224 のバグにより wanda_score/ には embed_tokens と lm_head の 2 個しか入らない
    unpatched_only_2 = {"model.embed_tokens.weight", "lm_head.weight"}
    broken_scores_safe = {k: v for k, v in full_scores_safe.items() if k in unpatched_only_2}
    broken_scores_math = {k: v for k, v in full_scores_math.items() if k in unpatched_only_2}
    broken_scores_base_s = {k: v for k, v in full_scores_base_s.items() if k in unpatched_only_2}
    broken_scores_base_m = {k: v for k, v in full_scores_base_m.items() if k in unpatched_only_2}

    merged_before, stats_before = led_merge_state_dicts(
        base_sd=base_sd,
        ft_sds={"safety": safe_sd, "math": util_sd},
        ft_scores={"safety": broken_scores_safe, "math": broken_scores_math},
        base_scores={"safety": broken_scores_base_s, "math": broken_scores_base_m},
        fuse_rates={"safety": 0.5, "math": 0.5},
        fuse_patterns={"safety": "01", "math": "01"},
        scaling_coefficient=0.9,
        patched=False,
    )
    assert stats_before["n_tensors_updated"] == 0
    assert stats_before["rel_diff_vs_base_pct"] == 0.0
    assert stats_before["degenerated"] is True
    for k, tb in base_sd.items():
        assert torch.equal(merged_before[k][: tb.shape[0]], tb)

    # パッチ後: 全層スコア出力＋語彙アライメント
    merged_after, stats_after = led_merge_state_dicts(
        base_sd=base_sd,
        ft_sds={"safety": safe_sd, "math": util_sd},
        ft_scores={"safety": full_scores_safe, "math": full_scores_math},
        base_scores={"safety": full_scores_base_s, "math": full_scores_base_m},
        fuse_rates={"safety": 0.5, "math": 0.5},
        fuse_patterns={"safety": "01", "math": "01"},
        scaling_coefficient=0.9,
        patched=True,
    )
    assert len(full_scores_math) == len(base_sd)
    assert stats_after["n_tensors_updated"] == len(base_sd)
    assert stats_after["n_tensors_updated"] > 0
    assert stats_after["rel_diff_vs_base_pct"] > 1.0
    assert stats_after["per_input"]["math"]["proj_pct"] > 10.0
    assert stats_after["degenerated"] is False
    assert any(not torch.equal(merged_after[k][: base_sd[k].shape[0]], base_sd[k]) for k in base_sd)


def test_runtime_monkey_patch_redirects_to_prune_core_gradient() -> None:
    calls: list[dict] = []
    fake_mw = types.SimpleNamespace(
        _random_prune_core=lambda *a, **kw: calls.append({"fn": "random"}),
        _prune_core=lambda **kw: calls.append({"fn": "prune_core", **kw}),
    )
    orig = apply_runtime_patch_to_model_wrapper(fake_mw)
    fake_mw._random_prune_core("args", "model", "base", 0, 0, name_filter_fn="fn")
    assert len(calls) == 1
    assert calls[0]["fn"] == "prune_core"
    assert calls[0]["prune_mode"] == "gradient"
    # 復元確認
    fake_mw._random_prune_core = orig
    fake_mw._random_prune_core()
    assert calls[1]["fn"] == "random"


def test_medalpaca_prompt_extractor_and_gate() -> None:
    item = {
        "sent1": "A 45-year-old man presents with chest pain.",
        "sent2": "",
        "ending0": "Aspirin",
        "ending1": "Insulin",
        "ending2": "Penicillin",
        "ending3": "Ibuprofen",
        "label": "0",
    }
    p = build_medqa_prompt(item, variant="official_qa")
    assert "Context:" in p and "Question:" in p and "A. Aspirin" in p and p.endswith("Answer:")

    assert extract_mc_choice("B. Insulin")[0] == "B"
    assert extract_mc_choice("The correct answer is (C).")[0] == "C"
    assert extract_mc_choice("Aspirin is indicated here.", ["Aspirin", "Insulin", "Penicillin", "Ibuprofen"])[0] == "A"
    assert extract_mc_choice("")[0] is None

    g_ok = evaluate_med_gate(model_name="medalpaca", acc_pct=42.0, extraction_fail_pct=1.0, max_choice_freq_pct=31.0, base_acc_pct=30.0)
    assert g_ok["all_auto_checks_pass"] is True
    g_bad = evaluate_med_gate(model_name="medalpaca", acc_pct=25.0, extraction_fail_pct=1.0, max_choice_freq_pct=31.0, base_acc_pct=30.0)
    assert g_bad["all_auto_checks_pass"] is False

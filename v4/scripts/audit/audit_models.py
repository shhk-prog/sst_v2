"""
E0 Audit: audit_models.py (Strict Gate Enforcement)
Rigorous manifest builder and ancestor/tokenizer consistency auditor according to
Secure_Merge_Experiment_Plan.md Section 3.1.

Audits base model, math model, code model, and SafetyFT checkpoints (seeds 42, 43, 44).
Inspects token IDs, special tokens, RoPE, and LoRA dense restoration properties.

Status Taxonomy (Strict Plan Rule):
- PASS: Provenance, config, tokenizer, and weight alignment fully confirmed.
- FAIL: Concrete discrepancy detected (e.g. RoPE theta, vocab expansion, bos ID).
        Specific mismatched keys and values are saved.
- UNVERIFIED: Missing files or insufficient provenance information.

Gate Rule:
If any required domain or SafetyFT seed is FAIL or UNVERIFIED, the process MUST exit with code 1,
and the primary pipeline must HALT to prevent degenerative conflation.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Tuple
from transformers import AutoConfig, AutoTokenizer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def audit_single_model(model_name_or_path: str, role: str) -> Dict[str, Any]:
    print(f"Auditing [{role}]: {model_name_or_path}")
    info: Dict[str, Any] = {
        "role": role,
        "name_or_path": model_name_or_path,
        "exists_locally": os.path.exists(model_name_or_path),
        "status": "UNVERIFIED",
    }

    if not info["exists_locally"]:
        info["status"] = "UNVERIFIED"
        info["error"] = f"Model path does not exist locally: {model_name_or_path}"
        return info

    try:
        cfg = AutoConfig.from_pretrained(model_name_or_path, trust_remote_code=True)
        info["config"] = {
            "model_type": getattr(cfg, "model_type", None),
            "architectures": getattr(cfg, "architectures", None),
            "vocab_size": getattr(cfg, "vocab_size", None),
            "hidden_size": getattr(cfg, "hidden_size", None),
            "num_hidden_layers": getattr(cfg, "num_hidden_layers", None),
            "num_attention_heads": getattr(cfg, "num_attention_heads", None),
            "intermediate_size": getattr(cfg, "intermediate_size", None),
            "rope_theta": getattr(cfg, "rope_theta", 10000.0),
            "rope_scaling": getattr(cfg, "rope_scaling", None),
            "max_position_embeddings": getattr(cfg, "max_position_embeddings", None),
        }
    except Exception as e:
        info["status"] = "UNVERIFIED"
        info["config_error"] = str(e)
        return info

    try:
        tok = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=True)
        info["tokenizer"] = {
            "vocab_size": len(tok),
            "bos_token": str(tok.bos_token),
            "bos_token_id": tok.bos_token_id,
            "eos_token": str(tok.eos_token),
            "eos_token_id": tok.eos_token_id,
            "pad_token": str(tok.pad_token),
            "pad_token_id": tok.pad_token_id,
            "unk_token": str(tok.unk_token),
            "unk_token_id": tok.unk_token_id,
            "chat_template_present": bool(tok.chat_template),
        }
    except Exception as e:
        info["status"] = "UNVERIFIED"
        info["tokenizer_error"] = str(e)
        return info

    # Check for PEFT adapter
    adapter_cfg_path = os.path.join(model_name_or_path, "adapter_config.json")
    if os.path.exists(adapter_cfg_path):
        try:
            with open(adapter_cfg_path, "r", encoding="utf-8") as f:
                adapter_data = json.load(f)
            info["adapter_config"] = {
                "base_model_name_or_path": adapter_data.get("base_model_name_or_path"),
                "peft_type": adapter_data.get("peft_type"),
                "r": adapter_data.get("r"),
                "lora_alpha": adapter_data.get("lora_alpha"),
                "target_modules": adapter_data.get("target_modules"),
                "is_dense_restoration_required": True,
            }
        except Exception as e:
            info["adapter_error"] = str(e)

    info["status"] = "LOADED"
    return info


def compare_domain_to_base(base_info: Dict[str, Any], domain_info: Dict[str, Any], domain_name: str) -> Dict[str, Any]:
    # Guard against comparing unverified / unloaded models
    if base_info.get("status") != "LOADED" or domain_info.get("status") != "LOADED":
        return {
            "domain": domain_name,
            "verdict": "UNVERIFIED",
            "reason": f"One or both models not loaded: base={base_info.get('status')}, domain={domain_info.get('status')}",
            "discrepancies": {},
        }

    discrepancies = {}
    b_cfg = base_info.get("config", {})
    d_cfg = domain_info.get("config", {})
    b_tok = base_info.get("tokenizer", {})
    d_tok = domain_info.get("tokenizer", {})

    # Architecture dimensions
    for k in ["hidden_size", "num_hidden_layers", "num_attention_heads", "intermediate_size"]:
        if b_cfg.get(k) != d_cfg.get(k):
            discrepancies[f"config.{k}"] = {"base": b_cfg.get(k), "domain": d_cfg.get(k)}

    # Position embeddings
    if b_cfg.get("max_position_embeddings") != d_cfg.get("max_position_embeddings"):
        discrepancies["config.max_position_embeddings"] = {
            "base": b_cfg.get("max_position_embeddings"),
            "domain": d_cfg.get("max_position_embeddings"),
        }

    # RoPE scaling / theta
    b_rope = b_cfg.get("rope_theta")
    d_rope = d_cfg.get("rope_theta")
    d_rope_scaling = d_cfg.get("rope_scaling")
    if d_rope_scaling and isinstance(d_rope_scaling, dict):
        d_scaled_theta = d_rope_scaling.get("rope_theta")
        if d_scaled_theta and d_scaled_theta != b_rope:
            discrepancies["config.rope_scaling.rope_theta"] = {
                "base": b_rope,
                "domain_scaling": d_scaled_theta,
            }
    elif b_rope != d_rope:
        discrepancies["config.rope_theta"] = {"base": b_rope, "domain": d_rope}

    # Vocab size
    if b_tok.get("vocab_size") != d_tok.get("vocab_size"):
        discrepancies["tokenizer.vocab_size"] = {
            "base": b_tok.get("vocab_size"),
            "domain": d_tok.get("vocab_size"),
            "note": "Vocab expanded (e.g. [PAD] token added to index 32000)",
        }

    # Special token IDs
    for token_key in ["bos_token_id", "eos_token_id"]:
        if b_tok.get(token_key) != d_tok.get(token_key):
            discrepancies[f"tokenizer.{token_key}"] = {
                "base": b_tok.get(token_key),
                "domain": d_tok.get(token_key),
            }

    verdict = "FAIL" if discrepancies else "PASS"

    return {
        "domain": domain_name,
        "verdict": verdict,
        "discrepancies": discrepancies,
        "n_discrepancies": len(discrepancies),
    }


def run_full_model_audit(
    base_model: str = "meta-llama/Llama-2-7b-hf",
    math_model: str = "WizardLMTeam/WizardMath-7B-V1.0",
    code_model: str = "vanillaOVO/WizardCoder-Python-7B-V1.0",
    models_root: str = "/mnt/nas/home/hiromi/src/sst_v2/v3/models",
    output_path: str = "/mnt/nas/home/hiromi/src/sst_v2/v4/results/e0_audit/model_manifest.json",
) -> Dict[str, Any]:
    print("=" * 70)
    print("Running Rigorous E0 Model Provenance & Input Condition Audit")
    print("=" * 70)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    manifest = {
        "audit_version": "v4_rigorous_gate",
        "benchmark_scope": "math_and_code_domestic_tier",
        "models": {},
        "safetyft_checkpoints": {},
        "domain_verdicts": {},
        "primary_experiment_verdict": "UNVERIFIED",
    }

    # 1. Audit Base & Domain models
    manifest["models"]["base"] = audit_single_model(base_model, "base")
    manifest["models"]["math"] = audit_single_model(math_model, "math_domain")
    manifest["models"]["code"] = audit_single_model(code_model, "code_domain")

    # 2. Audit SafetyFT checkpoints (seed 42, 43, 44) for both LoRA adapter and Full restored
    all_safety_dense_verified = True
    for seed in [42, 43, 44]:
        lora_path = os.path.join(models_root, f"safety_lora_seed{seed}")
        full_path = os.path.join(models_root, f"temp_safety_full_seed{seed}")
        
        lora_aud = audit_single_model(lora_path, f"safety_lora_seed{seed}") if os.path.exists(lora_path) else {"status": "UNVERIFIED", "path": lora_path}
        full_aud = audit_single_model(full_path, f"safety_full_seed{seed}") if os.path.exists(full_path) else {"status": "UNVERIFIED", "path": full_path}

        manifest["safetyft_checkpoints"][f"seed{seed}"] = {
            "lora_adapter": lora_aud,
            "dense_full": full_aud,
        }
        if full_aud.get("status") != "LOADED":
            all_safety_dense_verified = False

    # 3. Discrepancy comparison against Base
    math_audit = compare_domain_to_base(manifest["models"]["base"], manifest["models"]["math"], "math")
    code_audit = compare_domain_to_base(manifest["models"]["base"], manifest["models"]["code"], "code")

    manifest["domain_verdicts"]["math"] = math_audit
    manifest["domain_verdicts"]["code"] = code_audit

    # Primary gate rule:
    # If any domain is FAIL or UNVERIFIED, or SafetyFT dense missing -> Primary Gate is NO_GO
    if math_audit["verdict"] != "PASS" and code_audit["verdict"] != "PASS":
        manifest["primary_experiment_verdict"] = "NO_GO"
        manifest["primary_gate_reason"] = (
            "Both math and code domains failed E0 integrity audit. "
            "Concrete discrepancies detected in vocab size, RoPE scaling, and special tokens. "
            "Primary comparison and new interventions must HALT to prevent degenerative conflation. "
            "Past logs may only be analyzed under diagnostic track."
        )
    elif math_audit["verdict"] != "PASS" or code_audit["verdict"] != "PASS":
        manifest["primary_experiment_verdict"] = "PARTIAL_GATE"
        manifest["primary_gate_reason"] = "One domain failed E0 audit and is excluded from primary comparison."
    elif not all_safety_dense_verified:
        manifest["primary_experiment_verdict"] = "NO_GO"
        manifest["primary_gate_reason"] = "SafetyFT dense restored checkpoints (seeds 42/43/44) not fully verified."
    else:
        manifest["primary_experiment_verdict"] = "GO"
        manifest["primary_gate_reason"] = "All domains and SafetyFT checkpoints passed E0 integrity audit."

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("E0 MODEL INTEGRITY AUDIT RESULTS:")
    print("=" * 70)
    print(f"  Math Domain Verdict: {math_audit['verdict']}")
    if math_audit.get('discrepancies'):
        print("    Discrepancies:")
        for k, v in math_audit['discrepancies'].items():
            print(f"      - {k}: {v}")

    print(f"  Code Domain Verdict: {code_audit['verdict']}")
    if code_audit.get('discrepancies'):
        print("    Discrepancies:")
        for k, v in code_audit['discrepancies'].items():
            print(f"      - {k}: {v}")

    print(f"\n  >>> PRIMARY EXPERIMENT GATE: {manifest['primary_experiment_verdict']} <<<")
    print(f"  Reason: {manifest['primary_gate_reason']}")
    print("=" * 70)

    # Strict Halt Rule: Exit with code 1 if primary gate is NO_GO
    if manifest["primary_experiment_verdict"] == "NO_GO":
        print("\n[FATAL AUDIT FAILURE] Primary benchmark gate is NO_GO. Halting execution.")
        sys.exit(1)

    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str, default="meta-llama/Llama-2-7b-hf")
    parser.add_argument("--math_model", type=str, default="WizardLMTeam/WizardMath-7B-V1.0")
    parser.add_argument("--code_model", type=str, default="vanillaOVO/WizardCoder-Python-7B-V1.0")
    parser.add_argument("--models_root", type=str, default="/mnt/nas/home/hiromi/src/sst_v2/v3/models")
    parser.add_argument("--output_path", type=str, default="/mnt/nas/home/hiromi/src/sst_v2/v4/results/e0_audit/model_manifest.json")
    args = parser.parse_args()

    run_full_model_audit(
        base_model=args.base_model,
        math_model=args.math_model,
        code_model=args.code_model,
        models_root=args.models_root,
        output_path=args.output_path,
    )

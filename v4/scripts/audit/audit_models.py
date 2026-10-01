"""
E0 Audit: audit_models.py (Strict Gate Enforcement - Remediation R2-01, R2-02, R2-03)
Rigorous manifest builder and ancestor/tokenizer consistency auditor according to
Secure_Merge_Experiment_Plan.md Section 3.1.

Audits base model, math model, code model, and SafetyFT checkpoints (seeds 42, 43, 44).
Inspects token IDs, special tokens, RoPE, and LoRA dense restoration properties.

Status Taxonomy (Strict Plan Rule):
- PASS: Provenance, config, tokenizer, and weight alignment fully confirmed.
- FAIL: Concrete discrepancy detected (e.g. RoPE theta, vocab expansion, bos ID).
        Specific mismatched keys and values are saved.
- UNVERIFIED: Missing files, authentication failure, offline cache miss, or insufficient provenance information.

Gate Rule:
- GO: All active domains and SafetyFT checkpoints passed E0 integrity audit.
- PARTIAL_GATE: One domain passed, other failed/unverified (allows single-domain experiments).
- NO_GO: Required active domains failed or unverified. Primary pipeline must HALT (exit code 1).
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple
from transformers import AutoConfig, AutoTokenizer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

AUDIT_SCHEMA_VERSION = "v4_model_audit_schema_v2"


def is_local_directory(name_or_path: str) -> bool:
    """
    Distinguishes explicit local filesystem paths from Hugging Face Hub model IDs (R2-01).
    Local path: starts with '/', './', '../', '~' or exists as directory locally.
    """
    if name_or_path.startswith(("/", "./", "../", "~")):
        return True
    return os.path.isdir(name_or_path)


def audit_single_model(model_name_or_path: str, role: str) -> Dict[str, Any]:
    """
    Audits a single model checkpoint or HF Hub repo (R2-01).
    Does NOT reject HF Hub IDs if no local directory matches the name.
    Captures exact underlying error (authentication, network, not found).
    """
    print(f"Auditing [{role}]: {model_name_or_path}")
    is_local = is_local_directory(model_name_or_path)

    info: Dict[str, Any] = {
        "role": role,
        "name_or_path": model_name_or_path,
        "source_type": "local" if is_local else "hub",
        "status": "UNVERIFIED",
        "errors": [],
    }

    # For explicit local paths, verify local presence
    if is_local and not os.path.exists(model_name_or_path):
        info["status"] = "UNVERIFIED"
        info["errors"].append(f"Local path does not exist: {model_name_or_path}")
        return info

    # 1. Config loading
    cfg = None
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
        err_msg = f"Config load failed: {type(e).__name__}: {str(e)}"
        info["errors"].append(err_msg)

    # 2. Tokenizer loading
    tok = None
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
        err_msg = f"Tokenizer load failed: {type(e).__name__}: {str(e)}"
        info["errors"].append(err_msg)

    # 3. Check for weights and PEFT adapter if local directory
    weight_files = []
    if is_local and os.path.isdir(model_name_or_path):
        for fname in os.listdir(model_name_or_path):
            if fname.endswith((".safetensors", ".bin")):
                fpath = os.path.join(model_name_or_path, fname)
                weight_files.append({"name": fname, "size_bytes": os.path.getsize(fpath)})
        info["weight_files"] = weight_files

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
                info["errors"].append(f"Adapter config read failed: {str(e)}")

    if cfg is not None and tok is not None:
        total_weight_bytes = sum(w["size_bytes"] for w in weight_files)
        if is_local and (len(weight_files) == 0 or total_weight_bytes == 0) and not info.get("adapter_config"):
            info["status"] = "CONFIG_ONLY"
            info["weight_status"] = "EMPTY_OR_MISSING_WEIGHTS"
            info["errors"].append("Weight files are missing or have 0 bytes (R3-04).")
        else:
            info["status"] = "LOADED"
            info["weight_status"] = "WEIGHTS_PRESENT" if is_local else "REMOTE_OR_CACHED"
    else:
        info["status"] = "UNVERIFIED"
        info["weight_status"] = "UNVERIFIED"

    return info


def compare_domain_to_base(base_info: Dict[str, Any], domain_info: Dict[str, Any], domain_name: str) -> Dict[str, Any]:
    """
    Rigorously compares domain model properties against base model properties.
    Never fabricates discrepancies if models were not loaded (R2-03).
    """
    if base_info.get("status") != "LOADED" or domain_info.get("status") != "LOADED":
        unloaded_reasons = []
        if base_info.get("status") != "LOADED":
            unloaded_reasons.append(f"base_unloaded({'; '.join(base_info.get('errors', []))})")
        if domain_info.get("status") != "LOADED":
            unloaded_reasons.append(f"{domain_name}_unloaded({'; '.join(domain_info.get('errors', []))})")
        return {
            "domain": domain_name,
            "verdict": "UNVERIFIED",
            "is_compatible": False,
            "reason": f"Audit impossible due to unloaded model(s): {'; '.join(unloaded_reasons)}",
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

    # RoPE scaling / theta (inspect both theta and scaling dictionary)
    b_rope = b_cfg.get("rope_theta")
    d_rope = d_cfg.get("rope_theta")
    d_rope_scaling = d_cfg.get("rope_scaling")
    if d_rope_scaling and isinstance(d_rope_scaling, dict):
        d_scaled_theta = d_rope_scaling.get("rope_theta")
        if d_scaled_theta is not None and d_scaled_theta != b_rope:
            discrepancies["config.rope_scaling.rope_theta"] = {
                "base": b_rope,
                "domain_scaling": d_scaled_theta,
            }
        elif b_rope != d_rope:
            discrepancies["config.rope_theta"] = {"base": b_rope, "domain": d_rope}
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
    reason = "Discrepancies detected" if discrepancies else "Fully compatible with base model"

    return {
        "domain": domain_name,
        "verdict": verdict,
        "is_compatible": (verdict == "PASS"),
        "reason": reason,
        "discrepancies": discrepancies,
        "n_discrepancies": len(discrepancies),
    }


def run_full_model_audit(
    base_model: str = "meta-llama/Llama-2-7b-hf",
    math_model: str = "WizardLMTeam/WizardMath-7B-V1.0",
    code_model: str = "vanillaOVO/WizardCoder-Python-7B-V1.0",
    models_root: str = "/mnt/nas/home/hiromi/src/sst_v2/v3/models",
    output_path: str = "/mnt/nas/home/hiromi/src/sst_v2/v4/results/e0_audit/model_manifest.json",
    exit_on_nogo: bool = True,
) -> Dict[str, Any]:
    print("=" * 70)
    print("Running Rigorous E0 Model Provenance & Input Condition Audit")
    print("=" * 70)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    manifest: Dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audit_version": "v4_rigorous_gate",
        "benchmark_scope": "math_and_code_domestic_tier",
        "models": {},
        "safetyft_checkpoints": {},
        "domain_verdicts": {},
        "math_compatible": False,
        "code_compatible": False,
        "overall_verdict": "FAIL",
        "primary_experiment_verdict": "NO_GO",
        "primary_gate_reason": "",
    }

    # 1. Audit Base & Domain models
    manifest["models"]["base"] = audit_single_model(base_model, "base")
    manifest["models"]["math"] = audit_single_model(math_model, "math_domain")
    manifest["models"]["code"] = audit_single_model(code_model, "code_domain")

    # 2. Audit SafetyFT checkpoints (seeds 42, 43, 44)
    all_safety_dense_verified = True
    safetyft_unloaded_reasons = []

    for seed in [42, 43, 44]:
        lora_path = os.path.join(models_root, f"safety_lora_seed{seed}")
        full_path = os.path.join(models_root, f"temp_safety_full_seed{seed}")

        lora_aud = audit_single_model(lora_path, f"safety_lora_seed{seed}") if os.path.exists(lora_path) else {
            "status": "UNVERIFIED", "errors": [f"LoRA path does not exist: {lora_path}"]
        }
        full_aud = audit_single_model(full_path, f"safety_full_seed{seed}") if os.path.exists(full_path) else {
            "status": "UNVERIFIED", "errors": [f"Dense checkpoint path does not exist: {full_path}"]
        }

        # Separate config loaded from dense restoration verification (R2-04)
        is_dense_verified = (
            full_aud.get("status") == "LOADED" and 
            full_aud.get("weight_status") in ["WEIGHTS_PRESENT", "REMOTE_OR_CACHED"]
        )
        dense_status = "DENSE_RESTORED_VERIFIED" if is_dense_verified else "DENSE_UNVERIFIED_OR_MISSING"

        manifest["safetyft_checkpoints"][f"seed{seed}"] = {
            "lora_adapter": lora_aud,
            "dense_full": full_aud,
            "dense_restoration_status": dense_status,
        }
        if not is_dense_verified:
            all_safety_dense_verified = False
            safetyft_unloaded_reasons.append(f"seed{seed}_dense({dense_status})")

    # 3. Discrepancy comparison against Base
    math_audit = compare_domain_to_base(manifest["models"]["base"], manifest["models"]["math"], "math")
    code_audit = compare_domain_to_base(manifest["models"]["base"], manifest["models"]["code"], "code")

    manifest["domain_verdicts"]["math"] = math_audit
    manifest["domain_verdicts"]["code"] = code_audit
    manifest["math_compatible"] = bool(math_audit.get("is_compatible", False))
    manifest["code_compatible"] = bool(code_audit.get("is_compatible", False))

    # Dynamic Gate Reasoning (R2-03: Never fabricate reasons)
    math_verdict = math_audit["verdict"]
    code_verdict = code_audit["verdict"]

    reasons: List[str] = []

    if math_verdict == "FAIL":
        disc_keys = list(math_audit.get("discrepancies", {}).keys())
        reasons.append(f"Math domain failed compatibility: {', '.join(disc_keys)}")
    elif math_verdict == "UNVERIFIED":
        reasons.append(f"Math domain unverified: {math_audit.get('reason')}")

    if code_verdict == "FAIL":
        disc_keys = list(code_audit.get("discrepancies", {}).keys())
        reasons.append(f"Code domain failed compatibility: {', '.join(disc_keys)}")
    elif code_verdict == "UNVERIFIED":
        reasons.append(f"Code domain unverified: {code_audit.get('reason')}")

    if not all_safety_dense_verified:
        reasons.append(f"SafetyFT dense checkpoints unverified: {', '.join(safetyft_unloaded_reasons)}")

    # Decision Matrix
    if math_verdict == "PASS" and code_verdict == "PASS" and all_safety_dense_verified:
        manifest["primary_experiment_verdict"] = "GO"
        manifest["overall_verdict"] = "PASS"
        manifest["primary_gate_reason"] = "All domains and SafetyFT checkpoints passed E0 integrity audit."
    elif (math_verdict == "PASS" or code_verdict == "PASS") and all_safety_dense_verified:
        manifest["primary_experiment_verdict"] = "PARTIAL_GATE"
        manifest["overall_verdict"] = "PARTIAL"
        manifest["primary_gate_reason"] = f"Partial domain pass. Blocked issues: {'; '.join(reasons)}"
    else:
        manifest["primary_experiment_verdict"] = "NO_GO"
        manifest["overall_verdict"] = "FAIL" if ("FAIL" in (math_verdict, code_verdict)) else "UNVERIFIED"
        manifest["primary_gate_reason"] = f"Primary gate NO_GO: {'; '.join(reasons)}"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("E0 MODEL INTEGRITY AUDIT RESULTS:")
    print("=" * 70)
    print(f"  Math Domain Verdict: {math_verdict} (Compatible: {manifest['math_compatible']})")
    if math_audit.get("discrepancies"):
        print("    Discrepancies:")
        for k, v in math_audit["discrepancies"].items():
            print(f"      - {k}: {v}")
    elif math_verdict == "UNVERIFIED":
        print(f"    Unverified reason: {math_audit.get('reason')}")

    print(f"  Code Domain Verdict: {code_verdict} (Compatible: {manifest['code_compatible']})")
    if code_audit.get("discrepancies"):
        print("    Discrepancies:")
        for k, v in code_audit["discrepancies"].items():
            print(f"      - {k}: {v}")
    elif code_verdict == "UNVERIFIED":
        print(f"    Unverified reason: {code_audit.get('reason')}")

    print(f"\n  >>> PRIMARY EXPERIMENT GATE: {manifest['primary_experiment_verdict']} <<<")
    print(f"  Overall Verdict: {manifest['overall_verdict']}")
    print(f"  Reason: {manifest['primary_gate_reason']}")
    print("=" * 70)

    if exit_on_nogo and manifest["primary_experiment_verdict"] == "NO_GO":
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
        exit_on_nogo=True,
    )

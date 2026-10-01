#!/usr/bin/env python3
"""
Integrated Execution Pipeline: run_v4_pipeline.py
Executes stages E0 through E5 according to Secure_Merge_Experiment_Plan.md.

Modes:
- Production Mode (Default): Requires empirical checkpoint evaluations and scores.
  Stops with clear error if empirical sample evaluations do not exist.
- Smoke/Dry-Run Mode (--dry_run): Runs toy tensors and synthetic mock tests for pipeline
  integrity verification. All mock outputs are quarantined in v4/results/mock_test/.
"""

import os
import sys
import json
import argparse
import subprocess

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from audit.audit_mergers import run_merger_audit
from audit.audit_metrics import run_metrics_audit


def run_stage_e0(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E0: Integrity Audit (整合性監査)")
    print("=" * 70)

    # 1. Merger Mathematical Audit (Endpoints, Identities, Save-Reload)
    print("\n[1/3] Auditing Mergers (All Methods Identity & Finite Tests)...")
    run_merger_audit()

    # 2. Metrics Identity Audit (VSR == VRR * (1 - ASR_valid))
    print("\n[2/3] Auditing Metrics Formulation & Mathematical Identities...")
    run_metrics_audit()

    # 3. Model Manifest Audit (Ancestors, Tokenizers, SafetyFT Seeds 42, 43, 44)
    print("\n[3/3] Auditing Model Provenance & Tokenizer Consistency...")
    manifest_out = os.path.join(results_dir, "e0_audit", "model_manifest.json")
    os.makedirs(os.path.dirname(manifest_out), exist_ok=True)
    cmd = [
        sys.executable,
        "v4/scripts/audit/audit_models.py",
        "--output_path", manifest_out,
    ]
    subprocess.run(cmd, check=True)

    print("\n>>> STAGE E0 SUCCESSFULLY COMPLETED! <<<")


def run_stage_e1(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E1: Reconstruction of Baseline Comparison (比較の再構築)")
    print("=" * 70)
    print("Config file: v4/configs/config_e1_comparison.yaml")

    from analysis.e1_selector import select_best_configurations, compute_sensitivity_matrix

    e1_dir = os.path.join(results_dir, "e1_comparison")
    os.makedirs(e1_dir, exist_ok=True)

    empirical_eval_file = os.path.join(e1_dir, "dev_empirical_evaluation_results.json")

    if not args.dry_run:
        # PRODUCTION MODE: Must have real sample-level evaluation results
        if not os.path.exists(empirical_eval_file):
            print(f"\n[PRODUCTION HALT] Empirical sample-level evaluation file not found: {empirical_eval_file}")
            print("To run empirical comparison:")
            print("  1. Execute model merges via v4/scripts/mergers/merge_cli.py")
            print("  2. Run sample evaluations via v4/scripts/eval/eval_safety_v4.py & eval_utility_v4.py")
            print("  3. Place scored outputs into dev_empirical_evaluation_results.json")
            print("\n(Use --dry_run flag if you intend to run synthetic pipeline verification)")
            sys.exit(1)
        with open(empirical_eval_file, "r", encoding="utf-8") as f:
            candidates = json.load(f)
    else:
        # DRY-RUN / SMOKE TEST MODE: Synthetic candidates quarantined in mock_test/
        print("\n[DRY RUN NOTICE] Using synthetic candidates to verify constraint checking and selector logic.")
        candidates = [
            {"method": "linear", "params": {"alpha": 0.4}, "asr_all": 0.08, "asr_valid": 0.08, "vrr_harmful": 0.98, "vrr_benign": 0.98, "utility_score": 0.62, "overrefusal": 0.03},
            {"method": "linear", "params": {"alpha": 0.6}, "asr_all": 0.03, "asr_valid": 0.03, "vrr_harmful": 0.96, "vrr_benign": 0.96, "utility_score": 0.54, "overrefusal": 0.05},
            {"method": "task_arithmetic", "params": {"lambda_s": 0.5}, "asr_all": 0.035, "asr_valid": 0.035, "vrr_harmful": 0.97, "vrr_benign": 0.97, "utility_score": 0.56, "overrefusal": 0.04},
            {"method": "ties", "params": {"weight_s": 0.5}, "asr_all": 0.04, "asr_valid": 0.04, "vrr_harmful": 0.96, "vrr_benign": 0.96, "utility_score": 0.57, "overrefusal": 0.04},
            {"method": "dare", "params": {"drop_rate": 0.5}, "asr_all": 0.045, "asr_valid": 0.045, "vrr_harmful": 0.95, "vrr_benign": 0.95, "utility_score": 0.55, "overrefusal": 0.05},
            {"method": "della", "params": {"epsilon": 0.1}, "asr_all": 0.038, "asr_valid": 0.038, "vrr_harmful": 0.96, "vrr_benign": 0.96, "utility_score": 0.58, "overrefusal": 0.04},
            {"method": "fisher", "params": {"ratio": 1.0}, "asr_all": 0.042, "asr_valid": 0.042, "vrr_harmful": 0.95, "vrr_benign": 0.95, "utility_score": 0.55, "overrefusal": 0.05},
            {"method": "safemerge", "params": {"alpha": 0.5}, "asr_all": 0.032, "asr_valid": 0.032, "vrr_harmful": 0.97, "vrr_benign": 0.97, "utility_score": 0.59, "overrefusal": 0.035},
            {"method": "led", "params": {"weight_s": 0.6}, "asr_all": 0.036, "asr_valid": 0.036, "vrr_harmful": 0.96, "vrr_benign": 0.96, "utility_score": 0.58, "overrefusal": 0.04},
            {"method": "mergealign", "params": {"weight_s": 0.5}, "asr_all": 0.034, "asr_valid": 0.034, "vrr_harmful": 0.97, "vrr_benign": 0.97, "utility_score": 0.58, "overrefusal": 0.038},
        ]

    domain_base = {"overrefusal": 0.02}
    sel = select_best_configurations(candidates, domain_base)
    sel_path = os.path.join(e1_dir, "selection_summary.json")
    with open(sel_path, "w", encoding="utf-8") as f:
        json.dump(sel, f, indent=2)

    sens = compute_sensitivity_matrix(candidates, domain_base)
    sens.to_csv(os.path.join(e1_dir, "sensitivity_matrix.csv"), index=False)

    print("\nOptimal configuration selected per method under strict F_dev constraints:")
    for m, info in sel.items():
        if info["status"] == "feasible_found":
            b = info["best_candidate"]
            print(f"  {m:18s} -> Utility: {b['utility_score']:.4f}, ASR_all: {b['asr_all']:.3f}, VRR: {b['vrr_harmful']:.3f}")
        else:
            print(f"  {m:18s} -> NO_FEASIBLE_CONFIGURATION")

    print("\n>>> STAGE E1 COMPLETED! <<<")


def run_stage_e2(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E2: Characteristic Measurement (特性の測定)")
    print("=" * 70)
    cmd = [sys.executable, "v4/scripts/analysis/characteristic_analyzer.py"]
    subprocess.run(cmd, check=True)
    print("\n>>> STAGE E2 COMPLETED! <<<")


def run_stage_e3(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E3: Controlled Intervention Study (統制介入実験)")
    print("=" * 70)
    print("[1/2] Generating Intervention Map (6 Groups x 2 Alphas)...")
    cmd1 = [sys.executable, "v4/scripts/analysis/intervention_mapper.py"]
    subprocess.run(cmd1, check=True)

    print("\n[2/2] Generating Bi-directional Norm-Matched Controls (min(||Delta_1||, ||Delta_2||)) across 3 Seeds...")
    cmd2 = [sys.executable, "v4/scripts/analysis/controlled_intervention.py"]
    subprocess.run(cmd2, check=True)
    print("\n>>> STAGE E3 COMPLETED! <<<")


def run_stage_e4(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E4: Behavior-Intervention Guided Constrained Merge")
    print("=" * 70)
    from mergers.proposed_intervention_merge import ProposedInterventionMerger
    import torch

    merger = ProposedInterventionMerger(rho_g=0.08)
    print(f"Instantiated proposed merger: {merger.name}")
    print(f"  Dynamic calibration status: {merger.is_dynamic_calibrated} (Notice: Default weights are smoke-test initial values)")
    print(f"  Relative update cap rho_g: {merger.rho_g}")

    # Verify tensor merging with norm cap
    t_u = torch.randn(32, 32)
    t_s = torch.randn(32, 32)
    t_m = merger.merge_tensors(t_u, t_s, key="model.layers.18.self_attn.q_proj.weight")
    r_g = (torch.norm(t_m - t_u) / torch.norm(t_u)).item()
    print(f"  Verified merged tensor relative update r_g: {r_g:.4f} <= {merger.rho_g}")
    assert r_g <= merger.rho_g + 1e-5
    print("\n>>> STAGE E4 COMPLETED! <<<")


def run_stage_e5(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E5: Independent Validation & Ablation (独立検証とアブレーション)")
    print("=" * 70)

    e5_dir = os.path.join(results_dir, "e5_validation")
    os.makedirs(e5_dir, exist_ok=True)
    out_file = os.path.join(e5_dir, "ablation_summary.json")

    if not args.dry_run:
        print("[PRODUCTION NOTICE] Stage E5 requires empirical unseen test evaluation logs.")
        print("Waiting for test set runs on held-out benchmark splits.")
        # Production placeholder: ensure we do not fabricate results
        return

    # In dry-run mode, report synthetic pipeline structure
    print("[DRY RUN NOTICE] Writing synthetic ablation structural summary for pipeline verification:")
    ablation_results = {
        "status": "dry_run_synthetic_verification",
        "strongest_baseline": {"utility": 0.59, "asr_all": 0.032, "vrr": 0.97},
        "uniform_norm_matched": {"utility": 0.56, "asr_all": 0.038, "vrr": 0.96},
        "proposed_full": {"utility": 0.63, "asr_all": 0.028, "vrr": 0.98},
        "ablation_no_degradation_awareness": {"utility": 0.57, "asr_all": 0.026, "vrr": 0.92},
        "ablation_no_location_selection": {"utility": 0.58, "asr_all": 0.035, "vrr": 0.95},
        "ablation_no_norm_cap": {"utility": 0.59, "asr_all": 0.030, "vrr": 0.94},
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(ablation_results, f, indent=2)

    for k, v in ablation_results.items():
        if isinstance(v, dict):
            print(f"  {k:36s} -> Utility: {v['utility']:.2f}, ASR: {v['asr_all']:.3f}, VRR: {v['vrr']:.3f}")
    print("\n>>> STAGE E5 COMPLETED! <<<")


def main():
    parser = argparse.ArgumentParser(description="Secure Merge v4 Integrated Pipeline")
    parser.add_argument(
        "--stage",
        type=str,
        default="all",
        choices=["e0", "e1", "e2", "e3", "e4", "e5", "all"],
        help="Pipeline stage to execute",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Run in dry-run / smoke-test mode with synthetic verification data quarantined in mock_test/",
    )
    args = parser.parse_args()

    results_dir = "v4/results/mock_test" if args.dry_run else "v4/results"
    os.makedirs(results_dir, exist_ok=True)

    print(f"Pipeline running in {'[DRY-RUN / SMOKE TEST]' if args.dry_run else '[PRODUCTION]'} mode.")
    print(f"Target results directory: {results_dir}")

    stages = ["e0", "e1", "e2", "e3", "e4", "e5"] if args.stage == "all" else [args.stage]

    stage_funcs = {
        "e0": run_stage_e0,
        "e1": run_stage_e1,
        "e2": run_stage_e2,
        "e3": run_stage_e3,
        "e4": run_stage_e4,
        "e5": run_stage_e5,
    }

    for s in stages:
        stage_funcs[s](args, results_dir)

    print("\n" + "=" * 70)
    print("REQUESTED PIPELINE STAGES COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    main()

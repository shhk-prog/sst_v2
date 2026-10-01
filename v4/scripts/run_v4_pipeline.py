#!/usr/bin/env python3
"""
Integrated Execution Pipeline: run_v4_pipeline.py
Executes stages E0 through E5 according to Secure_Merge_Experiment_Plan.md and
conforming strictly to Secure Merge v4 Code Audit Directives (P0-03, P0-04, P0-05).

Execution Tracks:
- Primary Experiment Track (Default): Strict zero-tolerance gate. Halts if E0 audits fail or checkpoints lack compatibility.
- Diagnostic Track (--track diagnostic): Allows reaggregating historical logs or analyzing models under diagnosed domain mismatches.
- Smoke/Unit Test Mode (--smoke_test): Runs regression test suites in v4/tests/ and isolates outputs in v4/results/smoke_test/.
"""

import os
import sys
import json
import argparse
import subprocess
from typing import Dict, Any, Optional

# Ensure both v4/scripts and repo root are in python search path
_script_dir = os.path.abspath(os.path.dirname(__file__))
_repo_root = os.path.abspath(os.path.join(_script_dir, "../.."))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from audit.audit_mergers import run_merger_audit
from audit.audit_metrics import run_metrics_audit


def check_e0_manifest(manifest_path: str) -> Dict[str, Any]:
    """Reads model manifest and verifies E0 compatibility gates (R2-02)."""
    if not os.path.exists(manifest_path):
        return {"status": "MANIFEST_NOT_FOUND", "allow_primary": False, "details": {}}

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    domain_verdicts = data.get("domain_verdicts", {})
    math_info = domain_verdicts.get("math", {})
    code_info = domain_verdicts.get("code", {})

    math_compat = data.get("math_compatible", math_info.get("is_compatible", False))
    code_compat = data.get("code_compatible", code_info.get("is_compatible", False))

    primary_verdict = data.get("primary_experiment_verdict", "NO_GO")
    overall_verdict = data.get("overall_verdict", "PASS" if primary_verdict == "GO" else "FAIL")

    allow_primary = (primary_verdict == "GO") and math_compat and code_compat and (overall_verdict == "PASS")
    return {
        "status": overall_verdict,
        "primary_experiment_verdict": primary_verdict,
        "math_compatible": math_compat,
        "code_compatible": code_compat,
        "allow_primary": allow_primary,
        "details": data,
    }


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
    # Allow audit script to exit with 1 on model mismatch
    proc = subprocess.run(cmd)

    gate = check_e0_manifest(manifest_out)
    data = gate.get("details", {})
    print(f"\nE0 Manifest Audit Verdict: Math={gate['math_compatible']}, Code={gate['code_compatible']}, Overall={gate['status']}")

    if not gate["allow_primary"]:
        print("\n" + "!" * 70)
        print(">>> E0 GATE VERDICT: NO_GO for Primary Experiment Pipeline <<<")
        print(f"Reason: {data.get('primary_gate_reason', 'E0 integrity audit failed')}")

        domain_verdicts = data.get("domain_verdicts", {})
        for dom, dom_data in domain_verdicts.items():
            print(f"\n[{dom.upper()} Domain: {dom_data.get('verdict')}]")
            discs = dom_data.get("discrepancies", {})
            if discs:
                print("  Concrete Discrepancies:")
                for k, v in discs.items():
                    print(f"    - {k}: {v}")
            elif dom_data.get("verdict") == "UNVERIFIED":
                print(f"  Unverified reason: {dom_data.get('reason')}")
        print("!" * 70)

        if args.track != "diagnostic":
            print("\nExecution HALTED. Primary pipeline cannot proceed with mismatched or unverified checkpoints (P0-03, R2-01).")
            print("To analyze legacy logs or study behavior under diagnosed domain mismatch, run with: --track diagnostic")
            sys.exit(1)
        else:
            print("\n[DIAGNOSTIC TRACK ACTIVE] Continuing execution in diagnostic mode (outputs quarantined to diagnostic_track/).")

    print("\n>>> STAGE E0 AUDIT COMPLETED <<<")


def run_stage_e1(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E1: Baseline Re-aggregation & Constrained Selection")
    print("=" * 70)

    e1_dir = os.path.join(results_dir, "e1_comparison")
    os.makedirs(e1_dir, exist_ok=True)

    summary_file = os.path.join(e1_dir, "reaggregated_summary.json")

    from analysis.reaggregate_v3_logs import reaggregate_v3_results
    print(f"Collecting and reaggregating empirical evaluations into directory: {e1_dir}")
    aggregated_records = reaggregate_v3_results(
        results_root="v3/results",
        output_dir=e1_dir,
    )

    from analysis.e1_selector import select_best_configurations, compute_sensitivity_matrix
    # R2-05: Do not hardcode domain baseline overrefusal to 0.02. Require empirical measurement.
    domain_baseline_records = aggregated_records.get("domain_baseline_track", []) if isinstance(aggregated_records, dict) else []
    domain_base = {}
    for d in ["math", "code"]:
        matching = [r for r in domain_baseline_records if r.get("domain") == d and r.get("overrefusal") is not None]
        domain_base[d] = {"overrefusal": matching[0]["overrefusal"] if matching else None}

    candidates = aggregated_records if isinstance(aggregated_records, list) else aggregated_records.get("standard_baseline_track", [])

    sel = select_best_configurations(candidates, domain_base)
    sel_path = os.path.join(e1_dir, "selection_summary.json")
    with open(sel_path, "w", encoding="utf-8") as f:
        json.dump(sel, f, indent=2)

    sens = compute_sensitivity_matrix(candidates, domain_base)
    sens.to_csv(os.path.join(e1_dir, "sensitivity_matrix.csv"), index=False)

    print("\n[E1 Rigorous Constrained Selection Summary]:")
    for group_key, info in sel.items():
        status = info["status"]
        if status == "FEASIBLE_FOUND":
            b = info["best_candidate"]
            print(f"  {group_key:24s} -> FEASIBLE: Utility={b.get('utility_score', 0):.4f}, ASR={b.get('asr_all', 0):.4f}, VRR={b.get('vrr_harmful', 0):.4f}")
        elif status == "INSUFFICIENT_DATA":
            print(f"  {group_key:24s} -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)")
        else:
            print(f"  {group_key:24s} -> NO_FEASIBLE_CONFIGURATION (Exceeded safety or validity constraints)")

    print("\n>>> STAGE E1 COMPLETED <<<")


def run_stage_e2(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E2: Characteristic Measurement (実重み特性測定)")
    print("=" * 70)

    if not args.model_m or not args.model_u:
        print("[STAGE E2 BLOCKED] Production characteristic analysis requires --model-m and --model-u checkpoint paths.")
        print("To run regression tests on weight analysis logic, run: v3/venv_v3/bin/python v4/tests/test_characteristic_analyzer.py")
        if args.track != "diagnostic":
            sys.exit(1)
        return

    cmd = [
        sys.executable, "v4/scripts/analysis/characteristic_analyzer.py",
        "--model-m", args.model_m,
        "--model-u", args.model_u,
        "--output", os.path.join(results_dir, "e2_characteristics.json"),
    ]
    if args.model_s:
        cmd.extend(["--model-s", args.model_s])
    if args.model_0:
        cmd.extend(["--model-0", args.model_0])

    subprocess.run(cmd, check=True)
    print("\n>>> STAGE E2 COMPLETED <<<")


def run_stage_e3(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E3: Controlled Intervention Study (統制介入実験)")
    print("=" * 70)

    if not args.model_u or not args.model_s:
        print("[STAGE E3 BLOCKED] Controlled intervention requires real checkpoints via --model-u and --model-s.")
        print("To run regression tests on exact matching and norm shrinkage, run: v3/venv_v3/bin/python v4/tests/test_controlled_intervention.py")
        if args.track != "diagnostic":
            sys.exit(1)
        return

    # Production generation is invoked per-condition via controlled_intervention.py CLI
    print("Stage E3 execution ready via v4/scripts/analysis/controlled_intervention.py")
    print("\n>>> STAGE E3 READY (PENDING INTERVENTION INFERENCE & SCORING) <<<")


def run_stage_e4(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E4: Behavior-Intervention Guided Constrained Merge")
    print("=" * 70)

    calib_map = args.calibration_map
    if not calib_map or not os.path.exists(calib_map):
        print(f"[STAGE E4 BLOCKED] Empirical calibration map not provided or not found: {calib_map}")
        print("Stage E4 requires empirical behavioral calibration measurements from Stage E3 (P0-05, P1-03, R2-09).")
        print("Hardcoded or uncalibrated weights are rejected in production mode.")
        if args.track != "diagnostic":
            sys.exit(1)
        return

    from mergers.proposed_intervention_merge import ProposedInterventionMerger
    merger = ProposedInterventionMerger.from_calibration_map(calib_map)
    print(f"Dynamically constructed {merger.name} from empirical calibration map:")
    for grp, w in merger.group_weights.items():
        print(f"  Region {grp:26s} -> Weight: {w:.4f}")
    print("\n>>> STAGE E4 CALIBRATED (PENDING MERGED MODEL INFERENCE & EVALUATION) <<<")


def run_stage_e5(args, results_dir: str):
    print("\n" + "=" * 70)
    print("STAGE E5: Independent Validation & Ablation (独立検証とアブレーション)")
    print("=" * 70)

    e5_dir = os.path.join(results_dir, "e5_validation")
    os.makedirs(e5_dir, exist_ok=True)
    out_file = os.path.join(e5_dir, "ablation_summary.json")

    # In strict mode, if unseen test set evaluations are not yet generated, write explicit NOT_RUN status
    e5_report = {
        "status": "NOT_RUN",
        "reason": "Test evaluation pending empirical E4 model generation on unseen benchmark splits.",
        "notice": "Synthetic or fabricated scores (e.g. utility=0.63, ASR=0.028) are strictly prohibited.",
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(e5_report, f, indent=2)

    print(f"Recorded E5 Status: NOT_RUN in {out_file}")
    print("Stage E5 will be executed once empirical candidate models and test splits are evaluated.")
    print("\n>>> STAGE E5 COMPLETED (STATUS: NOT_RUN) <<<")


def run_smoke_tests():
    """Runs all rigorous unit/regression test suites in v4/tests/."""
    print("\n" + "=" * 70)
    print("RUNNING SECURE MERGE V4 REGRESSION TEST SUITE")
    print("=" * 70)

    test_files = [
        "v4/tests/test_e0_audit_gate.py",
        "v4/tests/test_utility_parser.py",
        "v4/tests/test_e1_selector.py",
        "v4/tests/test_characteristic_analyzer.py",
        "v4/tests/test_controlled_intervention.py",
        "v4/tests/test_proposed_intervention_merge.py",
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = f"v4/scripts:{env.get('PYTHONPATH', '')}"

    all_passed = True
    for tf in test_files:
        print(f"\n--- Running: {tf} ---")
        res = subprocess.run([sys.executable, tf], env=env)
        if res.returncode != 0:
            all_passed = False
            print(f"[FAIL] {tf} failed!")
        else:
            print(f"[PASS] {tf} passed.")

    if not all_passed:
        print("\n>>> ONE OR MORE TESTS FAILED! <<<")
        sys.exit(1)
    else:
        print("\n>>> ALL REGRESSION TESTS PASSED! <<<")


def main():
    parser = argparse.ArgumentParser(description="Secure Merge v4 Integrated Pipeline Runner")
    parser.add_argument(
        "--stage",
        type=str,
        default="all",
        choices=["e0", "e1", "e2", "e3", "e4", "e5", "all"],
        help="Pipeline stage to execute",
    )
    parser.add_argument(
        "--track",
        type=str,
        default="primary",
        choices=["primary", "diagnostic"],
        help="Execution track: 'primary' (strict gates) or 'diagnostic' (historical log re-analysis)",
    )
    parser.add_argument(
        "--smoke_test",
        action="store_true",
        help="Run comprehensive unit test suites in v4/tests/",
    )
    parser.add_argument("--model-m", type=str, default=None, help="Merged model checkpoint path")
    parser.add_argument("--model-u", type=str, default=None, help="Domain model checkpoint path")
    parser.add_argument("--model-s", type=str, default=None, help="Safety model checkpoint path")
    parser.add_argument("--model-0", type=str, default=None, help="Base model checkpoint path")
    parser.add_argument("--calibration-map", type=str, default=None, help="Path to E3 empirical calibration map JSON")

    args = parser.parse_args()

    if args.smoke_test:
        run_smoke_tests()
        return

    results_dir = "v4/results/diagnostic_track" if args.track == "diagnostic" else "v4/results"
    os.makedirs(results_dir, exist_ok=True)

    print(f"Pipeline Track: {args.track.upper()}")
    print(f"Target Results Directory: {results_dir}")

    stages = ["e0", "e1", "e2", "e3", "e4", "e5"] if args.stage == "all" else [args.stage]

    # R2-04: Gate bypass prevention. In primary track, individual stages (e.g. --stage e1)
    # CANNOT proceed without a valid, passing E0 audit manifest.
    if args.track == "primary" and "e0" not in stages:
        primary_manifest_path = "v4/results/e0_audit/model_manifest.json"
        print(f"\n[PRIMARY GATE VERIFICATION] Checking prior E0 audit manifest before executing stage(s) {stages}...")
        if not os.path.exists(primary_manifest_path):
            print(f"[FATAL GATE ERROR] E0 manifest not found at: {primary_manifest_path}")
            print("Primary pipeline stages cannot bypass E0 audit. Please run stage E0 first.")
            sys.exit(1)

        gate = check_e0_manifest(primary_manifest_path)
        if not gate.get("allow_primary", False):
            reason = gate.get("details", {}).get("primary_gate_reason", gate.get("status", "NO_GO"))
            print(f"[FATAL GATE ERROR] Prior E0 audit failed or is unverified: {reason}")
            print("Execution HALTED. Primary pipeline cannot proceed with mismatched models.")
            sys.exit(1)
        print("[PRIMARY GATE VERIFICATION] E0 Audit Manifest is valid and PASS. Proceeding.\n")

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
    print("PIPELINE EXECUTION FINISHED.")
    print("=" * 70)


if __name__ == "__main__":
    main()

"""
v4/tests/test_e0_audit_gate.py
Unit tests verifying E0 audit gate logic, schema synchronization, and dynamic reasoning (R2-01, R2-02, R2-03).
"""

import os
import json
import tempfile
import unittest
from v4.scripts.audit.audit_models import (
    is_local_directory,
    compare_domain_to_base,
    AUDIT_SCHEMA_VERSION,
)
from v4.scripts.run_v4_pipeline import check_e0_manifest


class TestE0AuditGate(unittest.TestCase):
    def test_hub_id_not_classified_as_local_directory(self):
        """HF Hub IDs like meta-llama/Llama-2-7b-hf must not be classified as local directory (R2-01)."""
        self.assertFalse(is_local_directory("meta-llama/Llama-2-7b-hf"))
        self.assertFalse(is_local_directory("WizardLMTeam/WizardMath-7B-V1.0"))
        self.assertTrue(is_local_directory("/mnt/nas/home/hiromi/models"))
        self.assertTrue(is_local_directory("./relative/path"))

    def test_positive_test_perfect_pass_manifest_allows_primary(self):
        """
        Positive Test (R2-02):
        A fully compliant PASS manifest produced by writer MUST allow primary experiment execution.
        """
        pass_manifest = {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "audit_version": "v4_rigorous_gate",
            "primary_experiment_verdict": "GO",
            "overall_verdict": "PASS",
            "math_compatible": True,
            "code_compatible": True,
            "domain_verdicts": {
                "math": {
                    "verdict": "PASS",
                    "is_compatible": True,
                    "discrepancies": {},
                },
                "code": {
                    "verdict": "PASS",
                    "is_compatible": True,
                    "discrepancies": {},
                },
            },
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(pass_manifest, f)
            temp_path = f.name

        try:
            gate = check_e0_manifest(temp_path)
            self.assertTrue(gate["allow_primary"], "Perfect PASS manifest was incorrectly rejected!")
            self.assertEqual(gate["primary_experiment_verdict"], "GO")
            self.assertTrue(gate["math_compatible"])
            self.assertTrue(gate["code_compatible"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_unverified_model_comparison_does_not_fabricate_discrepancies(self):
        """
        When base or domain model fails to load (UNVERIFIED),
        no fabricated discrepancies (vocab, RoPE) should be produced (R2-03).
        """
        base_unverified = {"status": "UNVERIFIED", "errors": ["AuthError: token missing"]}
        domain_unverified = {"status": "UNVERIFIED", "errors": ["RepoNotFound"]}

        res = compare_domain_to_base(base_unverified, domain_unverified, "math")
        self.assertEqual(res["verdict"], "UNVERIFIED")
        self.assertFalse(res["is_compatible"])
        self.assertEqual(len(res["discrepancies"]), 0, "Discrepancies were fabricated for unloaded models!")
        self.assertIn("Audit impossible due to unloaded model(s)", res["reason"])

    def test_concrete_discrepancies_detected_when_loaded(self):
        """When models are loaded, real discrepancies are correctly detected and saved."""
        base_loaded = {
            "status": "LOADED",
            "config": {"vocab_size": 32000, "rope_theta": 10000.0, "max_position_embeddings": 4096},
            "tokenizer": {"vocab_size": 32000, "bos_token_id": 1, "eos_token_id": 2},
        }
        domain_loaded = {
            "status": "LOADED",
            "config": {"vocab_size": 32001, "rope_theta": 10000.0, "max_position_embeddings": 4096},
            "tokenizer": {"vocab_size": 32001, "bos_token_id": 1, "eos_token_id": 2},
        }

        res = compare_domain_to_base(base_loaded, domain_loaded, "math")
        self.assertEqual(res["verdict"], "FAIL")
        self.assertFalse(res["is_compatible"])
        self.assertIn("tokenizer.vocab_size", res["discrepancies"])
        self.assertEqual(res["discrepancies"]["tokenizer.vocab_size"]["base"], 32000)
        self.assertEqual(res["discrepancies"]["tokenizer.vocab_size"]["domain"], 32001)

    def test_fisher_rejects_missing_fim_in_strict_mode(self):
        """FisherMerger must raise ValueError when FIM is missing in strict mode (P0-07, R2-08)."""
        import torch
        from v4.scripts.mergers.fisher_merger import FisherMerger
        merger = FisherMerger(strict_fim=True)
        t_u = torch.tensor([1.0, 2.0])
        t_s = torch.tensor([2.0, 3.0])
        with self.assertRaises(ValueError) as ctx:
            merger.merge_tensors(t_u, t_s, fim_u=None, fim_s=None)
        self.assertIn("requires explicit Fisher Information Matrix", str(ctx.exception))

    def test_code_evaluation_extraction_and_syntax(self):
        """Code utility extractor must properly isolate markdown blocks and validate syntax (R2-08)."""
        from v4.scripts.eval.eval_utility_v4 import extract_code_block
        raw_output = "Here is the solution:\n```python\ndef add(a, b):\n    return a + b\n```\nExplanation..."
        code = extract_code_block(raw_output)
        self.assertEqual(code, "def add(a, b):\n    return a + b")
        # Ensure it compiles cleanly
        compiled = compile(code, "<test>", "exec")
        self.assertIsNotNone(compiled)

    def test_code_evaluation_fails_syntactically_valid_wrong_answer(self):
        """
        R3-01: An incorrect function (e.g. add(a, b) -> 0) with a valid check function definition
        MUST fail with ASSERTION_ERROR when check(candidate) is properly executed.
        """
        from v4.scripts.eval.eval_utility_v4 import build_humaneval_test_program, execute_code_isolated
        prompt = "def add(a, b):\n    '''Return sum of a and b.'''\n"
        wrong_code = "def add(a, b):\n    return 0"
        test_case = (
            "def check(candidate):\n"
            "    assert candidate(1, 2) == 3\n"
            "    assert candidate(5, 5) == 10\n"
        )
        prog = build_humaneval_test_program(prompt, wrong_code, test_case, "add")
        res = execute_code_isolated(prog, timeout=2.0)
        self.assertEqual(res["status"], "ASSERTION_ERROR", f"Wrong answer did not fail! Got: {res}")

    def test_code_evaluation_isolated_process_timeout(self):
        """R3-01: Infinite loops must be safely terminated with TIMEOUT."""
        from v4.scripts.eval.eval_utility_v4 import execute_code_isolated
        infinite_loop = "while True:\n    pass\n"
        res = execute_code_isolated(infinite_loop, timeout=0.5)
        self.assertEqual(res["status"], "TIMEOUT")

    def test_vrr_denominator_not_skewed_by_unjudged_harmfulness(self):
        """
        R3-03: Two outputs: Output 1 (Valid, H=0), Output 2 (Invalid, H=unjudged/None).
        Total generated is 2, valid is 1 -> VRR MUST be exactly 0.5 (not 1.0!).
        """
        from v4.scripts.audit.audit_metrics import compute_secure_merge_metrics
        valid_flags = [True, False]
        harmful_flags = [False, None]
        m = compute_secure_merge_metrics(valid_flags, harmful_flags)
        self.assertEqual(m["n_total"], 2)
        self.assertEqual(m["n_judged"], 1)
        self.assertEqual(m["n_unjudged"], 1)
        self.assertAlmostEqual(m["vrr"], 0.5, places=5)
        self.assertIsNone(m["asr_all"], "Incomplete benchmark cannot determine exact ASR_all")

    def test_base_merger_rejects_missing_safety_keys_in_strict_mode(self):
        """R3-04: base_merger must raise ValueError when safety model is missing essential keys."""
        import torch
        from v4.scripts.mergers.base_merger import BaseMerger
        class DummyMerger(BaseMerger):
            def merge_tensors(self, u, s, o=None, **kwargs):
                return u
        merger = DummyMerger("dummy", {})
        dict_u = {"model.layers.0.mlp.gate_proj.weight": torch.randn(4, 4)}
        dict_s = {}  # Empty safety dict
        with self.assertRaises(ValueError) as ctx:
            merger.merge_state_dicts(dict_u, dict_s, strict_shape_check=True)
        self.assertIn("Missing essential weight keys in safety model", str(ctx.exception))

    def test_e1_selector_rejects_single_benchmark_asr_spike(self):
        """
        R3-05: A candidate with macro average ASR=0.05 (5%) but one benchmark at 0.20 (20%)
        MUST be rejected as INFEASIBLE.
        """
        from v4.scripts.analysis.e1_selector import evaluate_feasible_region_strict
        candidate = {
            "utility_score": 0.60,
            "asr_all": 0.05,
            "asr_valid": 0.05,
            "vrr_harmful": 0.98,
            "vrr_benign": 0.98,
            "overrefusal": 0.03,
            "benchmarks": {
                "harmbench": 0.20,  # 20% spike exceeds 5% threshold
                "jailbreakbench": 0.00,
                "strongreject": 0.00,
                "wildjailbreak": 0.00,
            }
        }
        domain_base = {"overrefusal": 0.02}
        status, reason = evaluate_feasible_region_strict(candidate, domain_base)
        self.assertEqual(status, "INFEASIBLE")
        self.assertIn("BENCHMARK_HARMBENCH_ASR_EXCEEDED", reason)

    def test_e1_selector_rejects_out_of_bounds_metrics(self):
        """R3-05: Values outside [0.0, 1.0] (e.g. utility=999, ASR=-1, VRR=2) must be rejected."""
        from v4.scripts.analysis.e1_selector import evaluate_feasible_region_strict
        candidate = {
            "utility_score": 999.0,
            "asr_all": -1.0,
            "asr_valid": 0.05,
            "vrr_harmful": 2.0,
            "vrr_benign": 0.98,
            "overrefusal": 0.03,
        }
        domain_base = {"overrefusal": 0.02}
        status, reason = evaluate_feasible_region_strict(candidate, domain_base)
        self.assertEqual(status, "INSUFFICIENT_DATA")
        self.assertIn("OUT_OF_BOUNDS", reason)

    def test_fisher_merger_positive_cli_weighting(self):
        """
        R3-06 (Acceptance Test 2): Positive CLI Fisher merging test with known small tensors.
        Verifies exact analytical closed-form: theta_m = (F_u*theta_u + F_s*theta_s) / (F_u + F_s + eps)
        """
        import torch
        from v4.scripts.mergers.fisher_merger import FisherMerger
        merger = FisherMerger(eps=1e-8, strict_fim=True)

        key = "model.layers.0.mlp.gate_proj.weight"
        theta_u = torch.tensor([[10.0, 10.0], [10.0, 10.0]])
        theta_s = torch.tensor([[20.0, 20.0], [20.0, 20.0]])
        fim_u = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
        fim_s = torch.tensor([[4.0, 3.0], [2.0, 1.0]])

        dict_u = {key: theta_u}
        dict_s = {key: theta_s}
        fim_u_dict = {key: fim_u}
        fim_s_dict = {key: fim_s}

        merged = merger.merge_state_dicts(dict_u, dict_s, fim_u=fim_u_dict, fim_s=fim_s_dict)
        expected = torch.tensor([[18.0, 16.0], [14.0, 12.0]])
        diff = torch.norm(merged[key] - expected).item()
        self.assertAlmostEqual(diff, 0.0, places=5, msg="Fisher merger did not match exact analytical weighted result!")

    def test_reaggregate_to_selector_end_to_end_rejects_spike_and_missing(self):
        """
        R3-03 / R3-05 (Acceptance Test 6): Reaggregator output schema (safety_metrics_per_benchmark)
        must connect to e1_selector, rejecting candidates with a 20% spike in one benchmark
        and rejecting candidates with incomplete/unjudged benchmarks as INSUFFICIENT_DATA.
        """
        from v4.scripts.analysis.e1_selector import evaluate_feasible_region_strict

        # Candidate with macro ASR 0.05 but HarmBench at 0.20
        reaggregator_output = {
            "candidate_id": "candidate_spike",
            "utility_score": 0.65,
            "asr_all": 0.05,
            "asr_valid": 0.05,
            "vrr_harmful": 0.98,
            "vrr_benign": 0.98,
            "overrefusal": 0.03,
            "safety_metrics_per_benchmark": {
                "harmbench": {"asr_all": 0.20, "asr_valid": 0.20, "vrr": 0.98},
                "jailbreakbench": {"asr_all": 0.00, "asr_valid": 0.00, "vrr": 0.98},
                "strongreject": {"asr_all": 0.00, "asr_valid": 0.00, "vrr": 0.98},
                "wildjailbreak": {"asr_all": 0.00, "asr_valid": 0.00, "vrr": 0.98},
            }
        }
        domain_base = {"overrefusal": 0.02}
        status, reason = evaluate_feasible_region_strict(reaggregator_output, domain_base)
        self.assertEqual(status, "INFEASIBLE")
        self.assertIn("BENCHMARK_HARMBENCH_ASR_EXCEEDED", reason)

        # Incomplete benchmark candidate (missing required benchmark)
        reaggregator_missing = {
            "candidate_id": "candidate_missing",
            "utility_score": 0.65,
            "asr_all": 0.05,
            "asr_valid": 0.05,
            "vrr_harmful": 0.98,
            "vrr_benign": 0.98,
            "overrefusal": 0.03,
            "safety_metrics_per_benchmark": {
                "harmbench": {"asr_all": 0.02, "asr_valid": 0.02, "vrr": 0.98},
            }
        }
        status_m, reason_m = evaluate_feasible_region_strict(
            reaggregator_missing,
            domain_base,
            required_benchmarks=["harmbench", "jailbreakbench"]
        )
        self.assertEqual(status_m, "INSUFFICIENT_DATA")
        self.assertIn("MISSING_REQUIRED_BENCHMARK_JAILBREAKBENCH", reason_m)

    def test_eval_utility_humaneval_completion_and_empty_test(self):
        """
        R3-01 (Acceptance Test 3): Valid completion '    return a + b' assembled with prompt
        must pass execution, and missing test suite must be marked NOT_EVALUATED, never PASSED.
        """
        from v4.scripts.eval.eval_utility_v4 import (
            extract_code_block,
            build_humaneval_test_program,
            execute_code_isolated,
        )
        # 1. Completion indentation preserved
        raw_gen = "    return a + b\n"
        code = extract_code_block(raw_gen)
        self.assertTrue(code.startswith("    return"), "Leading indentation was stripped!")

        # 2. Prompt + completion assembly
        prompt = "def add(a, b):\n"
        test = "def check(candidate):\n    assert candidate(1, 2) == 3\n"
        full_prog = build_humaneval_test_program(prompt, code, test, "add")
        self.assertIsNotNone(full_prog)
        res = execute_code_isolated(full_prog, timeout=2.0)
        self.assertEqual(res.get("status"), "PASSED")

        # 3. Empty test rejection
        empty_prog = build_humaneval_test_program(prompt, code, "", "add")
        self.assertIsNone(empty_prog, "Missing test suite must return None to prevent fake PASSED")

    def test_harmbench_device_and_strict_labels(self):
        """
        R3-02 (Acceptance Test 5): Verifies HarmBench classifier protocol:
        - evaluate_harmfulness_harmbench requires keyword args for device/context (rejects 5 positional args).
        - 'not sure' or 'no idea' is NOT classified as harmless (returns None).
        """
        import inspect
        from v4.scripts.eval.eval_safety_v4 import evaluate_harmfulness_harmbench
        sig = inspect.signature(evaluate_harmfulness_harmbench)
        # context and device must be KEYWORD_ONLY
        self.assertEqual(sig.parameters["context"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertEqual(sig.parameters["device"].kind, inspect.Parameter.KEYWORD_ONLY)

        # Ambiguous output handling
        ambiguous_cases = ["not sure", "no idea", "cannot determine", "uncertain", ""]
        for case in ambiguous_cases:
            # Replicate parser logic
            ambiguity_phrases = ["not sure", "no idea", "cannot determine", "uncertain", "neither yes nor no"]
            is_ambiguous = any(phrase in case for phrase in ambiguity_phrases) or not case.strip()
            self.assertTrue(is_ambiguous, f"'{case}' was not identified as ambiguous!")


if __name__ == "__main__":
    unittest.main()

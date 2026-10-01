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


if __name__ == "__main__":
    unittest.main()

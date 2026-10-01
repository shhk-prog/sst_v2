"""
E0 Audit: audit_mergers.py
Verifies mathematical integrity, endpoints, identity merges, and finite values for ALL merge methods.
Includes reload consistency (save -> reload -> compare weights & logits).
Adheres strictly to Secure_Merge_Experiment_Plan.md Section 3.2.
"""

import sys
import os
import shutil
import tempfile
import torch
import torch.nn as nn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from mergers import get_merger, MERGER_REGISTRY


class ToyModel(nn.Module):
    def __init__(self, d_in=32, d_out=32):
        super().__init__()
        self.fc1 = nn.Linear(d_in, d_out, bias=False)
        self.fc2 = nn.Linear(d_out, d_out, bias=False)

    def forward(self, x):
        return self.fc2(torch.relu(self.fc1(x)))


def run_merger_audit():
    print("=" * 60)
    print("Running Rigorous E0 Merger Mathematical Audit")
    print("=" * 60)

    torch.manual_seed(42)
    device = torch.device("cpu")

    # Toy tensors
    shape = (64, 64)
    theta_0 = torch.randn(shape, dtype=torch.float32, device=device)
    delta_u = torch.randn(shape, dtype=torch.float32, device=device) * 0.1
    delta_s = torch.randn(shape, dtype=torch.float32, device=device) * 0.1
    theta_u = theta_0 + delta_u
    theta_s = theta_0 + delta_s

    audit_results = {}

    # Test 1: Linear Safety-Patch Endpoints
    print("\n[Audit 1] Linear Safety-Patch Endpoints:")
    linear_0 = get_merger("linear", alpha=0.0).merge_tensors(theta_u, theta_s)
    linear_1 = get_merger("linear", alpha=1.0).merge_tensors(theta_u, theta_s)
    diff_u = (linear_0 - theta_u).abs().max().item()
    diff_s = (linear_1 - theta_s).abs().max().item()
    print(f"  alpha=0.0 endpoint diff from theta_u: {diff_u:.8f}")
    print(f"  alpha=1.0 endpoint diff from theta_s: {diff_s:.8f}")
    assert diff_u < 1e-6, "Linear alpha=0 must strictly equal theta_u!"
    assert diff_s < 1e-6, "Linear alpha=1 must strictly equal theta_s!"
    audit_results["linear_endpoints"] = "PASSED"

    # Test 2: Task Arithmetic Endpoints & Distinction
    print("\n[Audit 2] Task Arithmetic Endpoints & Distinction:")
    ta_u_only = get_merger("task_arithmetic", lambda_u=1.0, lambda_s=0.0).merge_tensors(theta_u, theta_s, theta_0)
    diff_ta_u = (ta_u_only - theta_u).abs().max().item()
    print(f"  lambda_u=1.0, lambda_s=0.0 diff from theta_u: {diff_ta_u:.8f}")
    assert diff_ta_u < 1e-6, "Task Arithmetic (lambda_u=1, lambda_s=0) must equal theta_u!"
    audit_results["task_arithmetic_endpoints"] = "PASSED"

    # Test 3: Identity Merging across ALL registered methods
    # When theta_u == theta_s == theta_0, merged must strictly equal theta_0
    print("\n[Audit 3] Identity Merging across ALL registered methods:")
    all_methods = sorted(list(set(MERGER_REGISTRY.keys())))
    for name in all_methods:
        merger = get_merger(name)
        res = merger.merge_tensors(theta_0, theta_0, theta_0, key="model.layers.15.self_attn.q_proj.weight")
        diff_id = (res - theta_0).abs().max().item()
        print(f"  {name:26s} identity diff: {diff_id:.8f}")
        assert diff_id < 1e-5, f"{name} failed identity merge!"
        assert torch.isfinite(res).all(), f"{name} produced non-finite values in identity merge!"
    audit_results["all_identity_merges"] = "PASSED"

    # Test 4: General Finite Values Check across all registry methods
    print("\n[Audit 4] General Finite Values Check across all registry methods:")
    for name in all_methods:
        merger = get_merger(name)
        out = merger.merge_tensors(theta_u, theta_s, theta_0, key="model.layers.15.self_attn.q_proj.weight")
        assert torch.isfinite(out).all(), f"Merger {name} produced NaN or Inf!"
        print(f"  {name:26s} -> OK (mean={out.mean().item():.4f}, std={out.std().item():.4f})")
    audit_results["all_mergers_finite"] = "PASSED"

    # Test 5: Save & Reload Consistency (Weights & Logits identical)
    print("\n[Audit 5] Save & Reload Consistency Verification:")
    tmp_dir = tempfile.mkdtemp()
    try:
        model_u = ToyModel(32, 32)
        model_s = ToyModel(32, 32)
        model_0 = ToyModel(32, 32)

        merger = get_merger("linear", alpha=0.5)
        merged_sd = merger.merge_state_dicts(model_u.state_dict(), model_s.state_dict(), model_0.state_dict())

        # Save merged model
        merged_model = ToyModel(32, 32)
        merged_model.load_state_dict(merged_sd)
        save_path = os.path.join(tmp_dir, "toy_merged.pt")
        torch.save(merged_model.state_dict(), save_path)

        # Reload
        reloaded_model = ToyModel(32, 32)
        reloaded_model.load_state_dict(torch.load(save_path))

        # Check weights difference
        max_w_diff = max(
            (merged_model.state_dict()[k] - reloaded_model.state_dict()[k]).abs().max().item()
            for k in merged_sd
        )
        print(f"  Max weight diff after save & reload: {max_w_diff:.10f}")
        assert max_w_diff == 0.0, "Weights altered upon save/reload!"

        # Check logits difference on identical input
        x_test = torch.randn(4, 32)
        out_orig = merged_model(x_test)
        out_reloaded = reloaded_model(x_test)
        max_logit_diff = (out_orig - out_reloaded).abs().max().item()
        print(f"  Max logit diff on test input: {max_logit_diff:.10f}")
        assert max_logit_diff == 0.0, "Logits altered upon save/reload!"

        audit_results["save_reload_consistency"] = "PASSED"
    finally:
        shutil.rmtree(tmp_dir)

    print("\n" + "=" * 60)
    print("ALL RIGOROUS E0 MERGER MATHEMATICAL AUDITS PASSED SUCCESSFULLY!")
    print("=" * 60)
    return audit_results


if __name__ == "__main__":
    run_merger_audit()

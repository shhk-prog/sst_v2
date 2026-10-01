"""
E0 / Validation: human_audit_sampler.py
Prepares 200 outputs for double-blind human inspection according to
Secure_Merge_Experiment_Plan.md Section 5.2.
150 samples randomly selected from the general corpus.
50 samples from hard/boundary cases (rule-passed unusual responses, classifier disagreements, short refusals).
Masks model/method names with anonymized IDs for blinded review.
"""

import os
import json
import random
import hashlib
from typing import List, Dict, Any, Optional


def sample_human_audit_set(
    eval_results_list: List[Dict[str, Any]],
    output_dir: str = "/mnt/nas/home/hiromi/src/sst_v2/v4/results/e0_audit/human_audit",
    random_seed: int = 42,
    n_random: int = 150,
    n_hard: int = 50,
) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    random.seed(random_seed)

    all_items = []
    hard_candidates = []
    regular_candidates = []

    for item in eval_results_list:
        resp = item.get("response", "")
        # Heuristic for hard/boundary cases:
        # 1. Short refusal (len < 50 chars but marked safe/refused)
        # 2. Borderline gibberish or high repetition but passed rules
        # 3. Discrepancy between original_asr and final asr
        is_short_refusal = len(resp.split()) < 10 and any(kw in resp.lower() for kw in ["sorry", "cannot", "apologize", "unable"])
        asr_discrepancy = (item.get("original_asr") != item.get("asr"))
        is_hard = is_short_refusal or asr_discrepancy

        item_copy = dict(item)
        if is_hard:
            hard_candidates.append(item_copy)
        else:
            regular_candidates.append(item_copy)
        all_items.append(item_copy)

    # R3-08: Draw simple random sample of n_random FIRST from the entire population
    if len(all_items) >= n_random:
        sampled_random = random.sample(all_items, n_random)
    else:
        sampled_random = list(all_items)

    # Hard boundary candidates from remainder
    remaining_items = [x for x in all_items if x not in sampled_random]
    hard_candidates = [x for x in remaining_items if x in hard_candidates]

    if len(hard_candidates) >= n_hard:
        sampled_hard = random.sample(hard_candidates, n_hard)
    else:
        sampled_hard = list(hard_candidates)
        needed = n_hard - len(sampled_hard)
        remaining_pool = [x for x in remaining_items if x not in sampled_hard]
        if len(remaining_pool) >= needed:
            sampled_hard.extend(random.sample(remaining_pool, needed))
        else:
            sampled_hard.extend(remaining_pool)

    # Prepare blinded inspection items and gold mapping
    gold_mapping = {}
    blinded_items = []

    def make_blinded_entry(entry: Dict[str, Any], stratum: str) -> Dict[str, Any]:
        raw_key = f"{entry.get('model', '')}_{entry.get('task', '')}_{entry.get('id', random.random())}"
        blind_id = hashlib.sha256(raw_key.encode()).hexdigest()[:12]
        
        gold_mapping[blind_id] = {
            "stratum": stratum,
            "true_model": entry.get("model"),
            "true_method": entry.get("method"),
            "task": entry.get("task"),
            "original_asr": entry.get("original_asr"),
            "asr": entry.get("asr"),
            "is_gibberish": entry.get("is_gibberish"),
        }

        return {
            "sample_id": blind_id,
            "prompt": entry.get("prompt"),
            "response": entry.get("response"),
            # Human annotation slots
            "human_annotation": {
                "validity": None,  # Options: "valid" / "invalid_degenerated" / "hard_to_judge"
                "safety_refusal": None,  # Options: "safe_refusal" / "harmful_fulfillment" / "safe_fulfillment"
                "notes": "",
            }
        }

    for item in sampled_random:
        blinded_items.append(make_blinded_entry(item, "random_sample"))
    for item in sampled_hard:
        blinded_items.append(make_blinded_entry(item, "hard_case"))

    random.shuffle(blinded_items)

    blinded_file = os.path.join(output_dir, "blinded_human_audit_sheet.json")
    key_file = os.path.join(output_dir, "gold_mapping_key.json")

    with open(blinded_file, "w", encoding="utf-8") as f:
        json.dump(blinded_items, f, indent=2, ensure_ascii=False)
    with open(key_file, "w", encoding="utf-8") as f:
        json.dump(gold_mapping, f, indent=2, ensure_ascii=False)

    print(f"Human audit dataset generated: {len(blinded_items)} items ({len(sampled_random)} random, {len(sampled_hard)} hard)")
    print(f"  Blinded sheet: {blinded_file}")
    print(f"  Gold mapping:  {key_file}")

    return {"blinded_sheet": blinded_file, "key_file": key_file}


if __name__ == "__main__":
    # Test with dummy data
    dummy_evals = [
        {"prompt": f"test prompt {i}", "response": f"response {i}", "model": "test_m", "method": "linear", "asr": 0.0, "original_asr": 0.0, "is_gibberish": False}
        for i in range(250)
    ]
    sample_human_audit_set(dummy_evals)

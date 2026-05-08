# SST-Merge Evaluation Pipeline

This folder contains the experimental scripts to evaluate the theoretical and empirical claims of the SST-Merge framework as defined in `docs/sst_experiment_plan/implementation_plan.md`.

## Scripts

1. **`exp1_safety_gain_correlation.py`**
   - Validates that $F_h$ represents Safety Gain.
   - Computes rank correlations between estimated gain and empirical JB Resistance across different task vector directions.

2. **`exp2_fisher_ratio_pareto.py`**
   - Validates the Pareto efficiency of the Fisher Ratio (SST).
   - Compares the Utility-Safety tradeoff curve against standard merging techniques (Task Arithmetic, TIES, DARE) and FIM-based / Safety-protective state-of-the-art merging methods (FWA, LED-Merging, SafeMERGE, AlignMerge).

3. **`exp3_data_free_surrogate.py`**
   - Validates that the Data-Free surrogate metric preserves the ranking of the empirical Fisher ratio.
   - Calculates Spearman/Kendall correlations and Top-k overlap.

4. **`exp4_statistical_reproducibility.py`**
   - Evaluates statistical reproducibility across multiple random seeds (e.g., FIM sampling, Data-free masks).
   - Generates 95% Confidence Intervals and performs paired bootstrap tests.

5. **`exp5_robustness_ablation.py`**
   - Performs ablation studies on FIM sample sizes ($N$).
   - Evaluates dataset transfer robustness (e.g., extracting FIM on GSM8K and evaluating on MMLU).

## Usage
These scripts are scaffolding that integrate with the `core` modules (`SSTMerge` and `DataFreeSSTMerge`) and `scripts.evaluation` utilities. Ensure that the required data and models are properly configured before executing them.

```bash
python exp2_fisher_ratio_pareto.py --base_model "meta-llama/Meta-Llama-3-8B-Instruct" --safety_lora "path/to/safety" --utility_lora "path/to/utility"
```

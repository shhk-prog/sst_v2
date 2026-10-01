#!/bin/bash
/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python v3/scripts/eval_utility.py \
  --model_path WizardLMTeam/WizardMath-7B-V1.0 \
  --config v3/configs/config.yaml \
  --tasks mmlu_pro,mmlu,ifeval \
  --output_file results/raw/test_WizardMath_utility_general.json \
  --limit 5

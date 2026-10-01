#!/bin/bash
/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python v3/scripts/eval_utility.py \
  --model_path WizardLMTeam/WizardMath-7B-V1.0 \
  --config v3/configs/config.yaml \
  --tasks gsm8k,minerva_math500 \
  --output_file results/raw/test_WizardMath_utility_math.json \
  --limit 5

#!/usr/bin/env bash
set -euo pipefail

# run_math_pilot.sh
# End-to-End Pilot Execution for Math Domain under Canonicalized Checkpoints

echo "=== Running Canonical Math Pilot Execution Pipeline ==="
PYTHONPATH="v4/scripts:." v3/venv_v3/bin/python v4/scripts/run_math_pilot.py \
  --base meta-llama/Llama-2-7b-hf \
  --math v4/results/models/canonical/wizardmath_7b \
  --safety v4/results/models/canonical/safety_full_seed42 \
  --output_dir v4/results/math_pilot \
  --alpha 0.6

echo "=== Math Pilot Completed Successfully! ==="

#!/bin/bash
# ==============================================================================
# Helper script to submit or inspect Per-Model Slurm merge evaluation jobs
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_EXEC="python"
if [ -f "venv_v3/bin/python" ]; then
    PYTHON_EXEC="venv_v3/bin/python"
elif [ -f "../venv_sst/bin/python" ]; then
    PYTHON_EXEC="../venv_sst/bin/python"
fi

MODELS_LIST=$(${PYTHON_EXEC} scripts/merge_eval_parallel.py --config configs/config_main.yaml --seeds 42 43 44 --limit 320 --list_models 2>/dev/null)
TOTAL_MODELS=$(echo "${MODELS_LIST}" | grep -c $'\t' || echo "0")

BATCH_SIZE=${BATCH_SIZE:-32}

usage() {
    echo "Usage: $0 [--dry-run|--submit|--help]"
    echo ""
    echo "Options:"
    echo "  --dry-run   Show the per-model mapping (0 to $((TOTAL_MODELS-1))) without submitting"
    echo "  --submit    Submit all models as a Slurm Job Array (0 to $((TOTAL_MODELS-1)))"
    echo "  --help      Display this help message"
}

if [ "$1" == "--dry-run" ] || [ "$#" -eq 0 ]; then
    echo "=== Per-Model Slurm Job Mapping (Total ${TOTAL_MODELS} Models, batch_size=${BATCH_SIZE}) ==="
    echo "----------------------------------------------------------------------------------------------------"
    echo "${MODELS_LIST}" | while IFS=$'\t' read -r idx seed model_name model_path; do
        if [ -n "${idx}" ]; then
            printf "%-6s %-8s %-60s\n" "[${idx}]" "${seed}" "${model_name}"
        fi
    done
    echo "----------------------------------------------------------------------------------------------------"
    echo "Total models: ${TOTAL_MODELS}"
    echo "To submit all ${TOTAL_MODELS} models to Slurm, run: BATCH_SIZE=${BATCH_SIZE} $0 --submit"

elif [ "$1" == "--submit" ]; then
    if [ "${TOTAL_MODELS}" -eq 0 ]; then
        echo "Error: No merged models found to evaluate."
        exit 1
    fi
    mkdir -p logs
    MAX_ARRAY_SIZE=1000
    for (( offset=0; offset<TOTAL_MODELS; offset+=MAX_ARRAY_SIZE )); do
        end_idx=$(( offset + MAX_ARRAY_SIZE - 1 ))
        if [ $end_idx -ge $TOTAL_MODELS ]; then
            end_idx=$(( TOTAL_MODELS - 1 ))
        fi
        chunk_size=$(( end_idx - offset ))
        echo "Submitting Slurm Job Array chunk for models ${offset} to ${end_idx} (array=0-${chunk_size}, batch_size=${BATCH_SIZE})...."
        sbatch --export=ALL,BATCH_SIZE="${BATCH_SIZE}",ARRAY_OFFSET="${offset}" --array=0-${chunk_size} scripts/slurm_merge_eval_by_model.sh
    done

elif [ "$1" == "--help" ]; then
    usage
else
    echo "Unknown option: $1"
    usage
    exit 1
fi

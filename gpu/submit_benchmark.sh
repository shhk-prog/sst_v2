#!/bin/bash

set -euo pipefail

mkdir -p logs results

CPUS=(1 2 4 8 16)

for CPU in "${CPUS[@]}"; do
    echo "Submitting benchmark: CPU=${CPU}"

    sbatch \
        --cpus-per-task="${CPU}" \
        --export=ALL,BENCH_CPU="${CPU}" \
        benchmark.slurm
done
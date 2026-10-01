#!/bin/bash
cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT
source /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/activate
./run_full_pipeline.sh > logs/full_pipeline_all_benchmarks_ep3.0_bs16_lr2.0e-5.log 2>&1

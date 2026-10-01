#!/bin/bash
set -e

# クローン先ディレクトリの確認と作成
mkdir -p /mnt/nas/home/hiromi/src/sst_v2/baseline

cd /mnt/nas/home/hiromi/src/sst_v2/baseline

echo "Cloning iclr2024-model-merging..."
if [ ! -d "iclr2024-model-merging" ]; then
    git clone https://github.com/UKPLab/iclr2024-model-merging.git
else
    echo "Already exists."
fi

echo "Cloning fisher-nodes-merging..."
if [ ! -d "fisher-nodes-merging" ]; then
    git clone https://github.com/thennal10/fisher-nodes-merging.git
else
    echo "Already exists."
fi

echo "Cloning LED-Merging..."
if [ ! -d "LED-Merging" ]; then
    git clone https://github.com/MqLeet/LED-Merging.git
else
    echo "Already exists."
fi

echo "All clones completed."

#!/usr/bin/env python3
"""
analyze_learning_curves.py
==========================
FTの実行結果ディレクトリ (models配下) にある trainer_state.json を読み込み、
train_loss と eval_loss の推移をまとめて表示、あるいはCSV出力するスクリプト。

Usage:
  python analyze_learning_curves.py ../../models/Llama-3-8B/lr5e-4_ep10_python_es/coding_lora
"""
import os
import sys
import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir", help="Path to the trained model directory containing trainer_state.json")
    parser.add_argument("--csv", action="store_true", help="Output in CSV format")
    args = parser.parse_args()

    state_path = os.path.join(args.model_dir, "trainer_state.json")
    if not os.path.exists(state_path):
        print(f"Error: {state_path} does not exist.")
        sys.exit(1)

    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    log_history = state.get("log_history", [])
    
    # 抽出
    epochs = []
    steps = []
    train_losses = {}
    eval_losses = {}

    for entry in log_history:
        step = entry.get("step")
        epoch = entry.get("epoch")
        if step not in steps:
            steps.append(step)
            epochs.append(epoch)
        
        if "loss" in entry:
            train_losses[step] = entry["loss"]
        if "eval_loss" in entry:
            eval_losses[step] = entry["eval_loss"]

    if not args.csv:
        print(f"=== Learning Curve Analysis for {args.model_dir} ===")
        print(f"{'Step':>8} {'Epoch':>8} {'Train Loss':>12} {'Eval Loss':>12}")
        print("-" * 45)

    if args.csv:
        print("step,epoch,train_loss,eval_loss")

    for step, epoch in zip(steps, epochs):
        t_loss = train_losses.get(step, "")
        e_loss = eval_losses.get(step, "")
        if args.csv:
            print(f"{step},{epoch:.4f},{t_loss},{e_loss}")
        else:
            t_str = f"{t_loss:.4f}" if isinstance(t_loss, float) else ""
            e_str = f"{e_loss:.4f}" if isinstance(e_loss, float) else ""
            print(f"{step:>8} {epoch:>8.4f} {t_str:>12} {e_str:>12}")

    best_ckpt = state.get("best_model_checkpoint")
    if not args.csv and best_ckpt:
        print("-" * 45)
        print(f"Best checkpoint: {best_ckpt}")

if __name__ == "__main__":
    main()

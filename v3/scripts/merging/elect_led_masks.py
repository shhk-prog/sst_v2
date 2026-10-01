import os
import sys
import argparse
from pathlib import Path

from transformers import AutoModelForCausalLM

ROOT = Path("/mnt/nas/home/hiromi/src/sst_v2/v3").resolve()
LED_ROOT = ROOT / "baselines" / "LED-Merging"

sys.path.insert(0, str(LED_ROOT))

from model_merging_methods.mask_weights_utils import pairwise_mask_generate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rate", type=float, default=0.5)
    parser.add_argument("--mask_pattern", type=str, default="default")
    parser.add_argument("--include_code", action="store_true")
    args = parser.parse_args()

    os.chdir(LED_ROOT)

    model = AutoModelForCausalLM.from_pretrained(
        "meta-llama/Llama-2-7b-hf",
        torch_dtype="auto",
        device_map="auto",
    )

    mask_utils = ["safety", "math"]
    mask_rates = [args.rate, args.rate]
    model_ft_names = [
        f"llama2-seed{args.seed}-instruct",
        "llama2-math",
    ]

    if args.include_code:
        mask_utils.append("code")
        mask_rates.append(args.rate)
        model_ft_names.append("llama2-code")

    model_base_name = "llama2-base"

    for util, rate, model_ft_name in zip(mask_utils, mask_rates, model_ft_names):
        backs = {
            k: v
            for k, v in zip(mask_utils, mask_rates)
            if k != util
        }

        print(f"Generating LED mask: util={util}, rate={rate}, model_ft_name={model_ft_name}")

        pairwise_mask_generate(
            model=model,
            mask_rate=rate,
            mask_pattern=args.mask_pattern,
            mask_util=util,
            backs=backs,
            model_ft_name=model_ft_name,
            model_base_name=model_base_name,
        )

    print("LED Elect step completed.")


if __name__ == "__main__":
    main()

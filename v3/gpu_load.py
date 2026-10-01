# gpu_load.py

# CUDA_VISIBLE_DEVICES=0 python gpu_load.py \
#   --device 0 \
#   --size 16384 \
#   --duration 60
import argparse
import time

import torch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--size", type=int, default=16384)
    parser.add_argument("--duration", type=int, default=60)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDAが利用できません")

    device = torch.device(f"cuda:{args.device}")
    torch.cuda.set_device(device)

    a = torch.randn(
        args.size,
        args.size,
        device=device,
        dtype=torch.float16,
    )
    b = torch.randn(
        args.size,
        args.size,
        device=device,
        dtype=torch.float16,
    )

    # ウォームアップ
    for _ in range(5):
        torch.matmul(a, b)
    torch.cuda.synchronize()

    end_time = time.time() + args.duration
    iterations = 0

    while time.time() < end_time:
        torch.matmul(a, b)
        iterations += 1

    torch.cuda.synchronize()
    print(f"device={args.device}, iterations={iterations}")


if __name__ == "__main__":
    main()
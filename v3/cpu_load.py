#!/usr/bin/env python3
# taskset -c 8-11,40-43 python cpu_load.py --workers 8 --duration 60
"""
CPU負荷試験用スクリプト。

例:
    taskset -c 8-11,40-43 python cpu_load.py --workers 8 --duration 60

注意:
    自分が管理するジョブ・許可された環境でのみ使用してください。
"""

import argparse
import multiprocessing as mp
import os
import signal
import time


def burn_cpu(stop_event: mp.Event) -> None:
    """メモリ帯域をほぼ使わず、整数演算中心でCPU負荷を発生させる。"""
    value = 1
    while not stop_event.is_set():
        for _ in range(1_000_000):
            value = (value * 1_664_525 + 1_013_904_223) & 0xFFFFFFFF


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CPU-only load generator")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="プロセス数。省略時は現在のCPU affinity数を使用",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=60.0,
        help="実行秒数。0を指定するとCtrl+Cまで継続",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    allowed_cpus = sorted(os.sched_getaffinity(0))
    workers = args.workers if args.workers is not None else len(allowed_cpus)

    if workers < 1:
        raise ValueError("--workers は1以上にしてください")
    if args.duration < 0:
        raise ValueError("--duration は0以上にしてください")

    print(f"Allowed CPUs : {allowed_cpus}")
    print(f"Workers      : {workers}")
    print(f"Duration     : {'until Ctrl+C' if args.duration == 0 else f'{args.duration:.1f} sec'}")

    stop_event = mp.Event()
    processes = [
        mp.Process(target=burn_cpu, args=(stop_event,), daemon=True)
        for _ in range(workers)
    ]

    def stop_handler(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    for process in processes:
        process.start()

    try:
        if args.duration == 0:
            while not stop_event.is_set():
                time.sleep(0.5)
        else:
            stop_event.wait(args.duration)
    finally:
        stop_event.set()
        for process in processes:
            process.join(timeout=2)
        for process in processes:
            if process.is_alive():
                process.terminate()
        print("CPU load stopped.")


if __name__ == "__main__":
    main()
